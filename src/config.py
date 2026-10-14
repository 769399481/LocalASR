"""
项目配置
"""

from pathlib import Path
from app_paths import PATHS, translation_model_path

# 项目根目录
PROJECT_ROOT = PATHS.data

# 模型目录
MODEL_PATH = PROJECT_ROOT / "models" / "large-v3"

# 输入输出目录
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PATHS.output
LOG_DIR = PATHS.logs

# GPU 自动检测
def default_asr_device():
    # ASR uses CTranslate2, independently of the CPU translation runtime.
    try:
        import ctranslate2
        return "cuda" if ctranslate2.get_cuda_device_count() else "cpu"
    except (ImportError, OSError, RuntimeError):
        return "cpu"


DEVICE = default_asr_device()

# GPU 推荐 float16
# CPU 推荐 int8
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

# 默认识别语言
# None 或 "auto" = 自动检测
# "en" = 英文
# "zh" = 中文
LANGUAGE = "en"

# beam 越大越准确，速度越慢
BEAM_SIZE = 5

# 支持的音频格式
SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".aac",
    ".ogg",
    ".mp4",
}

# 是否跳过已完成文件
SKIP_EXISTING = True

# 每个任务要求的输出格式；完成判定与导出使用同一配置。
OUTPUT_FORMATS = ("txt", "docx", "json", "srt", "vtt")

# Optional offline translation; ASR's LANGUAGE remains independently configured.
TRANSLATION_ENABLED = False
TRANSLATION_SOURCE_LANGUAGE = "en"
TRANSLATION_TARGET_LANGUAGE = "zh-Hans"
TRANSLATION_BACKEND = "marian_local"
TRANSLATION_MODEL_PATH = translation_model_path()
