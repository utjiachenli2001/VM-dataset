"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CELL DIVISION TASK CONFIGURATION                   ║
║                                                                              ║
║  Bio_Cell_1: Predict Division Stage                                          ║
║  Configuration for generating mitosis cell division prediction tasks.        ║
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
    #  CELL DIVISION SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Chromosome settings
    chromosome_count: int = Field(
        default=4,
        description="Number of chromosomes (fixed at 4 for simplicity)"
    )

    # Color scheme (classic biology textbook colors)
    cell_membrane_color: tuple[int, int, int] = Field(
        default=(144, 238, 144),  # Light green
        description="Cell membrane color (RGB)"
    )

    cytoplasm_color: tuple[int, int, int] = Field(
        default=(220, 255, 220),  # Very light green
        description="Cytoplasm fill color (RGB)"
    )

    nucleus_color: tuple[int, int, int] = Field(
        default=(255, 218, 185),  # Peach/tan
        description="Nuclear envelope color (RGB)"
    )

    nucleus_fill_color: tuple[int, int, int] = Field(
        default=(255, 239, 213),  # Papaya whip (lighter)
        description="Nucleus interior fill color (RGB)"
    )

    chromatin_color: tuple[int, int, int] = Field(
        default=(139, 119, 101),  # Tan/brown for diffuse chromatin
        description="Chromatin color in interphase (RGB)"
    )

    chromosome_color: tuple[int, int, int] = Field(
        default=(70, 130, 180),  # Steel blue
        description="Condensed chromosome color (RGB)"
    )

    spindle_color: tuple[int, int, int] = Field(
        default=(169, 169, 169),  # Dark gray
        description="Spindle fiber color (RGB)"
    )

    centrosome_color: tuple[int, int, int] = Field(
        default=(139, 69, 19),  # Saddle brown
        description="Centrosome/pole color (RGB)"
    )

    # Label settings
    label_color: tuple[int, int, int] = Field(
        default=(0, 0, 0),  # Black
        description="Text label color (RGB)"
    )

    background_color: tuple[int, int, int] = Field(
        default=(255, 255, 255),  # White
        description="Background color (RGB)"
    )
