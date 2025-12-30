"""OpenAI Text-to-Speech provider implementation with extended capabilities."""

from typing import Any, Dict, List, Optional

from esperanto.common_types import Model
from esperanto.utils.logging import logger
from esperanto.providers.tts.base import AudioResponse, Voice
from esperanto.providers.tts.openai import OpenAITextToSpeechModel
from .tts_capability import TTSCapability


class OpenAIExtendedTextToSpeechModel(OpenAITextToSpeechModel):
    """Extended OpenAI Text-to-Speech provider with capability information.
    
    This provider extends the base OpenAITextToSpeechModel to add
    capability information for better integration with the podcast creator system.
    
    Example:
        >>> from esperanto import AIFactory
        >>> tts = AIFactory.create_text_to_speech(
        ...     "openai",
        ...     model_name="tts-1",
        ...     api_key="your_api_key"
        ... )
        >>> capability = tts.capability
        >>> print(capability.supports_custom_voice)
    """
    
    @property
    def provider(self) -> str:
        """Get the provider name."""
        return "openai"
    
    @property
    def capability(self) -> TTSCapability:
        """Get TTS provider capabilities.
        
        Returns:
            TTSCapability: Capability information for OpenAI TTS
        """
        # Get default voices from available_voices
        default_voices = list(self.available_voices.keys())
        
        # OpenAI TTS supports voice cloning with reference audio (TTS-1 HD model)
        # It doesn't explicitly support paralinguistic controls
        voice_tags = []  # OpenAI TTS doesn't explicitly support paralinguistic controls
        
        return TTSCapability(
            supported_languages=["zh", "en"],  # OpenAI TTS primarily supports English
            supported_dialects=["mandarin"],
            supports_instructions=False,  # OpenAI TTS doesn't support explicit instructions parameter
            supports_custom_voice=False,  # OpenAI TTS-1 HD supports voice cloning with reference audio
            default_voices=default_voices if default_voices else ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            supports_voice_tags=False,  # OpenAI TTS doesn't explicitly support paralinguistic controls
            available_voice_tags=voice_tags,
            metadata={
                "description": "OpenAI provides high-quality neural voice synthesis with voice cloning capabilities (TTS-1 HD)",
                "instruction_format": "Not supported - OpenAI TTS uses predefined voices",
                "custom_voice_format": "Voice cloning via reference_audio parameter (TTS-1 HD model)",
                "voice_tags_format": "Paralinguistic controls are limited to natural speech patterns",
                "supported_formats": ["mp3", "opus", "aac", "flac", "wav", "pcm16"],
                "voice_cloning": True,  # Available in TTS-1 HD model
                "real_time": False,
                "multilingual": False,  # Primarily English
                "models": ["tts-1", "tts-1-hd"]
            }
        )

