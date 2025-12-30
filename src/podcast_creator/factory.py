"""
自定义 AI 工厂，支持自定义 provider
"""
import importlib
from typing import Dict, List, Type
from esperanto.factory import AIFactory

class CustomAIFactory(AIFactory):
    """扩展的 AI 工厂，支持自定义 provider"""
    _custom_providers = {
        "language": {
            # 集成腾讯混元（OpenAI兼容接口）
            "tencent": "podcast_creator.providers.tencent_llm:TencentLanguageModel",
            # 新增 DASHSCOPE 通义千问 Qwen LLM
            "qwen": "podcast_creator.providers.qwen_llm:QwenLanguageModel",
            "erine": "podcast_creator.providers.erine_llm:ErineLanguageModel",
        },
        "embedding": {
            #"my_custom_embedding": "custom_embedding:CustomEmbeddingModel",
        },
        # 新增 TTS 提供商集成（阿里云通义千问 Qwen TTS via DashScope）
        "text_to_speech": {
            "elevenlabs": "podcast_creator.providers.elevenlabs_tts:ElevenLabsExtendedTextToSpeechModel",  # Extended ElevenLabs with capability
            "openai": "podcast_creator.providers.openai_tts:OpenAIExtendedTextToSpeechModel",  # Extended OpenAI with capability
            "qwen": "podcast_creator.providers.qwen_tts:QWenTextToSpeechModel",
            "kokoro": "podcast_creator.providers.kokoro_tts:KokoroTextToSpeechModel",
            "v3api": "podcast_creator.providers.v3api_tts:V3APITextToSpeechModel",
            "laozhang": "podcast_creator.providers.laozhang_tts:LaoZhangTextToSpeechModel",
            "indextts": "podcast_creator.providers.index_tts:IndexTTSTextToSpeechModel",
            "soulx": "podcast_creator.providers.soulx_tts:SoulXTextToSpeechModel",
        },
        # 可以添加其他服务类型
    }
    
    @classmethod
    def _import_provider_class(cls, service_type: str, provider: str) -> Type:
        # 首先检查自定义 provider
        if (service_type in cls._custom_providers and 
            provider in cls._custom_providers[service_type]):
            
            module_path = cls._custom_providers[service_type][provider]
            module_name, class_name = module_path.split(":")
            
            try:
                module = importlib.import_module(module_name)
                return getattr(module, class_name)
            except ImportError as e:
                raise ImportError(f"Failed to import custom provider {provider}: {e}")
        
        # 回退到原始工厂逻辑
        return super()._import_provider_class(service_type, provider)
    
    @classmethod
    def get_available_providers(cls) -> Dict[str, List[str]]:
        """获取所有可用的 provider（包括自定义的）"""
        base_providers = super().get_available_providers()
        
        # 合并自定义 provider
        for service_type, providers in cls._custom_providers.items():
            if service_type in base_providers:
                base_providers[service_type].extend(providers.keys())
            else:
                base_providers[service_type] = list(providers.keys())
        
        return base_providers