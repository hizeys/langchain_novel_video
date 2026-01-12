import os
import time
from typing import List, Optional, Dict, Any
from volcenginesdkarkruntime import Ark
from app.config import Config
from app.utils.logger import setup_logger
from app.utils.file_ops import image_to_base64, download_image, download_video
from app.services.llm import generate_image_prompt, generate_video_prompt
import json

logger = setup_logger(__name__)

# 豆包文生图
def generate_image(prompt: str, size: str = "1440x2560", save_path: Optional[str] = None, max_retries: int = 3, characters: List[str] = None) -> str:
    """生成图片"""
    # 参数验证
    if not prompt or not isinstance(prompt, str):
        logger.error("图片描述不能为空且必须是字符串")
        return "生成图片失败：图片描述不能为空且必须是字符串"
    
    if size not in ["2048x2048","2560x1440","1440x2560"]:
        logger.warning(f"无效的图片尺寸：{size}，将使用默认尺寸1440x2560")
        size = "1440x2560"
    
    # 检查并添加人物写真参考
    reference_images = []
    character_names = []
    if characters:
        for character in characters:
            portrait_path = os.path.join(Config.CHARACTER_DIR, f"{character}.png")
            if os.path.exists(portrait_path):
                base64_image = image_to_base64(portrait_path)
                if not base64_image.startswith("转换失败"):
                    reference_images.append(f"data:image/png;base64,{base64_image}")
                    character_names.append(character)
                    logger.info(f"找到人物 {character} 的写真并转换为base64编码")
                else:
                    logger.error(f"人物 {character} 的写真转换为base64失败：{base64_image}")

    logger.info(f"开始生成图片，提示词：{prompt[:50]}...")
    if reference_images:
        logger.info(f"使用 {len(reference_images)} 张人物写真作为参考")
    
    # 构建API请求参数
    api_params = {
        "model": "doubao-seedream-4-5-251128",
        "prompt": prompt,
        "size": size,
        "watermark": False,
    }

    if reference_images:
        enhanced_prompt = prompt
        for i in range(0,len(character_names)):
            enhanced_prompt += f",{character_names[i]} 的外貌特征如图{i}所示"
        api_params.update({"image":reference_images})
        api_params["prompt"] = enhanced_prompt

    retry_count = 0
    while retry_count < max_retries:
        try:
            client = Ark(
                api_key=Config.DOUBAO_API_KEY,
                base_url="https://ark.cn-beijing.volces.com/api/v3",
            )
            
            logger.debug(f"调用豆包API生成图片，重试次数：{retry_count}")
            
            response = client.images.generate(**api_params)
            
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                logger.info(f"图片生成成功，URL：{image_url}")
                
                if save_path:
                    logger.info(f"开始下载图片到：{save_path}")
                    result = download_image(image_url, save_path)
                    if "成功" in result:
                        logger.info(f"图片下载成功：{save_path}")
                        return image_url
                    else:
                        logger.error(f"图片下载失败：{result}")
                        return image_url
                
                return image_url
            else:
                error_msg = response.error.message if hasattr(response, 'error') and response.error else "未知错误"
                logger.error(f"图片生成失败：{error_msg}")
                return f"生成图片失败：{error_msg}"
                
        except Exception as e:
            retry_count += 1
            logger.error(f"图片生成异常（{retry_count}/{max_retries}）：{str(e)}")
            if retry_count < max_retries:
                logger.info(f"{retry_count}秒后重试...")
                time.sleep(retry_count) # Backoff
            else:
                logger.error(f"图片生成失败，已达到最大重试次数：{max_retries}")
                return f"生成图片失败，已达到最大重试次数：{str(e)}"

def poll_video_status(client: Ark, task_id: str, scene_id: str, max_retries: int, poll_interval: int) -> str:
    """轮询查询视频生成结果"""
    video_url = None
    for i in range(max_retries):
        logger.debug(f"场景 {scene_id} 第{i+1}次查询视频生成结果...")
        
        try:
            fetch_result = client.content_generation.tasks.get(task_id=task_id)
            status = fetch_result.status
            
            if status == 'succeeded':
                video_url = fetch_result.content.video_url
                if video_url:
                    logger.info(f"场景 {scene_id} 视频生成成功！视频URL：{video_url}")
                    if hasattr(fetch_result, 'usage'):
                        logger.info(f"视频生成消耗tokens:{fetch_result.usage.completion_tokens}")
                    break
            elif status == 'failed' or status == 'cancelled':
                error_msg = fetch_result.error
                logger.error(f"场景 {scene_id} 视频生成失败：{error_msg.message}")
                raise Exception(f"场景 {scene_id} 视频生成失败：{error_msg.message}")
            else:
                logger.info(f"场景 {scene_id} 视频生成中，当前状态：{status}")
        except Exception as e:
            logger.warning(f"场景 {scene_id} 查询视频生成结果失败，将重试：{e}")
        
        if i < max_retries - 1:
            time.sleep(poll_interval)
    
    if not video_url:
        logger.error(f"场景 {scene_id} 视频生成超时或失败")
        raise Exception(f"场景 {scene_id} 视频生成超时或失败")
    
    return video_url

def generate_single_video(scene_info: Dict[str, Any], video_dir: str, duration: float = None) -> Dict[str, Any]:
    """生成单个场景的视频"""
    scene_id = scene_info["scene_id"]
    # 优先使用Start Frame作为视频生成的首帧
    image_url = scene_info.get("image_url_start")
    image_path = scene_info.get("image_path_start")
    
    logger.info(f"生成场景 {scene_id} 的视频...")
    
    try:
        # 生成视频提示词
        video_prompt = generate_video_prompt(scene_info)
        # Try to parse strict JSON of prompt if it returns JSON string
        try:
             json_prompt = json.loads(video_prompt)
             if isinstance(json_prompt, dict) and "video_prompt" in json_prompt:
                 video_prompt = json_prompt["video_prompt"]
                 narration = json_prompt["narration"]
        except:
             pass # assume it is raw text if not json

        logger.info(f"场景 {scene_id} 的视频生成提示词：{video_prompt}")

        # Determine duration
        video_duration = int(duration if duration is not None else Config.VIDEO_DURATION)

        client = Ark(
            api_key=Config.DOUBAO_API_KEY,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        video_task_result = client.content_generation.tasks.create(
            model="doubao-seedance-1-0-pro-250528",
            content=[
                {
                    "type":"text",
                    "text":f"{video_prompt} --duration {video_duration} --resolution {Config.VIDEO_RESOLUTION}",
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":f"data:image/jpeg;base64,{scene_info['image_base64_start']}"
                    },
                    "role":"first_frame"
                },
                {
                    "type":"image_url",
                    "image_url":{
                        "url":f"data:image/jpeg;base64,{scene_info['image_base64_end']}"
                    },
                    "role":"last_frame"
                }

            ],
        )
        
        task_id = video_task_result.id
        logger.info(f"场景 {scene_id} 的视频生成任务ID：{task_id}")
        
        video_url = poll_video_status(
            client=client,
            task_id=task_id,
            scene_id=scene_id,
            max_retries=Config.MAX_VIDEO_RETRIES,
            poll_interval=Config.VIDEO_POLL_INTERVAL
        )
        
        os.makedirs(video_dir, exist_ok=True)
        save_path = os.path.join(video_dir, f"{scene_id}.mp4")
        video_result = download_video(video_url, save_path)
        logger.info(f"场景 {scene_id} {video_result}")
        
        return {
            "scene_id": scene_id,
            "video_url": video_url,
            "video_path": save_path,
            "narration": narration
        }
    except Exception as e:
        logger.error(f"生成场景 {scene_id} 的视频失败: {e}")
        raise
