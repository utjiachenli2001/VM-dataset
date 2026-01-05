"""
LEGO Construction Assembly Task Configuration

Defines settings for generating LEGO instruction step data.
"""

from typing import List, Tuple
from pydantic import Field
from core import GenerationConfig


# LEGO Color Palette (official-ish colors)
LEGO_COLORS = {
    "red": (201, 26, 9),
    "blue": (0, 85, 191),
    "yellow": (245, 205, 47),
    "green": (0, 146, 71),
    "white": (255, 255, 255),
    "black": (30, 30, 30),
    "orange": (254, 138, 24),
    "lime": (166, 202, 85),
    "light_gray": (180, 180, 180),
    "dark_gray": (100, 100, 100),
}

# Basic brick types: (width_studs, depth_studs, height_plates)
# Standard brick height = 3 plates
BRICK_TYPES = {
    "1x1": (1, 1, 3),
    "1x2": (1, 2, 3),
    "2x2": (2, 2, 3),
    "2x4": (2, 4, 3),
}


class TaskConfig(GenerationConfig):
    """
    LEGO Construction Assembly task configuration.

    Inherited from GenerationConfig:
        - num_samples: int          # Number of samples to generate
        - domain: str               # Task domain name
        - difficulty: Optional[str] # Difficulty level
        - random_seed: Optional[int] # For reproducibility
        - output_dir: Path          # Where to save outputs
        - image_size: tuple[int, int] # Image dimensions
    """

    # Override defaults
    domain: str = Field(default="lego")
    image_size: Tuple[int, int] = Field(default=(512, 512))

    # Video settings
    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )

    video_fps: int = Field(
        default=15,
        description="Video frame rate"
    )

    # LEGO-specific settings
    stud_size: int = Field(
        default=20,
        description="Size of one stud in pixels (base unit for isometric rendering)"
    )

    brick_height_px: int = Field(
        default=24,
        description="Height of one standard brick in pixels"
    )

    available_colors: List[str] = Field(
        default=["red", "blue", "yellow", "green", "white", "orange"],
        description="Colors to use for bricks"
    )

    available_brick_types: List[str] = Field(
        default=["1x1", "1x2", "2x2", "2x4"],
        description="Brick types to use"
    )

    # Instruction layout settings
    step_number_size: int = Field(
        default=36,
        description="Font size for step number"
    )

    callout_scale: float = Field(
        default=0.8,
        description="Scale factor for piece callout area"
    )

    show_arrows: bool = Field(
        default=True,
        description="Show arrow indicators for piece placement"
    )

    # Animation settings
    animation_hold_frames: int = Field(
        default=8,
        description="Frames to hold at start and end"
    )

    animation_move_frames: int = Field(
        default=20,
        description="Frames for piece movement"
    )

    animation_snap_frames: int = Field(
        default=6,
        description="Frames for snap effect"
    )
