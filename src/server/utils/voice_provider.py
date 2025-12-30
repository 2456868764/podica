"""
Voice provider utilities for the Podcast Creator Studio.

Handles voice selection for different TTS providers.
"""

import streamlit as st
import base64
import tempfile
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    # from esperanto import AIFactory
    from podcast_creator.factory import CustomAIFactory as AIFactory
    from podcast_creator.providers.tts_capability import TTSCapability
    ESPERANTO_AVAILABLE = True
except ImportError:
    ESPERANTO_AVAILABLE = False
    TTSCapability = None


class VoiceProvider:
    """Voice provider utility for getting available voices from TTS providers."""
    
    @staticmethod
    def is_esperanto_available() -> bool:
        """Check if esperanto library is available."""
        return ESPERANTO_AVAILABLE
    
    @staticmethod
    def get_available_voices(provider: str, model: str = None) -> Dict[str, str]:
        """
        Get available voices for a TTS provider.
        
        Args:
            provider: TTS provider name (elevenlabs, openai, google)
            model: Optional model name for the provider
            
        Returns:
            Dictionary mapping voice names to voice IDs
        """
        if not ESPERANTO_AVAILABLE:
            return {}
        
        try:
            # Create TTS instance based on provider
            if provider == "elevenlabs":
                model = model or "eleven_flash_v2_5"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "openai":
                model = model or "tts-1"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "google":
                model = model or "standard"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "qwen":
                model = model or "qwen3-tts-flash"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "kokoro":
                model = model or "kokoro-82m"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "indextts" or provider == "index-tts":
                model = model or "index-tts"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "soulx":
                model = model or "SoulX-Podcast-1.7B"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "v3api":
                model = model or "tts-1"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "laozhang":
                model = model or "gpt-4o-mini-tts"
                tts = AIFactory.create_text_to_speech(provider, model)    
            else:
                return {}
            
            # Get available voices
            voices = tts.available_voices
            print(f"Available voices for {provider}: {voices}")
            
            # Process voices based on provider
            if provider == "elevenlabs":
                # ElevenLabs returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif provider == "indextts" or provider == "index-tts":
                # IndexTTS returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif provider == "soulx":
                # SoulX returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif  provider == "kokoro":
                # Kokoro returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif provider == "qwen":
                # Qwen returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif provider == "v3api":
                # V3API returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }    
            elif provider == "laozhang":
                # LaoZhang returns a dict with voice objects
                return {
                    f"{voice.name} ({voice.gender}, {voice.description[:50]}...)": voice.id
                    for voice in voices.values()
                }
            elif provider == "openai":
                # OpenAI has predefined voices
                return {
                    "Alloy": "alloy",
                    "Echo": "echo", 
                    "Fable": "fable",
                    "Onyx": "onyx",
                    "Nova": "nova",
                    "Shimmer": "shimmer"
                }
            elif provider == "google":
                # Google has many voices, return a simplified set
                return {
                    "Standard A": "en-US-Standard-A",
                    "Standard B": "en-US-Standard-B",
                    "Standard C": "en-US-Standard-C",
                    "Standard D": "en-US-Standard-D",
                    "Wavenet A": "en-US-Wavenet-A",
                    "Wavenet B": "en-US-Wavenet-B",
                    "Wavenet C": "en-US-Wavenet-C",
                    "Wavenet D": "en-US-Wavenet-D"
                }
            else:
                return {}
                
        except Exception as e:
            st.error(f"Error getting voices for {provider}: {str(e)}")
            return {}
    
    @staticmethod
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_cached_voices(provider: str, model: str = None) -> Dict[str, str]:
        """
        Get cached available voices for a TTS provider.
        
        Args:
            provider: TTS provider name
            model: Optional model name
            
        Returns:
            Dictionary mapping voice names to voice IDs
        """
        return VoiceProvider.get_available_voices(provider, model)
    
    @staticmethod
    def render_voice_selector(
        provider: str, 
        model: str,
        current_voice_id: str = "",
        key: str = "voice_selector",
        help_text: str = "Choose a voice for this speaker"
    ) -> str:
        """
        Render a voice selector widget.
        
        Args:
            provider: TTS provider name
            model: Model name
            current_voice_id: Currently selected voice ID
            key: Unique key for the widget
            help_text: Help text for the widget
            
        Returns:
            Selected voice ID
        """
        if not ESPERANTO_AVAILABLE:
            st.warning("⚠️ Esperanto library not available. Using text input for voice ID.")
            return st.text_input(
                "Voice ID:", 
                value=current_voice_id,
                key=key,
                help="Enter the voice ID manually"
            )
        
        # Get available voices
        voices = VoiceProvider.get_cached_voices(provider, model)
        
        # Check if provider supports custom voice
        capability = VoiceProvider.get_tts_capability(provider, model)
        supports_custom_voice = capability and capability.supports_custom_voice if capability else False
        
        if not voices:
            st.warning(f"⚠️ No voices available for {provider}. Using text input.")
            return st.text_input(
                "Voice ID:", 
                value=current_voice_id,
                key=key,
                help="Enter the voice ID manually"
            )
        
        # Find current selection
        voice_names = list(voices.keys())
        voice_ids = list(voices.values())
        
        # Add "custom" option if provider supports custom voice
        if supports_custom_voice:
            voice_names.append("🎤 Custom (自定义声音)")
            voice_ids.append("custom")
        
        # Try to find current voice in the list
        current_index = 0
        if current_voice_id:
            try:
                current_index = voice_ids.index(current_voice_id)
            except ValueError:
                # Voice not found, add it as an option
                voice_names.insert(0, f"Current: {current_voice_id}")
                voice_ids.insert(0, current_voice_id)
                current_index = 0
        
        # Show selectbox
        selected_name = st.selectbox(
            "Voice:",
            voice_names,
            index=current_index,
            key=key,
            help=help_text
        )
        
        # Return the corresponding voice ID
        selected_index = voice_names.index(selected_name)
        return voice_ids[selected_index]
    
    @staticmethod
    def get_voice_preview_url(provider: str, voice_id: str) -> Optional[str]:
        """
        Get preview URL for a voice if available.
        
        Args:
            provider: TTS provider name
            voice_id: Voice ID
            
        Returns:
            Preview URL if available, None otherwise
        """
        if not ESPERANTO_AVAILABLE or provider != "elevenlabs":
            return None
        
        try:
            tts = AIFactory.create_text_to_speech(provider, "eleven_flash_v2_5")
            voices = tts.available_voices
            
            for voice in voices.values():
                if voice.id == voice_id:
                    return voice.preview_url
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def render_voice_preview(provider: str, voice_id: str):
        """
        Render voice preview if available.
        
        Args:
            provider: TTS provider name
            voice_id: Voice ID
        """
        if provider == "elevenlabs" and voice_id:
            preview_url = VoiceProvider.get_voice_preview_url(provider, voice_id)
            if preview_url:
                st.audio(preview_url, format="audio/mp3")
    
    @staticmethod
    def get_default_voices(provider: str) -> Dict[str, str]:
        """
        Get default voices for a provider when API is not available.
        
        Args:
            provider: TTS provider name
            
        Returns:
            Dictionary of default voices
        """
        defaults = {
            "elevenlabs": {
                "Aria": "9BWtsMINqrJLrRacOk9x",
                "Sarah": "EXAVITQu4vr4xnSDxMaL",
                "Laura": "FGY2WhTYpPnrIDTdsKH5",
                "Charlie": "IKne3meq5aSn9XLyUdCD",
                "George": "JBFqnCBsd6RMkjVDRZzb",
                "Brian": "nPczCjzI2devNBz1zQrb",
                "Daniel": "onwK4e9ZLuTAKqWW03F9",
                "Lily": "pFZP5JQG7iQjIQuC4Bku"
            },
            "openai": {
                "Alloy": "alloy",
                "Echo": "echo",
                "Fable": "fable", 
                "Onyx": "onyx",
                "Nova": "nova",
                "Shimmer": "shimmer"
            },
            "google": {
                "Standard A": "en-US-Standard-A",
                "Standard B": "en-US-Standard-B",
                "Standard C": "en-US-Standard-C",
                "Standard D": "en-US-Standard-D"
            }
        }
        
        return defaults.get(provider, {})
    
    @staticmethod
    def get_tts_capability(provider: str, model: str = None) -> Optional[TTSCapability]:
        """
        Get TTS provider capability.
        
        Args:
            provider: TTS provider name
            model: Optional model name
            
        Returns:
            TTSCapability object if available, None otherwise
        """
        if not ESPERANTO_AVAILABLE or TTSCapability is None:
            return None
        
        try:
            # Create TTS instance based on provider
            if provider == "indextts" or provider == "index-tts":
                model = model or "index-tts"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "soulx":
                model = model or "SoulX-Podcast-1.7B"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "kokoro":
                model = model or "kokoro-82m"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "qwen":
                model = model or "qwen3-tts-flash"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "laozhang":
                model = model or "gpt-4o-mini-tts"
                tts = AIFactory.create_text_to_speech(provider, model)
            elif provider == "v3api":
                model = model or "tts-1"
                tts = AIFactory.create_text_to_speech(provider, model)
            else:
                return None
            
            # Get capability
            if hasattr(tts, 'capability'):
                return tts.capability
            return None
        except Exception as e:
            st.warning(f"无法获取 {provider} 的能力信息: {str(e)}")
            return None
    
    @staticmethod
    def render_custom_voice_upload(
        provider: str,
        model: str = None,
        current_custom_voice: Optional[str] = None,
        key: str = "custom_voice_upload",
        help_text: str = "上传自定义 WAV 音频文件作为参考声音"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Render custom voice upload widget if provider supports it.
        
        Args:
            provider: TTS provider name
            model: Optional model name
            current_custom_voice: Currently uploaded custom voice (base64 or file path)
            key: Unique key for the widget
            help_text: Help text for the widget
            
        Returns:
            Tuple of (custom_voice_data, custom_voice_filename)
            - custom_voice_data: Base64 encoded audio data or file path
            - custom_voice_filename: Original filename
        """
        # Check if provider supports custom voice
        capability = VoiceProvider.get_tts_capability(provider, model)
        
        if not capability or not capability.supports_custom_voice:
            return None, None
        
        st.markdown("**自定义声音 (Custom Voice):**")
        st.info(f"💡 {provider} 支持自定义声音。您可以上传 WAV 格式的参考音频文件。")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "上传 WAV 音频文件",
            type=['wav'],
            key=f"{key}_uploader",
            help=help_text
        )
        
        custom_voice_data = None
        custom_voice_filename = None
        
        if uploaded_file is not None:
            # Validate file type
            if uploaded_file.type not in ['audio/wav', 'audio/x-wav', 'audio/wave']:
                st.error("❌ 仅支持 WAV 格式的音频文件")
                return None, None
            
            # Read file content
            audio_bytes = uploaded_file.read()
            
            # Save file to disk in a dedicated directory
            # Use resources/custom_voices directory
            # Get the resources directory (assuming it's relative to the server directory)
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            server_dir = os.path.dirname(current_file_dir)
            root_dir = os.path.dirname(server_dir)
            custom_voices_dir = os.path.join(root_dir, "resources", "custom_voices")
            
            # Create directory if it doesn't exist
            os.makedirs(custom_voices_dir, exist_ok=True)
            
            # Generate unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_extension = os.path.splitext(uploaded_file.name)[1] or '.wav'
            safe_filename = f"{timestamp}_{unique_id}{file_extension}"
            
            # Save file
            file_path = os.path.join(custom_voices_dir, safe_filename)
            with open(file_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Store file path instead of base64
            custom_voice_data = file_path
            custom_voice_filename = uploaded_file.name
            
            st.success(f"✅ 已上传: {uploaded_file.name} ({len(audio_bytes)} 字节)")
            st.info(f"📁 文件已保存到: {file_path}")
            
            # Play preview
            st.audio(audio_bytes, format='audio/wav')
            
        elif current_custom_voice:
            # Show existing custom voice
            # Check if it's a file path or base64 encoded
            if os.path.exists(current_custom_voice):
                # It's a file path
                st.info(f"📎 当前自定义声音文件: {os.path.basename(current_custom_voice)}")
                try:
                    st.audio(current_custom_voice, format='audio/wav')
                    custom_voice_data = current_custom_voice
                    # Try to get original filename from metadata or use basename
                    custom_voice_filename = os.path.basename(current_custom_voice)
                except Exception as e:
                    st.warning(f"⚠️ 无法播放音频文件: {str(e)}")
            else:
                # Try to decode if it's base64 (for backward compatibility)
                try:
                    if isinstance(current_custom_voice, str) and len(current_custom_voice) > 100:
                        # Likely base64 encoded (legacy format)
                        audio_bytes = base64.b64decode(current_custom_voice)
                        st.info(f"📎 当前自定义声音 (Base64 格式)")
                        st.audio(audio_bytes, format='audio/wav')
                        # Keep base64 for backward compatibility, but suggest migrating
                        custom_voice_data = current_custom_voice
                except Exception:
                    st.warning(f"⚠️ 无法读取自定义声音数据")
        
        return custom_voice_data, custom_voice_filename