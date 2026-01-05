"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK CONFIGURATION                             ║
║                                                                               ║
║  Configuration for Construction_Stack_1: Block Rearrangement Task             ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Block Stacking Task Configuration.

    Task: Rearrange colored blocks from initial state to target state
    using Tower of Hanoi-style rules (only move top block).

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

    domain: str = Field(default="construction_stack")
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
    #  BLOCK STACKING SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    num_stacks: int = Field(
        default=3,
        ge=2,
        le=3,
        description="Number of stacks available (2-3, Hanoi-style)"
    )

    min_blocks: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Minimum number of blocks"
    )

    max_blocks: int = Field(
        default=5,
        ge=3,
        le=6,
        description="Maximum number of blocks"
    )

    block_colors: list[str] = Field(
        default=[
            "#E74C3C",  # Red
            "#3498DB",  # Blue
            "#2ECC71",  # Green
            "#F1C40F",  # Yellow
            "#9B59B6",  # Purple
            "#E67E22",  # Orange
        ],
        description="Available block colors (hex)"
    )

    block_color_names: list[str] = Field(
        default=["Red", "Blue", "Green", "Yellow", "Purple", "Orange"],
        description="Human-readable color names"
    )

    block_width: int = Field(
        default=60,
        description="Width of each block in pixels"
    )

    block_height: int = Field(
        default=40,
        description="Height of each block in pixels"
    )

    # ══════════════════════════════════════════════════════════════════════════
    #  ANIMATION SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    lift_frames: int = Field(
        default=8,
        description="Frames for lifting block up"
    )

    move_frames: int = Field(
        default=12,
        description="Frames for horizontal movement"
    )

    lower_frames: int = Field(
        default=8,
        description="Frames for lowering block down"
    )

    hold_frames: int = Field(
        default=10,
        description="Frames to hold at start and end"
    )

    pause_between_moves: int = Field(
        default=5,
        description="Pause frames between moves"
    )
