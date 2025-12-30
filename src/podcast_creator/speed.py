import json
from pathlib import Path
from typing import Dict, List, Union

from pydantic import BaseModel, Field, field_validator
from loguru import logger


class SpeedConfig(BaseModel):
    """Collection of speed configurations."""
    speeds: Dict[str, float] = Field(default_factory=lambda: {
        "slow": 0.9,
        "normal": 1.0,
        "fast": 1.1,
    }, description="Dictionary of speed configurations")

    def get_speed_names(self) -> List[str]:
        """Get speed names."""
        return list(self.speeds.keys())
       
    def get_speed_name_value(self, name: str) -> float:
        """Get speed value by name."""
        if name not in self.speeds:
            available = self.get_speed_names()
            logger.warning(f"Speed '{name}' not found. Available speeds: {available}")
            return 1.0
        return self.speeds[name]

def load_speed_config() -> "SpeedConfig":
    """Load speed configurations.

    Returns:
        SpeedConfig: Loaded speed configuration object.
    """
    return SpeedConfig()
        
