"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LEVER TASK CONFIGURATION                            ║
║                                                                               ║
║  Configuration for lever/torque balance task generator.                       ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Lever/torque balance task configuration.

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

    domain: str = Field(default="lever")
    image_size: tuple[int, int] = Field(default=(640, 480))

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    generate_videos: bool = Field(
        default=True,
        description="Whether to generate ground truth videos"
    )

    video_fps: int = Field(
        default=15,
        description="Video frame rate"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  LEVER PHYSICS SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Distance settings (in meters from fulcrum)
    max_distance: int = Field(
        default=3,
        description="Maximum distance from fulcrum (1 to max_distance)"
    )

    # Weight settings (in kg)
    min_weight: int = Field(
        default=1,
        description="Minimum object weight in kg"
    )

    max_weight: int = Field(
        default=10,
        description="Maximum object weight in kg"
    )

    # Object count settings
    min_objects_per_side: int = Field(
        default=1,
        description="Minimum objects per side"
    )

    max_objects_per_side: int = Field(
        default=3,
        description="Maximum objects per side"
    )

    # Animation settings
    tilt_angle: float = Field(
        default=22.0,
        description="Maximum tilt angle in degrees when lever tips"
    )

    # Include balanced cases
    include_balanced: bool = Field(
        default=True,
        description="Include cases where torques are equal (no tipping)"
    )

    balanced_probability: float = Field(
        default=0.15,
        description="Probability of generating a balanced case (0.0 to 1.0)"
    )
