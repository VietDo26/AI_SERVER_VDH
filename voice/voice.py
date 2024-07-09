import requests  # Used for making HTTP requests
import json  # Used for working with JSON data
import sys
from pathlib import Path
import os
import typing
from typing import Iterator, Optional, Union

from elevenlabs import play
from elevenlabs.client import ElevenLabs
from moviepy.editor import VideoFileClip, AudioFileClip

sys.path.append(str(Path(__file__).parent.parent))
PARENT_PATH = str(Path(__file__).parent)

# key = '33828ef4c5e064103aba7abdbad41b05'
# 33828ef4c5e064103aba7abdbad41b05
KEY = '33828ef4c5e064103aba7abdbad41b05'
def main():
    client = ElevenLabs(
        api_key=KEY,
    )
    response = client.voices.get_all()
    print(len(response.voices))
    # voice = client.clone(
    #     name="Ronaldo",
    #     files=["./ronaldo_speake.mp3"],
    # )
    
    # files = ["./ronaldo_speake.mp3"]
    # add_voice_response =client.voices.add(
    #     name="CR7",
    #     files = [open(file, "rb") for file in files]
    # )    

    # print(PARENT_PATH)
    

    # convert_audio_of_video(api_key=KEY, voice_id=add_voice_response.voice_id, video_file_path="/home/viet/workspace/AI_SERVER_VDH/voice/video_30s.mp4", output_path_video="./test_output.mp4")
    # os.remove('/home/viet/workspace/AI_SERVER_VDH/voice/temp.mp3')
    # create_video_with_voice_cloning(user_id=str('123'), files= ["abc"], video_file_path= "/home/viet/workspace/AI_SERVER_VDH/media/user_id_0123/00005/targetvideo_0123_00005.mp4",output_path_video='./videotest.mp4')

    

def create_video_with_voice_cloning(user_id:int ,files: typing.List[str], video_file_path:str , output_path_video:str):
    client = ElevenLabs(
        api_key=KEY,
    )
    add_voice_response =client.voices.add(
        name= user_id,
        files = [open(file, "rb") for file in files]
    )

    convert_audio_of_video(api_key=KEY,voice_id=add_voice_response.voice_id, video_file_path=video_file_path, output_path_video=output_path_video)    
    

def exchange_audio_of_video(video_path:str, audio_path:str, output_filename:str):
    # Define the paths to your video and audio files
    video_path = video_path
    audio_path = audio_path

    # Load the video clip
    video_clip = VideoFileClip(video_path)

    # Load the audio clip
    audio_clip = AudioFileClip(audio_path)

    # Ensure the audio clip duration is at least as long as the video clip
    if audio_clip.duration < video_clip.duration:
        print(f"Warning: Audio clip is shorter than video clip. It will be looped.")
        # Loop the audio clip to match the video duration
        audio_clip = audio_clip.set_duration(video_clip.duration)

    # Set the new audio track for the video clip
    new_video_clip = video_clip.set_audio(audio_clip)

    # Define the output filename (optional, change if needed)
    output_filename = output_filename

    # Write the new video with the replaced audio track
    new_video_clip.write_videofile(output_filename)

    # Print success message
    print(f"Video audio successfully replaced. Output file: {output_filename}")

# def convert_audio_of_video(api_key:str, voice_id:str, audio_file_path:str, output_path_video:str ):
#     # Define constants for the script
#     CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
#     XI_API_KEY = api_key # Your API key for authentication
#     VOICE_ID = voice_id  # ID of the voice model to use
#     AUDIO_FILE_PATH = audio_file_path  # Path to the input audio file
#     # OUTPUT_PATH = output_path  # Path to save the output audio file
#     OUTPUT_PATH = os.path.join(PARENT_PATH,'temp.mp3')
#     # Construct the URL for the Speech-to-Speech API request
#     sts_url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}/stream"

#     # Set up headers for the API request, including the API key for authentication
#     headers = {
#         "Accept": "application/json",
#         "xi-api-key": XI_API_KEY
#     }

#     # Set up the data payload for the API request, including model ID and voice settings
#     # Note: voice settings are converted to a JSON string
#     data = {
#         "model_id": "eleven_english_sts_v2",
#         "voice_settings": json.dumps({
#             "stability": 0.5,
#             "similarity_boost": 0.8,
#             "style": 0.0,
#             "use_speaker_boost": True
#         })
#     }

#     # Set up the files to send with the request, including the input audio file
#     files = {
#         "audio": open(AUDIO_FILE_PATH, "rb")
#     }

#     # Make the POST request to the STS API with headers, data, and files, enabling streaming response
#     response = requests.post(sts_url, headers=headers, data=data, files=files, stream=True)

#     # Check if the request was successful
#     if response.ok:
#         # Open the output file in write-binary mode
#         with open(OUTPUT_PATH, "wb") as f:
#             # Read the response in chunks and write to the file
#             for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
#                 f.write(chunk)
#         # Inform the user of success
#         print("Audio stream saved successfully.")
#     else:
#         # Print the error message if the request was not successful
#         print(response.text)

#     exchange_audio_of_video(video_path=audio_file_path, audio_path=OUTPUT_PATH , output_filename = output_path_video)
#     os.remove(OUTPUT_PATH)
def convert_audio_of_video(api_key:str, voice_id:str, video_file_path:str, output_path_video:str ):
    # Define constants for the script
    CHUNK_SIZE = 1024  # Size of chunks to read/write at a time
    XI_API_KEY = api_key # Your API key for authentication
    VOICE_ID = voice_id  # ID of the voice model to use
    AUDIO_FILE_PATH = video_file_path  # Path to the input audio file
    # OUTPUT_PATH = output_path  # Path to save the output audio file
    OUTPUT_PATH = os.path.join(PARENT_PATH,'temp.mp3')
    # Construct the URL for the Speech-to-Speech API request
    sts_url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}/stream"

    # Set up headers for the API request, including the API key for authentication
    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    # Set up the data payload for the API request, including model ID and voice settings
    # Note: voice settings are converted to a JSON string
    data = {
        "model_id": "eleven_english_sts_v2",
        "voice_settings": json.dumps({
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        })
    }

    # Set up the files to send with the request, including the input audio file
    files = {
        "audio": open(AUDIO_FILE_PATH, "rb")
    }

    # Make the POST request to the STS API with headers, data, and files, enabling streaming response
    response = requests.post(sts_url, headers=headers, data=data, files=files, stream=True)

    # Check if the request was successful
    if response.ok:
        # Open the output file in write-binary mode
        with open(OUTPUT_PATH, "wb") as f:
            # Read the response in chunks and write to the file
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)
        # Inform the user of success
        print("Audio stream saved successfully.")
    else:
        # Print the error message if the request was not successful
        print(response.text)

    exchange_audio_of_video(video_path=AUDIO_FILE_PATH, audio_path=OUTPUT_PATH , output_filename = output_path_video)
    os.remove(OUTPUT_PATH)


if __name__ == "__main__":
    main()

