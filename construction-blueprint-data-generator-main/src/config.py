"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK CONFIGURATION                             ║
║                                                                               ║
║  Construction Blueprint - Missing Piece Task                                  ║
║  A structure with a gap and 4 candidate pieces to choose from                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Configuration for Construction Blueprint - Missing Piece task.

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

    domain: str = Field(default="construction_blueprint")
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
    #  TASK-SPECIFIC SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    grid_size: int = Field(
        default=8,
        description="Size of the grid (grid_size x grid_size)"
    )

    num_candidates: int = Field(
        default=4,
        description="Number of candidate pieces to choose from"
    )

    min_structure_blocks: int = Field(
        default=12,
        description="Minimum number of blocks in the structure"
    )

    max_structure_blocks: int = Field(
        default=20,
        description="Maximum number of blocks in the structure"
    )
