from pathlib import Path
import shutil
from .util import load_json,run,require_binary

def render(project,captions=True):
    project=Path(project); require_binary('ffmpeg'); require_binary('ffprobe'); m=load_json(project/'work'/'manifest.json'); w,h=m.get('resolution',[1920,1080]); fps=m.get('fps',30); work=project/'work'/'renders'; work.mkdir(parents=True,exist_ok=True); clips=[]
    for s in m['scenes']:
        out=work/f"scene_{s['id']:03}.mp4"; gen=project/s['generated_video']; key=project/s['keyframe'] if s.get('keyframe') else None; dur=s['duration']
        if gen.exists(): run(['ffmpeg','-y','-stream_loop','-1','-i',gen,'-t',dur,'-vf',f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p','-an','-c:v','libx264','-crf','18',out])
        elif key and key.exists(): run(['ffmpeg','-y','-loop','1','-i',key,'-t',dur,'-vf',f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={max(1,int(dur*fps))}:s={w}x{h}:fps={fps},format=yuv420p",'-an','-c:v','libx264','-crf','18',out])
        else: run(['ffmpeg','-y','-f','lavfi','-i',f'color=c=black:s={w}x{h}:r={fps}','-t',dur,'-an','-c:v','libx264','-pix_fmt','yuv420p',out])
        clips.append(out)
    concat=work/'concat.txt'; concat.write_text('\n'.join(f"file '{p.resolve().as_posix()}'" for p in clips),encoding='utf-8'); visual=work/'visual.mp4'; run(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c','copy',visual]); output=project/'output'/'youtube_master.mp4'; output.parent.mkdir(parents=True,exist_ok=True); narration=project/m['narration']; codec='h264_nvenc' if shutil.which('nvidia-smi') else 'libx264'; run(['ffmpeg','-y','-i',visual,'-i',narration,'-map','0:v','-map','1:a','-c:v',codec,'-c:a','aac','-b:a','192k','-movflags','+faststart','-shortest',output]); print(f'Created: {output}'); return output
