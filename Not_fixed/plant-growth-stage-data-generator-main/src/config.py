"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BIO_GROWTH TASK CONFIGURATION                       ║
║                                                                               ║
║  Configuration for plant growth stage prediction task.                        ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional, Tuple
from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Plant growth stage prediction task configuration.

    Inherited from GenerationConfig:
        - num_samples: int          # Number of samples to generate
        - domain: str               # Task domain name
        - difficulty: Optional[str] # Difficulty level
        - random_seed: Optional[int] # For reproducibility
        - output_dir: Path          # Where to save outputs
        - image_size: tuple[int, int] # Image dimensions
    """

    # ══════════════════════════════════════════════════════════════════════════
    #  OVERRIDE DEFAULTS
    # ══════════════════════════════════════════════════════════════════════════

    domain: str = Field(default="bio_growth")
    image_size: Tuple[int, int] = Field(default=(512, 512))

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )

    video_fps: int = Field(
        default=10,
        description="Video frame rate"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  PLANT GROWTH TASK-SPECIFIC SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Layout settings
    ground_level: float = Field(
        default=0.45,
        description="Ground line position as fraction from top (0.45 = 45% from top)"
    )

    # Plant appearance
    stem_color: Tuple[int, int, int] = Field(
        default=(34, 139, 34),
        description="RGB color for stem (forest green)"
    )

    leaf_color: Tuple[int, int, int] = Field(
        default=(50, 205, 50),
        description="RGB color for leaves (lime green)"
    )

    root_color: Tuple[int, int, int] = Field(
        default=(210, 180, 140),
        description="RGB color for roots (tan)"
    )

    flower_color: Optional[Tuple[int, int, int]] = Field(
        default=None,
        description="RGB color for flowers (random if None)"
    )

    fruit_color: Optional[Tuple[int, int, int]] = Field(
        default=None,
        description="RGB color for fruits (random if None)"
    )

    # Background colors
    sky_color: Tuple[int, int, int] = Field(
        default=(135, 206, 235),
        description="RGB color for sky (light blue)"
    )

    soil_color: Tuple[int, int, int] = Field(
        default=(139, 90, 43),
        description="RGB color for soil (brown)"
    )

    grass_color: Tuple[int, int, int] = Field(
        default=(34, 139, 34),
        description="RGB color for grass line (green)"
    )

    # Animation settings
    transition_frames: int = Field(
        default=30,
        description="Number of frames for growth transition"
    )

    hold_frames: int = Field(
        default=8,
        description="Number of frames to hold at start and end"
    )

    show_time_indicator: bool = Field(
        default=True,
        description="Show sun animation during growth"
    )
