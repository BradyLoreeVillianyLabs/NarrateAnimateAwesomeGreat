from pathlib import Path
import json, subprocess, shutil, re

AUDIO_EXTS={'.wav','.mp3','.m4a','.aac','.flac','.ogg'}
IMAGE_EXTS={'.png','.jpg','.jpeg','.webp'}

def run(cmd,check=True):
    print('+',' '.join(str(x) for x in cmd)); return subprocess.run([str(x) for x in cmd],check=check)
def capture(cmd): return subprocess.check_output([str(x) for x in cmd],text=True).strip()
def ffprobe_duration(path):
    return float(capture(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',path]))
def require_binary(name):
    p=shutil.which(name)
    if not p: raise RuntimeError(f'Required executable not found on PATH: {name}')
    return p
def save_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def natural_key(p): return [int(x) if x.isdigit() else x.lower() for x in re.split(r'(\d+)',Path(p).name)]
def find_narration(project):
    c=[p for p in Path(project).iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTS and p.stem.lower().startswith('narration')]
    if not c: raise FileNotFoundError('No narration.wav/mp3/m4a/etc found in project root.')
    return sorted(c,key=natural_key)[0]
def list_keyframes(project):
    d=Path(project)/'keyframes'; return sorted([p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS],key=natural_key) if d.exists() else []
def seconds_to_srt(t):
    ms=int(round(max(0,t)*1000)); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000); return f'{h:02}:{m:02}:{s:02},{ms:03}'
