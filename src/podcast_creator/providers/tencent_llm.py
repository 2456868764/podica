"""
腾讯兼容OpenAI的LLM实现
"""

"""Tencent-compatible language model implementation."""

import os
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Union, cast

from esperanto.common_types import Model
from esperanto.providers.llm.openai import OpenAILanguageModel
from esperanto.utils.logging import logger

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.runnables import RunnableConfig

if TYPE_CHECKING:
    from langchain_openai import ChatOpenAI


class TencentChatModel(BaseChatModel):
    """Custom LangChain chat model implementation for Tencent Hunyuan."""
    
    model_name: str
    temperature: float = 0.5
    top_p: float = 0.95
    max_tokens: Optional[int] = 2000
    streaming: bool = False
    base_url: str
    api_key: str
    client_kwargs: Dict[str, Any] = {}
    model_kwargs: Dict[str, Any] = {}
    
    class Config:
        """Configuration for this pydantic object."""
        arbitrary_types_allowed = True
    
    def __init__(
        self,
        model: str,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: Optional[int] = 2000,
        streaming: bool = False,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the TencentChatModel."""
        # Set API configuration
        base_url = base_url or os.getenv("TENCENT_BASE_URL")
        if not base_url:
            raise ValueError(
                "Tencent base URL is required. "
                "Set TENCENT_BASE_URL environment variable or provide base_url."
            )
        
        api_key = api_key or os.getenv("TENCENT_API_KEY") or "not-required"
        
        # Ensure base_url doesn't end with trailing slash for consistency
        if base_url.endswith("/"):
            base_url = base_url.rstrip("/")
            
        # Set additional model kwargs
        model_kwargs = model_kwargs or {}
        
        # Initialize the parent class with all parameters
        super().__init__(
            model_name=model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            streaming=streaming,
            base_url=base_url,
            api_key=api_key,
            model_kwargs=model_kwargs,
            **kwargs
        )
    
    @property
    def _llm_type(self) -> str:
        """Return the type of LLM."""
        return "tencent-hunyuan"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                openai_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openai_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                openai_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, ChatMessage):
                openai_messages.append({"role": message.role, "content": message.content})
            else:
                openai_messages.append({"role": "user", "content": str(message.content)})
        return openai_messages
    
    def _create_chat_result(self, response_data: Dict[str, Any]) -> ChatResult:
        """Create a ChatResult from the API response."""
        choices = response_data.get("choices", [])
        if not choices:
            return ChatResult(generations=[])
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        # 确保内容是正确解码的字符串，而不是转义的 Unicode
        # if isinstance(content, str):
        #     # 如果内容是 JSON 字符串，尝试解析它
        #     if content.strip().startswith('{') and content.strip().endswith('}'):
        #         try:
        #             import json
        #             # 确保 JSON 解析时不会将 Unicode 转义序列转换回原始字符
        #             parsed_content = json.loads(content)
        #             # 将解析后的对象转换回 JSON 字符串，但不使用 Unicode 转义
        #             content = json.dumps(parsed_content, ensure_ascii=False)
        #         except Exception:
        #             # 如果解析失败，保留原始内容
        #             content = content.strip()
        #             logger.warning(f"Failed to parse JSON content: {content}")
        #             pass
        
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                import json
                # 确保 JSON 解析时不会将 Unicode 转义序列转换回原始字符
                parsed_content = json.loads(content)
                print(f"parsed_content: {parsed_content}")
            except Exception:
                # 如果解析失败，保留原始内容
                logger.warning(f"Failed to parse JSON content: {content}")
                raise ValueError(f"Failed to parse JSON content: {content}")
                
        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={
                "finish_reason": choices[0].get("finish_reason"),
                "model": response_data.get("model"),
            }
        )
        
        return ChatResult(generations=[generation])
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> ChatResult:
        """Generate a response from the model."""
        import requests
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "messages": self._convert_messages_to_openai_format(messages),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,
        }
        
        # Add max_tokens if specified
        if self.max_tokens is not None:
            # Ensure max_tokens doesn't exceed 2000 to prevent LengthFinishReasonError
            payload["max_tokens"] = min(self.max_tokens, 2000)
        # Add stop sequences if specified
        if stop:
            payload["stop"] = stop
            
        # Add additional model kwargs
        payload.update(self.model_kwargs)

        print(f"chat complete payload: {payload}")
        
        # Make the API request
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(),
            json=payload
        )
        
        # Handle errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            except Exception:
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            raise RuntimeError(f"OpenAI-compatible endpoint error: {error_message}")
        
        # Parse the response
        response_data = response.json()

        print(f"chat complete response data: {response_data}")
        
        # Create and return the chat result
        return self._create_chat_result(response_data)
    
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs
    ) -> ChatResult:
        """Generate a response from the model asynchronously."""
        import aiohttp
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "messages": self._convert_messages_to_openai_format(messages),
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False,
        }
        
        # Add max_tokens if specified
        if self.max_tokens is not None:
            # Ensure max_tokens doesn't exceed 2000 to prevent LengthFinishReasonError
            payload["max_tokens"] = min(self.max_tokens, 2000)
        
        # Add stop sequences if specified
        if stop:
            payload["stop"] = stop
            
        print(f"async chat complete payload:=================\n {payload}\n=================")
        
        # Add additional model kwargs
        payload.update(self.model_kwargs)
        
        # Make the API request asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            ) as response:
                # Handle errors
                if response.status >= 400:
                    try:
                        error_data = await response.json()
                        error_message = error_data.get("error", {}).get("message", f"HTTP {response.status}")
                    except Exception:
                        error_message = f"HTTP {response.status}: {await response.text()}"
                    
                    raise RuntimeError(f"OpenAI-compatible endpoint error: {error_message}")
                
                # Parse the response
                response_data = await response.json()
                print(f"async chat complete response data:=================\n {response_data}\n=================")
        
        # Create and return the chat result
        return self._create_chat_result(response_data)
    
    async def ainvoke(
        self, 
        input: Union[str, List[BaseMessage]], 
        config: Optional[RunnableConfig] = None,
        **kwargs
    ) -> BaseMessage:
        """Asynchronously invoke the model with the given input."""
        # Convert string input to a message if needed
        if isinstance(input, str):
            input_messages = [HumanMessage(content=input)]
        else:
            input_messages = input
        
        # Generate the response
        result = await self._agenerate(
            messages=input_messages,
            run_manager=None if config is None else AsyncCallbackManagerForLLMRun.configure(
                callbacks=config.get("callbacks"),
                inheritable_callbacks=config.get("inheritable_callbacks"),
                tags=config.get("tags"),
                inheritable_tags=config.get("inheritable_tags"),
                metadata=config.get("metadata"),
                inheritable_metadata=config.get("inheritable_metadata"),
            ),
            **kwargs
        )
        
        # Return the first generation's message
        if result.generations:
            return result.generations[0].message
        else:
            return AIMessage(content="")


class TencentLanguageModel(OpenAILanguageModel):
    """Tencent language model implementation for custom endpoints."""

    base_url: Optional[str] = None
    api_key: Optional[str] = None

    def __post_init__(self):
        """Initialize OpenAI-compatible configuration."""
        # Initialize _config first (from base class)
        if not hasattr(self, '_config'):
            self._config = {}
        
        # Update with any provided config
        if hasattr(self, "config") and self.config:
            self._config.update(self.config)
        
        # Configuration precedence: Factory config > Environment variables > Default
        self.base_url = (
            self.base_url or 
            self._config.get("base_url") or 
            os.getenv("TENCENT_BASE_URL")
        )
        self.api_key = (
            self.api_key or 
            self._config.get("api_key") or 
            os.getenv("TENCENT_API_KEY")
        )
        
        # Validation
        if not self.base_url:
            raise ValueError(
                "Tencent base URL is required. "
                "Set TENCENT_BASE_URL environment variable or provide base_url in config."
            )
        # Use a default API key if none is provided (some endpoints don't require authentication)
        if not self.api_key:
            self.api_key = "not-required"

        # Ensure base_url doesn't end with trailing slash for consistency
        if self.base_url.endswith("/"):
            self.base_url = self.base_url.rstrip("/")

        # Call parent's post_init to set up HTTP clients and normalized response handling
        super().__post_init__()

    def _handle_error(self, response) -> None:
        """Handle HTTP error responses with graceful degradation."""
        if response.status_code >= 400:
            # Log original response for debugging
            logger.debug(f"OpenAI-compatible endpoint error: {response.text}")
            
            # Try to parse OpenAI-format error
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            except Exception:
                # Fall back to HTTP status code
                error_message = f"HTTP {response.status_code}: {response.text}"
            
            raise RuntimeError(f"OpenAI-compatible endpoint error: {error_message}")
    
    def _normalize_response(self, response_data: Dict[str, Any]) -> "ChatCompletion":
        """Normalize OpenAI-compatible response to our format with graceful fallback."""
        from esperanto.common_types import ChatCompletion, Choice, Message, Usage
        
        print(f"raw response data: {response_data}")
        # Handle missing or incomplete response fields gracefully
        response_id = response_data.get("id", "chatcmpl-unknown")
        created = response_data.get("created", 0)
        model = response_data.get("model", self.get_model_name())
        
        # Handle choices array
        choices = response_data.get("choices", [])
        normalized_choices = []
        
        for choice in choices:
            message = choice.get("message", {})
            normalized_choice = Choice(
                index=choice.get("index", 0),
                message=Message(
                    content=message.get("content", ""),
                    role=message.get("role", "assistant"),
                ),
                finish_reason=choice.get("finish_reason", "stop"),
            )
            normalized_choices.append(normalized_choice)
        
        # If no choices, create a default one
        if not normalized_choices:
            normalized_choices = [Choice(
                index=0,
                message=Message(content="", role="assistant"),
                finish_reason="stop"
            )]
        
        # Handle usage information
        usage_data = response_data.get("usage", {})
        usage = Usage(
            completion_tokens=usage_data.get("completion_tokens", 0),
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
        
        return ChatCompletion(
            id=response_id,
            choices=normalized_choices,
            created=created,
            model=model,
            provider=self.provider,
            usage=usage,
        )

    def _normalize_chunk(self, chunk_data: Dict[str, Any]) -> "ChatCompletionChunk":
        """Normalize OpenAI-compatible stream chunk to our format with graceful fallback."""
        from esperanto.common_types import ChatCompletionChunk, StreamChoice, DeltaMessage
        
        # Handle missing or incomplete chunk fields gracefully
        chunk_id = chunk_data.get("id", "chatcmpl-unknown")
        created = chunk_data.get("created", 0)
        model = chunk_data.get("model", self.get_model_name())
        
        # Handle choices array
        choices = chunk_data.get("choices", [])
        normalized_choices = []
        
        for choice in choices:
            delta = choice.get("delta", {})
            normalized_choice = StreamChoice(
                index=choice.get("index", 0),
                delta=DeltaMessage(
                    content=delta.get("content", ""),
                    role=delta.get("role", "assistant"),
                    function_call=delta.get("function_call"),
                    tool_calls=delta.get("tool_calls"),
                ),
                finish_reason=choice.get("finish_reason"),
            )
            normalized_choices.append(normalized_choice)
        
        # If no choices, create a default one
        if not normalized_choices:
            normalized_choices = [StreamChoice(
                index=0,
                delta=DeltaMessage(content="", role="assistant"),
                finish_reason=None
            )]
        
        return ChatCompletionChunk(
            id=chunk_id,
            choices=normalized_choices,
            created=created,
            model=model,
        )

    def _get_api_kwargs(self, exclude_stream: bool = False) -> Dict[str, Any]:
        """Get API kwargs with graceful feature fallback.
        
        Args:
            exclude_stream: If True, excludes streaming-related parameters.
            
        Returns:
            Dict containing API parameters for the request.
        """
        # Get base kwargs from parent
        kwargs = super()._get_api_kwargs(exclude_stream)
        
        # For OpenAI-compatible endpoints, we attempt all features
        # and let the endpoint handle graceful degradation
        # This includes streaming, JSON mode, and other OpenAI features
        
        return kwargs

    def _is_reasoning_model(self) -> bool:
        return False
    
    @property
    def models(self) -> List[Model]:
        """List all available models for this provider.
        
        Note: This attempts to fetch models from the /models endpoint.
        If the endpoint doesn't support this, it will return an empty list.
        """
        try:
            response = self.client.get(
                f"{self.base_url}/models",
                headers=self._get_headers()
            )
            self._handle_error(response)
            
            models_data = response.json()
            return [
                Model(
                    id=model["id"],
                    owned_by=model.get("owned_by", "custom"),
                    context_window=model.get("context_window", None),
                    type="language",
                )
                for model in models_data.get("data", [])
            ]
        except Exception as e:
            # Log the error but don't fail completely
            logger.debug(f"Could not fetch models from OpenAI-compatible endpoint: {e}")
            return []

    def _get_default_model(self) -> str:
        """Get the default model name.
        
        For OpenAI-compatible endpoints, we use a generic default
        that users should override with their specific model.
        """
        return "hunyuan-turbos-latest"

    @property
    def provider(self) -> str:
        """Get the provider name."""
        return "tencent"

    def to_langchain(self) -> TencentChatModel:
        """Convert to a custom LangChain chat model.

        Returns:
            TencentChatModel: A custom LangChain chat model for Tencent Hunyuan.
        """
        model_kwargs = {}
        if self.structured and isinstance(self.structured, dict):
            structured_type = self.structured.get("type")
            if structured_type in ["json", "json_object"]:
                model_kwargs["response_format"] = {"type": "json_object"}

        # Ensure max_tokens doesn't exceed 2000 to prevent LengthFinishReasonError
        max_tokens = min(self.max_tokens, 2000) if self.max_tokens is not None else 2000
  
     
        # Create and return the custom TencentChatModel
        return TencentChatModel(
            model=self.get_model_name(),
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=max_tokens,
            streaming=self.streaming,
            api_key=self.api_key,
            base_url=self.base_url,
            model_kwargs=model_kwargs,
        )