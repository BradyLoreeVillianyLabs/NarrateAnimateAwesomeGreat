from pathlib import Path
import re
from .util import ffprobe_duration,find_narration,list_keyframes,save_json,seconds_to_srt

def sentence_split(text): return [p.strip() for p in re.split(r'(?<=[.!?])\s+',re.sub(r'\s+',' ',text.strip())) if p.strip()]
def group_sentences(sentences,target_words=28):
    groups=[]; buf=[]; count=0
    for s in sentences:
        wc=len(s.split())
        if buf and count+wc>target_words: groups.append(' '.join(buf)); buf=[]; count=0
        buf.append(s); count+=wc
    if buf: groups.append(' '.join(buf))
    return groups

def plan(project,use_whisper=False):
    project=Path(project); text=(project/'story.txt').read_text(encoding='utf-8'); narration=find_narration(project); duration=ffprobe_duration(narration)
    groups=group_sentences(sentence_split(text)); weights=[max(1,len(g.split())) for g in groups]; total=sum(weights); cursor=0.; keys=list_keyframes(project); scenes=[]
    for i,(g,w) in enumerate(zip(groups,weights),1):
        end=duration if i==len(groups) else cursor+duration*w/total; key=None
        if keys: key=keys[min(len(keys)-1,int((i-1)*len(keys)/max(1,len(groups))))].relative_to(project).as_posix()
        scenes.append({'id':i,'start':round(cursor,3),'end':round(end,3),'duration':round(end-cursor,3),'text':g,'keyframe':key,'generated_video':f'generated/scene_{i:03}.mp4','motion':['push_in','pan_left','push_out','pan_right'][(i-1)%4],'importance':0.5}); cursor=end
    manifest={'version':1,'title':project.name.replace('-',' ').title(),'narration':narration.relative_to(project).as_posix(),'duration':round(duration,3),'resolution':[1920,1080],'fps':30,'scenes':scenes}
    save_json(project/'work'/'manifest.json',manifest); out=project/'work'/'subtitles.srt'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text('\n'.join(f"{s['id']}\n{seconds_to_srt(s['start'])} --> {seconds_to_srt(s['end'])}\n{s['text']}\n" for s in scenes),encoding='utf-8'); return manifest
