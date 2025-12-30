import os
import sys
from pathlib import Path
import re
import numpy as np
import torch
from dataclasses import dataclass
from typing import Optional, List
import logging

import soundfile as sf

# Import dialect utilities
try:
    from dialect_utils import (
        get_dialect_tag,
        add_dialect_tag_to_text,
        get_default_dialect_prompt,
        is_dialect_supported,
        normalize_dialect_name
    )
except ImportError:
    # Fallback if dialect_utils is not available
    def get_dialect_tag(dialect): return ""
    def add_dialect_tag_to_text(text, dialect): return text
    def get_default_dialect_prompt(dialect, speaker_index=0): return ""
    def is_dialect_supported(dialect): return False
    def normalize_dialect_name(dialect): return dialect

def convert_voice_tags_to_soulx_format(text: str) -> str:
    """
    将文本中的 voice_tag 格式从 [tag] 转换为 SoulX 格式 <|tag|>
    
    Args:
        text: 包含 [tag] 格式的文本
    
    Returns:
        转换后的文本，所有 [tag] 格式都被转换为 <|tag|>
    
    Examples:
        "哈哈[laughter]，这真是太有趣了！" -> "哈哈<|laughter|>，这真是太有趣了！"
        "嗯[sigh]，我觉得这个问题比较复杂。" -> "嗯<|sigh|>，我觉得这个问题比较复杂。"
        "让我想想[breathing]...我觉得可以这样处理。" -> "让我想想<|breathing|>...我觉得可以这样处理。"
        "已经是<|breathing|>格式" -> "已经是<|breathing|>格式" (不重复转换)
    """
    if not text:
        return text
    
    # 匹配 [tag] 格式，其中 tag 不包含 [ ] 字符
    # 使用正则表达式替换 [tag] 为 <|tag|>
    # 使用负向后顾断言 (?<!<) 排除已经是 <|tag|> 格式的情况
    pattern = r'(?<!<)\[([^\[\]<>]+)\]'
    
    def replace_tag(match):
        tag = match.group(1)
        return f'<|{tag}|>'
    
    return re.sub(pattern, replace_tag, text)

# Add SoulX-Podcast-main to path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
soulx_dir = os.path.join(current_dir, "SoulX-Podcast-main")
if soulx_dir not in sys.path:
    sys.path.insert(0, soulx_dir)

try:
    from soulxpodcast.config import Config, SoulXPodcastLLMConfig, SamplingParams
    from soulxpodcast.utils.dataloader import PodcastInferHandler
    from soulxpodcast.utils.commons import set_all_random_seed
    from soulxpodcast.models.soulxpodcast import SoulXPodcast
    import s3tokenizer
except ImportError as e:
    # If soulxpodcast is installed as a package, it should work without path manipulation
    # Try importing again without adding path
    from soulxpodcast.config import Config, SoulXPodcastLLMConfig, SamplingParams
    from soulxpodcast.utils.dataloader import PodcastInferHandler
    from soulxpodcast.utils.commons import set_all_random_seed
    from soulxpodcast.models.soulxpodcast import SoulXPodcast
    import s3tokenizer

# Import logger (already configured)
try:
    from logger import logger
except ImportError:
    # Fallback if logger module is not available
    import logging
    logger = logging.getLogger("llm-service")

@dataclass
class SoulXTTSConfig:
    """
    Configuration for SoulX TTS.
    model_path: 模型保存路径
    device: 计算设备 ("cpu" 或 "cuda")
    sampling_rate: 输出音频采样率
    llm_engine: LLM引擎 ("hf" 或 "vllm")
    fp16_flow: 是否使用FP16精度的Flow模型
    seed: 随机种子
    """
    model_path: str
    device: str = "cuda"
    sampling_rate: int = 24000
    llm_engine: str = "hf"
    fp16_flow: bool = False
    seed: int = 1988

@dataclass
class SoulXTTSParam:
    text: str
    spk_audio_prompt: str
    spk_text_prompt: Optional[str] = None
    output_path: Optional[str] = None
    temperature: float = 0.6
    top_k: int = 100
    top_p: float = 0.9
    repetition_penalty: float = 1.25
    verbose: bool = False
    # 方言支持参数
    dialect: Optional[str] = None  # 方言类型，如 "sichuan", "henan", "yue", "mandarin"
    dialect_prompt: Optional[str] = None  # 方言提示文本（包含方言标记），如果为 None 则使用默认提示文本

class SoulXTTS:
    """
    SoulX TTS 类实现文本转语音。
    支持单说话人语音合成，使用参考音频进行零样本语音克隆。
    """
    def __init__(self, config: SoulXTTSConfig):
        self.config = config
        self.device = config.device
        self.sampling_rate = config.sampling_rate
        self.model = None
        self.dataset = None
        self._load_model()
        
    def _load_model(self):
        """加载 SoulX TTS 模型"""
        try:
            logger.info(f"Loading SoulX TTS model from {self.config.model_path}")
            logger.info(f"Using LLM engine: {self.config.llm_engine}")
            
            # 设置随机种子
            set_all_random_seed(self.config.seed)
            
            # 加载配置
            hf_config = SoulXPodcastLLMConfig.from_initial_and_json(
                initial_values={"fp16_flow": self.config.fp16_flow},
                json_file=f"{self.config.model_path}/soulxpodcast_config.json"
            )
            
            # 创建Config对象
            model_config = Config(
                model=self.config.model_path,
                enforce_eager=True,
                llm_engine=self.config.llm_engine,
                hf_config=hf_config
            )
            
            # 初始化模型
            self.model = SoulXPodcast(model_config)
            
            # 初始化数据集处理器
            self.dataset = PodcastInferHandler(
                self.model.llm.tokenizer,
                None,
                model_config
            )
            
            logger.info("SoulX TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SoulX TTS model: {str(e)}")
            raise
        
    def generate_speech(self, param: SoulXTTSParam) -> np.ndarray:
        """
        生成语音
        :param param: SoulXTTSParam 参数对象
        :return: 生成的语音 numpy 数组
        """
        try:
            # 设置随机种子
            torch.manual_seed(self.config.seed)
            np.random.seed(self.config.seed)
            
            # 如果没有提供参考文本，使用空字符串
            spk_text_prompt = param.spk_text_prompt or ""
            
            # 处理方言
            use_dialect_prompt = False
            dialect_prompt_text = None
            processed_text = param.text
            
            if param.dialect:
                normalized_dialect = normalize_dialect_name(param.dialect)
                if normalized_dialect and normalized_dialect != "mandarin":
                    # 使用提供的方言提示文本，或获取默认的
                    if param.dialect_prompt:
                        dialect_prompt_text = param.dialect_prompt
                    else:
                        dialect_prompt_text = get_default_dialect_prompt(normalized_dialect, speaker_index=0)
                    
                    if dialect_prompt_text:
                        use_dialect_prompt = True
                        logger.info(f"Using dialect: {normalized_dialect}, dialect_prompt: {dialect_prompt_text[:50]}...")
                    
                    # 为文本添加方言标记（如果还没有）
                    processed_text = add_dialect_tag_to_text(processed_text, normalized_dialect)
            
            # 转换 voice_tags 格式：将 [tag] 转换为 <|tag|>
            # 在方言处理之后进行转换，确保方言标记和 voice_tags 都能正确处理
            processed_text = convert_voice_tags_to_soulx_format(processed_text)
            if processed_text != param.text:
                logger.debug(f"Converted voice tags: {param.text[:100]}... -> {processed_text[:100]}...")
            # 构建数据项（单说话人）
            dataitem = {
                "key": "soulx_tts_001",
                "prompt_text": [spk_text_prompt],
                "prompt_wav": [param.spk_audio_prompt],
                "text": [processed_text],
                "spk": [0],  # 单说话人，使用索引0
            }
            
            # 如果使用方言，添加方言提示文本
            if use_dialect_prompt and dialect_prompt_text:
                dataitem["dialect_prompt_text"] = [dialect_prompt_text]
            
            # 更新数据源
            self.dataset.update_datasource([dataitem])
            
            # 获取处理后的数据
            data = self.dataset[0]
            
            # 准备模型输入
            prompt_mels_for_llm, prompt_mels_lens_for_llm = s3tokenizer.padding(data["log_mel"])
            spk_emb_for_flow = torch.tensor(data["spk_emb"])
            prompt_mels_for_flow = torch.nn.utils.rnn.pad_sequence(
                data["mel"], batch_first=True, padding_value=0
            )
            prompt_mels_lens_for_flow = torch.tensor(data['mel_len'])
            text_tokens_for_llm = data["text_tokens"]
            prompt_text_tokens_for_llm = data["prompt_text_tokens"]
            spk_ids = data["spks_list"]
            
            # 采样参数
            sampling_params = SamplingParams(
                temperature=param.temperature,
                repetition_penalty=param.repetition_penalty,
                top_k=param.top_k,
                top_p=param.top_p,
                use_ras=True,
                win_size=25,
                tau_r=0.2
            )
            
            infos = [data["info"]]
            processed_data = {
                "prompt_mels_for_llm": prompt_mels_for_llm,
                "prompt_mels_lens_for_llm": prompt_mels_lens_for_llm,
                "prompt_text_tokens_for_llm": prompt_text_tokens_for_llm,
                "text_tokens_for_llm": text_tokens_for_llm,
                "prompt_mels_for_flow_ori": prompt_mels_for_flow,
                "prompt_mels_lens_for_flow": prompt_mels_lens_for_flow,
                "spk_emb_for_flow": spk_emb_for_flow,
                "sampling_params": sampling_params,
                "spk_ids": spk_ids,
                "infos": infos,
                "use_dialect_prompt": use_dialect_prompt,
            }
            
            # 如果使用方言，添加方言相关的 token 数据
            if use_dialect_prompt and "dialect_prompt_text_tokens" in data:
                processed_data["dialect_prompt_text_tokens_for_llm"] = data["dialect_prompt_text_tokens"]
                processed_data["dialect_prefix"] = data.get("dialect_prefix", [])
            
            if param.verbose:
                logger.info(f"Generating speech for text: {param.text[:50]}...")
            
            # 模型推理
            with torch.no_grad():
                results_dict = self.model.forward_longform(**processed_data)
            
            # 拼接音频（单说话人情况下通常只有一个）
            target_audio = None
            for wav in results_dict["generated_wavs"]:
                if target_audio is None:
                    target_audio = wav
                else:
                    target_audio = torch.cat([target_audio, wav], dim=1)
            
            # 转换为numpy数组
            audio_array = target_audio.cpu().squeeze(0).numpy()
            
            # 保存到文件（如果指定）
            if param.output_path:
                output_path = Path(param.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                sf.write(str(output_path), audio_array, self.sampling_rate)
                if param.verbose:
                    logger.info(f"Audio saved to {output_path}")
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Failed to generate speech: {str(e)}")
            raise


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    SOULX_MODEL_PATH = "/path/to/SoulX-Podcast-1.7B"  # 替换为实际模型路径
    
    tts = SoulXTTS(SoulXTTSConfig(
        model_path=SOULX_MODEL_PATH,
        device="cuda",
        llm_engine="hf",
        fp16_flow=False
    ))
    
    zh_text = """Istio 是一个开源的服务网格，它透明地层叠到现有的分布式应用程序上。Istio 强大的功能提供了一种统一且更高效的方式来保护、连接和监控服务。"""
    
    spk_audio_prompt = os.path.join(current_dir, "example", "voice_01.wav")  # 替换为实际参考音频路径
    output_path = os.path.join(current_dir, "example", "soulx_output.wav")
    
    print(f"Generating speech...")
    final_audio = tts.generate_speech(SoulXTTSParam(
        text=zh_text,
        spk_audio_prompt=spk_audio_prompt,
        spk_text_prompt="这是一个参考音频的文本内容。",  # 可选
        output_path=output_path,
        verbose=True
    ))
    
    print(f"\nAudio generated successfully!")
    print(f"Audio length: {len(final_audio) / 24000:.2f} seconds")
    print(f"Audio saved to {output_path}")




