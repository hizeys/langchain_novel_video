import os
import re
import requests
import base64
from typing import Dict
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def download_file(url: str, save_path: str, file_type: str = "文件") -> str:
    """
    通用文件下载函数
    
    Args:
        url: 文件的完整网址
        save_path: 本地保存路径
        file_type: 文件类型（用于日志显示）
    
    Returns:
        下载结果信息
    """
    try:
        # 确保保存目录存在
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        # 发送GET请求
        response = requests.get(url, stream=True) # stream=True支持大文件流式下载
        response.raise_for_status() # 检查请求是否成功（状态码200）

        # 以二进制写入模式保存文件
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192): # 分块写入
                file.write(chunk)
        return f"{file_type}已成功保存至：{save_path}"
    except requests.exceptions.RequestException as e:
        logger.error(f"{file_type}下载失败：{e}")
        return f"下载失败，错误信息：{e}"
    except OSError as e:
        logger.error(f"{file_type}保存失败：{e}")
        return f"保存失败，错误信息：{e}" 
    except Exception as e:
        logger.error(f"{file_type}下载和保存失败：{e}")
        return f"下载和保存失败，错误信息：{e}"

def download_image(url: str, save_path: str) -> str:
    """下载图片并保存到本地"""
    return download_file(url, save_path, "图片")

def download_video(url: str, save_path: str) -> str:
    """下载视频并保存到本地"""
    return download_file(url, save_path, "视频")

def image_to_base64(image_path: str) -> str:
    """
    将本地图片转换为base64编码
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string
    except Exception as e:
        logger.error(f"图片转换为base64失败：{e}")
        return f"转换失败，错误信息：{e}"

def load_novel(file_path: str) -> Dict[str, str]:
    """
    加载小说文件并按章节分割
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 按章节分割
        chapters: Dict[str, str] = {}
        # 匹配“第xx章”直到出现两个换行符作为章节标题结束
        chapter_pattern = re.compile(r'(第\d+章.*?)\n\n', re.DOTALL)
        matches = chapter_pattern.findall(content)

        for i, match in enumerate(matches):
            # 提取章节标题
            title_match = re.match(r'(第\d+章.*)', match)
            if title_match:
                title = title_match.group(1)
                # 获取章节内容
                if i < len(matches) - 1:
                    start_idx = content.index(match)
                    end_idx = content.index(matches[i+1])
                    chapter_content = content[start_idx:end_idx].strip()
                else:
                    start_idx = content.index(match)
                    chapter_content = content[start_idx:].strip()
                chapters[title] = chapter_content
        return chapters
    except Exception as e:
        logger.error(f"加载小说失败: {e}")
        return {}
