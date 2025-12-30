import os
from pathlib import Path
import re
import numpy as np
import torch
from dataclasses import dataclass
from typing import Optional
import soundfile as sf
import tempfile

# Import logger (already configured)
try:
    from logger import logger
except ImportError:
    # Fallback if logger module is not available
    import logging
    logger = logging.getLogger("llm-service")

# Set Hugging Face cache directory before importing IndexTTS2
# This must be done before importing indextts modules
# Note: infer_v2.py sets HF_HUB_CACHE to './checkpoints/hf_cache' (relative path)
# We override it here with absolute path from config
def _setup_hf_cache(cache_dir: Optional[str] = None):
    """Setup Hugging Face cache directory"""
    if cache_dir:
        # Convert to absolute path
        cache_dir = os.path.abspath(cache_dir)
    else:
        # Use default from config
        try:
            from config import config
            cache_dir = getattr(config, 'INDEX_TTS_HF_CACHE_DIR', None)
            if cache_dir:
                cache_dir = os.path.abspath(cache_dir)
        except ImportError:
            cache_dir = None
    
    if cache_dir:
        # Create directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        # Set multiple environment variables for compatibility
        # These must be set before importing any huggingface_hub or transformers modules
        os.environ['HF_HUB_CACHE'] = cache_dir
        os.environ['HF_HOME'] = cache_dir
        os.environ['TRANSFORMERS_CACHE'] = cache_dir
        os.environ['HF_DATASETS_CACHE'] = cache_dir
        # Also set XDG_CACHE_HOME for some libraries
        os.environ['XDG_CACHE_HOME'] = cache_dir
        logger.info(f"Set Hugging Face cache directory to: {cache_dir}")
        logger.info(f"Environment variable HF_HUB_CACHE = {os.environ.get('HF_HUB_CACHE')}")

# Setup cache directory before importing IndexTTS2
# This will override the default './checkpoints/hf_cache' in infer_v2.py
_setup_hf_cache()

from indextts.infer_v2 import IndexTTS2

@dataclass
class IndexTTSConfig:
    """
    Configuration for IndexTTS.
    model_path: 模型保存路径（例如存放 TorchScript 文件的位置）
    device: 计算设备 ("cpu" 或 "cuda")
    sampling_rate: 输出音频采样率
    language: 语言参数，默认 "auto"
    hf_cache_dir: Hugging Face 缓存目录（可选，默认使用 config.INDEX_TTS_HF_CACHE_DIR）
    """
    model_path: str
    device: str = "cpu"
    sampling_rate: int = 24000
    language: str = "auto"
    hf_cache_dir: Optional[str] = None

@dataclass
class IndexTTSParam:
    text: str
    spk_audio_prompt: str
    emo_text: Optional[str] = None
    use_emo_text: bool = False
    emo_audio_prompt: Optional[str] = None
    output_path: Optional[str] = None
    verbose: bool = False

class IndexTTS:
    """
    KokoroTTS 类实现文本转语音。假定使用 TorchScript 模型保存，
    """
    def __init__(self, config: IndexTTSConfig):
        self.config = config
        self.device = config.device
        self.sampling_rate = config.sampling_rate
        self.model = None
        
        # Setup HF cache directory if specified
        if config.hf_cache_dir:
            _setup_hf_cache(config.hf_cache_dir)
        
        self._load_model()
        
    def _load_model(self):
        """加载 Index TTS 模型"""
        try:
           logger.info("load indextts model from %s", self.config.model_path)
           logger.info("HF cache directory: %s", os.environ.get('HF_HUB_CACHE', 'default'))
           self.model  = IndexTTS2(cfg_path=os.path.join(self.config.model_path, "config.yaml"), model_dir=self.config.model_path, device=self.device, use_fp16=False, use_deepspeed=False)
           logger.info("IndexTTS pipeline voices loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load IndexTTS model: {str(e)}")
            raise
        
    def generate_speech(self, param: IndexTTSParam) -> np.ndarray:
        """
        生成语音
        :param param: IndexTTSParam 参数对象
        :return: 生成的语音 numpy 数组
        """
        temp_output_path = None
        try:
            # IndexTTS infer 方法需要 output_path，如果没有提供则创建临时文件
            if param.output_path:
                output_path = param.output_path
            else:
                # 创建临时文件
                temp_output_path = tempfile.NamedTemporaryFile(
                    suffix='.wav', 
                    delete=False,
                    dir=os.path.dirname(os.path.abspath(__file__))
                )
                output_path = temp_output_path.name
                temp_output_path.close()
                logger.debug(f"Created temporary output path: {output_path}")
            
            # 构建 infer 参数，output_path 是必需的
            infer_params = {
                'text': param.text,
                'spk_audio_prompt': param.spk_audio_prompt,
                'output_path': output_path,
                'use_emo_text': param.use_emo_text,
                'verbose': param.verbose
            }
            
            # Only add optional parameters if they are not None
            if param.emo_text is not None:
                infer_params['emo_text'] = param.emo_text
                infer_params['emo_alpha'] = 0.6
            if param.emo_audio_prompt is not None:
                infer_params['emo_audio_prompt'] = param.emo_audio_prompt
            
            # 调用 infer 方法（它会将音频保存到 output_path）
            logger.info(f"Calling IndexTTS infer with output_path: {output_path}")
            result = self.model.infer(**infer_params)
            
            # infer 方法可能返回文件路径或 None，我们需要从文件读取音频
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Audio file was not generated at expected path: {output_path}")
            
            # 从文件读取音频数据
            audio, sampling_rate = sf.read(output_path)
            logger.info(f"Loaded audio from {output_path}, shape: {audio.shape}, sampling_rate: {sampling_rate}")
            
            # 确保返回的是 numpy 数组
            if isinstance(audio, np.ndarray):
                return audio
            else:
                return np.array(audio)
                
        except Exception as e:
            logger.error(f"Failed to generate speech: {str(e)}")
            raise
        finally:
            # 清理临时文件
            if temp_output_path and os.path.exists(temp_output_path.name):
                try:
                    os.unlink(temp_output_path.name)
                    logger.debug(f"Cleaned up temporary file: {temp_output_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_output_path.name}: {e}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    INDEX_TTS_MODEL_PATH = "/Users/jun/GolandProjects/competition/tencent-hunyuan-ai-podcast/src/llm/checkpoints/IndexTeam/IndexTTS-2"
    tts = IndexTTS(IndexTTSConfig(model_path=INDEX_TTS_MODEL_PATH))
    en_text = """istio is an open source service mesh that layers transparently onto existing distributed applications. Istio’s powerful features provide a uniform and more efficient way to secure, connect, and monitor services. Istio is the path to load balancing, service-to-service authentication, and monitoring – with few or no service code changes."""
    zh_text = """Istio 是一个开源的服务网格，它透明地层叠到现有的分布式应用程序上。Istio 强大的功能提供了一种统一且更高效的方式来保护、连接和监控服务。Istio 是负载均衡、服务间认证和监控的途径，而无需对服务代码进行重大更改。"""
    emo_text = """Tone: The voice should be refined, formal, and delightfully theatrical, reminiscent of a charming radio announcer from the early 20th century.
Pacing: The speech should flow smoothly at a steady cadence, neither rushed nor sluggish, allowing for clarity and a touch of grandeur.
Pronunciation: Words should be enunciated crisply and elegantly, with an emphasis on vintage expressions and a slight flourish on key phrases.
Emotion: The delivery should feel warm, enthusiastic, and welcoming, as if addressing a distinguished audience with utmost politeness.
Inflection: Gentle rises and falls in pitch should be used to maintain engagement, adding a playful yet dignified flair to each sentence.
Word Choice: The script should incorporate vintage expressions like splendid, marvelous, posthaste, and ta-ta for now, avoiding modern slang.
"""
#     emo_text = """
#    Voice Affect: Low, hushed, and suspenseful; convey tension and intrigue.
# Tone: Deeply serious and mysterious, maintaining an undercurrent of unease throughout.
# Pacing: Slow, deliberate, pausing slightly after suspenseful moments to heighten drama.
# Emotion: Restrained yet intense—voice should subtly tremble or tighten at key suspenseful points.
# Emphasis: Highlight sensory descriptions ("footsteps echoed," "heart hammering," "shadows melting into darkness") to amplify atmosphere.
# Pronunciation: Slightly elongated vowels and softened consonants for an eerie, haunting effect.
# Pauses: Insert meaningful pauses after phrases like "only shadows melting into darkness," and especially before the final line, to enhance suspense dramatically."""

    spk_audio_prompt = os.path.join(current_dir, "example", "voice_12.wav")
    output_path = os.path.join(current_dir, "example", "output.wav")
    print(f"output_path: {output_path}")
    final_audio = tts.generate_speech(IndexTTSParam(
        text=zh_text,
        spk_audio_prompt=spk_audio_prompt,
        output_path=output_path,
        verbose=False,
        emo_audio_prompt = None,
        use_emo_text=True,
        emo_text=emo_text
    ))
    
    output_path = Path("output.wav")
    sf.write(output_path, final_audio, 24000)
    print(f"\nAudio saved to {output_path.absolute()}")
