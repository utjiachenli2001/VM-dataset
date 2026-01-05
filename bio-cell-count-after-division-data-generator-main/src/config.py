"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BIO_CELL TASK CONFIGURATION                             ║
║                                                                              ║
║  Configuration for cell division counting task.                              ║
║  Simulates exponential cell growth: Final = Initial × 2^N                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Cell division task configuration.

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

    domain: str = Field(default="bio_cell")
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
    #  CELL DIVISION TASK SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Cell count parameters
    min_initial_cells: int = Field(
        default=1,
        description="Minimum number of initial cells"
    )
    max_initial_cells: int = Field(
        default=4,
        description="Maximum number of initial cells"
    )

    min_divisions: int = Field(
        default=1,
        description="Minimum number of division cycles"
    )
    max_divisions: int = Field(
        default=3,
        description="Maximum number of division cycles (keep <= 3 for manageability)"
    )

    # Cell appearance
    cell_color: tuple[int, int, int] = Field(
        default=(144, 238, 144),
        description="Cell membrane color (light green)"
    )
    nucleus_color: tuple[int, int, int] = Field(
        default=(34, 139, 34),
        description="Nucleus color (dark green)"
    )
    cell_outline_color: tuple[int, int, int] = Field(
        default=(60, 179, 113),
        description="Cell outline color (medium sea green)"
    )

    # Layout settings
    background_color: tuple[int, int, int] = Field(
        default=(240, 248, 255),
        description="Background color (alice blue - light)"
    )
    text_color: tuple[int, int, int] = Field(
        default=(30, 30, 30),
        description="Text color for labels"
    )

    # Animation settings
    hold_frames: int = Field(
        default=8,
        description="Frames to hold at start/end of each cycle"
    )
    division_frames: int = Field(
        default=20,
        description="Frames for division animation per cycle"
    )
    reorganize_frames: int = Field(
        default=10,
        description="Frames for cells to reorganize after division"
    )
