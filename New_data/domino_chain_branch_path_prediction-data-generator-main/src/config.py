"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN CONFIGURATION                          ║
║                                                                               ║
║  Configuration for Domino Chain Branch Path Prediction task.                  ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Domino Chain task-specific configuration.

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

    domain: str = Field(default="domino_chain")
    image_size: tuple[int, int] = Field(default=(512, 512))

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
    #  DOMINO CHAIN SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Structure settings
    trunk_length_min: int = Field(
        default=1,
        description="Minimum number of dominos in trunk before junction"
    )
    trunk_length_max: int = Field(
        default=3,
        description="Maximum number of dominos in trunk before junction"
    )
    branch_length_min: int = Field(
        default=2,
        description="Minimum number of dominos per branch"
    )
    branch_length_max: int = Field(
        default=4,
        description="Maximum number of dominos per branch"
    )

    # Block settings
    block_probability: float = Field(
        default=0.3,
        description="Probability of having a blocked branch (0.0 to 1.0)"
    )

    # Visual settings
    domino_width: int = Field(
        default=20,
        description="Width of each domino rectangle in pixels"
    )
    domino_height: int = Field(
        default=50,
        description="Height of each domino rectangle in pixels"
    )
    domino_spacing: int = Field(
        default=60,
        description="Spacing between dominos in pixels"
    )

    # Colors (RGB tuples)
    trunk_color: tuple[int, int, int] = Field(
        default=(100, 100, 100),
        description="Color for trunk dominos (gray)"
    )
    branch_a_color: tuple[int, int, int] = Field(
        default=(220, 60, 60),
        description="Color for branch A dominos (red)"
    )
    branch_b_color: tuple[int, int, int] = Field(
        default=(60, 120, 220),
        description="Color for branch B dominos (blue)"
    )
    start_color: tuple[int, int, int] = Field(
        default=(60, 180, 60),
        description="Color for START domino (green)"
    )
    fallen_alpha: float = Field(
        default=0.6,
        description="Opacity multiplier for fallen dominos"
    )
    background_color: tuple[int, int, int] = Field(
        default=(245, 245, 240),
        description="Background color"
    )

    # Branch angle
    branch_angle: float = Field(
        default=35.0,
        description="Angle of branches from vertical (degrees)"
    )
