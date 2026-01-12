import os
import logging
from typing import Optional
from app.config import Config
from app.services.llm import extract_character_appearance, generate_image_prompt
from app.services.media import generate_image

# Reuse central logger
logger = logging.getLogger("app.core.character")

def generate_character_portrait_workflow(novel_text: str, character_name: str) -> Optional[str]:
    """
    生成人物写真工作流
    
    Args:
        novel_text: 小说文本
        character_name: 人物名称
    
    Returns:
        生成的图像保存路径，或None（如果失败）
    """
    logger.info(f"开始处理人物: {character_name}")
    
    # 1. 提取人物外貌特征
    logger.info("1. 正在从小说中提取人物外貌特征...")
    appearance_features = extract_character_appearance(novel_text, character_name)
    if not appearance_features:
        logger.error("无法提取人物外貌特征")
        return None
    logger.info(f"提取到的外貌特征: {appearance_features}")
    
    # 2. 生成文生图提示词
    logger.info("2. 正在生成文生图提示词...")
    scene_content = f"人物{character_name}的外貌特征：{appearance_features}"
    prompt = generate_image_prompt(scene_content)
    if not prompt:
        logger.error("无法生成文生图提示词")
        return None
    logger.info(f"生成的提示词: {prompt}")
    
    # 3. 生成人物写真并保存
    logger.info("3. 正在生成人物写真...")
    os.makedirs(Config.CHARACTER_DIR, exist_ok=True)
    save_path = os.path.join(Config.CHARACTER_DIR, f"{character_name}.png")
    
    # Note: Character portraits don't use reference images themselves usually, 
    # but the function signature supports it. Here we just generate base based on text.
    image_url = generate_image(prompt, size="1440x2560", save_path=save_path)
    
    if image_url and not image_url.startswith("生成图片失败"):
        logger.info(f"人物{character_name}的写真生成完成！")
        return save_path
    else:
        logger.error(f"人物{character_name}的写真生成失败")
        return None
