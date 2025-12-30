"""DashScope Qwen TTS provider implementation (Alibaba Cloud)."""

import os
from pathlib import Path
import requests
import asyncio
from typing import Any, Dict, List, Optional, Union

from esperanto.common_types import Model
from esperanto.utils.logging import logger
import dashscope

from esperanto.providers.tts.base import AudioResponse, Voice, TextToSpeechModel
from .tts_capability import TTSCapability

class QWenTextToSpeechModel(TextToSpeechModel):
    """Qwen Text-to-Speech provider using DashScope SDK.

    This provider calls dashscope.MultiModalConversation to synthesize speech
    with Qwen3-TTS models (e.g., qwen3-tts-flash). Only non-streaming mode is
    supported per current requirement: we obtain a final audio URL and fetch
    WAV bytes from it.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize Qwen TTS provider.

        Args:
            model_name: Name of the model to use (default: qwen3-tts-flash)
            api_key: DashScope API key. If not provided, read from DASHSCOPE_API_KEY
            base_url: DashScope HTTP API base URL for the region
            config: Additional configuration options
            **kwargs: Additional configuration options
        """
        config = (config or {})
        config.update(kwargs)

        # Read configuration (env -> config -> params)
        self.base_url = (
            base_url or
            config.get("base_url") or
            os.getenv("DASHSCOPE_BASE_URL") or
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        )
        self.api_key = (
            api_key or
            config.get("api_key") or
            os.getenv("DASHSCOPE_API_KEY")
        )

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for Qwen TTS provider.")

        # Configure DashScope SDK base URL for region
        # dashscope.base_http_api_url = self.base_url

        # Parent init (we don't use OpenAI clients here, but keep base metadata)
        super().__init__(
            model_name=model_name or self._get_default_model(),
            api_key=self.api_key,
            base_url=self.base_url,
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

    def _get_models(self) -> List[Model]:
        """Get available Qwen TTS models.
        
        This method is required by the TextToSpeechModel base class.
        
        Returns:
            List of available models
        """
        return [
            Model(
                id=self.model_name,
                owned_by="dashscope",
                context_window=None,
                type="text_to_speech",
            )
        ]

    @property
    def models(self) -> List[Model]:
        """Return available Qwen TTS models (static)."""
        return self._get_models()

    @property
    def available_voices(self) -> Dict[str, Voice]:
        """Return known Qwen voices.
        DashScope does not expose a REST voice listing endpoint; we provide a
        small static set that is commonly available. Users can still pass any
        supported voice string.
        """
        voices: Dict[str, Voice] = {}
        for vid in ["Cherry", "Jennifer", "Katerina", "Elias", "Jada","Sunny","Kiki"]:
            voices[vid] = Voice(
                name=vid,
                id=vid,
                gender="Female",
                language_code="auto",
                description=f"Qwen TTS voice {vid}",
            )

        for vid in ["Ethan", "Nofish", "Ryan", "Dylan", "Li","Marcus","Roy","Peter","Rocky","Eric"]:
            voices[vid] = Voice(
                name=vid,
                id=vid,
                gender="Male",
                language_code="auto",
                description=f"Qwen TTS voice {vid}",
            )    
        return voices

    def _get_default_model(self) -> str:
        """Get the default model name.

        For OpenAI-compatible endpoints, we use a generic default
        that users should override with their specific model.
        """
        return "qwen3-tts-flash"

    @property
    def provider(self) -> str:
        """Get the provider name."""
        return "qwen"
    
    @property
    def capability(self) -> TTSCapability:
        """Get TTS provider capabilities.
        
        Returns:
            TTSCapability: Capability information for Qwen TTS
        """
        # Get default voices from available_voices
        default_voices = list(self.available_voices.keys())
        # Qwen TTS supports paralinguistic controls (voice tags)
        voice_tags = []
        
        return TTSCapability(
            supported_languages=["zh", "en"],  # Chinese and English
            supported_dialects=["mandarin"],
            supports_instructions=False,  # Qwen TTS doesn't support instructions parameter
            supports_custom_voice=False,  # Qwen TTS doesn't support custom voice upload
            default_voices=default_voices if default_voices else ["default"],
            supports_voice_tags=False,  # Qwen supports paralinguistic controls
            available_voice_tags=voice_tags,
            metadata={
                "description": "Qwen TTS (Alibaba Cloud DashScope) supports multiple pre-trained voices",
                "voice_selection": "Select from predefined voice list",
                "voice_tags_format": "Paralinguistic controls: laughter, sighs, breaths, pauses, coughs. Can be embedded in text."
            }
        )

    def generate_speech(
        self,
        text: str,
        voice: str = "Cherry",
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AudioResponse:
        """Generate speech via DashScope Qwen TTS.

        Args:
            text: Text to convert to speech
            voice: Voice to use (default: "Cherry")
            output_file: Optional path to save the audio file
            **kwargs: Additional parameters, e.g. language_type="Auto"

        Returns:
            AudioResponse containing audio data and metadata
        """
        try:
            language_type = kwargs.pop("language_type", "Auto")
            print(f"Qwen TTS request: text={text}, voice={voice}, model={self.model_name} language_type={language_type}, api_key={self.api_key}")
            response = dashscope.MultiModalConversation.call(
                model=self.model_name,
                api_key=self.api_key,
                text=text,
                voice=voice,
                language_type=language_type,
                stream=False,
            )

            print(f"Qwen TTS response: {response}")


            audio_url = response.output.audio.url
            resp = requests.get(audio_url)
            resp.raise_for_status()
            audio_bytes = resp.content

            # Save to file if requested
            if output_file:
                out = Path(output_file)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(audio_bytes)

            return AudioResponse(
                audio_data=audio_bytes,
                content_type="audio/wav",
                model=self.model_name,
                voice=voice,
                provider=self.provider,
                metadata={"text": text, "language_type": language_type},
            )
        except Exception as e:
            import traceback
            logger.error(f"Qwen TTS error details:\n{traceback.format_exc()}")
            raise RuntimeError(f"Failed to generate speech: {str(e)}") from e

    async def agenerate_speech(
        self,
        text: str,
        voice: str = "Cherry",
        output_file: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> AudioResponse:
        """Async wrapper for generate_speech using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_speech(text=text, voice=voice, output_file=output_file, **kwargs),
        )


if __name__ == "__main__":
    """简单的命令行测试入口。
    使用示例：
        python -m podcast_creator.providers.qwen_tts --text "你好，通义千问语音合成测试" --voice Cherry --output qwen_tts_test.wav
    或者直接运行文件：
        python podcast/podcast-creator/src/podcast_creator/providers/qwen_tts.py --text "欢迎使用" --voice Cherry --output qwen_tts_test.wav
    需要环境变量：
        - DASHSCOPE_API_KEY（必需）
        - DASHSCOPE_BASE_URL（可选，默认 https://dashscope-intl.aliyuncs.com/api/v1）
    """
    import argparse
    import sys
    from pathlib import Path
    import os

    parser = argparse.ArgumentParser(description="Qwen TTS 测试")
    parser.add_argument("--text", type=str, default="你好，欢迎使用通义千问语音合成测试。", help="需要合成的文本")
    parser.add_argument("--voice", type=str, default="Cherry", help="语音名称，如 Cherry/Dylan/Jada/Sunny")
    parser.add_argument("--output", type=str, default="qwen_tts_test.wav", help="输出音频文件路径（wav）")
    parser.add_argument("--base-url", type=str, default=os.getenv("DASHSCOPE_BASE_URL"), help="DashScope 基础 URL")
    parser.add_argument("--api-key", type=str, default=os.getenv("DASHSCOPE_API_KEY"), help="DashScope API Key")
    args = parser.parse_args()

    if not args.api_key:
        print("错误：未设置 DASHSCOPE_API_KEY。请设置环境变量或使用 --api-key 指定。")
        sys.exit(1)

    # 规范化输出路径
    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        model = QWenTextToSpeechModel(
            api_key=args.api_key,
            base_url=args.base_url,
        )
        resp = model.generate_speech(text=args.text, voice=args.voice, output_file=str(out_path))
        print(
            f"生成成功: {out_path}\n"
            f"模型: {resp.model}, 提供商: {resp.provider}, 语音: {resp.voice}\n"
            f"格式: {resp.content_type}, 字节数: {len(resp.audio_data)}"
        )
        sys.exit(0)
    except Exception as e:
        print(f"生成失败: {e}")
        sys.exit(2)