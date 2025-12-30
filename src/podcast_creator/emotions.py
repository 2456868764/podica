import json
from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseModel, Field, field_validator
from loguru import logger

class Emotion(BaseModel):
    """Single emotion configuration for voice generation."""
    name: str = Field(..., description="Name of the emotion/speaking style")
    text: List[str] = Field(..., description="Voice characteristics and delivery instructions")
    category: List[str] = Field(default=[], description="Category of the emotion")
    description: str = Field(default="", description="Description of the emotion")

    def get_voice_instructions(self) -> str:
        """Get combined voice instructions as a single string."""
        return "\n".join(self.text)


class EmotionConfig(BaseModel):
    """Collection of emotion configurations."""
    emotions: Dict[str, Emotion] = Field(..., description="Dictionary of emotion configurations")
    categories: List[str] = Field(..., description="List of available emotion categories")

    def get_emotion(self, name: str) -> Emotion:
        """Get emotion configuration by name."""
        if name not in self.emotions:
            available = self.get_emotions_names()
            raise ValueError(f"Emotion '{name}' not found. Available emotions: {available}")
        return self.emotions[name]

    def get_emotions_names(self) -> List[str]:
        """Get list of all available emotion names."""
        return list(self.emotions.keys())

    def get_all_emotions(self) -> List[Emotion]:
        """Get list of all available emotion configurations."""
        return list(self.emotions.values())    

    def get_default_emotion(self) -> Emotion:
        """Get the default emotion configuration."""
        return self.get_emotion("Neutral")    

    def load_from_json(self, json_path: Union[str, Path]) -> "EmotionConfig":
        """Load emotion configuration from JSON file."""
        import json
        
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Emotions config file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If categories are not in the file, derive them from emotions
        if "categories" not in data:
            categories = set()
            if "emotions" in data:
                for emotion_data in data["emotions"].values():
                    if category := emotion_data.get("category"):
                        categories.add(category)
            data["categories"] = sorted(list(categories))

        return EmotionConfig(**data)

    @classmethod
    def from_json_file(cls, json_path: Union[str, Path]) -> "EmotionConfig":
        """Create EmotionConfig instance from JSON file.""" 
        config = cls(emotions={}, categories=[])
        return config.load_from_json(json_path)


def load_emotions_config(project_root: Path = None) -> "EmotionConfig":
    """
    Load the emotions configuration from a file.

    This function implements a priority cascade for locating the configuration file:
    1. Check for a configured emotions config file path.
    2. Check the current working directory for 'emotions_config.json'.
    3. Check for bundled default 'emotions_config.json'.

    Args:
        project_root: The root directory of the project. Defaults to the current working directory.

    Returns:
        EmotionConfig: The loaded emotions configuration.
    """
    # Priority 1: Check for a configured emotions config file path
    try:
        from .config import ConfigurationManager
        config_manager = ConfigurationManager()
        emotions_config_path = config_manager.get_config("emotions_config")
        logger.info(f"Emotions config path from config: {emotions_config_path}")
        if emotions_config_path and isinstance(emotions_config_path, str):
            config_path = Path(emotions_config_path)
            logger.info(f"Emotions config path from config: {config_path}")
            if config_path.exists():
                return EmotionConfig.from_json_file(config_path)
    except Exception:
        pass  # Fall back to default behavior

    # Priority 2: Use existing file-based loading (working directory)
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / "emotions_config.json"
    
    if config_path.exists():
        return EmotionConfig.from_json_file(config_path)

    # Priority 3: Try bundled defaults
    try:
        import importlib.resources as resources
        
        package_resources = resources.files("podcast_creator.resources")
        resource_file = package_resources / "emotions_config.json"
        
        if resource_file.is_file():
            return EmotionConfig.from_json_file(resource_file)
    except Exception:
        pass

    # If we get here, config not found
    raise ValueError(
        "Emotions config not found. Please ensure it exists in one of:\n"
        "1. A configured file path via configure('emotions_config', '/path/to/file.json')\n"
        "2. ./emotions_config.json\n"
        "3. Run 'podcast-creator init' to create default configuration."
    )

        

