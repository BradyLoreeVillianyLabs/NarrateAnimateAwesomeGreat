from pathlib import Path
import shutil
from .util import run,require_binary

def upscale(project,scale=2):
    project=Path(project); require_binary('ffmpeg'); exe=shutil.which('realesrgan-ncnn-vulkan') or shutil.which('realesrgan-ncnn-vulkan.exe')
    if not exe: raise RuntimeError('realesrgan-ncnn-vulkan not found on PATH')
    src=project/'output'/'youtube_master.mp4'; frames=project/'work'/'upscale_frames'; enhanced=project/'work'/'upscale_enhanced'; frames.mkdir(parents=True,exist_ok=True); enhanced.mkdir(parents=True,exist_ok=True)
    run(['ffmpeg','-y','-i',src,frames/'%08d.png']); run([exe,'-i',frames,'-o',enhanced,'-n','realesr-animevideov3','-s',scale,'-t','256','-f','png']); dst=project/'output'/f'youtube_master_upscaled_{scale}x.mp4'; run(['ffmpeg','-y','-framerate','30','-i',enhanced/'%08d.png','-i',src,'-map','0:v','-map','1:a?','-c:v','h264_nvenc' if shutil.which('nvidia-smi') else 'libx264','-c:a','copy','-pix_fmt','yuv420p',dst]); return dst
