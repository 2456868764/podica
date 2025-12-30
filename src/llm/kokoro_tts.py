import os
from pathlib import Path
import re
import numpy as np
import torch
from dataclasses import dataclass
from typing import Optional
from kokoro import KModel, KPipeline
from config import config
import soundfile as sf

# Import logger (already configured)
try:
    from logger import logger
except ImportError:
    # Fallback if logger module is not available
    import logging
    logger = logging.getLogger("llm-service")

@dataclass
class TTSConfig:
    """
    Configuration for Kokoro TTS.
    model_path: 模型保存路径（例如存放 TorchScript 文件的位置）
    device: 计算设备 ("cpu" 或 "cuda")
    sampling_rate: 输出音频采样率
    language: 语言参数，默认 "auto"
    """
    model_path: str
    device: str = "cpu"
    sampling_rate: int = 24000
    language: str = "auto"

class KokoroTTS:
    """
    KokoroTTS 类实现文本转语音。假定使用 TorchScript 模型保存，
    """
    def __init__(self, config: TTSConfig):
        self.config = config
        self.device = config.device
        self.sampling_rate = config.sampling_rate
        self.model = None
        self.pipeline = None
        self.pipeline_zh = None
        self.repo_id = "hexgrad/Kokoro-82M-v1.1-zh"
        self._load_model()
        
    def _load_model(self):
        """加载 Kokoro TTS 模型，假定模型文件为 {model_path}/model.pt"""
        try:
            model_file = f"{self.config.model_path}/kokoro-v1_1-zh.pth"
            config_file = f"{self.config.model_path}/config.json"
            logger.info(f"Loading Kokoro TTS model from {model_file} config from {config_file}")
            self.model = KModel(self.repo_id,config_file, model_file)
            self.model.to(self.device)
            logger.info("Kokoro TTS model loaded successfully")
            self.pipeline = KPipeline(lang_code='a', repo_id=self.repo_id, device=self.device, model=self.model)
            self.pipeline_zh = KPipeline(lang_code='z',repo_id=self.repo_id, device=self.device, model=self.model)
            logger.info("Kokoro TTS pipeline loaded successfully")
            # start to load pipeline vo
            voices = config.VOICE_MAPPINGS["kokoro"]
            for voice_id, voice in voices.items():
                voice_path = os.path.join(self.config.model_path, "voices" , voice + ".pt")
                logger.info(f"Loading voice {voice_id} from {voice_path}")
                self.pipeline.voices[voice] = torch.load(voice_path, weights_only=True)
            
            voices = config.VOICE_MAPPINGS["kokoro_zh"]
            for voice_id, voice in voices.items():
                voice_path = os.path.join(self.config.model_path, "voices" , voice + ".pt")
                logger.info(f"Loading voice {voice_id} from {voice_path}")
                self.pipeline_zh.voices[voice] = torch.load(voice_path, weights_only=True)

            logger.info("Kokoro TTS pipeline voices loaded successfully")


        except Exception as e:
            logger.error(f"Failed to load Kokoro TTS model: {str(e)}")
            raise
        
    def generate_speech(self, text: str, speaker: str, language: str = "auto", speed: float = 1.0) -> np.ndarray:
        generator = self.pipeline
        if language == "zh":
            generator = self.pipeline_zh
        
        all_audio = []
        for gs, ps, audio in generator(text, voice=speaker, speed=speed, split_pattern=r'\n+'):
            if audio is not None:
                if isinstance(audio, np.ndarray):
                    audio = torch.from_numpy(audio).float()
                all_audio.append(audio)
                print(f"\nGenerated segment: {gs}")
                print(f"Phonemes: {ps}")
        
        # Save audio
        if all_audio:
            final_audio = torch.cat(all_audio, dim=0)
            return final_audio.numpy()
        else:
            print("Error: Failed to generate audio")
            return np.array([])


if __name__ == "__main__":
    KOKORO_MODEL_PATH = "/Users/jun/GolandProjects/competition/tencent-hunyuan-ai-podcast/src/llm/models/hexgrad/Kokoro-82M-v1.1-zh"
    tts = KokoroTTS(TTSConfig(model_path=KOKORO_MODEL_PATH))
    en_text = """istio is an open source service mesh that layers transparently onto existing distributed applications. Istio’s powerful features provide a uniform and more efficient way to secure, connect, and monitor services. Istio is the path to load balancing, service-to-service authentication, and monitoring – with few or no service code changes."""
    zh_text = """Istio 是一个开源的服务网格，它透明地层叠到现有的分布式应用程序上。Istio 强大的功能提供了一种统一且更高效的方式来保护、连接和监控服务。Istio 是负载均衡、服务间认证和监控的途径，而无需对服务代码进行重大更改。"""
    final_audio = tts.generate_speech(zh_text, "zf_xiaobei", "zh", 1.05)

    output_path = Path("output.wav")
    sf.write(output_path, final_audio, 24000)
    print(f"\nAudio saved to {output_path.absolute()}")
