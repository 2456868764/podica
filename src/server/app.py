"""
Podica Studio - Streamlit界面

一个全面的网页界面，用于管理说话人配置、剧集配置，
以及使用podcast-creator库生成播客。
"""

from jinja2.utils import pass_context
import nest_asyncio
nest_asyncio.apply()

import streamlit as st
import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
# Add the parent directory to the path to import podcast_creator
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)
# sys.path.append(root_dir)
print(f"root_dir: {root_dir}")
print(f"sys.path: {sys.path}")

from content_core.logging import configure_logging
# 启用 debug 级别日志
configure_logging(debug=True)

RESOURCES_DIR = os.path.join(root_dir, "resources")

EPISODE_CONFIG_FILE = os.path.join(RESOURCES_DIR, "episodes_config.json")
SPEAKERS_CONFIG_FILE = os.path.join(RESOURCES_DIR, "speakers_config.json")
EMOTIONS_CONFIG_FILE = os.path.join(RESOURCES_DIR, "emotions_config.json")
PROMPTS_DIR = os.path.join(RESOURCES_DIR, "prompts")
OUTPUT_DIR = os.path.join(RESOURCES_DIR, "output")

# Import utilities
from utils import EpisodeManager, ProfileManager, ContentExtractor, run_async_in_streamlit, ErrorHandler, VoiceProvider, ProviderChecker

# Use current working directory for all profile management
# WORKING_DIR = Path.cwd()

WORKING_DIR = RESOURCES_DIR

# 配置页面
st.set_page_config(
    page_title="Podica Studio",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f1f1f;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        margin: 0;
        opacity: 0.9;
    }
    
    .quick-action-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 0.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .quick-action-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def main():
    """主应用程序入口点。"""
    
    # 标题
    st.markdown('<div class="main-header">🎙️ Podica Studio</div>', unsafe_allow_html=True)
    
    # 初始化会话状态中的当前页面
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 首页"
    
    # 处理程序化导航
    if st.session_state.get('navigate_to_library', False):
        st.session_state.current_page = "📚 剧集库"
        st.session_state.navigate_to_library = False
    
    # 侧边栏导航
    with st.sidebar:
        st.title("导航")
        st.markdown("---")
        
        # 导航菜单
        pages = [
            "🏠 首页",
            "🎙️ 说话人配置", 
            "📺 剧集配置",
            "🎬 生成播客",
            "📚 剧集库"
        ]
        
        # 使用按钮替代下拉框进行页面导航
        selected_page = None
        for i, p in enumerate(pages):
            is_active = (st.session_state.current_page == p)
            btn_label = f"{p} {'✅' if is_active else ''}"
            if st.button(btn_label, key=f"navigation_btn_{i}", use_container_width=True):
                selected_page = p
        
        # 如果点击了按钮，则更新当前页面
        if selected_page and selected_page != st.session_state.current_page:
            st.session_state.current_page = selected_page
            st.rerun()
        
    # 使用会话状态中的当前页面
    page = st.session_state.current_page
    
    # 路由到适当的页面
    if page == "🏠 首页":
        show_home_page()
    elif page == "🎙️ 说话人配置":
        show_speaker_profiles_page()
    elif page == "📺 剧集配置":
        show_episode_profiles_page()
    elif page == "🎬 生成播客":
        show_generate_podcast_page()
    elif page == "📚 剧集库":
        show_episode_library_page()

def show_home_page():
    """显示带有仪表板和快速统计信息的首页。"""
    st.subheader("欢迎使用Podica Studio")
    st.markdown("您的AI驱动播客创作一站式解决方案")
    
    # 初始化管理器
    episode_manager = EpisodeManager(base_output_dir= os.path.join(WORKING_DIR, "output"))
    profile_manager = ProfileManager(working_dir=WORKING_DIR)
    
    # 获取统计数据
    try:
        episodes_stats = episode_manager.get_episodes_stats()
        profiles_stats = profile_manager.get_profiles_stats()
        
        # 快速统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{episodes_stats['total_episodes']}</p>
                <p class="stat-label">总剧集数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{profiles_stats['speaker_profiles_count']}</p>
                <p class="stat-label">说话人配置</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-number">{profiles_stats['episode_profiles_count']}</p>
                <p class="stat-label">剧集配置</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 最近剧集
        st.subheader("最近剧集")
        
        recent_episodes = episode_manager.scan_episodes_directory()
        if recent_episodes:
            for episode in recent_episodes[:5]:  # 显示最近5个剧集
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{episode.name}**")
                    if episode.created_date:
                        st.markdown(f"*创建时间: {episode.created_date.strftime('%Y-%m-%d %H:%M')}*")
                    if episode.duration:
                        st.markdown(f"*时长: {episode_manager.format_duration(episode.duration)}*")
                
                with col2:
                    if episode.audio_file and st.button("▶️ 播放", key=f"play_{episode.name}"):
                        st.session_state.selected_episode = episode
                        st.session_state.current_page = "📚 剧集库"
                        st.rerun()
                
                with col3:
                    if st.button("📄 详情", key=f"details_{episode.name}"):
                        st.session_state.selected_episode = episode
                        st.session_state.current_page = "📚 剧集库"
                        st.rerun()
                
                st.markdown("---")
        else:
            st.info("📝 未找到剧集。开始生成您的第一个播客吧！")
        
        st.markdown("---")
        
        # 提供商状态
        st.markdown("---")
        ProviderChecker.show_provider_status()
        
        
    
    except Exception as e:
        st.error(f"加载首页数据时出错: {str(e)}")
        st.markdown("请检查所有必需的文件是否就位并重试。")

def show_speaker_profiles_page():
    """显示说话人配置管理页面。"""
    st.subheader("🎙️ 说话人配置")
    st.markdown("管理您的说话人设置")
    
    # 初始化配置管理器
    profile_manager = ProfileManager(working_dir=WORKING_DIR)
    
    # 加载配置
    try:
        profiles = profile_manager.load_speaker_profiles()
        profile_names = list(profiles.get("profiles", {}).keys())
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ 新建配置", use_container_width=True):
                st.session_state.show_new_speaker_form = True
                st.rerun()
        
        # with col2:
        #     if st.button("📁 导入", use_container_width=True):
        #         st.session_state.show_import_speaker_form = True
        #         st.rerun()
        
        # with col3:
        #     if st.button("💾 导出全部", use_container_width=True):
        #         export_data = profile_manager.export_speaker_profiles()
        #         st.download_button(
        #             label="下载 speakers_config.json",
        #             data=json.dumps(export_data, indent=2),
        #             file_name="speakers_config.json",
        #             mime="application/json"
        #         )
        
        st.markdown("---")
        
        # 导入表单
        if st.session_state.get("show_import_speaker_form", False):
            st.subheader("📁 导入说话人配置")
            
            uploaded_file = st.file_uploader(
                "选择要导入的JSON文件",
                type=['json'],
                key="speaker_import_file"
            )
            
            if uploaded_file is not None:
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    imported_names = profile_manager.import_speaker_profiles(file_content)
                    
                    if imported_names:
                        st.success(f"✅ 成功导入 {len(imported_names)} 个配置: {', '.join(imported_names)}")
                        st.session_state.show_import_speaker_form = False
                        st.rerun()
                    else:
                        st.warning("⚠️ 未导入新配置。请检查配置是否已存在或文件格式是否正确。")
                except Exception as e:
                    st.error(f"❌ 导入配置时出错: {str(e)}")
            
            if st.button("❌ 取消导入"):
                st.session_state.show_import_speaker_form = False
                st.rerun()
            
            st.markdown("---")
        
        # 新建配置表单
        if st.session_state.get("show_new_speaker_form", False):
            st.subheader("➕ 创建新的说话人配置")
            
            profile_name = st.text_input("配置名称:", placeholder="例如: my_podcasters", key="new_profile_name")
            
            col1, col2 = st.columns(2)
            with col1:
                tts_provider = ProviderChecker.render_tts_provider_selector(
                    "TTS提供商:",
                    current_provider="elevenlabs",
                    key="new_tts_provider",
                    help_text="选择文本转语音提供商"
                )
            with col2:
                # 获取所选提供商的默认模型
                defaults = ProviderChecker.get_default_models(tts_provider)
                default_model = defaults.get("tts", "eleven_flash_v2_5")
                tts_model = st.text_input("TTS模型:", value=default_model, key="new_tts_model")
            
            st.markdown("### 说话人")
            
            # 在会话状态中初始化说话人
            if 'new_speakers' not in st.session_state:
                st.session_state.new_speakers = [{'name': '', 'voice_id': '', 'backstory': '', 'personality': '', 'custom_voice': None}]
            
            for i, speaker in enumerate(st.session_state.new_speakers):
                st.markdown(f"**说话人 {i+1}:**")
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    speaker_name = st.text_input("姓名:", key=f"new_speaker_name_{i}", value=speaker.get('name', ''))
                    
                    # 带有提供商特定声音的声音选择器
                    voice_id = VoiceProvider.render_voice_selector(
                        provider=tts_provider,
                        model=tts_model,
                        current_voice_id=speaker.get('voice_id', ''),
                        key=f"new_voice_id_{i}",
                        help_text=f"从{tts_provider}选择声音"
                    )
                    
                    # 如果可用，显示声音预览
                    if voice_id and tts_provider == "elevenlabs":
                        with st.expander("🎵 声音预览"):
                            VoiceProvider.render_voice_preview(tts_provider, voice_id)
                    
                    # 只有当 voice 为 "custom" 时才显示上传组件
                    custom_voice_data = None
                    custom_voice_filename = None
                    if voice_id == "custom":
                        # 检查是否支持自定义 voice，如果支持则显示上传组件
                        custom_voice_data, custom_voice_filename = VoiceProvider.render_custom_voice_upload(
                            provider=tts_provider,
                            model=tts_model,
                            current_custom_voice=speaker.get('custom_voice'),
                            key=f"new_custom_voice_{i}",
                            help_text=f"上传 WAV 格式的自定义参考音频（{tts_provider} 支持）"
                        )
                    
                    backstory = st.text_area("背景故事:", key=f"new_backstory_{i}", value=speaker.get('backstory', ''))
                    personality = st.text_area("性格特点:", key=f"new_personality_{i}", value=speaker.get('personality', ''))
                    
                    # 更新说话人数据
                    speaker_data = {
                        'name': speaker_name,
                        'voice_id': voice_id,
                        'backstory': backstory,
                        'personality': personality
                    }
                    
                    # 如果有自定义 voice，添加到数据中
                    if custom_voice_data:
                        speaker_data['custom_voice'] = custom_voice_data
                        speaker_data['custom_voice_filename'] = custom_voice_filename
                    elif 'custom_voice' in speaker and speaker.get('custom_voice'):
                        # 保留现有的自定义 voice
                        speaker_data['custom_voice'] = speaker.get('custom_voice')
                        speaker_data['custom_voice_filename'] = speaker.get('custom_voice_filename')
                    
                    st.session_state.new_speakers[i] = speaker_data
                
                with col2:
                    if len(st.session_state.new_speakers) > 1:
                        if st.button("🗑️", key=f"new_remove_speaker_{i}"):
                            st.session_state.new_speakers.pop(i)
                            st.rerun()
                
                st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ 添加说话人", key="new_add_speaker") and len(st.session_state.new_speakers) < 4:
                    st.session_state.new_speakers.append({'name': '', 'voice_id': '', 'backstory': '', 'personality': '', 'custom_voice': None})
                    st.rerun()
            
            st.markdown("---")
            
            # 操作按钮
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 创建配置", type="primary", key="create_speaker_profile"):
                    if not profile_name:
                        st.error("配置名称不能为空")
                    elif profile_name in profile_names:
                        st.error(f"配置 '{profile_name}' 已存在")
                    else:
                        # 创建配置数据
                        profile_data = {
                            "tts_provider": tts_provider,
                            "tts_model": tts_model,
                            "speakers": st.session_state.new_speakers
                        }
                        
                        # 验证配置
                        validation_errors = profile_manager.validate_speaker_profile(profile_data)
                        if validation_errors:
                            st.error("❌ 验证错误:")
                            for error in validation_errors:
                                st.error(f"• {error}")
                        else:
                            # 创建配置
                            if profile_manager.create_speaker_profile(profile_name, profile_data):
                                st.success(f"✅ 配置 '{profile_name}' 创建成功！")
                                st.session_state.show_new_speaker_form = False
                                if 'new_speakers' in st.session_state:
                                    del st.session_state.new_speakers
                                st.rerun()
                            else:
                                st.error("❌ 创建配置失败")
            
            with col2:
                if st.button("❌ 取消", key="cancel_new_speaker"):
                    st.session_state.show_new_speaker_form = False
                    if 'new_speakers' in st.session_state:
                        del st.session_state.new_speakers
                    st.rerun()
            
            st.markdown("---")
        
        # 编辑配置表单
        if st.session_state.get("edit_speaker_profile"):
            edit_profile_name = st.session_state.edit_speaker_profile
            edit_profile_data = profile_manager.get_speaker_profile(edit_profile_name)
            
            if edit_profile_data:
                st.subheader(f"✏️ 编辑说话人配置: {edit_profile_name}")
                
                col1, col2 = st.columns(2)
                with col1:
                    current_tts_provider = edit_profile_data.get('tts_provider', 'elevenlabs')
                    tts_provider = ProviderChecker.render_tts_provider_selector(
                        "TTS提供商:",
                        current_provider=current_tts_provider,
                        key="edit_speaker_tts_provider",
                        help_text="选择文本转语音提供商"
                    )
                with col2:
                    # 获取所选提供商的默认模型
                    defaults = ProviderChecker.get_default_models(tts_provider)
                    default_model = defaults.get("tts", "eleven_flash_v2_5")
                    
                    current_tts_model = edit_profile_data.get('tts_model', default_model)
                    tts_model = st.text_input(
                        "TTS模型:", 
                        value=current_tts_model,
                        key="edit_speaker_tts_model"
                    )
                
                st.markdown("### 说话人")
                
                # 初始化编辑说话人
                if 'edit_speakers' not in st.session_state:
                    st.session_state.edit_speakers = edit_profile_data.get('speakers', [])
                
                for i, speaker in enumerate(st.session_state.edit_speakers):
                    st.markdown(f"**说话人 {i+1}:**")
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        speaker_name = st.text_input(
                            "姓名:", 
                            key=f"edit_speaker_name_{i}", 
                            value=speaker.get('name', '')
                        )
                        
                        # 带有提供商特定声音的声音选择器
                        voice_id = VoiceProvider.render_voice_selector(
                            provider=tts_provider,
                            model=tts_model,
                            current_voice_id=speaker.get('voice_id', ''),
                            key=f"edit_voice_id_{i}",
                            help_text=f"从{tts_provider}选择声音"
                        )
                        
                        # 如果可用，显示声音预览
                        if voice_id and tts_provider == "elevenlabs":
                            with st.expander("🎵 声音预览"):
                                VoiceProvider.render_voice_preview(tts_provider, voice_id)
                        
                        # 只有当 voice 为 "custom" 时才显示上传组件
                        custom_voice_data = None
                        custom_voice_filename = None
                        if voice_id == "custom":
                            # 检查是否支持自定义 voice，如果支持则显示上传组件
                            custom_voice_data, custom_voice_filename = VoiceProvider.render_custom_voice_upload(
                                provider=tts_provider,
                                model=tts_model,
                                current_custom_voice=speaker.get('custom_voice'),
                                key=f"edit_custom_voice_{i}",
                                help_text=f"上传 WAV 格式的自定义参考音频（{tts_provider} 支持）"
                            )
                        
                        backstory = st.text_area(
                            "背景故事:", 
                            key=f"edit_backstory_{i}", 
                            value=speaker.get('backstory', '')
                        )
                        personality = st.text_area(
                            "性格特点:", 
                            key=f"edit_personality_{i}", 
                            value=speaker.get('personality', '')
                        )
                        
                        # 更新说话人数据
                        speaker_data = {
                            'name': speaker_name,
                            'voice_id': voice_id,
                            'backstory': backstory,
                            'personality': personality
                        }
                        
                        # 如果有自定义 voice，添加到数据中
                        if custom_voice_data:
                            speaker_data['custom_voice'] = custom_voice_data
                            speaker_data['custom_voice_filename'] = custom_voice_filename
                        elif 'custom_voice' in speaker and speaker.get('custom_voice'):
                            # 保留现有的自定义 voice
                            speaker_data['custom_voice'] = speaker.get('custom_voice')
                            speaker_data['custom_voice_filename'] = speaker.get('custom_voice_filename')
                        
                        st.session_state.edit_speakers[i] = speaker_data
                    
                    with col2:
                        if len(st.session_state.edit_speakers) > 1:
                            if st.button("🗑️", key=f"edit_remove_speaker_{i}"):
                                st.session_state.edit_speakers.pop(i)
                                st.rerun()
                    
                    st.markdown("---")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("➕ 添加说话人", key="edit_add_speaker") and len(st.session_state.edit_speakers) < 4:
                        st.session_state.edit_speakers.append({'name': '', 'voice_id': '', 'backstory': '', 'personality': '', 'custom_voice': None})
                        st.rerun()
                
                st.markdown("---")
                
                # 操作按钮
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 保存更改", type="primary", key="save_speaker_changes"):
                        # 更新配置数据
                        updated_profile_data = {
                            "tts_provider": tts_provider,
                            "tts_model": tts_model,
                            "speakers": st.session_state.edit_speakers
                        }
                        
                        # 验证配置
                        validation_errors = profile_manager.validate_speaker_profile(updated_profile_data)
                        if validation_errors:
                            st.error("❌ 验证错误:")
                            for error in validation_errors:
                                st.error(f"• {error}")
                        else:
                            # 更新配置
                            if profile_manager.update_speaker_profile(edit_profile_name, updated_profile_data):
                                st.success(f"✅ 配置 '{edit_profile_name}' 更新成功！")
                                st.session_state.edit_speaker_profile = None
                                if 'edit_speakers' in st.session_state:
                                    del st.session_state.edit_speakers
                                st.rerun()
                            else:
                                st.error("❌ 更新配置失败")
                
                with col2:
                    if st.button("❌ 取消编辑", key="cancel_edit_speaker"):
                        st.session_state.edit_speaker_profile = None
                        if 'edit_speakers' in st.session_state:
                            del st.session_state.edit_speakers
                        st.rerun()
                
                st.markdown("---")
            else:
                st.error(f"未找到说话人配置 '{edit_profile_name}'")
                st.session_state.edit_speaker_profile = None
                st.rerun()
        
        # 显示现有配置
        st.subheader("现有说话人配置")
        
        if profile_names:
            for profile_name in profile_names:
                profile_data = profiles["profiles"][profile_name]
                
                with st.expander(f"🎙️ {profile_name}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**TTS提供商:** {profile_data.get('tts_provider', '无')}")
                        st.markdown(f"**TTS模型:** {profile_data.get('tts_model', '无')}")
                        st.markdown(f"**说话人数量:** {len(profile_data.get('speakers', []))}")
                        
                        # 显示说话人
                        speakers = profile_data.get('speakers', [])
                        if speakers:
                            st.markdown("**说话人:**")
                            for i, speaker in enumerate(speakers):
                                voice_info = speaker.get('voice_id', '无声音ID')
                                if speaker.get('custom_voice'):
                                    voice_info += " 🎤 (自定义声音)"
                                st.markdown(f"• **{speaker.get('name', '未命名')}** - {voice_info}")
                    
                    with col2:
                        st.markdown("**操作:**")
                        
                        # 编辑按钮
                        if st.button("✏️ 编辑", key=f"edit_{profile_name}"):
                            st.session_state.edit_speaker_profile = profile_name
                            st.rerun()
                        
                        # 克隆按钮
                        if st.button("📋 克隆", key=f"clone_{profile_name}"):
                            new_name = f"{profile_name}_copy"
                            if profile_manager.clone_speaker_profile(profile_name, new_name):
                                st.success(f"✅ 配置已克隆为 '{new_name}'")
                                st.rerun()
                            else:
                                st.error("❌ 克隆配置失败")
                        
                        # 导出按钮
                        export_data = profile_manager.export_speaker_profiles([profile_name])
                        st.download_button(
                            label="💾 导出",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"{profile_name}_speaker_config.json",
                            mime="application/json",
                            key=f"export_{profile_name}"
                        )
                        
                        # 删除按钮
                        if st.button("🗑️ 删除", key=f"delete_{profile_name}"):
                            if profile_manager.delete_speaker_profile(profile_name):
                                st.success(f"✅ 配置 '{profile_name}' 已删除")
                                st.rerun()
                            else:
                                st.error("❌ 删除配置失败")
        else:
            st.info("未找到说话人配置。创建您的第一个配置以开始使用！")
    
    except Exception as e:
        st.error(f"加载说话人配置时出错: {str(e)}")
        st.markdown("请检查您的配置文件并重试。")

def show_episode_profiles_page():
    """显示剧集配置管理页面。"""
    st.subheader("📺 剧集配置")
    st.markdown("管理您的剧集设置")
    
    # 定义可用的提供商
    all_providers = ["openai", "anthropic", "google", "groq", "ollama", "openrouter", "azure", "mistral", "deepseek", "xai", "tencent", "qwen", "kokoro", "erine"]
    
    # 初始化配置管理器
    profile_manager = ProfileManager(working_dir=WORKING_DIR)
    
    # 加载配置
    try:
        profiles = profile_manager.load_episode_profiles()
        profile_names = list(profiles.get("profiles", {}).keys())
        speaker_profile_names = profile_manager.get_speaker_profile_names()
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("➕ 新建配置", use_container_width=True):
                st.session_state.show_new_episode_form = True
                st.rerun()
        
        # with col2:
        #     if st.button("📁 导入", use_container_width=True):
        #         st.session_state.show_import_episode_form = True
        #         st.rerun()
        #     pass_context
        
        # with col3:
        #     if st.button("💾 导出全部", use_container_width=True):
        #         export_data = profile_manager.export_episode_profiles()
        #         st.download_button(
        #             label="下载 episodes_config.json",
        #             data=json.dumps(export_data, indent=2),
        #             file_name="episodes_config.json",
        #             mime="application/json"
        #         )
        
        st.markdown("---")
        
        # 导入表单
        if st.session_state.get("show_import_episode_form", False):
            st.subheader("📁 导入剧集配置")
            
            uploaded_file = st.file_uploader(
                "选择要导入的JSON文件",
                type=['json'],
                key="episode_import_file"
            )
            
            if uploaded_file is not None:
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    imported_names = profile_manager.import_episode_profiles(file_content)
                    
                    if imported_names:
                        st.success(f"✅ 成功导入 {len(imported_names)} 个配置: {', '.join(imported_names)}")
                        st.session_state.show_import_episode_form = False
                        st.rerun()
                    else:
                        st.warning("⚠️ 未导入新配置。请检查配置是否已存在或文件格式是否正确。")
                except Exception as e:
                    st.error(f"❌ 导入配置时出错: {str(e)}")
            
            if st.button("❌ 取消导入"):
                st.session_state.show_import_episode_form = False
                st.rerun()
            
            st.markdown("---")
        
        # 新建配置表单
        if st.session_state.get("show_new_episode_form", False):
            st.subheader("➕ 创建新的剧集配置")
            
            profile_name = st.text_input("配置名称:", placeholder="例如: my_tech_talks", key="new_episode_name")
            
            if speaker_profile_names:
                speaker_config = st.selectbox("说话人配置:", speaker_profile_names, key="new_episode_speaker")
            else:
                st.error("⚠️ 未找到说话人配置。请先创建说话人配置。")
                speaker_config = None
            
            st.markdown("### AI模型配置")
            
            # 大纲模型配置
            st.markdown("**大纲生成:**")
            col1, col2 = st.columns(2)
            with col1:
                outline_provider = ProviderChecker.render_provider_selector(
                    "大纲提供商:",
                    all_providers,
                    current_provider="openai",
                    key="new_episode_outline_provider",
                    help_text="选择用于生成播客大纲的AI提供商"
                )
            with col2:
                # 获取所选提供商的默认模型
                defaults = ProviderChecker.get_default_models(outline_provider)
                default_outline_model = defaults.get("outline", "gpt-4o")
                
                outline_model = st.text_input(
                    "大纲模型:",
                    value=default_outline_model,
                    placeholder=default_outline_model,
                    key="new_episode_outline_model"
                )
            
            # 脚本模型配置
            st.markdown("**脚本生成:**")
            col1, col2 = st.columns(2)
            with col1:
                transcript_provider = ProviderChecker.render_provider_selector(
                    "脚本提供商:",
                    all_providers,
                    current_provider="openai",
                    key="new_episode_transcript_provider",
                    help_text="选择用于生成播客脚本的AI提供商"
                )
            with col2:
                # 获取所选提供商的默认模型
                defaults = ProviderChecker.get_default_models(transcript_provider)
                default_transcript_model = defaults.get("transcript", "gpt-4o")
                
                transcript_model = st.text_input(
                    "脚本模型:",
                    value=default_transcript_model,
                    placeholder=default_transcript_model,
                    key="new_episode_transcript_model"
                )
            
            num_segments = st.slider("分段数量:", 1, 10, 4, key="new_episode_segments")
            default_briefing = st.text_area(
                "默认简介:", 
                value="创建一个关于该主题的有趣讨论",
                height=100,
                key="new_episode_briefing"
            )
            
            st.markdown("---")
            
            # 操作按钮
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 创建配置", type="primary", key="create_episode_profile"):
                    if not profile_name:
                        st.error("配置名称不能为空")
                    elif profile_name in profile_names:
                        st.error(f"配置 '{profile_name}' 已存在")
                    elif not speaker_config:
                        st.error("必须选择说话人配置")
                    else:
                        # 创建配置数据
                        profile_data = {
                            "speaker_config": speaker_config,
                            "outline_model": outline_model,
                            "outline_provider": outline_provider,
                            "transcript_model": transcript_model,
                            "transcript_provider": transcript_provider,
                            "num_segments": num_segments,
                            "default_briefing": default_briefing
                        }
                        
                        # 验证配置
                        validation_errors = profile_manager.validate_episode_profile(profile_data)
                        if validation_errors:
                            st.error("❌ 验证错误:")
                            for error in validation_errors:
                                st.error(f"• {error}")
                        else:
                            # 创建配置
                            if profile_manager.create_episode_profile(profile_name, profile_data):
                                st.success(f"✅ 配置 '{profile_name}' 创建成功！")
                                st.session_state.show_new_episode_form = False
                                st.rerun()
                            else:
                                st.error("❌ 创建配置失败")
            
            with col2:
                if st.button("❌ 取消", key="cancel_new_episode"):
                    st.session_state.show_new_episode_form = False
                    st.rerun()
            
            st.markdown("---")
        
        # 编辑配置表单
        if st.session_state.get("edit_episode_profile"):
            edit_profile_name = st.session_state.edit_episode_profile
            edit_profile_data = profile_manager.get_episode_profile(edit_profile_name)
            
            if edit_profile_data:
                st.subheader(f"✏️ 编辑剧集配置: {edit_profile_name}")
                
                # 配置名称（允许重命名）
                new_profile_name = st.text_input(
                    "配置名称:", 
                    value=edit_profile_name,
                    key="edit_episode_profile_name"
                )
                
                if speaker_profile_names:
                    current_speaker_index = 0
                    if edit_profile_data['speaker_config'] in speaker_profile_names:
                        current_speaker_index = speaker_profile_names.index(edit_profile_data['speaker_config'])
                    
                    speaker_config = st.selectbox(
                        "说话人配置:", 
                        speaker_profile_names, 
                        index=current_speaker_index,
                        key="edit_episode_speaker"
                    )
                else:
                    st.error("⚠️ 未找到说话人配置。")
                    speaker_config = edit_profile_data.get('speaker_config', '')
                
                st.markdown("### AI模型配置")
                
                # 大纲模型配置
                st.markdown("**大纲生成:**")
                col1, col2 = st.columns(2)
                with col1:
                    current_outline_provider = edit_profile_data.get('outline_provider', 'openai')
                    outline_provider = ProviderChecker.render_provider_selector(
                        "大纲提供商:",
                        all_providers,
                        current_provider=current_outline_provider,
                        key="edit_episode_outline_provider",
                        help_text="选择用于生成播客大纲的AI提供商"
                    )
                with col2:
                    # 获取所选提供商的默认模型
                    defaults = ProviderChecker.get_default_models(outline_provider)
                    default_model = defaults.get("outline", "gpt-4o")
                    
                    current_outline_model = edit_profile_data.get('outline_model', default_model)
                    outline_model = st.text_input(
                        "大纲模型:", 
                        value=current_outline_model,
                        placeholder=default_model,
                        key="edit_episode_outline_model"
                    )
                
                # 脚本模型配置
                st.markdown("**脚本生成:**")
                col1, col2 = st.columns(2)
                with col1:
                    current_transcript_provider = edit_profile_data.get('transcript_provider', 'openai')
                    transcript_provider = ProviderChecker.render_provider_selector(
                        "脚本提供商:",
                        all_providers,
                        current_provider=current_transcript_provider,
                        key="edit_episode_transcript_provider",
                        help_text="选择用于生成播客脚本的AI提供商"
                    )
                with col2:
                    # 获取所选提供商的默认模型
                    defaults = ProviderChecker.get_default_models(transcript_provider)
                    default_model = defaults.get("transcript", "gpt-4o")
                    
                    current_transcript_model = edit_profile_data.get('transcript_model', default_model)
                    transcript_model = st.text_input(
                        "脚本模型:", 
                        value=current_transcript_model,
                        placeholder=default_model,
                        key="edit_episode_transcript_model"
                    )
                
                num_segments = st.slider(
                    "分段数量:", 
                    1, 10, 
                    value=edit_profile_data.get('num_segments', 4),
                    key="edit_episode_segments"
                )
                
                language = st.selectbox(
                    "语言选择:",
                    options=["中文", "英文"],
                    index=0 if edit_profile_data.get('language', '中文') == '中文' else 1,
                    key="edit_episode_language"
                )
                
                # Dialect selection (only shown when language is Chinese)
                # Get supported dialects from TTS provider capability
                dialect = None
                dialect_options_display = []
                dialect_map = {}
                
                if language == "中文":
                    # Get speaker config to determine TTS provider
                    speaker_config_name = edit_profile_data.get('speaker_config')
                    if speaker_config_name:
                        speaker_profile_data = profile_manager.get_speaker_profile(speaker_config_name)
                        if speaker_profile_data:
                            tts_provider = speaker_profile_data.get('tts_provider')
                            tts_model = speaker_profile_data.get('tts_model')
                            
                            if tts_provider:
                                # Get TTS capability
                                capability = VoiceProvider.get_tts_capability(tts_provider, tts_model)
                                if capability and capability.supported_dialects:
                                    supported_dialects = capability.supported_dialects
                                    
                                    # Map dialect codes to display names
                                    dialect_display_map = {
                                        "mandarin": "普通话",
                                        "cantonese": "粤语",
                                        "sichuanese": "四川话",
                                        "henanese": "河南话",
                                        "shanghainese": "上海话"
                                    }
                                    
                                    # Build dialect options from supported dialects
                                    for dialect_code in supported_dialects:
                                        display_name = dialect_display_map.get(dialect_code, dialect_code)
                                        dialect_options_display.append(display_name)
                                        dialect_map[display_name] = dialect_code
                                    
                                    # If no dialects supported, default to mandarin
                                    if not dialect_options_display:
                                        dialect_options_display = ["普通话"]
                                        dialect_map["普通话"] = "mandarin"
                                else:
                                    # Fallback: default dialects if capability not available
                                    dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                                    dialect_map = {
                                        "普通话": "mandarin",
                                        "粤语": "cantonese",
                                        "四川话": "sichuanese",
                                        "河南话": "henanese"
                                    }
                            else:
                                # Fallback if no TTS provider
                                dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                                dialect_map = {
                                    "普通话": "mandarin",
                                    "粤语": "cantonese",
                                    "四川话": "sichuanese",
                                    "河南话": "henanese"
                                }
                        else:
                            # Fallback if speaker profile not found
                            dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                            dialect_map = {
                                "普通话": "mandarin",
                                "粤语": "cantonese",
                                "四川话": "sichuanese",
                                "河南话": "henanese"
                            }
                    else:
                        # Fallback if no speaker config
                        dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                        dialect_map = {
                            "普通话": "mandarin",
                            "粤语": "cantonese",
                            "四川话": "sichuanese",
                            "河南话": "henanese"
                        }
                    
                    if dialect_options_display:
                        current_dialect = edit_profile_data.get('dialect', 'mandarin')
                        # Reverse lookup to find display name
                        current_dialect_display = "普通话"
                        for display, value in dialect_map.items():
                            if value == current_dialect:
                                current_dialect_display = display
                                break
                        
                        selected_dialect = st.selectbox(
                            "方言选择:",
                            options=dialect_options_display,
                            index=dialect_options_display.index(current_dialect_display) if current_dialect_display in dialect_options_display else 0,
                            key="edit_episode_dialect"
                        )
                        dialect = dialect_map.get(selected_dialect, "mandarin")
                
                default_briefing = st.text_area(
                    "默认简介:", 
                    value=edit_profile_data.get('default_briefing', ''),
                    height=100,
                    key="edit_episode_briefing"
                )
                
                st.markdown("---")
                
                # 操作按钮
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 保存更改", type="primary", key="save_episode_changes"):
                        if not new_profile_name.strip():
                            st.error("配置名称不能为空")
                        elif new_profile_name != edit_profile_name and new_profile_name in profile_names:
                            st.error(f"配置名称 '{new_profile_name}' 已存在")
                        else:
                            # 更新配置数据
                            updated_profile_data = {
                                "speaker_config": speaker_config,
                                "outline_model": outline_model,
                                "outline_provider": outline_provider,
                                "transcript_model": transcript_model,
                                "transcript_provider": transcript_provider,
                                "num_segments": num_segments,
                                "language": language,
                                "dialect": dialect if language == "中文" else None,
                                "default_briefing": default_briefing            
                            }
                            
                            # 验证配置
                            validation_errors = profile_manager.validate_episode_profile(updated_profile_data)
                            if validation_errors:
                                st.error("❌ 验证错误:")
                                for error in validation_errors:
                                    st.error(f"• {error}")
                            else:
                                # 处理重命名
                                if new_profile_name != edit_profile_name:
                                    # 创建新配置
                                    if profile_manager.create_episode_profile(new_profile_name, updated_profile_data):
                                        # 删除旧配置
                                        if profile_manager.delete_episode_profile(edit_profile_name):
                                            st.success(f"✅ 配置已从 '{edit_profile_name}' 重命名为 '{new_profile_name}' 并更新成功！")
                                        else:
                                            st.warning(f"✅ 新配置 '{new_profile_name}' 已创建，但删除旧配置 '{edit_profile_name}' 失败")
                                    else:
                                        st.error("❌ 创建重命名配置失败")
                                else:
                                    # 更新现有配置
                                    if profile_manager.update_episode_profile(edit_profile_name, updated_profile_data):
                                        st.success(f"✅ 配置 '{edit_profile_name}' 更新成功！")
                                    else:
                                        st.error("❌ 更新配置失败")
                                
                                st.session_state.edit_episode_profile = None
                                st.rerun()
                
                with col2:
                    if st.button("❌ 取消编辑", key="cancel_edit_episode"):
                        st.session_state.edit_episode_profile = None
                        st.rerun()
                
                st.markdown("---")
            else:
                st.error(f"未找到剧集配置 '{edit_profile_name}'")
                st.session_state.edit_episode_profile = None
                st.rerun()
        
        # 显示现有配置
        st.subheader("现有剧集配置")
        
        if profile_names:
            # 以网格形式显示
            cols = st.columns(3)
            
            for i, profile_name in enumerate(profile_names):
                profile_data = profiles["profiles"][profile_name]
                
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### 📺 {profile_name}")
                        st.markdown(f"**说话人:** {profile_data.get('speaker_config', '无')}")
                        st.markdown(f"**分段数量:** {profile_data.get('num_segments', '无')}")
                        st.markdown(f"**语言:** {profile_data.get('language', '中文')}")
                        
                        outline_provider = profile_data.get('outline_provider', 'openai')
                        outline_model = profile_data.get('outline_model', '无')
                        st.markdown(f"**大纲:** {outline_provider}/{outline_model}")
                        
                        transcript_provider = profile_data.get('transcript_provider', 'openai')
                        transcript_model = profile_data.get('transcript_model', '无')
                        st.markdown(f"**脚本:** {transcript_provider}/{transcript_model}")
                        
                        # 操作按钮
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("✏️ 编辑", key=f"edit_ep_{profile_name}", use_container_width=True):
                                st.session_state.edit_episode_profile = profile_name
                                st.rerun()
                        
                        with col2:
                            if st.button("📋 克隆", key=f"clone_ep_{profile_name}", use_container_width=True):
                                new_name = f"{profile_name}_copy"
                                if profile_manager.clone_episode_profile(profile_name, new_name):
                                    st.success(f"✅ 已克隆为 '{new_name}'")
                                    st.rerun()
                                else:
                                    st.error("❌ 克隆失败")
                        
                        # 导出按钮
                        export_data = profile_manager.export_episode_profiles([profile_name])
                        st.download_button(
                            label="💾 导出",
                            data=json.dumps(export_data, indent=2),
                            file_name=f"{profile_name}_episode_config.json",
                            mime="application/json",
                            key=f"export_ep_{profile_name}",
                            use_container_width=True
                        )
                        
                        # 删除按钮
                        if st.button("🗑️ 删除", key=f"delete_ep_{profile_name}", use_container_width=True):
                            if profile_manager.delete_episode_profile(profile_name):
                                st.success(f"✅ 已删除 '{profile_name}'")
                                st.rerun()
                            else:
                                st.error("❌ 删除失败")
                        
                        # 在展开器中显示更多详情
                        with st.expander("📋 详情"):
                            st.markdown(f"**大纲提供商:** {profile_data.get('outline_provider', 'openai')}")
                            st.markdown(f"**大纲模型:** {profile_data.get('outline_model', '无')}")
                            st.markdown(f"**脚本提供商:** {profile_data.get('transcript_provider', 'openai')}")
                            st.markdown(f"**脚本模型:** {profile_data.get('transcript_model', '无')}")
                            st.markdown("**默认简介:**")
                            st.text(profile_data.get('default_briefing', '未设置简介'))
        else:
            st.info("未找到剧集配置。创建您的第一个配置以开始使用！")
    
    except Exception as e:
        st.error(f"加载剧集配置时出错: {str(e)}")
        st.markdown("请检查您的配置文件并重试。")

def show_generate_podcast_page():
    """显示播客生成页面。"""
    st.subheader("🎬 生成播客")
    st.markdown("创建新的播客剧集")
    # 初始化管理器
    profile_manager = ProfileManager(working_dir=WORKING_DIR)
    episode_manager = EpisodeManager(base_output_dir= os.path.join(WORKING_DIR, "output"))
    
    try:
        # 加载可用的配置文件
        episode_profiles = profile_manager.get_episode_profile_names()
        speaker_profiles = profile_manager.get_speaker_profile_names()
        
        if not episode_profiles:
            st.error("⚠️ 未找到剧集配置文件。请先创建一个剧集配置文件。")
            if st.button("📺 前往剧集配置"):
                st.session_state.current_page = "📺 Episode Profiles"
                st.rerun()
            return
        
        # 内容输入部分
        st.markdown("### 步骤 1: 内容收集")
        
        # 初始化内容片段的会话状态
        if 'content_pieces' not in st.session_state:
            st.session_state.content_pieces = []
        
        # 添加新内容部分
        with st.expander("➕ 添加内容", expanded=len(st.session_state.content_pieces) == 0):
            content_source = st.radio(
                "内容来源:",
                ["文本输入", "文件上传", "网址"],
                horizontal=True,
                key="new_content_source"
            )
            
            if content_source == "文本输入":
                text_content = st.text_area("输入您的内容:", height=150, placeholder="在此粘贴您的内容...", key="new_text_input")
                
                if st.button("📝 添加文本内容", disabled=not text_content.strip()):
                    if text_content.strip():
                        content_piece = {
                            'type': 'text',
                            'title': f"文本内容 {len(st.session_state.content_pieces) + 1}",
                            'content': text_content.strip(),
                            'source': '直接输入'
                        }
                        st.session_state.content_pieces.append(content_piece)
                        st.rerun()
            
            elif content_source == "文件上传":
                uploaded_file = st.file_uploader(
                    "上传文件:", 
                    type=['txt', 'pdf', 'docx', 'md', 'json'],
                    help="支持的格式: TXT, PDF, DOCX, MD, JSON",
                    key="new_file_uploader"
                )
                
                if uploaded_file is not None and st.button("📄 添加文件内容"):
                    try:
                        if ContentExtractor.is_content_core_available():
                            with st.spinner("正在从文件中提取内容..."):
                                extracted_content = ContentExtractor.extract_from_uploaded_file(uploaded_file)
                                content_piece = {
                                    'type': 'file',
                                    'title': uploaded_file.name,
                                    'content': extracted_content,
                                    'source': f"文件: {uploaded_file.name}"
                                }
                                st.session_state.content_pieces.append(content_piece)
                                st.success(f"✅ 已添加来自 {uploaded_file.name} 的内容")
                                st.rerun()
                        else:
                            st.error("⚠️ content-core 库不可用。请使用以下命令安装: `pip install content-core`")
                    except Exception as e:
                        st.error(f"❌ 提取内容时出错: {str(e)}")
            
            else:  # URL
                url = st.text_input("输入网址:", placeholder="https://example.com/article", key="new_url_input")
                
                if url and st.button("🔗 添加网址内容"):
                    if ContentExtractor.validate_url(url):
                        try:
                            if ContentExtractor.is_content_core_available():
                                with st.spinner("正在从网址提取内容..."):
                                    extracted_content = run_async_in_streamlit(ContentExtractor.extract_from_url, url)
                                    content_piece = {
                                        'type': 'url',
                                        'title': url,
                                        'content': extracted_content,
                                        'source': f"网址: {url}"
                                    }
                                    st.session_state.content_pieces.append(content_piece)
                                    st.success("✅ 已添加来自网址的内容")
                                    st.rerun()
                            else:
                                st.error("⚠️ content-core 库不可用。请使用以下命令安装: `pip install content-core`")
                        except Exception as e:
                            ErrorHandler.handle_streamlit_error(e, {"url": url})
                    else:
                        st.error("❌ 无效或无法访问的网址")
        
        # 显示内容片段
        if st.session_state.content_pieces:
            st.markdown("### 内容片段")
            
            total_content = ""
            total_chars = 0
            total_words = 0
            
            for i, piece in enumerate(st.session_state.content_pieces):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # 显示内容片段信息
                        type_icon = {"text": "📝", "file": "📄", "url": "🔗"}.get(piece['type'], "📄")
                        st.markdown(f"**{type_icon} {piece['title']}**")
                        st.markdown(f"*来源: {piece['source']}*")
                        
                        # 内容统计
                        piece_stats = ContentExtractor.get_content_stats(piece['content'])
                        st.markdown(f"📊 {piece_stats['character_count']} 字符, {piece_stats['word_count']} 词")
                        
                        # 预览
                        with st.expander("👀 预览"):
                            preview = ContentExtractor.truncate_content(piece['content'], 300)
                            st.text(preview)
                    
                    with col2:
                        # 上移/下移按钮
                        if i > 0:
                            if st.button("⬆️", key=f"move_up_{i}", help="上移"):
                                st.session_state.content_pieces[i], st.session_state.content_pieces[i-1] = st.session_state.content_pieces[i-1], st.session_state.content_pieces[i]
                                st.rerun()
                        
                        if i < len(st.session_state.content_pieces) - 1:
                            if st.button("⬇️", key=f"move_down_{i}", help="下移"):
                                st.session_state.content_pieces[i], st.session_state.content_pieces[i+1] = st.session_state.content_pieces[i+1], st.session_state.content_pieces[i]
                                st.rerun()
                    
                    with col3:
                        # 删除按钮
                        if st.button("🗑️", key=f"delete_content_{i}", help="删除"):
                            st.session_state.content_pieces.pop(i)
                            st.rerun()
                
                # 添加到统计
                total_chars += piece_stats['character_count']
                total_words += piece_stats['word_count']
            
            # 操作
            if st.button("🔄 清除所有内容", type="secondary"):
                st.session_state.content_pieces = []
                st.rerun()
            
            # 设置生成内容（传递数组而不是连接的字符串）
            content_pieces = st.session_state.content_pieces
            content_stats = {
                'character_count': total_chars,
                'word_count': total_words,
                'paragraph_count': len(st.session_state.content_pieces),  # 片段数量而不是段落
                'estimated_reading_time': max(1, total_words // 200)
            }
        else:
            st.info("📝 尚未添加内容。使用上方的\"添加内容\"部分添加文本、文件或网址。")
            content_pieces = []
            content_stats = None
        
        st.markdown("---")
        
        # 配置部分
        st.markdown("### 步骤 2: 配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            episode_profile = st.selectbox(
                "剧集配置:",
                episode_profiles,
                help="选择预配置的剧集配置文件",
                key="episode_profile_select"
            )
        
        with col2:
            use_defaults = st.checkbox("使用配置文件默认值", value=True, key="use_profile_defaults")
        
        # 加载选定的配置文件数据
        profile_data = profile_manager.get_episode_profile(episode_profile)
        
        if profile_data:
            st.markdown(f"**配置信息:** {profile_data.get('default_briefing', '无描述')}")
            
            # 覆盖选项
            if not use_defaults:
                with st.expander("🔧 覆盖设置", expanded=True):
                    outline_provider = profile_data.get('outline_provider', 'openai')
                    speaker_config = st.selectbox(
                        "说话人配置:",
                        speaker_profiles,
                        index=speaker_profiles.index(profile_data['speaker_config']) if profile_data['speaker_config'] in speaker_profiles else 0
                    )
                    
                    outline_model = st.text_input(
                        "大纲模型:",
                        value=profile_data.get('outline_model', 'gpt-4o')
                    )

                    transcript_provider = profile_data.get('transcript_provider', 'openai')
                    
                    transcript_model = st.text_input(
                        "文稿模型:",
                        value=profile_data.get('transcript_model', 'gpt-4o')
                    )
                    
                    num_segments = st.slider(
                        "段落数量:",
                        1, 10,
                        value=profile_data.get('num_segments', 4)
                    )

                    # language
                    language = st.selectbox(
                        "语言:",
                        ["中文", "英文"],
                        index=0 if profile_data['language'] == "中文" else 1
                    )
                    
                    # Dialect selection (only shown when language is Chinese)
                    # Get supported dialects from TTS provider capability
                    dialect = None
                    dialect_options_display = []
                    dialect_map = {}
                    
                    if language == "中文":
                        # Get speaker config to determine TTS provider
                        speaker_config_name = speaker_config
                        if speaker_config_name:
                            speaker_profile_data = profile_manager.get_speaker_profile(speaker_config_name)
                            if speaker_profile_data:
                                tts_provider = speaker_profile_data.get('tts_provider')
                                tts_model = speaker_profile_data.get('tts_model')
                                
                                if tts_provider:
                                    # Get TTS capability
                                    capability = VoiceProvider.get_tts_capability(tts_provider, tts_model)
                                    if capability and capability.supported_dialects:
                                        supported_dialects = capability.supported_dialects
                                        
                                        # Map dialect codes to display names
                                        dialect_display_map = {
                                            "mandarin": "普通话",
                                            "cantonese": "粤语",
                                            "sichuanese": "四川话",
                                            "henanese": "河南话",
                                            "shanghainese": "上海话"
                                        }
                                        
                                        # Build dialect options from supported dialects
                                        for dialect_code in supported_dialects:
                                            display_name = dialect_display_map.get(dialect_code, dialect_code)
                                            dialect_options_display.append(display_name)
                                            dialect_map[display_name] = dialect_code
                                        
                                        # If no dialects supported, default to mandarin
                                        if not dialect_options_display:
                                            dialect_options_display = ["普通话"]
                                            dialect_map["普通话"] = "mandarin"
                                    else:
                                        # Fallback: default dialects if capability not available
                                        dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                                        dialect_map = {
                                            "普通话": "mandarin",
                                            "粤语": "cantonese",
                                            "四川话": "sichuanese",
                                            "河南话": "henanese"
                                        }
                                else:
                                    # Fallback if no TTS provider
                                    dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                                    dialect_map = {
                                        "普通话": "mandarin",
                                        "粤语": "cantonese",
                                        "四川话": "sichuanese",
                                        "河南话": "henanese"
                                    }
                            else:
                                # Fallback if speaker profile not found
                                dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                                dialect_map = {
                                    "普通话": "mandarin",
                                    "粤语": "cantonese",
                                    "四川话": "sichuanese",
                                    "河南话": "henanese"
                                }
                        else:
                            # Fallback if no speaker config
                            dialect_options_display = ["普通话", "粤语", "四川话", "河南话"]
                            dialect_map = {
                                "普通话": "mandarin",
                                "粤语": "cantonese",
                                "四川话": "sichuanese",
                                "河南话": "henanese"
                            }
                        
                        if dialect_options_display:
                            current_dialect = profile_data.get('dialect', 'mandarin')
                            # Reverse lookup to find display name
                            current_dialect_display = "普通话"
                            for display, value in dialect_map.items():
                                if value == current_dialect:
                                    current_dialect_display = display
                                    break
                            
                            dialect = st.selectbox(
                                "方言:",
                                options=dialect_options_display,
                                index=dialect_options_display.index(current_dialect_display) if current_dialect_display in dialect_options_display else 0
                            )
                            dialect = dialect_map.get(dialect, "mandarin")
                    
                    briefing = st.text_area(
                        "指令:",
                        value=profile_data.get('default_briefing', ''),
                        height=100
                    )
                    
                    briefing_suffix = st.text_input(
                        "指令后缀:",
                        placeholder="额外的指示..."
                    )
            else:
                # 使用配置文件默认值
                speaker_config = profile_data.get('speaker_config')
                if not speaker_config:
                    st.error("⚠️ 配置文件缺少 'speaker_config' 字段")
                    return
                outline_model = profile_data.get('outline_model', 'gpt-4o')
                transcript_model = profile_data.get('transcript_model', 'gpt-4o')
                transcript_provider = profile_data.get('transcript_provider', 'openai')
                outline_provider = profile_data.get('outline_provider', 'openai')
                num_segments = profile_data.get('num_segments', 4)
                language = profile_data.get('language', '中文')
                dialect = profile_data.get('dialect') if language == "中文" else None
                briefing = profile_data.get('default_briefing', '')
                briefing_suffix = ""
        
        st.markdown("---")
        
        # # 指令编辑器部分
        # st.markdown("### 步骤 3: 指令编辑器")
        
        # # 如果不存在或配置文件已更改，则在会话状态中初始化指令
        # if 'custom_briefing' not in st.session_state or 'last_episode_profile' not in st.session_state:
        #     st.session_state.custom_briefing = briefing
        #     st.session_state.last_episode_profile = episode_profile
        # elif st.session_state.last_episode_profile != episode_profile:
        #     # 配置文件已更改，更新指令
        #     st.session_state.custom_briefing = briefing
        #     st.session_state.last_episode_profile = episode_profile
        
        # # 始终显示指令编辑器
        # col1, col2 = st.columns([3, 1])
        # with col1:
        #     custom_briefing = st.text_area(
        #         "编辑指令:",
        #         value=st.session_state.custom_briefing,
        #         height=120,
        #         help="编辑将发送给AI模型用于播客生成的指令",
        #         key="custom_briefing_editor"
        #     )
        # with col2:
        #     if st.button("🔄 重置为默认值", key="reset_briefing"):
        #         st.session_state.custom_briefing = briefing
        #         st.rerun()
        
        # # 更新会话状态
        # st.session_state.custom_briefing = custom_briefing
        
        # # 显示指令预览
        # if custom_briefing:
        #     with st.expander("📋 指令预览"):
        #         st.markdown("**将发送给AI的最终指令:**")
        #         final_briefing = custom_briefing
        #         if not use_defaults and briefing_suffix:
        #             final_briefing += f"\n\n{briefing_suffix}"
        #         st.text(final_briefing)
        
        # st.markdown("---")
        
        # 输出设置部分
        st.markdown("### 步骤 3: 输出设置")
        col1, col2 = st.columns(2)
        
        with col1:
            episode_name = st.text_input(
                "剧集名称:",
                placeholder="my_awesome_podcast",
                help="这将用作文件夹名称"
            )
        
        with col2:
            output_dir = "output"
            # output_dir = st.text_input(
            #     "输出目录:",
            #     value="output",
            #     help="播客输出的基本目录",
            # )
        
        # 检查剧集是否存在
        if episode_name:
            episode_exists = episode_manager.check_episode_exists(episode_name)
            if episode_exists:
                st.warning(f"⚠️ 剧集'{episode_name}'已存在。生成将覆盖现有文件。")
                overwrite_confirmed = st.checkbox("✅ 我理解并希望覆盖", key="overwrite_confirm")
            else:
                overwrite_confirmed = True
        else:
            overwrite_confirmed = True
        
        st.markdown("---")
        
        # 生成部分
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 验证内容片段而不是连接的内容
            has_valid_content = bool(content_pieces and any(
                piece.get('content', '').strip() and len(piece.get('content', '').strip()) >= 10 
                for piece in content_pieces
            ))
            
            can_generate = (
                has_valid_content and 
                episode_name and 
                overwrite_confirmed
            )
            
            if not content_pieces:
                st.info("📝 请添加内容片段以生成播客")
            elif not has_valid_content:
                st.error("❌ 内容片段太短或无效。请在至少一个片段中提供至少10个字符的有意义文本。")
            elif not episode_name:
                st.error("❌ 请提供剧集名称")
            elif not overwrite_confirmed:
                st.error("❌ 请确认覆盖以继续")
        
        with col2:
            if st.button(
                "🎬 生成播客", 
                type="primary", 
                disabled=not can_generate,
                use_container_width=True
            ):
                st.session_state.start_generation = True
                st.rerun()
        
        # 处理播客生成
        if st.session_state.get("start_generation", False):
            st.session_state.start_generation = False
            
            # 显示生成进度
            progress_container = st.container()
            status_container = st.container()
            
            progress_bar = progress_container.progress(0)
            status_text = status_container.empty()
            
            try:
                status_text.text("🚀 开始播客生成...")
                progress_bar.progress(10)
                
                # 导入播客创建器
                try:
                    from podcast_creator import create_podcast, configure
                    # 配置使用当前工作目录
                    configure("output_dir", str(WORKING_DIR))
                    configure("prompts_dir", PROMPTS_DIR)
                    configure("speakers_config", SPEAKERS_CONFIG_FILE)
                    configure("episode_config", EPISODE_CONFIG_FILE)
                    configure("emotions_config", EMOTIONS_CONFIG_FILE)
                    podcast_creator_available = True
                except ImportError:
                    podcast_creator_available = False
                    st.error("❌ podcast-creator 库不可用。请先安装它。")
                    return
                
                if podcast_creator_available:
                    status_text.text("📝 准备生成参数...")
                    progress_bar.progress(20)
                    
                    # 准备参数
                    generation_params = {
                        "content": [piece['content'] for piece in content_pieces],
                        "episode_name": episode_name,
                        "output_dir":  os.path.join(WORKING_DIR, output_dir, episode_name),
                    }
                    
                    # 如果不使用默认值，添加覆盖
                    if use_defaults:
                        generation_params.update({
                            "episode_profile": episode_profile
                        })
                    else: 
                        generation_params.update({
                            "speaker_config": speaker_config,
                            "outline_provider": outline_provider,
                            "transcript_provider": transcript_provider,
                            "outline_model": outline_model,
                            "transcript_model": transcript_model,
                            "num_segments": num_segments,
                            "language": language,
                            "dialect": dialect if language == "中文" else None,
                            "briefing": briefing
                        })
                        if briefing_suffix:
                            generation_params["briefing_suffix"] = briefing_suffix
                    # else:
                    #     # 即使使用默认值，如果修改了自定义指令，也使用它
                    #     if st.session_state.custom_briefing != briefing:
                    #         generation_params["briefing"] = st.session_state.custom_briefing
                    
                    print(f"Generation params: {generation_params}")
                    status_text.text("🎙️ 正在生成播客... 这可能需要几分钟...")
                    progress_bar.progress(30)
                    
                    # 生成播客
                    async def generate():
                        return await create_podcast(**generation_params)
                    
                    result = run_async_in_streamlit(generate)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ 播客生成完成！")
                    
                    # 成功生成后清除内容
                    st.session_state.generated_content = ""
                    st.session_state.content_stats = None
                    st.session_state.content_pieces = []
                    
                    # 显示成功消息
                    st.success(f"🎉 播客'{episode_name}'生成成功！")
                    
                    if 'final_output_file_path' in result:
                        st.markdown(f"**音频文件:** `{result['final_output_file_path']}`")
                    
                    # 快速操作
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📚 在库中查看", type="primary"):
                            st.session_state.current_page = "📚 Episode Library"
                            st.session_state.navigate_to_library = True
                            st.rerun()
                    
                    with col2:
                        if st.button("🎬 生成另一个"):
                            st.rerun()
                    
                    # 清理进度指示器
                    progress_bar.empty()
                    status_text.empty()
            
            except Exception as e:
                # 清理进度指示器
                progress_bar.empty()
                status_text.empty()
                
                # 处理错误
                total_content_length = sum(len(piece.get('content', '')) for piece in content_pieces) if content_pieces else 0
                ErrorHandler.handle_streamlit_error(e, {
                    "episode_name": episode_name,
                    "episode_profile": episode_profile,
                    "content_pieces_count": len(content_pieces) if content_pieces else 0,
                    "total_content_length": total_content_length
                })
                
                # 显示重试按钮
                if st.button("🔄 重试生成", type="primary"):
                    st.session_state.start_generation = True
                    st.rerun()
    
    except Exception as e:
        st.error(f"加载生成页面时出错: {str(e)}")
        st.markdown("请检查您的配置并重试。")

def show_episode_library_page():
    """显示节目库和播放页面。"""
    st.subheader("📚 节目库")
    st.markdown("浏览和播放您生成的节目")
    
    # Initialize episode manager
    episode_manager = EpisodeManager(base_output_dir=os.path.join(WORKING_DIR, "output"))
    
    try:
        # Load episodes
        all_episodes = episode_manager.scan_episodes_directory()
        
        if not all_episodes:
            st.info("📝 未找到节目。从生成您的第一个播客开始吧！")
            if st.button("🎬 生成您的第一个播客", type="primary"):
                st.session_state.current_page = "🎬 Generate Podcast"
                st.rerun()
            return
        
        # # Search and filter controls
        # col1, col2, col3 = st.columns([2, 1, 1])
        
        # with col1:
        #     search_query = st.text_input("🔍 搜索节目:", placeholder="按名称搜索...")
        
        # with col2:
        #     sort_by = st.selectbox("排序方式:", ["最新", "最旧", "A-Z", "时长"])
        
        # with col3:
        #     view_mode = st.radio("视图:", ["网格", "列表"], horizontal=True)
        
        # # Filter and sort episodes
        view_mode = "网格"
        filtered_episodes = episode_manager.search_episodes("", all_episodes)
        sorted_episodes = episode_manager.sort_episodes(filtered_episodes, "最新")
        
        # Show episode count
        st.markdown(f"**找到 {len(sorted_episodes)} 个节目**")
        st.markdown("---")
        
        # Handle selected episode for playback
        selected_episode = st.session_state.get("selected_episode")
        
        # Episode playback section
        if selected_episode and selected_episode.audio_file:
            with st.container(border=True):
                st.markdown(f"### 🎵 正在播放: {selected_episode.name}")
                
                # Audio player
                if Path(selected_episode.audio_file).exists():
                    audio_file = open(selected_episode.audio_file, 'rb')
                    audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format='audio/mp3')
                    audio_file.close()
                    
                    # Episode details
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if selected_episode.duration:
                            st.metric("时长", episode_manager.format_duration(selected_episode.duration))
                    
                    with col2:
                        if selected_episode.speakers_count:
                            st.metric("说话人数", selected_episode.speakers_count)
                    
                    with col3:
                        if selected_episode.file_size:
                            st.metric("文件大小", episode_manager.format_file_size(selected_episode.file_size))
                    
                    # Action buttons
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("📄 查看文本", use_container_width=True):
                            st.session_state.show_transcript = True
                            st.rerun()
                    
                    with col2:
                        if st.button("📊 查看大纲", use_container_width=True):
                            st.session_state.show_outline = True
                            st.rerun()
                    
                    with col3:
                        # Download button
                        if st.download_button(
                            label="⬇️ 下载",
                            data=audio_bytes,
                            file_name=f"{selected_episode.name}.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        ):
                            st.success("📥 下载已开始！")
                    
                    with col4:
                        if st.button("🗑️ 删除", use_container_width=True):
                            st.session_state.confirm_delete = selected_episode.name
                            st.rerun()
                else:
                    st.error("❌ 未找到音频文件")
                
                # Show transcript
                if st.session_state.get("show_transcript", False):
                    if selected_episode.transcript_file and Path(selected_episode.transcript_file).exists():
                        with st.expander("📄 文本记录", expanded=True):
                            try:
                                with open(selected_episode.transcript_file, 'r', encoding='utf-8') as f:
                                    transcript_data = json.load(f)
                                
                                if isinstance(transcript_data, list):
                                    for i, segment in enumerate(transcript_data):
                                        if isinstance(segment, dict):
                                            speaker = segment.get('speaker', f'说话人 {i+1}')
                                            # Try multiple possible field names for the text content
                                            text = (segment.get('text') or 
                                                   segment.get('content') or 
                                                   segment.get('dialogue') or 
                                                   segment.get('message') or 
                                                   segment.get('speech') or '')
                                            
                                            # Debug: Show available keys if text is empty
                                            if not text and st.session_state.get('debug_transcript', False):
                                                st.warning(f"调试 - 片段 {i+1} 键: {list(segment.keys())}")
                                                st.json(segment)
                                            
                                            if text:
                                                st.markdown(f"**{speaker}:** {text}")
                                                st.markdown("---")
                                            else:
                                                st.markdown(f"**{speaker}:** *[未找到内容]*")
                                                st.markdown("---")
                                else:
                                    st.text(str(transcript_data))
                                
                                # Add debug toggle
                                if st.checkbox("🐛 调试模式 - 显示原始数据", key="debug_transcript_toggle"):
                                    st.session_state.debug_transcript = True
                                    st.json(transcript_data)
                                else:
                                    st.session_state.debug_transcript = False
                            except Exception as e:
                                st.error(f"加载文本记录时出错: {str(e)}")
                            
                            if st.button("❌ 关闭文本记录"):
                                st.session_state.show_transcript = False
                                st.rerun()
                    else:
                        st.error("❌ 未找到文本记录文件")
                
                # Show outline
                if st.session_state.get("show_outline", False):
                    if selected_episode.outline_file and Path(selected_episode.outline_file).exists():
                        with st.expander("📊 大纲", expanded=True):
                            try:
                                with open(selected_episode.outline_file, 'r', encoding='utf-8') as f:
                                    outline_data = json.load(f)
                                st.json(outline_data)
                            except Exception as e:
                                st.error(f"加载大纲时出错: {str(e)}")
                            
                            if st.button("❌ 关闭大纲"):
                                st.session_state.show_outline = False
                                st.rerun()
                    else:
                        st.error("❌ 未找到大纲文件")
                
                # Stop playback button
                if st.button("⏹️ 停止播放"):
                    st.session_state.selected_episode = None
                    st.session_state.show_transcript = False
                    st.session_state.show_outline = False
                    st.rerun()
            
            st.markdown("---")
        
        # Handle delete confirmation
        if st.session_state.get("confirm_delete"):
            episode_to_delete = st.session_state.confirm_delete
            
            st.warning(f"⚠️ 您确定要删除节目 '{episode_to_delete}' 吗？")
            st.markdown("此操作无法撤销，将永久删除所有节目文件。")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ 是的，删除", type="primary"):
                    # Find the episode to delete
                    for episode in sorted_episodes:
                        if episode.name == episode_to_delete:
                            if episode_manager.delete_episode(episode.path):
                                st.success(f"✅ 节目 '{episode_to_delete}' 已成功删除")
                                if st.session_state.get("selected_episode") and st.session_state.selected_episode.name == episode_to_delete:
                                    st.session_state.selected_episode = None
                                st.session_state.confirm_delete = None
                                st.rerun()
                            else:
                                st.error("❌ 删除节目失败")
                            break
            
            with col2:
                if st.button("❌ 取消"):
                    st.session_state.confirm_delete = None
                    st.rerun()
            
            st.markdown("---")
        
        # Display episodes
        if view_mode == "网格":
            # Grid view
            cols = st.columns(3)
            
            for i, episode in enumerate(sorted_episodes):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### 🎙️ {episode.name}")
                        
                        if episode.created_date:
                            st.markdown(f"**创建时间:** {episode.created_date.strftime('%Y-%m-%d %H:%M')}")
                        
                        if episode.duration:
                            st.markdown(f"**时长:** {episode_manager.format_duration(episode.duration)}")
                        
                        if episode.speakers_count:
                            st.markdown(f"**说话人数:** {episode.speakers_count}")
                        
                        if episode.profile_used:
                            st.markdown(f"**配置文件:** {episode.profile_used}")
                        
                        # Action buttons
                        if episode.audio_file and st.button("▶️ 播放", key=f"play_grid_{i}", use_container_width=True):
                            st.session_state.selected_episode = episode
                            st.rerun()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if episode.transcript_file and st.button("📄", key=f"transcript_grid_{i}", help="查看文本"):
                                st.session_state.selected_episode = episode
                                st.session_state.show_transcript = True
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️", key=f"delete_grid_{i}", help="删除节目"):
                                st.session_state.confirm_delete = episode.name
                                st.rerun()
        
        else:
            # List view
            for i, episode in enumerate(sorted_episodes):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.markdown(f"### 🎙️ {episode.name}")
                        if episode.created_date:
                            st.markdown(f"*创建时间: {episode.created_date.strftime('%Y-%m-%d %H:%M')}*")
                    
                    with col2:
                        info_lines = []
                        if episode.duration:
                            info_lines.append(f"时长: {episode_manager.format_duration(episode.duration)}")
                        if episode.speakers_count:
                            info_lines.append(f"说话人数: {episode.speakers_count}")
                        if episode.profile_used:
                            info_lines.append(f"配置文件: {episode.profile_used}")
                        
                        for line in info_lines:
                            st.markdown(line)
                    
                    with col3:
                        if episode.audio_file and st.button("▶️ 播放", key=f"play_list_{i}"):
                            st.session_state.selected_episode = episode
                            st.rerun()
                        
                        if episode.transcript_file and st.button("📄 文本", key=f"transcript_list_{i}"):
                            st.session_state.selected_episode = episode
                            st.session_state.show_transcript = True
                            st.rerun()
                        
                        if st.button("🗑️ 删除", key=f"delete_list_{i}"):
                            st.session_state.confirm_delete = episode.name
                            st.rerun()
        
        # Library statistics
        if sorted_episodes:
            with st.expander("📊 库统计", expanded=False):
                stats = episode_manager.get_episodes_stats()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("总节目数", stats['total_episodes'])
                
                with col2:
                    if stats['total_duration'] > 0:
                        total_hours = stats['total_duration'] / 3600
                        st.metric("总时长", f"{total_hours:.1f} 小时")
                
                with col3:
                    if stats['average_duration'] > 0:
                        st.metric("平均时长", episode_manager.format_duration(stats['average_duration']))
                
                with col4:
                    if stats['total_size'] > 0:
                        st.metric("总大小", episode_manager.format_file_size(stats['total_size']))
    
    except Exception as e:
        st.error(f"加载节目库时出错: {str(e)}")
        st.markdown("请检查您的输出目录并重试。")

if __name__ == "__main__":
    main()