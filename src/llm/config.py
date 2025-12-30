import os
from typing import Dict, Optional
from pydantic_settings import BaseSettings
import torch

from logger import logger  # 使用已配置好的 logger

current_dir = os.path.dirname(os.path.abspath(__file__))

class ModelConfig(BaseSettings):
    """Model configuration
    https://deepinfra.com/hexgrad/Kokoro-82M
    
    """
    ROOT_DIR: str = current_dir
    # Chat model settings
    CHAT_MODEL_PATH: str = os.path.join(current_dir, "models", "tencent", "Hunyuan-7B-Instruct")

    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"

    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "kokoro")  # Options: kokoro, index-tts, soulx
    # Note: index-tts and soulx may require different conda environments due to package conflicts
    # Set TTS_PROVIDER environment variable to switch between them
    
    # Embedding model settings
    EMBEDDING_MODEL_PATH: str = os.path.join(current_dir, "models", "maidalun1020", "bce-embedding-base_v1")
    
    # TTS model settings
    TTS_MODEL_PATH: str = os.path.join(current_dir, "models", "microsoft", "speecht5_tts")
    TTS_VOCODER_PATH: str = os.path.join(current_dir, "models", "microsoft", "speecht5_hifigan")

    # TTS model settings
    KOKORO_MODEL_PATH: str = os.path.join(current_dir, "models", "hexgrad", "Kokoro-82M-v1.1-zh")

    # IndexTTS model settings
    INDEX_TTS_MODEL_PATH: str = os.path.join(current_dir, "checkpoints", "IndexTeam", "IndexTTS-2")
    INDEX_TTS_HF_CACHE_DIR: str = os.path.join(current_dir, "checkpoints", "hf_cache")  # Hugging Face cache directory
    
    # SoulX TTS model settings
    SOULX_MODEL_PATH: str = os.path.join(current_dir, "pretrained_models", "SoulX-Podcast-1.7B-dialect")
    SOULX_LLM_ENGINE: str = "hf"  # "hf" or "vllm"
    SOULX_FP16_FLOW: bool = False
    SOULX_SPK_TEXT_PROMPT: Optional[str] = None  # Optional reference text
    SOULX_BASE_MODEL_PATH: str = os.path.join(current_dir, "pretrained_models", "SoulX-Podcast-1.7B")
    SOULX_DIALECTAL_MODEL_PATH: str = os.path.join(current_dir, "pretrained_models", "SoulX-Podcast-1.7B-dialect")
    
    # TTS embeddings dataset settings
    EMBEDDINGS_DATASET_NAME: str = "Matthijs/cmu-arctic-xvectors"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 9000
    
    # Voice mappings for TTS
    VOICE_MAPPINGS: Dict[str, Dict[str, str]] = {
        "speecht5": {
            "default": "0",
            "ash": "0",      # bdl (male)
            "ballad": "1",   # clb (female)
            "coral": "2",    # jmk (male)
            "sage": "3",     # ksp (male)
            "verse": "4",    # rms (male)
            # 兼容旧版本
            "alloy": "0",
            "echo": "1",
            "fable": "2",
            "onyx": "3",
            "nova": "4",
            "shimmer": "5"
        },


# CHOICES = {
# '🇺🇸 🚺 Heart ❤️': 'af_heart',
# '🇺🇸 🚺 Bella 🔥': 'af_bella',
# '🇺🇸 🚺 Nicole 🎧': 'af_nicole',
# '🇺🇸 🚺 Aoede': 'af_aoede',
# '🇺🇸 🚺 Kore': 'af_kore',
# '🇺🇸 🚺 Sarah': 'af_sarah',
# '🇺🇸 🚺 Nova': 'af_nova',
# '🇺🇸 🚺 Sky': 'af_sky',
# '🇺🇸 🚺 Alloy': 'af_alloy',
# '🇺🇸 🚺 Jessica': 'af_jessica',
# '🇺🇸 🚺 River': 'af_river',
# '🇺🇸 🚹 Michael': 'am_michael',
# '🇺🇸 🚹 Fenrir': 'am_fenrir',
# '🇺🇸 🚹 Puck': 'am_puck',
# '🇺🇸 🚹 Echo': 'am_echo',
# '🇺🇸 🚹 Eric': 'am_eric',
# '🇺🇸 🚹 Liam': 'am_liam',
# '🇺🇸 🚹 Onyx': 'am_onyx',
# '🇺🇸 🚹 Santa': 'am_santa',
# '🇺🇸 🚹 Adam': 'am_adam',
# '🇬🇧 🚺 Emma': 'bf_emma',
# '🇬🇧 🚺 Isabella': 'bf_isabella',
# '🇬🇧 🚺 Alice': 'bf_alice',
# '🇬🇧 🚺 Lily': 'bf_lily',
# '🇬🇧 🚹 George': 'bm_george',
# '🇬🇧 🚹 Fable': 'bm_fable',
# '🇬🇧 🚹 Lewis': 'bm_lewis',
# '🇬🇧 🚹 Daniel': 'bm_daniel',
# '🇬🇧 🚺xiaobei': 'zf_xiaobei',
# '🇬🇧 🚺xiaobei': 'zf_xiaoni',
# '🇬🇧 🚺xiaobei': 'zf_xiaoxiao',
# '🇬🇧 🚺xiaobei': 'zf_xiaoyi',
# '🇬🇧 🚹zm_yunjian': 'zm_yunjian',
# '🇬🇧 🚹zm_yunxi': 'zm_yunxi',
# '🇬🇧 🚺zm_yunxia': 'zm_yunxia',
# '🇬🇧 🚹zm_yunxi': 'zm_yunyang',
# }

        "kokoro": {
            "default": "am_liam",
            # 兼容旧版本
            "alloy": "am_liam",
            "echo": "am_echo",
            "ash": "am_michael",
            "coral":"af_aoede",
            "fable": "am_eric",
            "onyx": "am_onyx",
            "nova": "af_jessica",
            "shimmer": "bf_alice",
            "sage": "bf_lily",
            "af_heart":"af_heart",
            "af_alloy": "af_alloy",
            "af_aoede": "af_aoede",
            "af_bella":"af_bella",
            "af_jessica":"af_jessica",
            "af_kore":"af_kore",
            "af_nicole": "af_nicole",
            "af_nova":"af_nova",
            "af_river":"af_river",
            "af_sarah":"af_sarah",
            "af_sky":"af_sky",
            "am_adam":"am_adam",
            "am_echo":"am_echo",
            "am_eric":"am_eric",
            "am_fenrir":"am_fenrir",
            "am_liam":"am_liam",
            "am_michael":"am_michael",
            "am_onyx":"am_onyx",
            "am_puck":"am_puck",
            "am_santa":"am_santa"
        },

        "kokoro_zh": {
            "default": "zm_081",
            # 兼容旧版本
            "alloy": "zm_052",
            "echo": "zm_011",
            "ash": "zm_081",
            "coral":"zf_017",
            "fable": "zm_031",
            "onyx": "zm_041",
            "nova": "zm_061",
            "shimmer": "zf_027",
            "sage": "zf_083",
            "zf_xiaobei": "zf_xiaobei",
            "zf_xiaoni": "zf_xiaoni",
            "zf_xiaoxiao": "zf_xiaoxiao",
            "zf_xiaoyi": "zf_xiaoyi",
            "zm_yunjian": "zm_yunjian",
            "zm_yunxi": "zm_yunxi",
            "zm_yunxia": "zm_yunxia",
            "zm_yunyang": "zm_yunyang"
        },
        
        "index-tts": {
            "default": "example/男声1.wav",
            # For IndexTTS, we use audio files as voice prompts
            # These should be paths to reference audio files
            "郭德纲": "example/郭德纲.wav",
            "蜡笔小新": "example/蜡笔小新.wav",
            "男声1": "example/男声1.wav",
            "男声2": "example/男声2.wav",
            "女生_安陵容":"example/女生_安陵容.wav",
            "女生_明兰": "example/女生_明兰.wav",
            "女生_新闻联播": "example/女生_新闻联播.wav",
            "女生_甄嬛": "example/女生_甄嬛.wav",
            "佩奇": "example/佩奇.wav",
            "童声_男": "example/童声_男.wav",
            "童声_女": "example/童声_女.wav",
            "星爷": "example/星爷.wav"
        },
        
        "soulx": {
            "default": "example/男声1.wav",
            # For IndexTTS, we use audio files as voice prompts
            # These should be paths to reference audio files
            "郭德纲": "example/郭德纲.wav",
            "蜡笔小新": "example/蜡笔小新.wav",
            "男声1": "example/男声1.wav",
            "男声2": "example/男声2.wav",
            "女生_安陵容":"example/女生_安陵容.wav",
            "女生_明兰": "example/女生_明兰.wav",
            "女生_新闻联播": "example/女生_新闻联播.wav",
            "女生_甄嬛": "example/女生_甄嬛.wav",
            "佩奇": "example/佩奇.wav",
            "童声_男": "example/童声_男.wav",
            "童声_女": "example/童声_女.wav",
            "星爷": "example/星爷.wav",
            "男生_soulx1": "example/男生_soulx1.wav",
            "女生_soulx1": "example/女生_soulx1.wav",
        }
    }
    
    class Config:
        env_prefix = "LLM_"  # 环境变量前缀

# 创建全局配置实例
config = ModelConfig()

if config.TTS_PROVIDER == "kokoro":
    logger.info("Loading Kokoro voices")
    voices_path = os.path.join(config.KOKORO_MODEL_PATH, "voices")
    # voice_path 目录下以 zf, zm 开头的文件
    voice_files = [f for f in os.listdir(voices_path) if f.startswith("zf_") or f.startswith("zm_")]
    # 从文件名中提取 voice_id
    voice_ids = [f.split(".")[0] for f in voice_files]
    # 添加到 VOICE_MAPPINGS["kokoro_zh"]
    for voice_id in voice_ids:
        config.VOICE_MAPPINGS["kokoro_zh"][voice_id] = voice_id
