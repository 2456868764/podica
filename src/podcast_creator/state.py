from operator import add
from pathlib import Path
from typing import Annotated, List, Optional, TypedDict, Union

from .core import Dialogue, Outline
from .speakers import SpeakerProfile
from .emotions import EmotionConfig
from .speed import SpeedConfig

class PodcastState(TypedDict):
    # Input data
    content: Union[str, List[str]]
    briefing: str
    num_segments: int

    # Generated content
    outline: Optional[Outline]
    transcript: List[Dialogue]

    # Audio processing
    audio_clips: Annotated[List[Path], add]
    final_output_file_path: Optional[Path]

    # Configuration
    output_dir: Path
    episode_name: str
    speaker_profile: Optional[SpeakerProfile]

    # Emotion configuration
    emotions_config: Optional[EmotionConfig]
    # speed names
    speed_config: Optional[SpeedConfig]
    # language
    language: str = "English"
    # dialect (optional, only applicable for Chinese)
    dialect: Optional[str] = None