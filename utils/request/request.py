import requests
import json
from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).parent.parent))
# def main():
#     url = 'https://bat-choice-needlessly.ngrok-free.app/api/v1/videodeepfake/finish'
#     video_id = '321'
#     video_path = '/home/viet/workspace/AI_SERVER_VDH/media/user_id_0003/00000/processedvideo_0003_00000.mp4'
#     # send_video_post_request(url, video_id, video_path)
#     send_video_post_request(url, video_id, video_path)
def send_video_chunked(url, video_id, video_path, chunk_size=1024 * 1024):
    """
    Send a large video file in chunks.

    Parameters:
    - url: The endpoint to which the request is sent.
    - video_id: The ID of the video.
    - video_path: The path to the video file.
    - chunk_size: The size of each chunk in bytes. Default is 1MB.

    Returns:
    - Response object from the requests library.
    """
    file_size = os.path.getsize(video_path)
    headers = {'Content-Range': f'bytes 0-{file_size-1}/{file_size}'}

    with open(video_path, 'rb') as video_file:
        for chunk in iter(lambda: video_file.read(chunk_size), b''):
            response = requests.post(url, headers=headers, files={'video': ('video.mp4', chunk, 'video/mp4')}, data={'videoId': video_id})
            if response.status_code != 200:
                print(f"Failed to upload chunk. Status code: {response.status_code}")
                print(response.text)
                return response
    
    return response
def send_video_post_request(url, video_id, video_path):
    """
    Send a POST request with a video ID and video file.

    Parameters:
    - url: The endpoint to which the request is sent.
    - video_id: The ID of the video.
    - video_path: The path to the video file.

    Returns:
    - Response object from the requests library.
    """
    
    # Create the payload
    # headers = {'Content-Type':'multipart/form-data; boundary=<calculated when request is sent>'}
    data = {'videoId': video_id}
    # files = {'file': open(video_path, 'rb')}
    with open(video_path, 'rb') as video_file:
        # Create the files dictionary with a correct key
        files = {'video': video_file}
        response = requests.post(url, data=data, files=files)

    print(response.status_code)
    print(response.json())
    return response
# def send_request():
#     url = "https://deepfakesnsapi.azurewebsites.net/api/v1/videodeepfake/create_deepfakevideo"
#     headers = {
#         'Content-Type': 'application/json'
#     }
#     data = {
#         "videoUrl": "http://test.com",
#         "size": "40",
#         "userId": "5"
#     }

#     response = requests.post(url, headers=headers, data=json.dumps(data))
#     # response = requests.post(url, headers=headers, data=data)
#     if response.status_code == 201:
#         print("Request was successful.")
#         print("Response:", response.json())
#     else:
#         print("Request failed.")
#         print("Status Code:", response.status_code)
#         print("Response:", response.text)

if __name__ == "__main__":
    main()
