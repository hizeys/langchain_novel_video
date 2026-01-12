import argparse
from app.config import Config
from app.core.workflow import create_workflow

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="小说视频生成工具")
    parser.add_argument("--test", action="store_true", help="启用测试模式")
    parser.add_argument("--no-test", dest="test", action="store_false", help="禁用测试模式")
    parser.add_argument("--max-scenes", type=int, default=Config.MAX_SCENES, help="最大生成场景数")
    parser.add_argument("--chapter", type=str, default=Config.TARGET_CHAPTER, help="目标章节")
    parser.add_argument("--novel-file", type=str, default=Config.NOVEL_FILE_PATH, help="小说文件路径")
    parser.set_defaults(test=Config.TEST_MODE)
    return parser.parse_args()

if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 根据命令行参数更新配置
    Config.TEST_MODE = args.test
    Config.MAX_SCENES = args.max_scenes
    Config.TARGET_CHAPTER = args.chapter
    Config.NOVEL_FILE_PATH = args.novel_file
    
    # 运行主程序
    create_workflow()
