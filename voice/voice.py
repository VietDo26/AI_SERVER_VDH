import requests  # Used for making HTTP requests
import json  # Used for working with JSON data
import sys
from pathlib import Path
import os
import typing
from typing import Iterator, Optional, Union

from elevenlabs import play, save
from elevenlabs.client import ElevenLabs
from moviepy.editor import VideoFileClip, AudioFileClip

sys.path.append(str(Path(__file__).parent.parent))
PARENT_PATH = str(Path(__file__).parent)

KEY = 
def main():
    client = ElevenLabs(
        api_key= KEY ,
    )
    response = client.voices.get_all()
    for voice in response.voices:
        print(voice.voice_id)

def remove_noise_audio(audio_path, output_path):
    client = ElevenLabs(
        api_key= KEY ,
    )
    audio = client.audio_isolation.audio_isolation(audio = open(audio_path, "rb"))
    save(audio,output_path)

def get_voice_by_userid(userid:str):
    userid = str(userid)
    client = ElevenLabs(
            api_key=KEY,
        )
    response = client.voices.get_all()
    for idx, voice in enumerate(response.voices):
        if voice.name == userid:
            return voice
    return None

def get_id_voice_by_userid(userid:str):
    voice = get_voice_by_userid(userid)
    return voice.voice_id if voice else None
def delete_voice_by_userid(userid:str):
    userid = str(userid)
    client = ElevenLabs(
            api_key=KEY,
        )
    id_voice = get_id_voice_by_userid(userid)
    if id_voice == None:
        # print("userid is not exist")
        return
    else:
         client.voices.delete(
            voice_id=id_voice,
        )
    
def create_video_with_voice_cloning(user_id:int ,files: typing.List[str], video_file_path:str , output_path_video:str):
    print("Starting Cloning Voice")
    client = ElevenLabs(
        api_key=KEY,
    )
    # clear old voice if exist
    delete_voice_by_userid(user_id)
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

