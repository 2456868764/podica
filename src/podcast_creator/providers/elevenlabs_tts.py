"""ElevenLabs Text-to-Speech provider implementation with extended capabilities."""

from typing import Any, Dict, List, Optional

from esperanto.common_types import Model
from esperanto.utils.logging import logger
from esperanto.providers.tts.base import AudioResponse, Voice
from esperanto.providers.tts.elevenlabs import ElevenLabsTextToSpeechModel
from .tts_capability import TTSCapability


class ElevenLabsExtendedTextToSpeechModel(ElevenLabsTextToSpeechModel):
    """Extended ElevenLabs Text-to-Speech provider with capability information.
    
    This provider extends the base ElevenLabsTextToSpeechModel to add
    capability information for better integration with the podcast creator system.
    
    Example:
        >>> from esperanto import AIFactory
        >>> tts = AIFactory.create_text_to_speech(
        ...     "elevenlabs",
        ...     model_name="eleven_flash_v2_5",
        ...     api_key="your_api_key"
        ... )
        >>> capability = tts.capability
        >>> print(capability.supports_custom_voice)
    """
    
    @property
    def provider(self) -> str:
        """Get the provider name."""
        return "elevenlabs"
    
    @property
    def capability(self) -> TTSCapability:
        """Get TTS provider capabilities.
        
        Returns:
            TTSCapability: Capability information for ElevenLabs TTS
        """
        # Get default voices from available_voices
        default_voices = list(self.available_voices.keys())
        
        # ElevenLabs supports voice cloning and custom voices
        # It also supports some paralinguistic controls through voice settings
        voice_tags = [
            "laughter",      # Can be achieved through voice settings
            "sigh",          # Can be achieved through voice settings
            "breath",        # Natural breathing sounds
            "pause",         # Natural pauses
        ]
        
        return TTSCapability(
            supported_languages=["en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "hu", "sv"],  # ElevenLabs supports many languages
            supported_dialects=["mandarin"],
            supports_instructions=True,  # ElevenLabs supports voice settings and style modifications
            supports_custom_voice=True,  # ElevenLabs supports voice cloning and custom voice upload
            default_voices=default_voices if default_voices else ["default"],
            supports_voice_tags=True,  # ElevenLabs supports some paralinguistic controls through voice settings
            available_voice_tags=voice_tags,
            metadata={
                "description": "ElevenLabs provides high-quality neural voice synthesis with voice cloning capabilities",
                "instruction_format": "Voice settings and style modifications via API parameters",
                "custom_voice_format": "Voice cloning via voice upload or reference audio",
                "voice_tags_format": "Paralinguistic controls can be achieved through voice settings and style modifications",
                "supported_formats": ["mp3", "wav", "pcm"],
                "voice_cloning": True,
                "real_time": True,
                "multilingual": True
            }
        )

