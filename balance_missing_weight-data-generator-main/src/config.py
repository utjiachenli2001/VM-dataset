"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BALANCE SCALE CONFIGURATION                         ║
║                                                                               ║
║  Configuration for Balance Scale missing weight puzzle generator.             ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Balance Scale task configuration.

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

    domain: str = Field(default="balance_scale")
    image_size: tuple[int, int] = Field(default=(600, 400))  # Wider for scale layout

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
    #  PUZZLE PARAMETERS
    # ══════════════════════════════════════════════════════════════════════════

    min_total_weight: int = Field(
        default=5,
        description="Minimum total weight for balanced scale"
    )

    max_total_weight: int = Field(
        default=20,
        description="Maximum total weight for balanced scale"
    )

    min_objects_per_side: int = Field(
        default=2,
        description="Minimum number of weight objects per side"
    )

    max_objects_per_side: int = Field(
        default=4,
        description="Maximum number of weight objects per side"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  VISUAL PARAMETERS
    # ══════════════════════════════════════════════════════════════════════════

    tilt_angle: float = Field(
        default=12.0,
        description="Degrees of tilt when scale is unbalanced"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  ANIMATION PARAMETERS
    # ══════════════════════════════════════════════════════════════════════════

    show_steps: bool = Field(
        default=True,
        description="Whether to show step-by-step equation solving"
    )

    step_display_frames: int = Field(
        default=15,
        description="Number of frames to display each step"
    )
