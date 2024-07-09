from pydantic import BaseModel

class VideoResponse(BaseModel):
    userId :int
    videoUrl: str
    size: str