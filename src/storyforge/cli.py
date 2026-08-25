from pathlib import Path
import argparse,shutil
from .planner import plan
from .prompts import export_prompts
from .render import render
from .upscale import upscale

def main():
    ap=argparse.ArgumentParser(prog='storyforge'); sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('doctor')
    p=sp.add_parser('init'); p.add_argument('project')
    p=sp.add_parser('plan'); p.add_argument('project'); p.add_argument('--whisper',action='store_true')
    p=sp.add_parser('prompts'); p.add_argument('project')
    p=sp.add_parser('render'); p.add_argument('project'); p.add_argument('--no-captions',action='store_true')
    p=sp.add_parser('upscale'); p.add_argument('project'); p.add_argument('--scale',type=int,choices=[2,3,4],default=2)
    a=ap.parse_args()
    if a.cmd=='doctor':
        for n in ['ffmpeg','ffprobe','nvidia-smi','realesrgan-ncnn-vulkan']: print(f'{n:24}',shutil.which(n) or 'not found / optional')
    elif a.cmd=='init':
        q=Path(a.project); [ (q/d).mkdir(parents=True,exist_ok=True) for d in ['keyframes','generated','music','sfx','work','output'] ]; (q/'story.txt').write_text('Paste your story here.\n',encoding='utf-8') if not (q/'story.txt').exists() else None
    elif a.cmd=='plan': plan(Path(a.project),a.whisper)
    elif a.cmd=='prompts': export_prompts(Path(a.project))
    elif a.cmd=='render': render(Path(a.project),not a.no_captions)
    elif a.cmd=='upscale': upscale(Path(a.project),a.scale)
if __name__=='__main__': main()
