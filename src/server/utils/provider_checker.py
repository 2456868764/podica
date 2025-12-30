"""
播客创作工作室的提供商可用性检查器。

根据环境变量检查哪些AI和TTS提供商可用。
"""

import os
import streamlit as st
from typing import Dict, List, Tuple

class ProviderChecker:
    """用于根据环境变量检查提供商可用性的工具类。"""
    
    @staticmethod
    def check_available_providers() -> Tuple[List[str], List[str]]:
        """
        根据环境变量检查哪些提供商可用。
        
        返回:
            (可用提供商, 不可用提供商) 的元组
        """
        provider_status = {}
        
        # AI/LLM 提供商
        if os.environ.get("OLLAMA_API_BASE") != "":
            provider_status["ollama"] = True
        
        if os.environ.get("GROQ_API_KEY") != "":
            provider_status["groq"] = True

        if os.environ.get("XAI_API_KEY") != "":
            provider_status["xai"] = True

        if os.environ.get("GOOGLE_API_KEY") != ""  or os.environ.get("GEMINI_API_KEY") != "":
            provider_status["gemini"] = True

        if os.environ.get("OPENROUTER_API_KEY") != "" and os.environ.get("OPENROUTER_BASE_URL") != "":
            provider_status["openrouter"] = True

        if os.environ.get("ANTHROPIC_API_KEY")!="":
            provider_status["anthropic"] = True

        # provider_status["ollama"] = os.environ.get("OLLAMA_API_BASE") is not None
        # provider_status["openai"] = os.environ.get("OPENAI_API_KEY") is not None
        # provider_status["groq"] = os.environ.get("GROQ_API_KEY") is not None
        # provider_status["xai"] = os.environ.get("XAI_API_KEY") is not None
        # provider_status["vertexai"] = (
        #     os.environ.get("VERTEX_PROJECT") is not None
        #     and os.environ.get("VERTEX_LOCATION") is not None
        #     and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is not None
        # )
        # provider_status["gemini"] = (
        #     os.environ.get("GOOGLE_API_KEY") is not None
        #     or os.environ.get("GEMINI_API_KEY") is not None
        # )
        # provider_status["openrouter"] = (
        #     os.environ.get("OPENROUTER_API_KEY") is not None
        #     and os.environ.get("OPENAI_API_KEY") is not None
        #     and os.environ.get("OPENROUTER_BASE_URL") is not None
        # )
        # provider_status["anthropic"] = os.environ.get("ANTHROPIC_API_KEY") is not None
        # provider_status["azure"] = (
        #     os.environ.get("AZURE_OPENAI_API_KEY") is not None
        #     and os.environ.get("AZURE_OPENAI_ENDPOINT") is not None
        #     and os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME") is not None
        #     and os.environ.get("AZURE_OPENAI_API_VERSION") is not None
        # )
        # provider_status["mistral"] = os.environ.get("MISTRAL_API_KEY") is not None
        # provider_status["deepseek"] = os.environ.get("DEEPSEEK_API_KEY") is not None

        if os.environ.get("OPENAI_API_KEY","") != "":
            provider_status["openai"] = True

        if os.environ.get("DASHSCOPE_API_KEY","") != "":
            provider_status["qwen"] = True

        if os.environ.get("TENCENT_API_KEY","") != "":
            provider_status["tencent"] = True

        # TTS 提供商
        if os.environ.get("KOKORO_BASE_URL","") != "":
            provider_status["kokoro"] = True
            
        if os.environ.get("ELEVENLABS_API_KEY","") != "":
            provider_status["elevenlabs"] = True

        if os.environ.get("V3API_API_KEY","") != "":
            provider_status["v3api"] = True

        if os.environ.get("LAOZHANG_API_KEY","") != "":
            provider_status["laozhang"] = True    

        if os.environ.get("DEEPSEEK_API_KEY","") != "":
            provider_status["deepseek"] = True

        if os.environ.get("INDEXTTS_BASE_URL","") != "":
            provider_status["indextts"] = True
            
        if os.environ.get("SOULX_BASE_URL","") != "":
            provider_status["soulx"] = True

        if os.environ.get("ERNIE_API_KEY","") != "":
            provider_status["erine"] = True

        # 注意: openai 和 google 已在上面的LLM中检查过，它们也提供TTS服务
        print(f"provider_status: {provider_status}")
        available_providers = [k for k, v in provider_status.items() if v]
        unavailable_providers = [k for k, v in provider_status.items() if not v]
        
        return available_providers, unavailable_providers
    
    @staticmethod
    def get_available_llm_providers() -> List[str]:
        """
        获取可用的LLM提供商列表。
        
        返回:
            可用LLM提供商名称列表
        """
        available_providers, _ = ProviderChecker.check_available_providers()
        
        # 仅筛选LLM提供商（排除仅TTS提供商）
        llm_providers = [
            "ollama", "openai", "groq", "xai", "vertexai", "gemini", 
            "openrouter", "anthropic", "azure", "mistral", "deepseek", "tencent", "qwen", "erine"
        ]
        
        return [p for p in llm_providers if p in available_providers]
    
    @staticmethod
    def get_available_tts_providers() -> List[str]:
        """
        获取可用的TTS提供商列表。
        
        返回:
            可用TTS提供商名称列表
        """
        available_providers, _ = ProviderChecker.check_available_providers()
        
        # TTS提供商
        tts_providers = ["elevenlabs", "openai", "kokoro", "laozhang", "v3api", "qwen", "indextts","soulx"]
        
        return [p for p in tts_providers if p in available_providers]
    
    @staticmethod
    def get_default_models(provider: str) -> Dict[str, str]:
        """
        获取提供商的默认模型。
        
        参数:
            provider: 提供商名称
            
        返回:
            包含默认模型的字典
        """
        defaults = {
            "openai": {
                "outline": "gpt-4o",
                "transcript": "gpt-4o",
                "tts": "tts-1"
            },
            "anthropic": {
                "outline": "claude-3-5-sonnet-20241022",
                "transcript": "claude-3-5-sonnet-20241022"
            },
            "gemini": {
                "outline": "gemini-1.5-pro",
                "transcript": "gemini-1.5-pro"
            },
            "google": {
                "outline": "gemini-1.5-pro",
                "transcript": "gemini-1.5-pro",
                "tts": "standard"
            },
            "groq": {
                "outline": "llama-3.1-70b-versatile",
                "transcript": "llama-3.1-70b-versatile"
            },
            "ollama": {
                "outline": "llama3.1",
                "transcript": "llama3.1"
            },
            "openrouter": {
                "outline": "meta-llama/llama-3.1-70b-instruct",
                "transcript": "meta-llama/llama-3.1-70b-instruct"
            },
            "azure": {
                "outline": "gpt-4o",
                "transcript": "gpt-4o"
            },
            "mistral": {
                "outline": "mistral-large-latest",
                "transcript": "mistral-large-latest"
            },
            "deepseek": {
                "outline": "deepseek-chat",
                "transcript": "deepseek-chat"
            },
            "xai": {
                "outline": "grok-beta",
                "transcript": "grok-beta"
            },
            "tencent": {
                "outline": "tencent-model",
                "transcript": "tencent-model"
            },
            "elevenlabs": {
                "tts": "eleven_flash_v2_5"
            }
        }
        
        return defaults.get(provider, {})
    
    @staticmethod
    def render_provider_selector(
        label: str,
        providers: List[str],
        current_provider: str = "",
        key: str = "",
        help_text: str = ""
    ) -> str:
        """
        Render a provider selector with only available providers.
        
        Args:
            label: Label for the selectbox
            providers: List of all possible providers
            current_provider: Currently selected provider
            key: Unique key for the widget
            help_text: Help text for the widget
            
        Returns:
            Selected provider
        """
        available_providers = ProviderChecker.get_available_llm_providers()
        
        # Filter providers to only available ones
        filtered_providers = [p for p in providers if p in available_providers]

        print(f"Available providers: {available_providers}")
        print(f"filtered providers: {filtered_providers}")
        
        if not filtered_providers:
            st.error("❌ No AI providers available. Please configure API keys.")
            return current_provider or ""
        
        # Find current selection index
        current_index = 0
        if current_provider and current_provider in filtered_providers:
            current_index = filtered_providers.index(current_provider)
        elif current_provider not in filtered_providers and filtered_providers:
            # Current provider not available, add it as disabled option
            filtered_providers.insert(0, f"{current_provider} (unavailable)")
            current_index = 0
        
        # 显示关于不可用提供商的警告
        unavailable_count = len(providers) - len(filtered_providers)
        # if unavailable_count > 0:
        #     st.info(f"ℹ️ {unavailable_count} 个提供商因缺少API密钥而不可用")
        
        selected = st.selectbox(
            label,
            filtered_providers,
            index=current_index,
            key=key,
            help=help_text
        )
        
        # 清理被标记为不可用的选择
        if selected and "(unavailable)" in selected:
            return selected.replace(" (unavailable)", "")
        
        return selected
    
    @staticmethod
    def render_tts_provider_selector(
        label: str,
        current_provider: str = "",
        key: str = "",
        help_text: str = ""
    ) -> str:
        """
        渲染仅包含可用提供商的TTS提供商选择器。
        
        参数:
            label: 选择框的标签
            current_provider: 当前选择的提供商
            key: 组件的唯一键
            help_text: 组件的帮助文本
            
        返回:
            选择的提供商
        """
        available_providers = ProviderChecker.get_available_tts_providers()
        
        if not available_providers:
            st.error("❌ 没有可用的TTS提供商。请配置API密钥。")
            return current_provider or ""
        
        # Find current selection index
        current_index = 0
        if current_provider and current_provider in available_providers:
            current_index = available_providers.index(current_provider)
        elif current_provider not in available_providers and available_providers:
            # Current provider not available, add it as disabled option
            available_providers.insert(0, f"{current_provider} (unavailable)")
            current_index = 0
        
        selected = st.selectbox(
            label,
            available_providers,
            index=current_index,
            key=key,
            help=help_text
        )
        
        # Clean up the selection if it was marked as unavailable
        if selected and "(unavailable)" in selected:
            return selected.replace(" (unavailable)", "")
        
        return selected
    
    @staticmethod
    def show_provider_status():
        """显示当前可用和不可用的提供商状态。"""
        available_providers, unavailable_providers = ProviderChecker.check_available_providers()
        
        st.markdown("### 🔌 提供商状态")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ 可用:**")
            if available_providers:
                for provider in sorted(available_providers):
                    st.markdown(f"- {provider}")
            else:
                st.markdown("*没有配置提供商*")
        
        with col2:
            st.markdown("**❌ 不可用:**")
            if unavailable_providers:
                for provider in sorted(unavailable_providers):
                    st.markdown(f"- {provider}")
            else:
                st.markdown("*所有提供商均已配置*")
        
        if unavailable_providers:
            with st.expander("🔧 配置帮助"):
                st.markdown("**要启用提供商，请设置以下环境变量:**")
                
                config_help = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY", 
                    "groq": "GROQ_API_KEY",
                    "xai": "XAI_API_KEY",
                    "mistral": "MISTRAL_API_KEY",
                    "deepseek": "DEEPSEEK_API_KEY",
                    "elevenlabs": "ELEVENLABS_API_KEY",
                    "gemini": "GOOGLE_API_KEY 或 GEMINI_API_KEY",
                    "vertexai": "VERTEX_PROJECT, VERTEX_LOCATION, GOOGLE_APPLICATION_CREDENTIALS",
                    "azure": "AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION",
                    "openrouter": "OPENROUTER_API_KEY, OPENAI_API_KEY, OPENROUTER_BASE_URL",
                    "ollama": "OLLAMA_API_BASE",
                    "tencent": "TENCENT_API_BASE, TENCENT_API_KEY"
                }
                
                for provider in sorted(unavailable_providers):
                    if provider in config_help:
                        st.markdown(f"**{provider}:** `{config_help[provider]}`")