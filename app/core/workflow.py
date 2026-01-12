import os
import json
import traceback
from typing import Dict, List, Optional, Any
from app.config import Config
from app.utils.logger import setup_logger
from app.utils.file_ops import load_novel, image_to_base64
from app.utils.video_ops import merge_videos, get_media_duration, merge_video_audio
from app.services.llm import generate_voice_script, generate_image_prompt
from app.services.media import generate_image, generate_single_video
from app.core.character import generate_character_portrait_workflow 
logger = setup_logger(__name__)

def generate_single_image_workflow(scene_id: str, scene_content: str, image_dir: str, characters: List[str] = None) -> Dict[str, Any]:
    """生成单个场景的图片（首尾帧）"""
    logger.info(f"生成场景 {scene_id} 的图像...")
    logger.debug(f"生成图像的场景描述：{scene_content}")
    logger.debug(f"场景中的人物：{characters}")
    
    try:
        # 生成文生图提示词（包含首尾帧）
        prompts = generate_image_prompt(scene_content)
        # Check for error
        if "start_frame" in prompts and prompts["start_frame"].startswith("生成失败"):
             raise Exception(prompts["start_frame"])

        image_prompt_start = prompts.get("start_frame")
        image_prompt_end = prompts.get("end_frame")
        
        logger.debug(f"场景 {scene_id} Start Prompt: {image_prompt_start}")
        logger.debug(f"场景 {scene_id} End Prompt: {image_prompt_end}")
        
        # 1. 生成 Start Frame
        save_path_start = os.path.join(image_dir, f"{scene_id}_start.jpeg")
        image_url_start = generate_image(image_prompt_start, save_path=save_path_start, characters=characters)
        if image_url_start.startswith("生成图片失败"):
             raise Exception(f"Start Frame error: {image_url_start}")
        image_base64_start = image_to_base64(save_path_start)
        logger.info(f"Start Frame saved to {save_path_start}")

        # 2. 生成 End Frame
        save_path_end = os.path.join(image_dir, f"{scene_id}_end.jpeg")
        image_url_end = generate_image(image_prompt_end, save_path=save_path_end, characters=characters)
        if image_url_end.startswith("生成图片失败"):
             raise Exception(f"End Frame error: {image_url_end}")
        image_base64_end = image_to_base64(save_path_end)
        logger.info(f"End Frame saved to {save_path_end}")
        
        return {
            "scene_id": scene_id,
            "scene_content": scene_content,
            "image_path_start": save_path_start,
            "image_url_start": image_url_start,
            "image_base64_start": image_base64_start,
            "image_prompt_start": image_prompt_start,
            "image_path_end": save_path_end,
            "image_url_end": image_url_end,
            "image_base64_end": image_base64_end,
            "image_prompt_end": image_prompt_end
        }
    except Exception as e:
        logger.error(f"生成场景 {scene_id} 的图像失败: {e}")
        raise

def create_workflow() -> Optional[Dict[str, Any]]:
    """手动编排工作流"""
    try:
        TEST_MODE = Config.TEST_MODE
        MAX_SCENES = Config.MAX_SCENES
        
        logger.info(f"1. 加载{Config.NOVEL_FILE_PATH}...")
        chapters = load_novel(Config.NOVEL_FILE_PATH)
        
        chapter_title = Config.TARGET_CHAPTER
        if chapter_title not in chapters:
            logger.error(f"未找到章节：{chapter_title}")
            raise Exception(f"未找到章节：{chapter_title}")
        
        chapter_content = chapters[chapter_title]
        logger.info(f"已加载{chapter_title}")
        
        logger.info("\n2. 生成口播文案...")
        script_file = os.path.join("history", "voice_script.json")
        os.makedirs("history", exist_ok=True)
        
        voice_script = None
        if os.path.exists(script_file):
            logger.info(f"发现已有文案文件 {script_file}，直接加载...")
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    voice_script = json.load(f)
                logger.info(f"成功加载{len(voice_script)}段口播文案")
            except Exception as e:
                logger.warning(f"加载文案文件失败: {e}，将重新生成")
        
        if not voice_script:
            voice_script_str = generate_voice_script(chapter_content)
            
            # 解析生成的JSON格式文案
            try:
                voice_script = json.loads(voice_script_str)
                logger.info(f"生成了{len(voice_script)}段口播文案")
                # 保存文案
                with open(script_file, 'w', encoding='utf-8') as f:
                    json.dump(voice_script, f, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                logger.warning(f"生成的文案不是标准JSON格式，无法进行多场景生成")
                logger.debug(f"文案内容：{voice_script_str[:100]}...")
                return None
        
        # 确定要生成的场景数量
        scene_count = len(voice_script)
        if TEST_MODE:
            scene_count = min(scene_count, MAX_SCENES)
            logger.info(f"测试模式：仅生成前{scene_count}个场景的视频")
        
        # 3. 生成所有小说人物的写真
        logger.info("\n3. 生成小说人物写真...")
        all_characters = set()
        for scene_id, scene_data in voice_script.items():
            if isinstance(scene_data, dict) and "character" in scene_data:
                characters = scene_data["character"]
                if isinstance(characters, list):
                    all_characters.update(characters)
        
        logger.info(f"从口播文案中提取到{len(all_characters)}个唯一人物：{', '.join(all_characters)}")
        
        # 生成每个人物的写真
        os.makedirs(Config.CHARACTER_DIR, exist_ok=True)
        for character_name in all_characters:
            portrait_path = os.path.join(Config.CHARACTER_DIR, f"{character_name}.png")
            if os.path.exists(portrait_path):
                logger.info(f"人物{character_name}的写真已存在，跳过生成")
                continue
            
            logger.info(f"正在生成人物{character_name}的写真...")
            try:
                result = generate_character_portrait_workflow(chapter_content, character_name)
                if result:
                    logger.info(f"人物{character_name}的写真生成成功，保存至：{result}")
                else:
                    logger.error(f"人物{character_name}的写真生成失败")
            except Exception as e:
                logger.error(f"生成人物{character_name}的写真时出错：{e}")
        
        logger.info("\n4. 根据文案生成图片...")
        image_dir = Config.IMAGE_DIR
        os.makedirs(image_dir, exist_ok=True)
        
        image_results: List[Dict[str, Any]] = []
        for i in range(1, scene_count + 1):
            scene_id = str(i)
            # 检查图片是否存在
            # 检查图片是否存在 (Start and End)
            # 检查图片是否存在 (Start and End)
            save_path_start = os.path.join(image_dir, f"{scene_id}_start.jpeg")
            save_path_end = os.path.join(image_dir, f"{scene_id}_end.jpeg")
            
            if os.path.exists(save_path_start) and os.path.exists(save_path_end):
                logger.info(f"场景 {scene_id} 图片(Start/End)已存在，跳过生成")
                if scene_id in voice_script:
                    image_results.append({
                        "scene_id": scene_id,
                        "scene_content": voice_script[scene_id]['content'],
                        "image_path_start": save_path_start,
                        "image_url_start": None, # Should define/load if needed, but not critical for resume unless needed for video gen url
                        "image_base64_start": image_to_base64(save_path_start), # Load base64 for video gen context
                        "image_prompt_start": "Loaded from file",
                        "image_path_end": save_path_end,
                        "image_url_end": None,
                        "image_base64_end": image_to_base64(save_path_end),
                        "image_prompt_end": "Loaded from file"
                    })
                continue

            if scene_id in voice_script:
                scene_content = voice_script[scene_id]['content']
                scene_characters = voice_script[scene_id].get('character', [])
                try:
                    image_result = generate_single_image_workflow(scene_id, scene_content, image_dir, characters=scene_characters)
                    image_results.append(image_result)
                except Exception as e:
                    logger.error(f"场景 {scene_id} 图片生成跳过 due to error")
        
        logger.info(f"成功生成了{len(image_results)}张图片")
        
        logger.info("\n5. 根据图片和文案生成视频...")
        video_dir = Config.VIDEO_DIR
        os.makedirs(video_dir, exist_ok=True)
        
        video_results: List[Dict[str, Any]] = []
        for scene_info in image_results:
            # 检查视频是否存在
            scene_id = scene_info["scene_id"]
            video_path = os.path.join(video_dir, f"{scene_id}.mp4")
            if os.path.exists(video_path):
                logger.info(f"场景 {scene_id} 视频已存在，跳过生成")
                video_results.append({
                    "scene_id": scene_id,
                    "video_url": None,
                    "video_path": video_path
                })
                continue
                
            try:
                # Calculate Duration
                audio_path = os.path.join("voice", f"{scene_id}.wav")
                video_duration = None
                if os.path.exists(audio_path):
                     logger.info(f"发现场景 {scene_id} 的音频文件：{audio_path}")
                     audio_duration = get_media_duration(audio_path)
                     if audio_duration > 0:
                         video_duration = min(audio_duration, 13.0)
                         logger.info(f"场景 {scene_id} 音频时长：{audio_duration}s，设置视频时长：{video_duration}s")
                     else:
                         logger.warning(f"场景 {scene_id} 音频时长获取失败或为0")
                
                video_result = generate_single_video(scene_info, video_dir, duration=video_duration)
                video_results.append(video_result)
            except Exception as e:
                logger.error(f"场景 {scene_info.get('scene_id')} 视频生成失败: {e}")
        
        logger.info(f"成功生成了{len(video_results)}个视频")

        logger.info("合并视频与音频")

        scene_count = len(video_results)
        for i in range(1, scene_count + 1):
            scene_id = str(i)
            video_path = os.path.join(video_dir, f"{scene_id}.mp4")
            audio_path = os.path.join("voice", f"{scene_id}.wav")
            output_path = os.path.join(video_dir, f"{scene_id}_voice.mp4")
            
            if os.path.exists(output_path):
                logger.info(f"场景 {scene_id} 合并后的视频已存在，跳过合并")
                continue
            
            if os.path.exists(video_path) and os.path.exists(audio_path):
                logger.info(f"正在合并场景 {scene_id} 的视频与音频...")
                merge_video_audio(video_path, audio_path, output_path)
        
        logger.info("\n6. 合并所有生成的视频...")
        video_paths = sorted(
            [result["video_path"].replace(".mp4", "_voice.mp4") for result in video_results if os.path.exists(result["video_path"].replace(".mp4", "_voice.mp4"))],
            key=lambda x: int(os.path.basename(x).split('_')[0])
        )
        
        merged_video_path = Config.MERGED_VIDEO_PATH
        merge_result = merge_videos(video_paths, merged_video_path)
        logger.info(f"{merge_result}")
        
        logger.info("\n✅ 任务完成！")
        return {
            "voice_script": voice_script,
            "image_results": image_results,
            "video_results": video_results,
            "merged_video_path": merged_video_path
        }
        
    except Exception as e:
        logger.error(f"\n❌ 任务失败：{e}")
        logger.debug(traceback.format_exc())
        return None
