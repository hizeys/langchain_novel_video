import os
import dotenv

dotenv.load_dotenv()

class Config:
    # API配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
    DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")
    
    # 模型配置
    LLM_MODEL = "qwen3-max" # Updated from tools.py preference or main.py? tools.py uses qwen3-max
    LLM_MODEL_PROVIDER = "openai"
    LLM_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 多媒体模型配置
    VIDEO_DURATION = 5  # 视频时长 秒 -1:根据场景内容自动调整(仅1.5pro)
    VIDEO_RESOLUTION = "480p"
    
    # 工作目录配置
    IMAGE_DIR = "image"
    VIDEO_DIR = "video"
    MERGED_VIDEO_PATH = "merged_video.mp4"
    CHARACTER_DIR = "character"
    
    # 小说配置
    NOVEL_FILE_PATH = "小说素材.txt"
    TARGET_CHAPTER = "第3章 闻姑娘还真是……娇气"
    
    # 测试配置
    TEST_MODE = True
    MAX_SCENES = 1
    
    # 视频生成配置
    MAX_VIDEO_RETRIES = 100
    VIDEO_POLL_INTERVAL = 8  # 视频轮询 秒 
