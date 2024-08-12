from moviepy.editor import *
from moviepy.editor import VideoFileClip
from pathlib import Path
import os
import pydub
from pydub import AudioSegment
folder_path= str(Path(__file__).parent)
def main():
    input_file_video ='/home/viet/workspace/AI_SERVER_VDH/utils/videoprocessing/processedvideo_0001_00010.mp4'
    input_file_audio = '/home/viet/workspace/AI_SERVER_VDH/utils/videoprocessing/audio_0001_00014.mp3'
    cut_video_focus_audio(input_file_video =input_file_video, input_file_audio = input_file_audio , output_file = input_file_video)
def cut_video_focus_audio(input_file_video, input_file_audio, output_file):
    duration_audio = get_audio_duration(input_file_audio)
    print(duration_audio)
    cut_video(input_file = input_file_video, output_file = output_file, start_time=0, end_time = duration_audio)
    print("cut_video_foc_audio success")

def cut_video(input_file, output_file, start_time, end_time):
    """
    Cut a video from start_time to end_time and save the result to output_file.

    Parameters:
    input_file (str): Path to the input video file.
    output_file (str): Path to save the output video file.
    start_time (float): Start time in seconds.
    end_time (float): End time in seconds.
    """
    with VideoFileClip(input_file) as video:
        print(video.duration, type(video.duration))
        if video.duration < end_time:
            print("time video ngan hon audio")
            return
        else:
            cut_video = video.subclip(start_time, end_time)
            cut_video.write_videofile(output_file,codec='libx264')
            # cut_video.write_videofile(output_file)
            print("cutting video success")

def get_audio_duration(file_path):
    audio = AudioSegment.from_file(file_path)
    duration = len(audio) / 1000.0  # duration in seconds
    return duration

def concatenateWarning(video_path: str, output_path:str):
    path_clip_warning = os.path.join(folder_path,'warning_fullhd.mp4')
    clip = VideoFileClip(video_path)
    clip_warning = VideoFileClip(path_clip_warning)
    clip_warning_resize = clip_warning.resize( (clip.w,clip.h) )
    final = concatenate_videoclips([clip_warning_resize, clip, clip_warning_resize])
    final.write_videofile(output_path)


if __name__ == "__main__":
    main()
