from pathlib import Path
import shutil

from .util import load_json, run, require_binary


def _subtitle_filter(path: Path) -> str:
    value = str(path.resolve()).replace("\\", "/")
    value = value.replace(":", r"\:").replace("'", r"\'")
    return f"subtitles='{value}':force_style='FontSize=26,Outline=2,Shadow=1,MarginV=48'"


def _render_generated(src: Path, out: Path, duration: float, w: int, h: int, fps: int):
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-stream_loop", "-1", "-i", src,
        "-t", f"{duration:.3f}", "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", out,
    ])


def _render_keyframe(src: Path, out: Path, duration: float, w: int, h: int, fps: int, motion: str):
    frames = max(1, int(round(duration * fps)))
    if motion == "push_out":
        z = "if(eq(on,1),1.12,max(1.0,zoom-0.0008))"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z = "1.08"
        x, y = f"(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z = "1.08"
        x, y = f"(iw-iw/zoom)*(on/{frames})", "ih/2-(ih/zoom/2)"
    else:
        z = "min(zoom+0.0008,1.12)"
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    vf = (
        f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,"
        f"crop={w*2}:{h*2},"
        f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},"
        "format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", src,
        "-t", f"{duration:.3f}", "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", out,
    ])


def _render_blank(out: Path, duration: float, w: int, h: int, fps: int):
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}",
        "-t", f"{duration:.3f}", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", out,
    ])


def _first_audio(directory: Path) -> Path | None:
    if not directory.exists():
        return None
    allowed = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
    return next((p for p in sorted(directory.iterdir()) if p.is_file() and p.suffix.lower() in allowed), None)


def _scene_sfx(project: Path, scene_id: int) -> list[Path]:
    directory = project / "sfx"
    if not directory.exists():
        return []
    prefix = f"{scene_id:03}"
    allowed = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
    return [p for p in sorted(directory.iterdir()) if p.is_file() and p.name.startswith(prefix) and p.suffix.lower() in allowed]


def render(project, captions=True):
    project = Path(project)
    require_binary("ffmpeg")
    require_binary("ffprobe")
    manifest = load_json(project / "work" / "manifest.json")
    w, h = manifest.get("resolution", [1920, 1080])
    fps = int(manifest.get("fps", 30))
    work = project / "work" / "renders"
    work.mkdir(parents=True, exist_ok=True)

    clips = []
    for scene in manifest.get("scenes", []):
        sid = int(scene["id"])
        duration = max(0.1, float(scene.get("duration", 0.1)))
        out = work / f"scene_{sid:03}.mp4"
        generated = project / str(scene.get("generated_video", ""))
        keyframe = project / str(scene.get("keyframe", "")) if scene.get("keyframe") else None
        if generated.is_file():
            _render_generated(generated, out, duration, w, h, fps)
        elif keyframe and keyframe.is_file():
            _render_keyframe(keyframe, out, duration, w, h, fps, str(scene.get("motion", "push_in")))
        else:
            _render_blank(out, duration, w, h, fps)
        clips.append(out)

    if not clips:
        raise RuntimeError("Manifest contains no scenes to render")

    concat = work / "concat.txt"
    concat.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in clips), encoding="utf-8")
    visual = work / "visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", visual])

    narration = project / manifest["narration"]
    if not narration.is_file():
        raise FileNotFoundError(f"Narration missing: {narration}")

    inputs = ["-i", visual, "-i", narration]
    audio_filters = ["[1:a]volume=1.0[narr]"]
    mix_labels = ["[narr]"]
    next_input = 2

    music = _first_audio(project / "music")
    if music:
        inputs += ["-stream_loop", "-1", "-i", music]
        audio_filters.append(f"[{next_input}:a]volume=0.10[music]")
        mix_labels.append("[music]")
        next_input += 1

    for scene in manifest.get("scenes", []):
        start_ms = int(round(float(scene.get("start", 0.0)) * 1000))
        for effect in _scene_sfx(project, int(scene["id"])):
            label = f"sfx{next_input}"
            inputs += ["-i", effect]
            audio_filters.append(
                f"[{next_input}:a]volume=0.45,adelay={start_ms}|{start_ms}[{label}]"
            )
            mix_labels.append(f"[{label}]")
            next_input += 1

    if len(mix_labels) == 1:
        audio_filters.append("[narr]anull[aout]")
    else:
        audio_filters.append(
            "".join(mix_labels) + f"amix=inputs={len(mix_labels)}:duration=first:normalize=0[aout]"
        )

    output = project / "output" / "youtube_master.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    codec = "h264_nvenc" if shutil.which("nvidia-smi") else "libx264"
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", ";".join(audio_filters),
        "-map", "0:v:0", "-map", "[aout]",
    ]

    subtitle = project / "work" / "subtitles.srt"
    if captions and subtitle.is_file():
        cmd += ["-vf", _subtitle_filter(subtitle)]

    if codec == "h264_nvenc":
        cmd += ["-c:v", codec, "-preset", "p5", "-cq", "19"]
    else:
        cmd += ["-c:v", codec, "-preset", "medium", "-crf", "18"]
    cmd += [
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-shortest", output,
    ]
    run(cmd)
    print(f"Created: {output}")
    return output
