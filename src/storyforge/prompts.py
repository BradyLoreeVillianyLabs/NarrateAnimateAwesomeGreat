from pathlib import Path
import csv
from .util import load_json
BASE='''Image-to-video task for a children's illustrated story.\n\nPreserve the supplied keyframe character identity, clothing, proportions, environment, props, palette, lighting and illustration style.\n\nAnimate this moment:\n{scene_text}\n\nUse subtle natural character and environmental motion plus gentle cinematic camera movement. No scene cuts, embedded text, morphing, costume changes, duplicated limbs, or unnecessary new characters.\n\nTarget duration: approximately {duration:.1f} seconds.\n'''
def export_prompts(project):
    project=Path(project); m=load_json(project/'work'/'manifest.json'); out=project/'work'/'prompts'; out.mkdir(parents=True,exist_ok=True); rows=[]
    for s in m['scenes']:
        p=out/f"scene_{s['id']:03}.txt"; p.write_text(BASE.format(scene_text=s['text'],duration=s['duration']),encoding='utf-8'); rows.append({'scene':s['id'],'start':s['start'],'duration':s['duration'],'keyframe':s.get('keyframe') or '','prompt':p.relative_to(project).as_posix(),'output':s['generated_video']})
    with (project/'work'/'generation_queue.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
