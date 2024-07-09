from moviepy.editor import *
from pathlib import Path
import os

folder_path= str(Path(__file__).parent)

def concatenateWarning(video_path: str, output_path:str):
    path_clip_warning = os.path.join(folder_path,'warning_fullhd.mp4')
    clip = VideoFileClip(video_path)
    clip_warning = VideoFileClip(path_clip_warning)
    clip_warning_resize = clip_warning.resize( (clip.w,clip.h) )
    final = concatenate_videoclips([clip_warning_resize, clip, clip_warning_resize])
    final.write_videofile(output_path)