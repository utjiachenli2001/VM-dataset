"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK CONFIGURATION                             ║
║                                                                               ║
║  Logic Gate Output Task Configuration                                         ║
║  Inherits common settings from core.GenerationConfig                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import List
from pydantic import Field
from core import GenerationConfig


class TaskConfig(GenerationConfig):
    """
    Logic Gate task-specific configuration.

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

    domain: str = Field(default="logic_gate")
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
    #  LOGIC GATE TASK-SPECIFIC SETTINGS
    # ══════════════════════════════════════════════════════════════════════════

    # Gate types to include in generation
    gate_types: List[str] = Field(
        default=["AND", "OR", "NOT", "XOR", "NAND", "NOR"],
        description="Types of logic gates to use"
    )

    # Difficulty settings
    min_gates: int = Field(
        default=1,
        description="Minimum number of gates in circuit"
    )

    max_gates: int = Field(
        default=4,
        description="Maximum number of gates in circuit"
    )

    min_inputs: int = Field(
        default=2,
        description="Minimum number of input wires"
    )

    max_inputs: int = Field(
        default=4,
        description="Maximum number of input wires"
    )

    # Visual settings
    color_zero: tuple[int, int, int] = Field(
        default=(65, 105, 225),  # Royal Blue
        description="Color for signal value 0"
    )

    color_one: tuple[int, int, int] = Field(
        default=(220, 20, 60),  # Crimson Red
        description="Color for signal value 1"
    )

    color_unknown: tuple[int, int, int] = Field(
        default=(128, 128, 128),  # Gray
        description="Color for unknown signal"
    )

    # Animation settings
    hold_frames: int = Field(
        default=5,
        description="Frames to hold at start and end"
    )

    propagation_frames: int = Field(
        default=15,
        description="Frames for signal propagation per gate"
    )
