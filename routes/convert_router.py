import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import sys
import os
import subprocess
import typing
from typing import List,Optional, Union

from fastapi import APIRouter, BackgroundTasks
from PIL import Image
import GPUtil
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import RedirectResponse,  FileResponse
from utils.database.database import insert_data_into_media_table, insert_data_into_users_table, get_file_size_and_duration, get_url_from_media_table_by_id, check_user_exists
from utils.videoprocessing.concatenate import concatenateWarning
from voice.voice import convert_audio_of_video, create_video_with_voice_cloning
from schemas.video_schema import VideoResponse
import time


folder_path= str(Path(__file__).parent.parent)

SERVER_MEDIA = ''
KEY = ''

router = APIRouter()

from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)


@router.get("/filevideo/")
async def filevideo(path: str):
    return FileResponse(path)    


def is_gpu_available():
    """Checks for GPU availability using GPUtil.

    Returns:
        bool: True if a GPU is available, False otherwise.
    """
    gpus = GPUtil.getAvailable()
    return len(gpus) > 0

@router.post("/convertvideodeepfake/")
async def convertvideodeepfake( user_id:int,
                               user_name:str, 
                               role_id:str,
                                images: typing.List[UploadFile] = File(...),
                                video: UploadFile = File(...),
                                audios: typing.List[UploadFile] = None
                    #    audios: Optional[List[bytes]] = File(None)
                    #    audios:  List[Union[UploadFile, None]] = File(None)
                       ) -> VideoResponse:
    # config
    output_video_encoder = 'hevc_nvenc'
    output_video_quality = 100  
    execution_providers = 'cuda' if is_gpu_available() else 'cpu'
    face_swapper_model = "inswapper_128_fp16"
    
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    os.makedirs(upload_dir_media, exist_ok=True)
    number_order = len(os.listdir(upload_dir_media))
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    

    os.makedirs(upload_dir_media, exist_ok=True)

    if audios is not None:
        print("with voice")
        # check file and save file audio
        audio_file_paths = []
        for index, audio in enumerate(audios) :
            if not audio.content_type.startswith("audio/"):
                raise HTTPException(status_code=400, detail="Only audio uploads allowed!")
            
            index_audio = audio.filename.rfind('.')
            file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}_{index}'+audio.filename[index_audio:]
            try:
                with open(file_path_audio, "wb") as buffer:
                    content = await audio.read()
                    buffer.write(content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")
            audio_file_paths.append(file_path_audio)
        # print(upload_dir_media)

        # check file image and save file image
        image_file_paths = []
        for index, image in enumerate(images) :
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image uploads allowed!")
            
            index_image = image.filename.rfind('.')
            file_path_image=upload_dir_media+f'/image_{user_id:04d}_{number_order:05d}_{index}'+image.filename[index_image:]
            try:
                pil_img = Image.open(image.file)
                pil_img.save(file_path_image)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
            image_file_paths.append(file_path_image)

        # save file video
        index_video = video.filename.rfind('.')
        file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        try:
            with open( file_path_video, "wb") as buffer:
                content = await video.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

        try:
            output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
            # print('output :', output)
            command = [
                "python3", "run.py", "--headless",
                "--target", f"{file_path_video}",
                "--output", f"{output}",
                "--execution-provider", f"{execution_providers}",
                "--output-video-encoder", f"{output_video_encoder}",
                "--frame-processors", "face_swapper", "face_enhancer",
                "--face-swapper-model", f"{face_swapper_model}",
                "--output-video-quality", f"{output_video_quality}"
                ]
            for image in image_file_paths:
                command.append("--source")
                command.append(image)
            result = subprocess.run(command)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')

        output_with_voice = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice'+video.filename[index_video:]
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= output , output_path_video=output_with_voice)
        
        # insert_data_into_database()
        output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice_final'+video.filename[index_video:]
        concatenateWarning(video_path=output_with_voice,output_path= output_final)
        print("with voice")
        link_url = f'/convertfile/filevideo/?path={output_final}'
        
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=str(audio_file_paths), 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        
    else:
        print("without voice")
        # save images
        image_file_paths = []
        for index, image in enumerate(images) :
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image uploads allowed!")
            
            index_image = image.filename.rfind('.')
            file_path_image=upload_dir_media+f'/image_{user_id:04d}_{number_order:05d}_{index}'+image.filename[index_image:]
            try:
                pil_img = Image.open(image.file)
                pil_img.save(file_path_image)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
            image_file_paths.append(file_path_image)

        # save video
        index_video = video.filename.rfind('.')
        file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        try:
            with open( file_path_video, "wb") as buffer:
                content = await video.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

        try:
            output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
            command = [
                "python3", "run.py", "--headless",
                "--target", f"{file_path_video}",
                "--output", f"{output}",
                "--execution-provider", f"{execution_providers}",
                "--output-video-encoder", f"{output_video_encoder}",
                "--frame-processors", "face_swapper", "face_enhancer",
                "--face-swapper-model", f"{face_swapper_model}",
                "--output-video-quality", f"{output_video_quality}"
                ]
            for image in image_file_paths:
                command.append("--source")
                command.append(image)
            result = subprocess.run(command)    
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')
        
        output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
        concatenateWarning(video_path=output,output_path= output_final)
        # print("without voice")
        link_url = f'/convertfile/filevideo/?path={output_final}'
        
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake without voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=None, 
            output_video_path=output, 
            size=size_file, 
            time=duration)
    return VideoResponse(
        userId= f"{user_id}",
        videoUrl= f"{link_url}",
        size= size_file
    )




@router.post("/convertvideodeepfake_background/")
async def convertvideodeepfake_back_ground( user_id:int,
                               user_name:str, 
                               role_id:str,
                                images: typing.List[UploadFile] = File(...),
                                video: UploadFile = File(...),
                                audios: typing.List[UploadFile] = None,
                                background_tasks: BackgroundTasks = BackgroundTasks()
                    #    audios: Optional[List[bytes]] = File(None)
                    #    audios:  List[Union[UploadFile, None]] = File(None)
                       ):
    # config
    output_video_encoder = 'hevc_nvenc'
    output_video_quality = 100  
    execution_providers = 'cuda' if is_gpu_available() else 'cpu'
    face_swapper_model = "inswapper_128_fp16"
    
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    os.makedirs(upload_dir_media, exist_ok=True)
    number_order = len(os.listdir(upload_dir_media))
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    

    os.makedirs(upload_dir_media, exist_ok=True)

    if audios is not None:
        print("with voice")
        # check file and save file audio
        audio_file_paths = []
        for index, audio in enumerate(audios) :
            if not audio.content_type.startswith("audio/"):
                raise HTTPException(status_code=400, detail="Only audio uploads allowed!")
            
            index_audio = audio.filename.rfind('.')
            file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}_{index}'+audio.filename[index_audio:]
            try:
                with open(file_path_audio, "wb") as buffer:
                    content = await audio.read()
                    buffer.write(content)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")
            audio_file_paths.append(file_path_audio)
        # print(upload_dir_media)

        # check file image and save file image
        image_file_paths = []
        for index, image in enumerate(images) :
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image uploads allowed!")
            
            index_image = image.filename.rfind('.')
            file_path_image=upload_dir_media+f'/image_{user_id:04d}_{number_order:05d}_{index}'+image.filename[index_image:]
            try:
                pil_img = Image.open(image.file)
                pil_img.save(file_path_image)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
            image_file_paths.append(file_path_image)

        # save file video
        index_video = video.filename.rfind('.')
        file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        try:
            with open( file_path_video, "wb") as buffer:
                content = await video.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

        try:
            output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
            output_with_voice = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice'+video.filename[index_video:]
            output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice_final'+video.filename[index_video:]
            # print('output :', output)
            command = [
                "python3", "run.py", "--headless",
                "--target", f"{file_path_video}",
                "--output", f"{output}",
                "--execution-provider", f"{execution_providers}",
                "--output-video-encoder", f"{output_video_encoder}",
                "--frame-processors", "face_swapper", "face_enhancer",
                "--face-swapper-model", f"{face_swapper_model}",
                "--output-video-quality", f"{output_video_quality}"
                ]
            for image in image_file_paths:
                command.append("--source")
                command.append(image)
            result = subprocess.run(command)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')

        output_with_voice = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice'+video.filename[index_video:]
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= output , output_path_video=output_with_voice)
        
        # insert_data_into_database()
        output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_withvoice_final'+video.filename[index_video:]
        concatenateWarning(video_path=output_with_voice,output_path= output_final)
        print("with voice")
        link_url = f'/convertfile/filevideo/?path={output_final}'
        
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=str(audio_file_paths), 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        
    else:
        print("without voice")
        # save images
        image_file_paths = []
        for index, image in enumerate(images) :
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Only image uploads allowed!")
            
            index_image = image.filename.rfind('.')
            file_path_image=upload_dir_media+f'/image_{user_id:04d}_{number_order:05d}_{index}'+image.filename[index_image:]
            try:
                pil_img = Image.open(image.file)
                pil_img.save(file_path_image)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")
            image_file_paths.append(file_path_image)

        # save video
        index_video = video.filename.rfind('.')
        file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        try:
            with open( file_path_video, "wb") as buffer:
                content = await video.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

        try:
            output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
            output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
            command = [
                "python3", "run.py", "--headless",
                "--target", f"{file_path_video}",
                "--output", f"{output}",
                "--execution-provider", f"{execution_providers}",
                "--output-video-encoder", f"{output_video_encoder}",
                "--frame-processors", "face_swapper", "face_enhancer",
                "--face-swapper-model", f"{face_swapper_model}",
                "--output-video-quality", f"{output_video_quality}"
                ]
            for image in image_file_paths:
                command.append("--source")
                command.append(image)
                
            background_tasks.add_task(heavy_task,
                                      command = command, 
                                      user_id = user_id, 
                                      user_name = user_name, 
                                      role_id = role_id, 
                                      image_file_paths = file_path_image, 
                                      file_path_video = file_path_video,
                                      audio_file_paths = None,
                                      output = output,
                                      output_with_voice = None,
                                      output_final = output_final
                                      )
            # result = subprocess.run(command)    
        except Exception as e:
            raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')     
    return "received a request to create a deepfake video"

def heavy_task(command, user_id, user_name, role_id, image_file_paths, file_path_video, audio_file_paths ,output,output_with_voice, output_final,type):
    if type == "video deepfake without voice":
        result = subprocess.run(command)
        concatenateWarning(video_path=output,output_path= output_final)
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=audio_file_paths, 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)
    elif type == "video deepfake with voice" :
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= output , output_path_video=output_with_voice)
        concatenateWarning(video_path=output_with_voice,output_path= output_final)
        print("with voice")
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=str(audio_file_paths), 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)
    elif type == "Video convert own voice":
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= file_path_video,output_path_video=output)
        concatenateWarning(video_path=output,output_path= output_final)
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='Video convert own voice', 
            input_image_path=None,
            input_video_path=file_path_video, 
            input_voice_path=audio_file_paths, 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)

@router.post("/convertvoice_with_owned_voice/")
async def convertvideo_with_owned_voice( user_id: int,
                                        user_name=str, 
                                        role_id=int,
                                        video: UploadFile = File(...),
                                        audios: typing.List[UploadFile] = File(...)
                       ):
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    number_order = len(os.listdir(upload_dir_media))
    
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    audio_file_paths = []
    for index, audio in enumerate(audios) :
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Only audio uploads allowed!")
        
        index_audio = audio.filename.rfind('.')
        file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}_{index}'+audio.filename[index_audio:]
        try:
            with open(file_path_audio, "wb") as buffer:
                content = await audio.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")
        audio_file_paths.append(file_path_audio)

    index_video = video.filename.rfind('.')
    file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
    try:
        with open( file_path_video, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")
    try:
        output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= file_path_video,output_path_video=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')
    
    
    output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
    concatenateWarning(video_path=output,output_path= output_final)
    link_url = f'/convertfile/filevideo/?path={output_final}'

    None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
    size_file, duration =  get_file_size_and_duration(output_final)
    insert_data_into_media_table(user_id=user_id,
        type='Video convert own voice', 
        input_image_path=None,
        input_video_path=file_path_video, 
        input_voice_path=audio_file_paths, 
        output_video_path=output, 
        size=size_file, 
        time=duration)
    return VideoResponse(
        userId= f"{user_id}",
        videoUrl= f"{link_url}",
        size = size_file
    )

@router.post("/convertvoice_with_owned_voice_background/")
async def convertvideo_with_owned_voice_background( user_id: int,
                                        user_name=str, 
                                        role_id=int,
                                        video: UploadFile = File(...),
                                        audios: typing.List[UploadFile] = File(...),
                                        background_tasks: BackgroundTasks = BackgroundTasks()
                       ):
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    number_order = len(os.listdir(upload_dir_media))
    
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    audio_file_paths = []
    for index, audio in enumerate(audios) :
        if not audio.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Only audio uploads allowed!")
        
        index_audio = audio.filename.rfind('.')
        file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}_{index}'+audio.filename[index_audio:]
        try:
            with open(file_path_audio, "wb") as buffer:
                content = await audio.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")
        audio_file_paths.append(file_path_audio)

    index_video = video.filename.rfind('.')
    file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
    try:
        with open( file_path_video, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")
    try:
        output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
        background_tasks.add_task(heavy_task,
                            command = None, 
                            user_id = user_id, 
                            user_name = user_name, 
                            role_id = role_id, 
                            image_file_paths = None, 
                            file_path_video = file_path_video,
                            audio_file_paths = audio_file_paths,
                            output = output,
                            output_with_voice =None,
                            output_final = output_final,
                            type= 'Video convert own voice')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')
    return "received a request to create convertvideo_with_owned_voice"

@router.post("/convertvideo_LipSyncer/")
async def convertvideo_LipSyncer( user_id:int,
                        user_name=str, 
                        role_id=int,
                       audio: UploadFile = File(...),
                       video: UploadFile = File(...)
                       ):
    # config
    # output_video_encoder = 'hevc_nvenc'
    output_video_quality = 100
    execution_providers = 'cuda' if is_gpu_available() else 'cpu'
    
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio uploads allowed!")

    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    number_order = len(os.listdir(upload_dir_media))
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    
    # print(upload_dir_media)
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)

    # print(upload_dir_media)
    index_audio = audio.filename.rfind('.')
    file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}'+audio.filename[index_audio:]

    try:
        with open(file_path_audio, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")

    index_video = video.filename.rfind('.')
    file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
    try:
        with open( file_path_video, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

    try:
        output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        command = [
            "python", "run.py", "--headless",
            "--source", f"{file_path_audio}",
            "--target", f"{file_path_video}",
            "--output", f"{output}",
            "--execution-provider", f'{execution_providers}',
            # "--output-video-encoder", f"{output_video_encoder}",
            "--frame-processors", "lip_syncer"
            # "--frame-processors", "lip_syncer", "face_enhancer"
        ]
        result = subprocess.run(command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')
    output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
    # concatenateWarning(video_path=output,output_path= output_final)
    link_url = f'/convertfile/filevideo/?path={output_final}'
    
    None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
    size_file, duration =  get_file_size_and_duration(output_final)
    insert_data_into_media_table(user_id=user_id,
        type='Video Lip Syncer', 
        input_image_path=None,
        input_video_path=file_path_video, 
        input_voice_path=file_path_audio, 
        output_video_path=output, 
        size=size_file, 
        time=duration)
    return VideoResponse(
        userId= f"{user_id}",
        videoUrl= f"{link_url}",
        size = size_file
    )
@router.post("/convertvideo_LipSyncer_background/")
async def convertvideo_LipSyncer_background( user_id:int,
                        user_name=str, 
                        role_id=int,
                       audio: UploadFile = File(...),
                       video: UploadFile = File(...),
                       background_tasks: BackgroundTasks = BackgroundTasks()
                       ):
    # config
    # output_video_encoder = 'hevc_nvenc'
    output_video_quality = 100
    execution_providers = 'cuda' if is_gpu_available() else 'cpu'
    
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Only audio uploads allowed!")

    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    number_order = len(os.listdir(upload_dir_media))
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    
    # print(upload_dir_media)
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)

    # print(upload_dir_media)
    index_audio = audio.filename.rfind('.')
    file_path_audio = upload_dir_media+f'/audio_{user_id:04d}_{number_order:05d}'+audio.filename[index_audio:]

    try:
        with open(file_path_audio, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")

    index_video = video.filename.rfind('.')
    file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
    try:
        with open( file_path_video, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")

    try:
        output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]

        command = [
            "python", "run.py", "--headless",
            "--source", f"{file_path_audio}",
            "--target", f"{file_path_video}",
            "--output", f"{output}",
            "--execution-provider", f'{execution_providers}',
            # "--output-video-encoder", f"{output_video_encoder}",
            "--frame-processors", "lip_syncer"
            # "--frame-processors", "lip_syncer", "face_enhancer"
        ]
        background_tasks.add_task(heavy_task,
                command = command, 
                user_id = user_id, 
                user_name = user_name, 
                role_id = role_id, 
                image_file_paths = None, 
                file_path_video = file_path_video,
                audio_file_paths = file_path_audio,
                output = output,
                output_with_voice =None,
                output_final = output_final,
                type= 'Video Lip Syncer')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')

    return "received a request to create video lip syncer"

@router.post("/convertvoice_withavailablevoice/")
async def onvertvoice_withavailablevoice( user_id: int,
                       user_name:str,
                       role_id: int,
                       voice_id:str,
                       video: UploadFile = File(...),
                       ) -> VideoResponse:
    if not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Only video uploads allowed!")

    upload_dir_media = os.path.join(folder_path,'media',f'user_id_{user_id:04d}')
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)
    number_order = len(os.listdir(upload_dir_media))
    upload_dir_media = os.path.join(upload_dir_media,f'{number_order:05d}')
    
    if not os.path.exists(upload_dir_media):
        os.makedirs(upload_dir_media)


    index_video = video.filename.rfind('.')
    file_path_video=upload_dir_media+f'/targetvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
    try:
        with open( file_path_video, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video: {e}")
    
    try:
        output = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}'+video.filename[index_video:]
        convert_audio_of_video(api_key=KEY, voice_id= voice_id, audio_file_path=file_path_video, output_path_video=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Faild to convert video {e}')
    
    # output_final = upload_dir_media + f'/processedvideo_{user_id:04d}_{number_order:05d}_final'+video.filename[index_video:]
    # concatenateWarning(video_path=output,output_path= output_final)
    link_url = f'/convertfile/filevideo/?path={output}'
    None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
    size_file, duration =  get_file_size_and_duration(output)
    insert_data_into_media_table(user_id=user_id,
        type='Only convert voice', 
        input_image_path=None,
        input_video_path=file_path_video, 
        input_voice_path=None, 
        output_video_path=output, 
        size=size_file, 
        time=duration)
    return VideoResponse(
        userId= f"{user_id}",
        videoUrl= f"{link_url}",
        size = size_file
    )

def heavy_task(command, user_id, user_name, role_id, image_file_paths, file_path_video, audio_file_paths ,output,output_with_voice, output_final,type):
    if type == "video deepfake without voice":
        result = subprocess.run(command)
        concatenateWarning(video_path=output,output_path= output_final)
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=audio_file_paths, 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)
    elif type == "video deepfake with voice" :
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= output , output_path_video=output_with_voice)
        concatenateWarning(video_path=output_with_voice,output_path= output_final)
        print("with voice")
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='video deepfake with voice', 
            input_image_path=str(image_file_paths),
            input_video_path=file_path_video, 
            input_voice_path=str(audio_file_paths), 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)
    elif type == "Video convert own voice":
        create_video_with_voice_cloning(user_id=str(user_id), files= audio_file_paths, video_file_path= file_path_video,output_path_video=output)
        concatenateWarning(video_path=output,output_path= output_final)
        link_url = f'/convertfile/filevideo/?path={output_final}'
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        insert_data_into_media_table(user_id=user_id,
            type='Video convert own voice', 
            input_image_path=None,
            input_video_path=file_path_video, 
            input_voice_path=audio_file_paths, 
            output_video_path=output, 
            size=size_file, 
            time=duration)
        print(link_url)
    elif type ==  'Video Lip Syncer':   
        result = subprocess.run(command)
        None if check_user_exists else insert_data_into_users_table(id=user_id, username=user_name, role_id=role_id)
        size_file, duration =  get_file_size_and_duration(output_final)
        link_url = f'/convertfile/filevideo/?path={output_final}'
        insert_data_into_media_table(user_id=user_id,
                type='Video Lip Syncer', 
                input_image_path=None,
                input_video_path=file_path_video, 
                input_voice_path=audio_file_paths, 
                output_video_path=output, 
                size=size_file, 
                time=duration)   
        print(link_url)