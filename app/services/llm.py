import json
from typing import Any, Dict
from langchain.chat_models import init_chat_model
from app.config import Config
from app.prompts import PORTAL_PROMPT, IMAGE_PROMPT, VIDEO_PROMPT
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def initialize_chat_model() -> Any:
    """初始化聊天模型"""
    return init_chat_model(
        model=Config.LLM_MODEL,
        model_provider=Config.LLM_MODEL_PROVIDER,
        api_key=Config.DASHSCOPE_API_KEY,
        base_url=Config.LLM_BASE_URL
    )

def generate_voice_script(chapter_content: str) -> str:
    """根据小说的一个章节内容生成口播文案"""
    try:
        logger.info("开始生成口播文案...")
        logger.debug(f"输入的章节内容：{chapter_content[:100]}...")
        
        model = initialize_chat_model()
        response = model.invoke([
                {"role": "system", "content": PORTAL_PROMPT},
                {"role": "user", "content": f"请根据以下章节内容生成口播文案：\n{chapter_content}"}
        ])
        
        content = response.content.strip()
        if content.startswith('```json'): # Clean markdown
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        if content.strip().startswith('```'): # Handle implicit json block
             content = content.replace('```', '')

        json.loads(content) # Validate
        
        logger.info("口播文案生成成功！")
        return content
    except json.JSONDecodeError as e:
        logger.error(f"生成的口播文案JSON格式无效：{e}")
        return f"生成的口播文案JSON格式无效，错误信息：{e}"
    except Exception as e:
        logger.error(f"生成口播文案失败：{e}", exc_info=True)
        return f"生成口播文案失败，错误信息：{e}"

def generate_image_prompt(scene_content: str) -> Dict[str, str]:
    """根据口播文案的一个场景生成文生图提示词（首帧+尾帧）"""
    try:
        logger.info("开始生成文生图提示词(Start/End)...")
        model = initialize_chat_model()
        response = model.invoke([
                {"role": "system", "content": IMAGE_PROMPT},
                {"role": "user", "content": f"请根据以下小说场景描述生成文生图提示词（包含start_frame和end_frame）：\n{scene_content}"}
        ])
        content = response.content.strip()
        # Clean markdown
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        if content.strip().startswith('```'):
             content = content.replace('```', '')
        
        try:
            prompts = json.loads(content)
            if "start_frame" not in prompts or "end_frame" not in prompts:
                raise ValueError("缺少start_frame或end_frame字段")
            logger.info("文生图提示词生成成功！")
            return prompts
        except json.JSONDecodeError:
            logger.error(f"生成的提示词非JSON格式: {content}")
            # Fallback: Treat entire content as start frame, empty end frame or try to fix
            return {"start_frame": content, "end_frame": content} 
            
    except Exception as e:
        logger.error(f"生成文生图提示词失败：{e}", exc_info=True)
        return {"start_frame": f"生成失败: {e}", "end_frame": f"生成失败: {e}"}

def generate_video_prompt(scene_info: Dict[str, Any]) -> str:
    """根据口播文案及首尾帧信息生成图生视频提示词"""
    try:
        logger.info("开始生成图生视频提示词...")
        model = initialize_chat_model()
        
        user_content = [
            {"type":"text","text":f"根据以下场景描述及首尾帧图片生成视频提示词:\n场景内容: {scene_info.get('scene_content','')}\nStart Prompt: {scene_info.get('image_prompt_start','')}\nEnd Prompt: {scene_info.get('image_prompt_end','')}"}
        ]
        
        # Add start image if available
        if "image_base64_start" in scene_info and scene_info["image_base64_start"]:
             user_content.append({"type":"image","base64":scene_info["image_base64_start"],"mime_type":"image/jpeg"})
        
        # Add end image if available
        if "image_base64_end" in scene_info and scene_info["image_base64_end"]:
             user_content.append({"type":"image","base64":scene_info["image_base64_end"],"mime_type":"image/jpeg"})

        response = model.invoke([
                {"role": "system", "content": VIDEO_PROMPT},
                {"role": "user", "content": user_content}
        ])
        content = response.content.strip()
        # Clean markdown
        if content.startswith('```'):
            lines = content.split('\n')
            if len(lines) > 1:
                content = lines[1] if not lines[0].lower().startswith('```') else '\n'.join(lines[1:])
            content = content.replace('```', '')
            
        logger.info("图生视频提示词生成成功！")
        return content.strip()
    except Exception as e:
        logger.error(f"生成图生视频提示词失败：{e}", exc_info=True)
        return f"生成图生视频提示词失败，错误信息：{e}"

def extract_character_appearance(novel_text: str, character_name: str) -> str:
    """从小说文本中提取人物的外貌特征"""
    try:
        model = initialize_chat_model()
        system_prompt = "你是一个专业的文学分析助手，请从小说文本中提取指定人物的外貌特征描述，只返回提取到的外貌特征，不要添加任何其他内容。"
        user_prompt = f"请从以下小说文本中提取人物{character_name}的外貌特征：\n{novel_text}"
        
        response = model.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        return str(response.content).strip()
    except Exception as e:
        logger.error(f"提取人物外貌特征时出错: {e}")
        return f"{character_name}的外貌特征：从小说中提取"
