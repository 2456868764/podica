"""
播客创作工作室的配置文件管理工具。

处理说话人和剧集配置文件的增删改查操作。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import streamlit as st
from copy import deepcopy

try:
    from podcast_creator import load_speaker_config, load_episode_config, configure
    PODCAST_CREATOR_AVAILABLE = True
except ImportError:
    PODCAST_CREATOR_AVAILABLE = False


class ProfileManager:
    """管理说话人和剧集配置文件，包括增删改查操作。"""
    
    def __init__(self, working_dir: str = "."):
        """
        初始化配置文件管理器。
        
        参数:
            working_dir: 配置文件的工作目录
        """
        self.working_dir = Path(working_dir)
        self.speakers_config_path = self.working_dir / "speakers_config.json"
        self.episodes_config_path = self.working_dir / "episodes_config.json"
        
        # Initialize config files if they don't exist
        self._ensure_config_files()
    
    def _ensure_config_files(self):
        """确保配置文件存在并具有默认结构。"""
        
        # Default speaker config structure
        default_speakers = {
            "profiles": {
                "ai_researchers": {
                    "tts_provider": "elevenlabs",
                    "tts_model": "eleven_flash_v2_5",
                    "speakers": [
                        {
                            "name": "Dr. Alex Chen",
                            "voice_id": "voice_id_1",
                            "backstory": "Senior AI researcher with focus on machine learning ethics",
                            "personality": "Thoughtful, asks probing questions, explains complex concepts clearly"
                        },
                        {
                            "name": "Jamie Rodriguez",
                            "voice_id": "voice_id_2", 
                            "backstory": "Tech journalist and startup advisor with 10 years experience",
                            "personality": "Enthusiastic, great at explanations, bridges technical and business perspectives"
                        }
                    ]
                },
                "solo_expert": {
                    "tts_provider": "elevenlabs",
                    "tts_model": "eleven_flash_v2_5",
                    "speakers": [
                        {
                            "name": "Dr. Sarah Mitchell",
                            "voice_id": "voice_id_3",
                            "backstory": "Expert educator and researcher with ability to explain complex topics",
                            "personality": "Clear, authoritative, engaging, uses analogies and examples"
                        }
                    ]
                }
            }
        }
        
        # Default episode config structure
        default_episodes = {
            "profiles": {
                "tech_discussion": {
                    "speaker_config": "ai_researchers",
                    "outline_model": "gpt-4o",
                    "transcript_model": "gpt-4o",
                    "num_segments": 4,
                    "default_briefing": "Create an engaging technical discussion that explores the topic in depth"
                },
                "solo_expert": {
                    "speaker_config": "solo_expert",
                    "outline_model": "gpt-4o", 
                    "transcript_model": "gpt-4o",
                    "num_segments": 3,
                    "default_briefing": "Create an educational explanation that breaks down complex concepts"
                }
            }
        }
        
        # Create speakers config if it doesn't exist
        if not self.speakers_config_path.exists():
            self._save_json(self.speakers_config_path, default_speakers)
        
        # Create episodes config if it doesn't exist
        if not self.episodes_config_path.exists():
            self._save_json(self.episodes_config_path, default_episodes)
    
    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """从文件加载JSON数据。"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"加载{file_path}时出错: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict[str, Any]) -> bool:
        """保存JSON数据到文件。"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"保存到{file_path}时出错: {e}")
            return False
    
    # 说话人配置管理
    
    def load_speaker_profiles(self) -> Dict[str, Any]:
        """加载所有说话人配置。"""
        return self._load_json(self.speakers_config_path)
    
    def get_speaker_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """获取特定的说话人配置。"""
        profiles = self.load_speaker_profiles()
        return profiles.get("profiles", {}).get(profile_name)
    
    def create_speaker_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """创建新的说话人配置。"""
        profiles = self.load_speaker_profiles()
        
        if profile_name in profiles.get("profiles", {}):
            st.error(f"说话人配置'{profile_name}'已存在")
            return False
        
        profiles.setdefault("profiles", {})[profile_name] = profile_data
        return self._save_json(self.speakers_config_path, profiles)
    
    def update_speaker_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """更新现有的说话人配置。"""
        profiles = self.load_speaker_profiles()
        
        if profile_name not in profiles.get("profiles", {}):
            st.error(f"未找到说话人配置'{profile_name}'")
            return False
        
        profiles["profiles"][profile_name] = profile_data
        return self._save_json(self.speakers_config_path, profiles)
    
    def delete_speaker_profile(self, profile_name: str) -> bool:
        """删除说话人配置。"""
        profiles = self.load_speaker_profiles()
        
        if profile_name not in profiles.get("profiles", {}):
            st.error(f"未找到说话人配置'{profile_name}'")
            return False
        
        del profiles["profiles"][profile_name]
        return self._save_json(self.speakers_config_path, profiles)
    
    def clone_speaker_profile(self, source_name: str, new_name: str) -> bool:
        """克隆说话人配置并使用新名称。"""
        source_profile = self.get_speaker_profile(source_name)
        
        if not source_profile:
            st.error(f"未找到源说话人配置'{source_name}'")
            return False
        
        cloned_profile = deepcopy(source_profile)
        return self.create_speaker_profile(new_name, cloned_profile)
    
    def get_speaker_profile_names(self) -> List[str]:
        """获取所有说话人配置名称列表。"""
        profiles = self.load_speaker_profiles()
        return list(profiles.get("profiles", {}).keys())
    
    # 剧集配置管理
    
    def load_episode_profiles(self) -> Dict[str, Any]:
        """加载所有剧集配置。"""
        return self._load_json(self.episodes_config_path)
    
    def get_episode_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """获取特定的剧集配置。"""
        profiles = self.load_episode_profiles()
        return profiles.get("profiles", {}).get(profile_name)
    
    def create_episode_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """创建新的剧集配置。"""
        profiles = self.load_episode_profiles()
        
        if profile_name in profiles.get("profiles", {}):
            st.error(f"剧集配置'{profile_name}'已存在")
            return False
        
        profiles.setdefault("profiles", {})[profile_name] = profile_data
        return self._save_json(self.episodes_config_path, profiles)
    
    def update_episode_profile(self, profile_name: str, profile_data: Dict[str, Any]) -> bool:
        """更新现有的剧集配置。"""
        profiles = self.load_episode_profiles()
        
        if profile_name not in profiles.get("profiles", {}):
            st.error(f"未找到剧集配置'{profile_name}'")
            return False
        
        profiles["profiles"][profile_name] = profile_data
        return self._save_json(self.episodes_config_path, profiles)
    
    def delete_episode_profile(self, profile_name: str) -> bool:
        """删除剧集配置。"""
        profiles = self.load_episode_profiles()
        
        if profile_name not in profiles.get("profiles", {}):
            st.error(f"未找到剧集配置'{profile_name}'")
            return False
        
        del profiles["profiles"][profile_name]
        return self._save_json(self.episodes_config_path, profiles)
    
    def clone_episode_profile(self, source_name: str, new_name: str) -> bool:
        """克隆剧集配置并使用新名称。"""
        source_profile = self.get_episode_profile(source_name)
        
        if not source_profile:
            st.error(f"未找到源剧集配置'{source_name}'")
            return False
        
        cloned_profile = deepcopy(source_profile)
        return self.create_episode_profile(new_name, cloned_profile)
    
    def get_episode_profile_names(self) -> List[str]:
        """获取所有剧集配置名称列表。"""
        profiles = self.load_episode_profiles()
        return list(profiles.get("profiles", {}).keys())
    
    # 导入/导出功能
    
    def export_speaker_profiles(self, profile_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """将说话人配置导出为字典。"""
        all_profiles = self.load_speaker_profiles()
        
        if profile_names is None:
            return all_profiles
        
        # 仅导出指定的配置
        exported = {"profiles": {}}
        for name in profile_names:
            if name in all_profiles.get("profiles", {}):
                exported["profiles"][name] = all_profiles["profiles"][name]
        
        return exported
    
    def export_episode_profiles(self, profile_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """将剧集配置导出为字典。"""
        all_profiles = self.load_episode_profiles()
        
        if profile_names is None:
            return all_profiles
        
        # 仅导出指定的配置
        exported = {"profiles": {}}
        for name in profile_names:
            if name in all_profiles.get("profiles", {}):
                exported["profiles"][name] = all_profiles["profiles"][name]
        
        return exported
    
    def import_speaker_profiles(self, file_content: str) -> List[str]:
        """
        从JSON内容导入说话人配置。
        
        参数:
            file_content: JSON内容字符串
            
        返回:
            导入的配置名称列表
        """
        try:
            import_data = json.loads(file_content)
            imported_names = []
            
            if "profiles" in import_data:
                current_profiles = self.load_speaker_profiles()
                
                for profile_name, profile_data in import_data["profiles"].items():
                    # 检查配置是否已存在
                    if profile_name in current_profiles.get("profiles", {}):
                        st.warning(f"说话人配置'{profile_name}'已存在，跳过")
                        continue
                    
                    if self.create_speaker_profile(profile_name, profile_data):
                        imported_names.append(profile_name)
                
                return imported_names
            else:
                st.error("无效格式：未找到'profiles'键")
                return []
                
        except json.JSONDecodeError as e:
            st.error(f"无效的JSON格式：{e}")
            return []
        except Exception as e:
            st.error(f"导入配置时出错：{e}")
            return []
    
    def import_episode_profiles(self, file_content: str) -> List[str]:
        """
        从JSON内容导入剧集配置。
        
        参数:
            file_content: JSON内容字符串
            
        返回:
            导入的配置名称列表
        """
        try:
            import_data = json.loads(file_content)
            imported_names = []
            
            if "profiles" in import_data:
                current_profiles = self.load_episode_profiles()
                
                for profile_name, profile_data in import_data["profiles"].items():
                    # 检查配置是否已存在
                    if profile_name in current_profiles.get("profiles", {}):
                        st.warning(f"剧集配置'{profile_name}'已存在，跳过")
                        continue
                    
                    if self.create_episode_profile(profile_name, profile_data):
                        imported_names.append(profile_name)
                
                return imported_names
            else:
                st.error("无效格式：未找到'profiles'键")
                return []
                
        except json.JSONDecodeError as e:
            st.error(f"无效的JSON格式：{e}")
            return []
        except Exception as e:
            st.error(f"导入配置时出错：{e}")
            return []
    
    # 验证功能
    
    def validate_speaker_profile(self, profile_data: Dict[str, Any]) -> List[str]:
        """
        验证说话人配置数据。
        
        参数:
            profile_data: 要验证的配置数据
            
        返回:
            验证错误列表（如果有效则为空）
        """
        errors = []
        
        # 检查必填字段
        if "tts_provider" not in profile_data:
            errors.append("TTS提供商是必填项")
        
        if "tts_model" not in profile_data:
            errors.append("TTS模型是必填项")
        
        if "speakers" not in profile_data:
            errors.append("说话人列表是必填项")
        elif not isinstance(profile_data["speakers"], list):
            errors.append("说话人必须是一个列表")
        elif len(profile_data["speakers"]) == 0:
            errors.append("至少需要一个说话人")
        else:
            # 验证每个说话人
            for i, speaker in enumerate(profile_data["speakers"]):
                if not isinstance(speaker, dict):
                    errors.append(f"说话人{i+1}必须是一个对象")
                    continue
                
                required_fields = ["name", "voice_id", "backstory", "personality"]
                for field in required_fields:
                    if field not in speaker:
                        errors.append(f"说话人{i+1}缺少必填字段：{field}")
        
        return errors
    
    def validate_episode_profile(self, profile_data: Dict[str, Any]) -> List[str]:
        """
        验证剧集配置数据。
        
        参数:
            profile_data: 要验证的配置数据
            
        返回:
            验证错误列表（如果有效则为空）
        """
        errors = []
        
        # 检查必填字段
        required_fields = ["speaker_config", "outline_model", "transcript_model", "num_segments"]
        for field in required_fields:
            if field not in profile_data:
                errors.append(f"缺少必填字段：{field}")
        
        # 验证段落数量
        if "num_segments" in profile_data:
            try:
                num_segments = int(profile_data["num_segments"])
                if num_segments < 1 or num_segments > 10:
                    errors.append("段落数量必须在1到10之间")
            except (ValueError, TypeError):
                errors.append("段落数量必须是有效的整数")
        
        # 验证说话人配置存在
        if "speaker_config" in profile_data:
            speaker_names = self.get_speaker_profile_names()
            if profile_data["speaker_config"] not in speaker_names:
                errors.append(f"未找到说话人配置'{profile_data['speaker_config']}'")
        
        return errors
    
    # 统计和信息
    
    def get_profiles_stats(self) -> Dict[str, Any]:
        """获取配置统计信息。"""
        speaker_profiles = self.load_speaker_profiles()
        episode_profiles = self.load_episode_profiles()
        
        return {
            "speaker_profiles_count": len(speaker_profiles.get("profiles", {})),
            "episode_profiles_count": len(episode_profiles.get("profiles", {})),
            "total_speakers": sum(
                len(profile.get("speakers", [])) 
                for profile in speaker_profiles.get("profiles", {}).values()
            )
        }