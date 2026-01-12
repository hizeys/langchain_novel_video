import os
import subprocess
from typing import List
import tempfile
import imageio_ffmpeg
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def merge_videos(video_paths: List[str], output_path: str) -> str:
    """
    使用ffmpeg合并多个视频文件，同时保留音频
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 检查视频文件是否存在
        valid_files = []
        for video_path in video_paths:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            valid_files.append(video_path)
        
        if not valid_files:
            return "没有有效的视频文件可以合并"
        
        # 创建一个临时文件列表
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
            for file in valid_files:
                # 确保路径格式正确
                abs_path = os.path.abspath(file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
            file_list_path = f.name
        
        try:
            # 获取ffmpeg可执行文件路径
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            # 使用ffmpeg的concat协议合并视频和音频
            cmd = [
                ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', file_list_path,
                '-c', 'copy',  # 直接复制流，不重新编码
                '-y',  # 覆盖输出文件
                output_path
            ]
            
            # 执行命令
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            logger.info(f"视频已成功合并至：{output_path}")
            return f"视频已成功合并至：{output_path}"
        finally:
            # 清理临时文件
            os.unlink(file_list_path)
    except FileNotFoundError as e:
        logger.error(f"视频合并失败，文件不存在：{e}")
        return f"合并失败，文件不存在：{e}"
    except OSError as e:
        logger.error(f"视频合并失败，保存错误：{e}")
        return f"保存失败，错误信息：{e}"
    except Exception as e:
        logger.error(f"视频合并失败：{e}", exc_info=True)
        return f"合并视频失败，错误信息：{e}"

def get_media_duration(file_path: str) -> float:
    """
    获取媒体文件（视频/音频）的时长（秒）
    """
    try:
        # 获取ffmpeg可执行文件路径
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        # 使用ffprobe获取时长
        # 注意：imageio_ffmpeg 不直接暴露 ffprobe，通常 ffmpeg 目录下会有 ffprobe
        # 或者我们可以直接使用 ffmpeg -i 命令解析输出
        
        cmd = [ffmpeg_path, '-i', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # ffmpeg -i 输出包含 "Duration: 00:00:05.12," 格式
        # 输出在 stderr 中
        output = result.stderr
        
        import re
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", output)
        if duration_match:
            hours = int(duration_match.group(1))
            minutes = int(duration_match.group(2))
            seconds = float(duration_match.group(3))
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
            
        return 0.0
    except Exception as e:
        logger.error(f"获取媒体时长失败: {e}")
        return 0.0

def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    将视频画面与音频文件合并
    :param video_path: 视频文件路径
    :param audio_path: 音频文件路径
    :param output_path: 输出文件路径
    :return: 是否成功
    """
    try:
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        # -c:v copy: Copy video stream
        # -c:a aac: Re-encode audio to aac (or copy if compatible, but aac is safe)
        # -map 0:v:0: Take first video stream from first input (video)
        # -map 1:a:0: Take first audio stream from second input (audio)
        # -shortest: Finish/cut when shortest stream ends (usually video matches audio duration now, effectively)
        # Actually, since we set video duration to match audio, they should be close.
        cmd = [
            ffmpeg_path,
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-y',
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except Exception as e:
        logger.error(f"合并视频与音频失败: {e}")
        return False
