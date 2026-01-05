"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK CONFIGURATION                             ║
║                                                                               ║
║  CUSTOMIZE THIS FILE to define your task-specific settings.                   ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Move-to-Target task configuration.

    Task: Move 2 objects (circles) to their corresponding target ring positions.

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

    domain: str = Field(default="move_to_target")
    image_size: tuple[int, int] = Field(default=(512, 512))

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
    #  OBJECT SETTINGS (2 objects with different colors)
    # ══════════════════════════════════════════════════════════════════════════

    object_radius: int = Field(
        default=30,
        description="Radius of the movable objects (circles)"
    )

    object_colors: tuple[tuple[int, int, int], tuple[int, int, int]] = Field(
        default=((244, 143, 177), (143, 188, 244)),
        description="RGB colors of the two objects (pink, blue)"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  TARGET RING SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    target_ring_radius: int = Field(
        default=35,
        description="Radius of the target rings (slightly larger than object)"
    )

    ring_colors: tuple[tuple[int, int, int], tuple[int, int, int]] = Field(
        default=((180, 100, 130), (100, 140, 180)),
        description="RGB colors of the two dashed target rings (matching objects)"
    )

    ring_dash_length: int = Field(
        default=8,
        description="Length of each dash in the target ring"
    )

    ring_gap_length: int = Field(
        default=6,
        description="Length of gaps between dashes"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  SCENE SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    bg_color: tuple[int, int, int] = Field(
        default=(220, 220, 220),
        description="RGB background color (light gray)"
    )

    min_distance: int = Field(
        default=80,
        description="Minimum distance between object start and its target"
    )

    max_distance: int = Field(
        default=250,
        description="Maximum distance between object start and its target"
    )

    min_separation: int = Field(
        default=80,
        description="Minimum separation between any two objects/targets"
    )

    margin: int = Field(
        default=50,
        description="Margin from canvas edges for placing objects"
    )
