from pathlib import Path
import re
from .util import ffprobe_duration, find_narration, list_keyframes, save_json, seconds_to_srt


def sentence_split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def group_sentences(sentences: list[str], target_words: int = 28) -> list[str]:
    groups: list[str] = []
    buf: list[str] = []
    count = 0
    for sentence in sentences:
        wc = len(sentence.split())
        if buf and count + wc > target_words:
            groups.append(" ".join(buf))
            buf, count = [], 0
        buf.append(sentence)
        count += wc
    if buf:
        groups.append(" ".join(buf))
    return groups


def _proportional_rows(groups: list[str], duration: float) -> list[tuple[float, float, str]]:
    weights = [max(1, len(g.split())) for g in groups]
    total = sum(weights)
    cursor = 0.0
    rows = []
    for i, (group, weight) in enumerate(zip(groups, weights), 1):
        end = duration if i == len(groups) else cursor + duration * weight / total
        rows.append((cursor, end, group))
        cursor = end
    return rows


def _whisper_rows(groups: list[str], narration: Path) -> tuple[list[tuple[float, float, str]], list[dict]]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install Whisper support with: pip install -e '.[whisper]'") from exc

    # Practical default for an 8 GB NVIDIA card. The model can be overridden later
    # without changing the manifest contract.
    model = WhisperModel("small", device="cuda", compute_type="int8_float16")
    segments_iter, _info = model.transcribe(
        str(narration), word_timestamps=True, vad_filter=True, beam_size=5
    )
    segments = list(segments_iter)
    if not segments:
        raise RuntimeError("Whisper found no speech in narration")

    speech = [(float(s.start), float(s.end), s.text.strip()) for s in segments]
    total_spoken = max(1, sum(len(text.split()) for _, _, text in speech))
    total_story = max(1, sum(len(group.split()) for group in groups))

    rows: list[tuple[float, float, str]] = []
    group_index = 0
    for start, end, spoken in speech:
        if group_index >= len(groups):
            break
        desired = max(1, round((len(spoken.split()) / total_spoken) * total_story))
        chosen: list[str] = []
        words = 0
        while group_index < len(groups) and (words < desired or not chosen):
            chosen.append(groups[group_index])
            words += len(groups[group_index].split())
            group_index += 1
        rows.append((start, end, " ".join(chosen)))

    if group_index < len(groups):
        tail = " ".join(groups[group_index:])
        if rows:
            start, end, text = rows[-1]
            rows[-1] = (start, end, (text + " " + tail).strip())
        else:
            rows.append((0.0, ffprobe_duration(narration), tail))

    words = []
    for segment in segments:
        for word in segment.words or []:
            words.append({
                "start": round(float(word.start), 3),
                "end": round(float(word.end), 3),
                "word": word.word.strip(),
            })
    return rows, words


def _assign_assets(project: Path, rows: list[tuple[float, float, str]]) -> list[dict]:
    keys = list_keyframes(project)
    motions = ["push_in", "pan_left", "push_out", "pan_right"]
    scenes = []
    for i, (start, end, text) in enumerate(rows, 1):
        key = None
        if keys:
            pos = min(len(keys) - 1, int((i - 1) * len(keys) / max(1, len(rows))))
            key = keys[pos].relative_to(project).as_posix()
        scenes.append({
            "id": i,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(max(0.1, end - start), 3),
            "text": text,
            "keyframe": key,
            "generated_video": f"generated/scene_{i:03}.mp4",
            "motion": motions[(i - 1) % len(motions)],
            "importance": 0.5,
        })
    return scenes


def plan(project, use_whisper: bool = False):
    project = Path(project)
    story_file = project / "story.txt"
    if not story_file.exists():
        raise FileNotFoundError("story.txt not found")
    text = story_file.read_text(encoding="utf-8")
    groups = group_sentences(sentence_split(text))
    if not groups:
        raise ValueError("story.txt is empty")

    narration = find_narration(project)
    duration = ffprobe_duration(narration)
    if duration <= 0:
        raise ValueError("Narration duration must be greater than zero")

    if use_whisper:
        rows, words = _whisper_rows(groups, narration)
    else:
        rows = _proportional_rows(groups, duration)
        words = None

    scenes = _assign_assets(project, rows)
    manifest = {
        "version": 2,
        "title": project.name.replace("-", " ").title(),
        "narration": narration.relative_to(project).as_posix(),
        "duration": round(duration, 3),
        "resolution": [1920, 1080],
        "fps": 30,
        "scenes": scenes,
        "words": words,
        "alignment": "faster-whisper" if use_whisper else "proportional",
    }
    save_json(project / "work" / "manifest.json", manifest)

    subtitles = project / "work" / "subtitles.srt"
    subtitles.parent.mkdir(parents=True, exist_ok=True)
    subtitles.write_text(
        "\n".join(
            f"{s['id']}\n{seconds_to_srt(s['start'])} --> {seconds_to_srt(s['end'])}\n{s['text']}\n"
            for s in scenes
        ),
        encoding="utf-8",
    )
    return manifest
