# LangChain Novel Video Generator

这是一个基于 LangChain/LangGraph 架构的自动化小说视频生成 Agent。它能够将纯文本小说章节转化成包含口播配音、角色一致性插画和动态视频的完整作品。

## 🌟 核心特性

- **LangGraph 工作流编排**：采用状态机模式管理复杂的视频生成流程，确保各环节高效衔接。
- **角色一致性 (Character Consistency)**：自动提取小说人物属性，生成固定的角色写真，并在后续场景生成中保持形象一致。
- **断点续传 (Breakpoint Resume)**：支持任务中断后自动跳过已完成的配音、图片和视频片段，从故障点继续。
- **智能文案拆解**：自动将小说章节拆分为适合口播的脚本场景，并匹配相应的视觉描述。
- **多模型支持**：支持通义千问 (Qwen)、豆包 (Doubao) 等多种 LLM 和多媒体生成模型。
- **自动视频合成**：自动对齐音频与视频时长，并完成所有场景片段的无缝拼接。

## 📂 项目结构

```text
langchain_novel_video/
├── app/
│   ├── core/           # 核心逻辑 (工作流、角色管理)
│   ├── services/       # 外部服务接口 (LLM、多媒体生成)
│   ├── utils/          # 工具类 (文件操作、视频处理、日志)
│   ├── config.py       # 项目全局配置
│   └── prompts.py      # 提示词模板
├── character/          # 存储生成的固定角色写真
├── history/            # 存储中间生成的文案脚本 (用于断点续传)
├── image/              # 每一个场景生成的图片 (首尾帧)
├── video/              # 生成的单场景视频片段
├── voice/              # 场景配音文件 (应手动/外部准备或集成)
├── main.py             # 命令行入口
└── 小说素材.txt        # 输入的小说文本
```

## 🛠️ 环境准备

1.  **克隆项目**
    ```bash
    git clone <repository-url>
    cd langchain_novel_video
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置文件**
    在根目录创建 `.env` 文件，配置相关 API Key：
    ```env
    DASHSCOPE_API_KEY=your_aliyun_api_key
    DOUBAO_API_KEY=your_doubao_api_key
    ```
    你也可以在 `app/config.py` 中修改以下配置：
    - `JIMENG_MODEL_NAME`: 即梦AI视频生成模型名称 (默认: `jimeng_i2v_first_tail_v30`)
    - `VIDEO_FRAME_RATE`: 视频帧率 (默认: `24`)
    - `VIDEO_MIN_FRAMES`: 视频最小帧数 (默认: `141`)
    - `VIDEO_MAX_FRAMES`: 视频最大帧数 (默认: `241`)

## 🚀 使用指南

### 快速启动
运行 `main.py` 开始生成默认章节的视频：
```bash
python main.py
```

### 命令行参数
| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `--test` / `--no-test` | 是否启用测试模式（仅生成少量场景） | `Config.TEST_MODE` |
| `--max-scenes` | 最大生成场景数 | `1` |
| `--chapter` | 指定要处理的章节标题 | 从 `Config` 读取 |
| `--novel-file` | 指定小说素材文件路径 | `小说素材.txt` |

**示例：**
```bash
python main.py --no-test --max-scenes 10 --chapter "第一章 重生"
```

## 🔄 工作流说明

1.  **解析小说**：加载素材文件，解析出目标章节内容。
2.  **文案生成**：LLM 分析章节并生成包含「场景描述」和「角色信息」的口播脚本。
3.  **角色固化**：针对脚本中出现的人物，生成高品质写真并保存，确保全片角色形象统一。
4.  **画面绘制**：根据场景描述和角色写真，生成各场景的首帧与尾帧。
5.  **视频生成**：通过 I2V (Image-to-Video) 技术，结合首尾帧生成动态视频片段。
6.  **音画合成**：将预设/生成的配音与视频片段合并。
7.  **最终拼接**：将所有场景片段合并成一个完整的 `merged_video.mp4`。

## 📝 注意事项

- 请确保网络环境能够正常访问 DashScope 等 API 服务。
- 视频生成耗时较长，建议先开启 `--test` 模式验证效果。
