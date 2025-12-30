"""TTS Capability data structure for TTS providers."""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class TTSCapability:
    """TTS Provider Capability information.
    
    This class describes the capabilities of a TTS provider, including:
    - Supported languages
    - Whether it supports instructions/emotion control
    - Whether it supports custom voice (upload WAV)
    - Default voice list
    - Whether it supports paralinguistic controls (voice tags) and available tags
    """
    
    # Supported languages (ISO 639-1 codes, e.g., ["en", "zh", "ja"])
    supported_languages: List[str]

    # Whether the provider supports instructions/emotion control
    supports_instructions: bool
    
    # Whether the provider supports custom voice (upload WAV file)
    supports_custom_voice: bool
    
    # Default voice list (list of voice IDs)
    default_voices: List[str]
    
    # Whether the provider supports paralinguistic controls (voice tags)
    # Paralinguistic controls include: laughter, sighs, breaths, pauses, etc.
    # These enhance the realism of synthesized speech
    supports_voice_tags: bool = False

        
    # Supported Chinese dialects (e.g., ["mandarin", "cantonese", "sichuanese", "henanese", "shanghainese"])
    # Only applicable when "zh" or "Chinese" is in supported_languages
    supported_dialects: Optional[List[str]] = None
    
    
    # Available paralinguistic control tags (voice tags)
    # Common tags: laughter, sigh, breath, pause, cough, etc.
    # These can be embedded in text or passed as parameters to enhance speech realism
    available_voice_tags: Optional[List[str]] = None
    
    # Optional: Additional metadata
    metadata: Optional[Dict[str, any]] = None
    
    def to_dict(self) -> Dict:
        """Convert capability to dictionary."""
        return {
            "supported_languages": self.supported_languages,
            "supported_dialects": self.supported_dialects or [],
            "supports_instructions": self.supports_instructions,
            "supports_custom_voice": self.supports_custom_voice,
            "default_voices": self.default_voices,
            "supports_voice_tags": self.supports_voice_tags,
            "available_voice_tags": self.available_voice_tags or [],
            "metadata": self.metadata or {}
        }

