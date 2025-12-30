from abc import ABC, abstractmethod
import io
import numpy as np
import scipy.io.wavfile
from typing import Dict, Optional, Tuple, Literal
import torch
import time
from transformers import SpeechT5Processor, SpeechT5HifiGan, SpeechT5ForTextToSpeech
from datasets import load_dataset
import soundfile as sf
from pydub import AudioSegment
from config import config
from langdetect import detect
import re
import os

# Import logger (already configured)
try:
    from logger import logger
except ImportError:
    # Fallback if logger module is not available
    import logging
    logger = logging.getLogger("llm-service")

# Dynamic imports for TTS modules that may conflict
# These will be imported on-demand based on configuration
_KokoroTTS = None
_TTSConfig = None
_IndexTTS = None
_IndexTTSParam = None
_IndexTTSConfig = None
_SoulXTTS = None
_SoulXTTSConfig = None
_SoulXTTSParam = None

def _import_kokoro_tts():
    """Dynamically import Kokoro TTS modules"""
    global _KokoroTTS, _TTSConfig
    if _KokoroTTS is None:
        try:
            from kokoro_tts import KokoroTTS, TTSConfig
            _KokoroTTS = KokoroTTS
            _TTSConfig = TTSConfig
            logger.info("Kokoro TTS modules imported successfully")
        except ImportError as e:
            logger.warning(f"Failed to import Kokoro TTS: {e}. Kokoro TTS functionality will be unavailable.")
            raise
    return _KokoroTTS, _TTSConfig

def _import_index_tts():
    """Dynamically import IndexTTS modules"""
    global _IndexTTS, _IndexTTSParam, _IndexTTSConfig
    if _IndexTTS is None:
        try:
            from index_tts import IndexTTS, IndexTTSParam, IndexTTSConfig
            _IndexTTS = IndexTTS
            _IndexTTSParam = IndexTTSParam
            _IndexTTSConfig = IndexTTSConfig
            logger.info("IndexTTS modules imported successfully")
        except ImportError as e:
            logger.warning(f"Failed to import IndexTTS: {e}. IndexTTS functionality will be unavailable.")
            raise
    return _IndexTTS, _IndexTTSParam, _IndexTTSConfig

def _import_soulx_tts():
    """Dynamically import SoulX TTS modules"""
    global _SoulXTTS, _SoulXTTSConfig, _SoulXTTSParam
    if _SoulXTTS is None:
        try:
            from soulx_tts import SoulXTTS, SoulXTTSConfig, SoulXTTSParam
            _SoulXTTS = SoulXTTS
            _SoulXTTSConfig = SoulXTTSConfig
            _SoulXTTSParam = SoulXTTSParam
            logger.info("SoulX TTS modules imported successfully")
        except ImportError as e:
            logger.warning(f"Failed to import SoulX TTS: {e}. SoulX TTS functionality will be unavailable.")
            raise
    return _SoulXTTS, _SoulXTTSConfig, _SoulXTTSParam


class AudioConverter:
    """Audio format conversion utility"""
    
    @staticmethod
    def convert_format(
        wav_data: bytes,
        target_format: Literal["mp3", "opus", "aac", "flac"],
        sampling_rate: int
    ) -> Tuple[bytes, str]:
        """Convert audio data to target format"""
        try:
            # Load WAV data
            audio = AudioSegment.from_wav(io.BytesIO(wav_data))
            
            # Set format-specific parameters
            format_params = {
                "mp3": {"format": "mp3", "codec": "libmp3lame", "mime": "audio/mpeg"},
                "opus": {"format": "opus", "codec": "libopus", "mime": "audio/opus"},
                "aac": {"format": "adts", "codec": "aac", "mime": "audio/aac"},
                "flac": {"format": "flac", "codec": "flac", "mime": "audio/flac"}
            }
            
            params = format_params[target_format]
            
            # Convert to target format
            output = io.BytesIO()
            audio.export(
                output,
                format=params["format"],
                codec=params["codec"],
                parameters=["-ar", str(sampling_rate)]
            )
            output.seek(0)
            
            return output.getvalue(), params["mime"]
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return wav_data, "audio/wav"

class BaseTTS(ABC):
    """Base class for TTS implementations"""
    
    @abstractmethod
    def load_model(self):
        """Load the TTS model"""
        pass
    
    @abstractmethod
    def generate_speech(
        self, 
        text: str, 
        voice: str,
        output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = "mp3",
        instructions: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        speed: Optional[float] = 1.0,
        dialect: Optional[str] = None,  # 方言类型，如 "sichuan", "henan", "yue"
        dialect_prompt: Optional[str] = None  # 方言提示文本（可选）
    ) -> Tuple[bytes, str]:
        """Generate speech from text
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier
            output_format: Output audio format
            instructions: Optional instructions/style parameter
            reference_audio: Optional path to reference audio file for voice cloning
            reference_text: Optional reference text for voice cloning
            speed: Speech speed multiplier
        """
        pass
    
    @property
    @abstractmethod
    def sampling_rate(self) -> int:
        """Get the sampling rate of the model"""
        pass


class KokoroTTSWrapper(BaseTTS):
    """Kokoro TTS implementation wrapper to match BaseTTS interface"""
    
    def __init__(self):
        self.model = None
        self._sampling_rate = 24000
        # Import Kokoro TTS modules on initialization
        try:
            KokoroTTS, TTSConfig = _import_kokoro_tts()
            self.KokoroTTS = KokoroTTS
            self.TTSConfig = TTSConfig
        except ImportError as e:
            logger.error(f"Kokoro TTS is not available: {e}")
            raise RuntimeError(
                "Kokoro TTS is not available. Please ensure the required packages are installed "
                "in the current conda environment, or set TTS_PROVIDER to a different value."
            ) from e
    
    def _detect_language(self, text: str) -> str:
        """
        检测文本语言，返回 'zh' 或 'en'
        """
        try:
            # 检查是否包含中文字符
            if re.search(r'[\u4e00-\u9fff]', text):
                return 'zh'
            
            # 使用 langdetect 进行语言检测
            lang = detect(text)
            if lang == 'zh-cn' or lang == 'zh-tw':
                return 'zh'
            return 'en'
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, fallback to 'auto'")
            return 'auto'
    
    def load_model(self):
        logger.info("Loading Kokoro TTS model...")
        tts_config = self.TTSConfig(
            model_path=config.KOKORO_MODEL_PATH,
            device=config.DEVICE  # 或 "cuda" 如果使用 GPU
        )
        self.model = self.KokoroTTS(tts_config)
        logger.info("Kokoro TTS model loaded successfully")
    
    def generate_speech(
        self, 
        text: str, 
        voice: str,
        output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = "mp3",
        instructions: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        speed: Optional[float] = 1.0,
        dialect: Optional[str] = None,  # 方言类型（Kokoro 不支持方言语音，但会保留文本中的方言标记）
        dialect_prompt: Optional[str] = None  # 方言提示文本（Kokoro 不支持）
    ) -> Tuple[bytes, str]:
        try:
            # 处理方言标记：移除方言标记（Kokoro 不支持方言语音生成）
            # 但保留文本内容以便后续处理
            try:
                from dialect_utils import remove_dialect_tag
                processed_text = remove_dialect_tag(text)
                if processed_text != text:
                    logger.info(f"Removed dialect tag from text (Kokoro doesn't support dialect)")
            except ImportError:
                processed_text = text
            
            # 检测语言
            detected_lang = self._detect_language(processed_text)
            logger.info(f"Detected language: {detected_lang} for text: {processed_text[:50]}...")
            
            # 根据语言选择声音映射
            voice_map = config.VOICE_MAPPINGS["kokoro_zh" if detected_lang == "zh" else "kokoro"]
            kokoro_voice = voice_map.get(voice, voice_map["default"])
            logger.info(f"Using Kokoro voice: {kokoro_voice} for OpenAI voice: {voice}")
            
            if instructions:
                logger.info(f"Instructions parameter provided: {instructions} (not used by Kokoro)")
            
            if dialect:
                logger.warning(f"Dialect '{dialect}' specified but Kokoro TTS doesn't support dialect generation. Using standard Chinese.")
            
            # 生成音频
            st = time.time()
            audio_array = self.model.generate_speech(
                processed_text,
                speaker=kokoro_voice,
                language=detected_lang,
                speed=speed
            )
            end = time.time()
            logger.info(f"Inference time: {end-st} s")
            
            # 转换为字节
            buffer = io.BytesIO()
            scipy.io.wavfile.write(buffer, rate=self.sampling_rate, data=audio_array)
            buffer.seek(0)
            wav_data = buffer.getvalue()
            
            # 转换为目标格式
            if output_format != "wav":
                return AudioConverter.convert_format(wav_data, output_format, self.sampling_rate)
            
            return wav_data, "audio/wav"
            
        except Exception as e:
            logger.error(f"Error generating speech with Kokoro: {str(e)}")
            raise
    
    @property
    def sampling_rate(self) -> int:
        return self._sampling_rate

class TTSFactory:
    """Factory class for creating TTS instances"""
    
    _instances: Dict[str, BaseTTS] = {}
    
    @classmethod
    def get_tts(cls, model_name: str = "kokoro") -> BaseTTS:
        """Get TTS instance based on model name"""
        if model_name not in cls._instances:
            if model_name == "kokoro":
                tts = KokoroTTSWrapper()
            elif model_name == "index-tts":
                tts = IndexTTSWrapper()
            elif model_name == "soulx":
                tts = SoulXTTSWrapper()
            else:
                raise ValueError(
                    f"Unknown TTS model: {model_name}. "
                    f"Supported models: kokoro, index-tts, soulx"
                )
            
            tts.load_model()
            cls._instances[model_name] = tts
        
        return cls._instances[model_name]

class IndexTTSWrapper(BaseTTS):
    """IndexTTS implementation wrapper to match BaseTTS interface"""
    
    def __init__(self):
        self.model = None
        self._sampling_rate = 24000
        # Import IndexTTS modules on initialization
        try:
            IndexTTS, IndexTTSParam, IndexTTSConfig = _import_index_tts()
            self.IndexTTS = IndexTTS
            self.IndexTTSParam = IndexTTSParam
            self.IndexTTSConfig = IndexTTSConfig
        except ImportError as e:
            logger.error(f"IndexTTS is not available: {e}")
            raise RuntimeError(
                "IndexTTS is not available. Please ensure the required packages are installed "
                "in the current conda environment, or set TTS_PROVIDER to a different value."
            ) from e
    
    def load_model(self):
        logger.info("Loading IndexTTS model...")
        # Get HF cache directory from config
        hf_cache_dir = getattr(config, 'INDEX_TTS_HF_CACHE_DIR', None)
        cfg = self.IndexTTSConfig(
            model_path=config.INDEX_TTS_MODEL_PATH,
            device=config.DEVICE,
            sampling_rate=self._sampling_rate,
            hf_cache_dir=hf_cache_dir
        )
        self.model = self.IndexTTS(cfg)
        logger.info("IndexTTS model loaded successfully")
    
    def generate_speech(
        self,
        text: str,
        voice: str,
        output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = "mp3",
        instructions: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        speed: Optional[float] = 1.0,
        dialect: Optional[str] = None,  # 方言类型（IndexTTS 不支持方言语音，但会保留文本中的方言标记）
        dialect_prompt: Optional[str] = None  # 方言提示文本（IndexTTS 不支持）
    ) -> Tuple[bytes, str]:
        try:
            # 处理方言标记：移除方言标记（IndexTTS 不支持方言语音生成）
            # 但保留文本内容以便后续处理
            try:
                from dialect_utils import remove_dialect_tag
                processed_text = remove_dialect_tag(text)
                if processed_text != text:
                    logger.info(f"Removed dialect tag from text (IndexTTS doesn't support dialect)")
            except ImportError:
                processed_text = text
            
            # For IndexTTS, we need to provide the required parameters
            # Use reference_audio if provided, otherwise get from config
            if reference_audio and os.path.exists(reference_audio):
                spk_audio_prompt = reference_audio
                logger.info(f"Using custom reference audio: {spk_audio_prompt}")
            else:
                # Get the voice prompt file path from config
                voice_prompt_file = config.VOICE_MAPPINGS.get("index-tts", {}).get(voice, "example/voice_12.wav")
                
                # Resolve the full path relative to the current directory
                current_dir = os.path.dirname(os.path.abspath(__file__))
                spk_audio_prompt = os.path.join(current_dir, voice_prompt_file)
                
                # Check if the voice prompt file exists
                if not os.path.exists(spk_audio_prompt):
                    logger.warning(f"Voice prompt file not found: {spk_audio_prompt}, using default")
                    spk_audio_prompt = os.path.join(current_dir, "example", "voice_12.wav")
            
            # Use instructions parameter as emo_text if provided
            emo_text = instructions if instructions else None
            use_emo_text = instructions is not None
            
            if reference_text:
                logger.info(f"Reference text provided: {reference_text[:50]}... (not used by IndexTTS)")
            
            if dialect:
                logger.warning(f"Dialect '{dialect}' specified but IndexTTS doesn't support dialect generation. Using standard Chinese.")
            
            st = time.time()
            audio_array = self.model.generate_speech(
                param=self.IndexTTSParam(
                    text=processed_text,
                    spk_audio_prompt=spk_audio_prompt,
                    emo_text=emo_text,
                    use_emo_text=use_emo_text,
                    emo_audio_prompt=None,
                    output_path=None,
                    verbose=False
                )
            )
            end = time.time()
            logger.info(f"Inference time: {end-st} s")
            
            # 转换为字节
            buffer = io.BytesIO()
            scipy.io.wavfile.write(buffer, rate=self.sampling_rate, data=audio_array)
            buffer.seek(0)
            wav_data = buffer.getvalue()
            
            # 转换为目标格式
            if output_format != "wav":
                return AudioConverter.convert_format(wav_data, output_format, self.sampling_rate)
            
            return wav_data, "audio/wav"
        except Exception as e:
            logger.error(f"Error generating speech with IndexTTS: {str(e)}")
            raise
    
    @property
    def sampling_rate(self) -> int:
        return self._sampling_rate

class SoulXTTSWrapper(BaseTTS):
    """SoulX TTS implementation wrapper to match BaseTTS interface"""
    
    def __init__(self):
        self.model = None
        self._sampling_rate = 24000
        # Import SoulX TTS modules on initialization
        try:
            SoulXTTS, SoulXTTSConfig, SoulXTTSParam = _import_soulx_tts()
            self.SoulXTTS = SoulXTTS
            self.SoulXTTSConfig = SoulXTTSConfig
            self.SoulXTTSParam = SoulXTTSParam
        except ImportError as e:
            logger.error(f"SoulX TTS is not available: {e}")
            raise RuntimeError(
                "SoulX TTS is not available. Please ensure the required packages are installed "
                "in the current conda environment, or set TTS_PROVIDER to a different value."
            ) from e
    
    def load_model(self):
        logger.info("Loading SoulX TTS model...")
        # Get model path from config, with fallback to environment variable
        model_path = getattr(config, 'SOULX_MODEL_PATH', None) or os.getenv('SOULX_MODEL_PATH')
        if not model_path:
            raise ValueError(
                "SOULX_MODEL_PATH not configured. "
                "Set SOULX_MODEL_PATH in config or environment variable."
            )
        
        # Get device from config
        device = getattr(config, 'DEVICE', 'cuda')
        llm_engine = getattr(config, 'SOULX_LLM_ENGINE', 'hf')
        fp16_flow = getattr(config, 'SOULX_FP16_FLOW', False)
        
        cfg = self.SoulXTTSConfig(
            model_path=model_path,
            device=device,
            sampling_rate=self._sampling_rate,
            llm_engine=llm_engine,
            fp16_flow=fp16_flow
        )
        self.model = self.SoulXTTS(cfg)
        logger.info("SoulX TTS model loaded successfully")
    
    def generate_speech(
        self,
        text: str,
        voice: str,
        output_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = "mp3",
        instructions: Optional[str] = None,
        reference_audio: Optional[str] = None,
        reference_text: Optional[str] = None,
        speed: Optional[float] = 1.0,
        dialect: Optional[str] = None,  # 方言类型，如 "sichuan", "henan", "yue"
        dialect_prompt: Optional[str] = None  # 方言提示文本（可选）
    ) -> Tuple[bytes, str]:
        try:
            # For SoulX TTS, we need to provide the required parameters
            # Use reference_audio if provided, otherwise get from config
            if reference_audio and os.path.exists(reference_audio):
                spk_audio_prompt = reference_audio
                logger.info(f"Using custom reference audio: {spk_audio_prompt}")
            else:
                # Get the voice prompt file path from config or use default
                voice_mappings = config.VOICE_MAPPINGS.get("soulx", {})
                voice_prompt_file = voice_mappings.get(voice, voice_mappings.get("default", "example/voice_01.wav"))
                
                # Resolve the full path relative to the current directory
                current_dir = os.path.dirname(os.path.abspath(__file__))
                spk_audio_prompt = os.path.join(current_dir, voice_prompt_file)
                
                # Check if the voice prompt file exists
                if not os.path.exists(spk_audio_prompt):
                    logger.warning(f"Voice prompt file not found: {spk_audio_prompt}, using default")
                    default_prompt = os.path.join(current_dir, "example", "voice_01.wav")
                    if os.path.exists(default_prompt):
                        spk_audio_prompt = default_prompt
                    else:
                        raise FileNotFoundError(
                            f"Reference audio file not found: {spk_audio_prompt}. "
                            "Please provide a valid reference audio file path or use reference_audio parameter."
                        )
            
            # Use reference_text if provided, otherwise get from config
            spk_text_prompt = reference_text or getattr(config, 'SOULX_SPK_TEXT_PROMPT', None)
            
            if instructions:
                logger.info(f"Instructions parameter provided: {instructions} (not used by SoulX)")
            
            # Log dialect usage if provided
            if dialect:
                logger.info(f"Using dialect: {dialect}")
            
            st = time.time()
            audio_array = self.model.generate_speech(
                param=self.SoulXTTSParam(
                    text=text,
                    spk_audio_prompt=spk_audio_prompt,
                    spk_text_prompt=spk_text_prompt,
                    output_path=None,
                    verbose=False,
                    dialect=dialect,
                    dialect_prompt=dialect_prompt
                )
            )
            end = time.time()
            logger.info(f"Inference time: {end-st} s")
            
            # 转换为字节
            buffer = io.BytesIO()
            scipy.io.wavfile.write(buffer, rate=self.sampling_rate, data=audio_array)
            buffer.seek(0)
            wav_data = buffer.getvalue()
            
            # 转换为目标格式
            if output_format != "wav":
                return AudioConverter.convert_format(wav_data, output_format, self.sampling_rate)
            
            return wav_data, "audio/wav"
        except Exception as e:
            logger.error(f"Error generating speech with SoulX: {str(e)}")
            raise
    
    @property
    def sampling_rate(self) -> int:
        return self._sampling_rate
