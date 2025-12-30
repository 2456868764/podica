"""OpenAI-compatible Text-to-Speech provider implementation."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from esperanto.common_types import Model
from esperanto.utils.logging import logger

from esperanto.providers.tts.base import AudioResponse, Voice, TextToSpeechModel
from esperanto.providers.tts.openai import OpenAITextToSpeechModel
from .tts_capability import TTSCapability

class KokoroTextToSpeechModel(OpenAITextToSpeechModel):
    """OpenAI-compatible Text-to-Speech provider implementation for custom endpoints.

    This provider extends OpenAI's TTS implementation to work with any OpenAI-compatible
    TTS endpoint, providing graceful fallback for features that may not be supported
    by all endpoints.

    Note: Unlike STT and Embedding providers that inherit from base classes and manually
    initialize HTTP clients, this TTS provider inherits from OpenAITextToSpeechModel
    to reuse existing client initialization and voice handling logic.

    Example:
        >>> from esperanto import AIFactory
        >>> tts = AIFactory.create_text_to_speech(
        ...     "openai-compatible",
        ...     model_name="piper-tts",
        ...     config={"base_url": "http://localhost:8000"}
        ... )
        >>> response = tts.generate_speech("Hello world", voice="default")
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize OpenAI-compatible TTS provider.

        Args:
            model_name: Name of the model to use
            api_key: API key for the provider. If not provided, will try to get from environment
            base_url: Base URL for the OpenAI-compatible endpoint
            config: Additional configuration options
            **kwargs: Additional configuration options
        """
        # Merge config and kwargs
        config = config or {}
        config.update(kwargs)

        # Configuration precedence: Direct params > config > Environment variables
        self.base_url = (
            base_url or
            config.get("base_url") or
            os.getenv("KOKORO_BASE_URL")
        )

        self.api_key = (
            api_key or
            config.get("api_key") or
            os.getenv("KOKORO_API_KEY")
        )

        # Validation
        if not self.base_url:
            raise ValueError(
                "Kokoro base URL is required. "
                "Set KOKORO_BASE_URL environment variable or provide base_url in config."
            )

        # Use a default API key if none is provided (some endpoints don't require authentication)
        if not self.api_key:
            logger.warning("No API key provided for OpenAI-compatible endpoint. Using default 'not-required' value.")
            self.api_key = "not-required"

        # Ensure base_url doesn't end with trailing slash for consistency
        if self.base_url.endswith("/"):
            self.base_url = self.base_url.rstrip("/")

        # Remove base_url and api_key from config to avoid duplication
        clean_config = {k: v for k, v in config.items() if k not in ['base_url', 'api_key']}

        # Call parent's __init__ to set up HTTP clients and other initialization
        super().__init__(
            model_name=model_name or self._get_default_model(),
            api_key=self.api_key,
            base_url=self.base_url,
            **clean_config
        )

    def _handle_error(self, response) -> None:
        """Handle HTTP error responses with graceful degradation."""
        if response.status_code >= 400:
            # Log original response for debugging
            logger.debug(f"OpenAI-compatible endpoint error: {response.text}")

            # Try to parse error message from multiple common formats
            try:
                error_data = response.json()
                # Try multiple error message formats
                error_message = (
                    error_data.get("error", {}).get("message") or
                    error_data.get("detail", {}).get("message") or  # Some APIs use this
                    error_data.get("message") or  # Direct message field
                    f"HTTP {response.status_code}"
                )
            except Exception:
                # Fall back to HTTP status code
                error_message = f"HTTP {response.status_code}: {response.text}"
            raise RuntimeError(f"OpenAI-compatible TTS endpoint error: {error_message}")

    @property
    def models(self) -> List[Model]:
        """List all available models for this provider.
        Note: This attempts to fetch models from the /models endpoint.
        If the endpoint doesn't support this, it will return an empty list.
        """
        try:
            return [
                Model(
                    id=self.model_name,
                    owned_by="Kokoro",
                    context_window=None,  # Audio models don't have context windows
                    type="text_to_speech",
                )
            ]
        except Exception as e:
            # Log the error but don't fail completely
            logger.info(f"Models endpoint not supported by OpenAI-compatible TTS endpoint: {e}")
            return []

    @property
    def available_voices(self) -> Dict[str, Voice]:
        """Get available voices from OpenAI-compatible TTS endpoint.

        This method attempts to fetch voices from a custom /audio/voices endpoint.
        If the endpoint doesn't support this, it falls back to a default voice.

        Returns:
            Dict[str, Voice]: Dictionary of available voices with their information
        """
        voices: Dict[str, Voice] = {}
        for vid in ["coral", "shimmer", "sage"]:
            voices[vid] = Voice(
                name=vid,
                id=vid,
                gender="Female",
                language_code="auto",
                description=f"Kokoro TTS voice {vid}",
            )
        for vid in ["alloy", "echo", "ash", "fable", "onyx", "nova"]:
            voices[vid] = Voice(
                name=vid,
                id=vid,
                gender="Male",
                language_code="auto",
                description=f"Kokoro TTS voice {vid}",
            )    
        return voices
        

    def _get_default_model(self) -> str:
        """Get the default model name.

        For OpenAI-compatible endpoints, we use a generic default
        that users should override with their specific model.
        """
        return "Kokoro-82M"

    @property
    def provider(self) -> str:
        """Get the provider name."""
        return "kokoro"
    
    @property
    def capability(self) -> TTSCapability:
        """Get TTS provider capabilities.
        
        Returns:
            TTSCapability: Capability information for Kokoro TTS
        """
        # Get default voices from available_voices
        default_voices = list(self.available_voices.keys())
        
        # Kokoro TTS may support some paralinguistic controls
        # Check if the provider supports voice tags (paralinguistic controls)
        voice_tags = []

        return TTSCapability(
            supported_languages=["zh", "en"],   # Chinese and English
            supported_dialects=["mandarin"],
            supports_instructions=False,  # Kokoro doesn't support instructions parameter
            supports_custom_voice=False,  # Kokoro doesn't support custom voice upload
            default_voices=default_voices if default_voices else ["default"],
            supports_voice_tags=False,  # Kokoro supports some paralinguistic controls
            available_voice_tags=voice_tags,
            metadata={
                "description": "Kokoro TTS supports multiple pre-trained voices",
                "voice_selection": "Select from predefined voice list",
                "voice_tags_format": "Paralinguistic controls: laughter, sighs, breaths, pauses. Can be embedded in text."
            }
        )

    def generate_speech(
        self,
        text: str,
        voice: str = "default",
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AudioResponse:
        """Generate speech from text using OpenAI-compatible Text-to-Speech API.

        Args:
            text: Text to convert to speech
            voice: Voice to use (default: "default")
            output_file: Optional path to save the audio file
            **kwargs: Additional parameters to pass to the API
        Returns:
            AudioResponse containing the audio data and metadata
        Raises:
            RuntimeError: If speech generation fails
        """
        try:
            # Prepare request payload using OpenAI standard format
            payload = {
                "model": self.model_name,
                "voice": voice,
                "input": text,  # OpenAI standard uses "input", not "text"
                **kwargs
            }
            print(f"Request Kokoro payload: {payload}")
            # Generate speech
            response = self.client.post(
                f"{self.base_url}/audio/speech",
                headers=self._get_headers(),
                json=payload
            )
            self._handle_error(response)

            # Get audio data (binary content)
            audio_data = response.content

            # Save to file if specified
            if output_file:
                output_file = Path(output_file)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(audio_data)

            return AudioResponse(
                audio_data=audio_data,
                content_type="audio/mp3",
                model=self.model_name,
                voice=voice,
                provider=self.provider,
                metadata={"text": text}
            )

        except Exception as e:
            raise RuntimeError(f"Failed to generate speech: {str(e)}") from e

    async def agenerate_speech(
        self,
        text: str,
        voice: str = "default",
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AudioResponse:
        """Generate speech from text using OpenAI-compatible Text-to-Speech API asynchronously.

        Args:
            text: Text to convert to speech
            voice: Voice to use (default: "default")
            output_file: Optional path to save the audio file
            **kwargs: Additional parameters to pass to the API

        Returns:
            AudioResponse containing the audio data and metadata

        Raises:
            RuntimeError: If speech generation fails
        """
        try:
            # Prepare request payload using OpenAI standard format
            payload = {
                "model": self.model_name,
                "voice": voice,
                "input": text,  # OpenAI standard uses "input", not "text"
                **kwargs
            }

            print(f"Request Kokoro payload: {payload}")

            # Generate speech
            response = await self.async_client.post(
                f"{self.base_url}/audio/speech",
                headers=self._get_headers(),
                json=payload
            )
            self._handle_error(response)

            # Get audio data (binary content)
            audio_data = response.content

            # Save to file if specified
            if output_file:
                output_file = Path(output_file)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_bytes(audio_data)

            return AudioResponse(
                audio_data=audio_data,
                content_type="audio/mp3",
                model=self.model_name,
                voice=voice,
                provider=self.provider,
                metadata={"text": text}
            )

        except Exception as e:
            raise RuntimeError(f"Failed to generate speech: {str(e)}") from e


# 测试代码
if __name__ == "__main__":
    import asyncio
    import os
    import sys
    
    async def test_kokoro_tts():
        """测试 KokoroTextToSpeechModel 类的功能"""
        print("开始测试 KokoroTextToSpeechModel...")
        
        # 设置环境变量（如果需要）
        os.environ.setdefault("KOKORO_BASE_URL", "http://localhost:9000/v1")  # 替换为实际的 API 地址
        
        # 创建 TTS 模型实例
        try:
            tts_model = KokoroTextToSpeechModel(
                model_name="Kokoro-82M",
                base_url=os.environ.get("KOKORO_BASE_URL")
            )
            print(f"成功创建 TTS 模型: {tts_model.model_name}")
            
            # 测试获取可用声音
            voices = tts_model.available_voices
            print(f"可用声音列表: {list(voices.keys())}")
            
            # 测试生成语音（同步方法）
            test_text = "这是一个测试文本，用于验证 Kokoro TTS 模型的功能。"
            voice_id = "echo"  # 使用一个可用的声音 ID
            output_file = "kokoro_tts_test.mp3"
            
            print(f"正在使用声音 '{voice_id}' 生成语音...")
            try:
                response = tts_model.generate_speech(
                    text=test_text,
                    voice=voice_id,
                    output_file=output_file
                )
                print(f"语音生成成功！输出文件: {output_file}")
                print(f"响应元数据: {response.metadata}")
                
                # 检查文件是否存在
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"文件大小: {file_size} 字节")
                else:
                    print(f"警告: 输出文件 {output_file} 未找到")
                
            except Exception as e:
                print(f"生成语音时出错: {str(e)}")
            
            # 测试异步生成语音
            print("\n测试异步语音生成...")
            try:
                async_output_file = "kokoro_tts_async_test.mp3"
                async_response = await tts_model.agenerate_speech(
                    text="这是一个异步生成的测试语音。",
                    voice=voice_id,
                    output_file=async_output_file
                )
                print(f"异步语音生成成功！输出文件: {async_output_file}")
                
            except Exception as e:
                print(f"异步生成语音时出错: {str(e)}")
                
        except Exception as e:
            print(f"测试过程中出错: {str(e)}")
            
        print("测试完成！")
    
    # 运行测试
    if sys.platform == "win32":
        # Windows 平台需要特殊处理异步事件循环
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_kokoro_tts())