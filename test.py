import requests
from schemas.video_schema import VideoResponse
import requests
import json
def main():
    send_request()

def send_request():
    url = "https://deepfakesnsapi.azurewebsites.net/api/v1/videodeepfake/create_deepfakevideo"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "videoUrl": "http://test.com",
        "size": "40",
        "userId": "5"
    }

    # response = requests.post(url, headers=headers, data=json.dumps(data))
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 201:
        print("Request was successful.")
        print("Response:", response.json())
    else:
        print("Request failed.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    main()
