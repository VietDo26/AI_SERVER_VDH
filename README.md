Installation
------------

```
    git clone https://github.com/VietDo26/DATN_AI_SERVER_GPU.git

    apt install git-all
    apt install curl
    apt install ffmpeg
```

With cpu:
```
    python install.py --onnxruntime [type] --skip-conda
    <!-- type = [default,openvino] -->

```

With GPU :
```
    !python install.py --onnxruntime [type] --skip-conda
    <!-- type = [cuda-11.8,cuda-12.2] -->
    

```
Usage
-----
Run the command
```  
    mkdir -p logs && touch logs/http.log
    python server.py
```

Run the command:


Documentation
-------------


