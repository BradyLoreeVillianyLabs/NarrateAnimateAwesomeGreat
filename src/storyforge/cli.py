from pathlib import Path
import argparse, json, shutil
from dataclasses import asdict
from .planner import plan
from .prompts import export_prompts
from .render import render
from .upscale import upscale
from .generate import generate_project
from .config import Settings, masked_provider_status
from .director import inspect_project, estimate_project, write_director_plan
from .flow_export import export_flow_packets


def parse_scene_ids(value: str | None):
    if not value:
        return None
    return {int(x.strip()) for x in value.split(',') if x.strip()}


def main():
    ap = argparse.ArgumentParser(prog='storyforge')
    sp = ap.add_subparsers(dest='cmd', required=True)
    sp.add_parser('doctor')
    sp.add_parser('providers')

    p = sp.add_parser('init'); p.add_argument('project')
    p = sp.add_parser('plan'); p.add_argument('project'); p.add_argument('--whisper', action='store_true')
    p = sp.add_parser('validate'); p.add_argument('project')
    p = sp.add_parser('director'); p.add_argument('project'); p.add_argument('--cloud-first', action='store_true')
    p = sp.add_parser('cost'); p.add_argument('project'); p.add_argument('--cloud-first', action='store_true')
    p = sp.add_parser('prompts'); p.add_argument('project')
    p = sp.add_parser('flow-pack'); p.add_argument('project')
    p = sp.add_parser('generate')
    p.add_argument('project')
    p.add_argument('--provider', choices=['flow','manual','veo','runway'], default=None)
    p.add_argument('--scenes', help='Comma-separated scene IDs, e.g. 1,4,7')
    p.add_argument('--dry-run', action='store_true')
    p = sp.add_parser('render'); p.add_argument('project'); p.add_argument('--no-captions', action='store_true')
    p = sp.add_parser('upscale'); p.add_argument('project'); p.add_argument('--scale', type=int, choices=[2,3,4], default=2)

    a = ap.parse_args()
    if a.cmd == 'doctor':
        for n in ['ffmpeg','ffprobe','nvidia-smi','realesrgan-ncnn-vulkan']:
            print(f'{n:24}', shutil.which(n) or 'not found / optional')
        print('providers               ', json.dumps(masked_provider_status()))
    elif a.cmd == 'providers':
        print(json.dumps(masked_provider_status(), indent=2))
    elif a.cmd == 'init':
        q = Path(a.project)
        [(q/d).mkdir(parents=True, exist_ok=True) for d in ['keyframes','generated','music','sfx','work','output','work/reviews']]
        if not (q/'story.txt').exists():
            (q/'story.txt').write_text('Paste your story here.\n', encoding='utf-8')
    elif a.cmd == 'plan':
        plan(Path(a.project), a.whisper)
    elif a.cmd == 'validate':
        result = inspect_project(Path(a.project))
        print(json.dumps(asdict(result), indent=2))
        if not result.valid:
            raise SystemExit(2)
    elif a.cmd == 'director':
        out = write_director_plan(Path(a.project), prefer_local=not a.cloud_first)
        print(out)
    elif a.cmd == 'cost':
        print(json.dumps(estimate_project(Path(a.project), prefer_local=not a.cloud_first), indent=2))
    elif a.cmd == 'prompts':
        export_prompts(Path(a.project))
    elif a.cmd == 'flow-pack':
        print(json.dumps(export_flow_packets(Path(a.project)), indent=2))
    elif a.cmd == 'generate':
        provider = a.provider or Settings.from_env().default_provider
        print(json.dumps(generate_project(Path(a.project), provider, parse_scene_ids(a.scenes), a.dry_run), indent=2, default=str))
    elif a.cmd == 'render':
        render(Path(a.project), not a.no_captions)
    elif a.cmd == 'upscale':
        upscale(Path(a.project), a.scale)


if __name__ == '__main__':
    main()
