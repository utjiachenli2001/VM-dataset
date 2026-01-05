"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CELL DIVISION TASK GENERATOR                       ║
║                                                                              ║
║  Bio_Cell_1: Predict Division Stage                                          ║
║  Generates mitosis cell division prediction tasks with animations.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
import math
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt, get_stage_name


class CellStage(Enum):
    """Stages of mitosis (cell division)."""
    INTERPHASE = "interphase"
    PROPHASE = "prophase"
    METAPHASE = "metaphase"
    ANAPHASE = "anaphase"
    TELOPHASE = "telophase"


# Stage progression order
STAGE_ORDER = [
    CellStage.INTERPHASE,
    CellStage.PROPHASE,
    CellStage.METAPHASE,
    CellStage.ANAPHASE,
    CellStage.TELOPHASE,
]


class TaskGenerator(BaseGenerator):
    """
    Cell division task generator.

    Generates mitosis prediction tasks where the model must predict
    what the cell will look like in the next stage of division.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Cell geometry (based on 512x512 image)
        self.width, self.height = config.image_size
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        # Cell dimensions
        self.cell_width = int(self.width * 0.7)
        self.cell_height = int(self.height * 0.5)
        self.nucleus_radius = int(min(self.cell_width, self.cell_height) * 0.35)

        # Chromosome settings
        self.chromosome_count = config.chromosome_count
        self.chromosome_size = int(self.width * 0.06)

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one cell division task pair."""

        # Randomly select a starting stage
        current_stage = random.choice(STAGE_ORDER)
        next_stage = self._get_next_stage(current_stage)

        # Render images
        first_image = self._render_cell(current_stage, show_question=True)
        final_image = self._render_cell(next_stage, show_question=False)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(current_stage, next_stage, task_id)

        # Select prompt based on current stage
        prompt = get_prompt(current_stage.value)

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    def _get_next_stage(self, current: CellStage) -> CellStage:
        """Get the next stage in the mitotic cycle."""
        current_idx = STAGE_ORDER.index(current)
        next_idx = (current_idx + 1) % len(STAGE_ORDER)
        return STAGE_ORDER[next_idx]

    # ══════════════════════════════════════════════════════════════════════════
    #  CELL RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_cell(self, stage: CellStage, show_question: bool = True) -> Image.Image:
        """Render a cell at a specific stage of mitosis."""
        img = Image.new("RGB", (self.width, self.height), self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Get stage-specific parameters
        params = self._get_stage_params(stage)

        # Draw components in order (back to front)
        self._draw_spindle_fibers(draw, stage, params)
        self._draw_cell_membrane(draw, stage, params)
        self._draw_nucleus(draw, stage, params)
        self._draw_chromosomes(draw, stage, params)
        self._draw_centrosomes(draw, stage, params)
        self._draw_labels(draw, stage, show_question)

        return img

    def _get_stage_params(self, stage: CellStage) -> dict:
        """Get rendering parameters for a specific stage."""
        params = {
            "cell_elongation": 1.0,  # How much the cell is stretched
            "pinch_amount": 0.0,  # How much the cell is pinching (0-1)
            "nucleus_visible": True,
            "nucleus_opacity": 1.0,
            "chromosomes_visible": False,
            "chromosomes_condensed": False,
            "chromosomes_split": False,  # Whether chromosomes are split into chromatids
            "spindle_visible": False,
            "chromosome_positions": [],  # List of (x, y) for each chromosome
        }

        if stage == CellStage.INTERPHASE:
            params["nucleus_visible"] = True
            params["nucleus_opacity"] = 1.0
            params["chromosomes_visible"] = False
            params["spindle_visible"] = False

        elif stage == CellStage.PROPHASE:
            params["nucleus_visible"] = True
            params["nucleus_opacity"] = 0.5  # Breaking down
            params["chromosomes_visible"] = True
            params["chromosomes_condensed"] = True
            params["spindle_visible"] = True
            # Scattered positions around nucleus
            params["chromosome_positions"] = self._get_scattered_positions()

        elif stage == CellStage.METAPHASE:
            params["nucleus_visible"] = False
            params["chromosomes_visible"] = True
            params["chromosomes_condensed"] = True
            params["spindle_visible"] = True
            # Aligned at center (metaphase plate)
            params["chromosome_positions"] = self._get_metaphase_positions()

        elif stage == CellStage.ANAPHASE:
            params["nucleus_visible"] = False
            params["cell_elongation"] = 1.2
            params["chromosomes_visible"] = True
            params["chromosomes_condensed"] = True
            params["spindle_visible"] = True
            # Split and moving to poles (8 chromatids now)
            params["chromosome_positions"] = self._get_anaphase_positions()
            params["chromosomes_split"] = True

        elif stage == CellStage.TELOPHASE:
            params["nucleus_visible"] = True
            params["nucleus_opacity"] = 0.7  # Reforming
            params["cell_elongation"] = 1.3
            params["pinch_amount"] = 0.4
            params["chromosomes_visible"] = True
            params["chromosomes_condensed"] = False  # Decondensing
            params["spindle_visible"] = False
            # At poles
            params["chromosome_positions"] = self._get_telophase_positions()
            params["chromosomes_split"] = True

        return params

    def _get_scattered_positions(self) -> List[Tuple[float, float]]:
        """Get scattered chromosome positions for Prophase."""
        positions = []
        radius = self.nucleus_radius * 0.6
        for i in range(self.chromosome_count):
            angle = (2 * math.pi * i / self.chromosome_count) + random.uniform(-0.3, 0.3)
            r = radius * random.uniform(0.5, 1.0)
            x = self.center_x + r * math.cos(angle)
            y = self.center_y + r * math.sin(angle)
            positions.append((x, y))
        return positions

    def _get_metaphase_positions(self) -> List[Tuple[float, float]]:
        """Get aligned chromosome positions for Metaphase (metaphase plate)."""
        positions = []
        spacing = self.chromosome_size * 2.5
        start_x = self.center_x - (self.chromosome_count - 1) * spacing / 2
        for i in range(self.chromosome_count):
            x = start_x + i * spacing
            y = self.center_y
            positions.append((x, y))
        return positions

    def _get_anaphase_positions(self) -> List[Tuple[float, float]]:
        """Get split chromosome positions for Anaphase (moving to poles)."""
        positions = []
        spacing = self.chromosome_size * 2.0
        pole_offset = self.cell_height * 0.25
        start_x = self.center_x - (self.chromosome_count - 1) * spacing / 2

        # Top pole chromatids
        for i in range(self.chromosome_count):
            x = start_x + i * spacing
            y = self.center_y - pole_offset
            positions.append((x, y))

        # Bottom pole chromatids
        for i in range(self.chromosome_count):
            x = start_x + i * spacing
            y = self.center_y + pole_offset
            positions.append((x, y))

        return positions

    def _get_telophase_positions(self) -> List[Tuple[float, float]]:
        """Get chromosome positions for Telophase (at poles)."""
        positions = []
        spacing = self.chromosome_size * 1.5
        pole_offset = self.cell_height * 0.35
        start_x = self.center_x - (self.chromosome_count - 1) * spacing / 2

        # Top pole
        for i in range(self.chromosome_count):
            x = start_x + i * spacing
            y = self.center_y - pole_offset
            positions.append((x, y))

        # Bottom pole
        for i in range(self.chromosome_count):
            x = start_x + i * spacing
            y = self.center_y + pole_offset
            positions.append((x, y))

        return positions

    def _draw_cell_membrane(self, draw: ImageDraw.Draw, stage: CellStage, params: dict):
        """Draw the cell membrane (outer boundary)."""
        elongation = params["cell_elongation"]
        pinch = params["pinch_amount"]

        cell_w = self.cell_width
        cell_h = int(self.cell_height * elongation)

        # Calculate bounding box
        left = self.center_x - cell_w // 2
        top = self.center_y - cell_h // 2
        right = self.center_x + cell_w // 2
        bottom = self.center_y + cell_h // 2

        if pinch > 0:
            # Draw pinched cell (two connected ovals for Telophase)
            self._draw_pinched_cell(draw, left, top, right, bottom, pinch)
        else:
            # Draw normal oval cell
            draw.ellipse(
                [left, top, right, bottom],
                fill=self.config.cytoplasm_color,
                outline=self.config.cell_membrane_color,
                width=3
            )

    def _draw_pinched_cell(self, draw: ImageDraw.Draw, left: int, top: int,
                           right: int, bottom: int, pinch: float):
        """Draw a pinched cell (for Telophase/Cytokinesis)."""
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        half_height = (bottom - top) // 2
        half_width = (right - left) // 2

        # Pinch width at center
        pinch_width = int(half_width * (1 - pinch * 0.6))

        # Draw as polygon for pinched shape
        points = []
        num_points = 60

        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            # Base ellipse
            x = half_width * math.cos(angle)
            y = half_height * math.sin(angle)

            # Apply pinch at center (y near 0)
            pinch_factor = math.exp(-abs(y) / (half_height * 0.3))
            x = x * (1 - pinch * 0.5 * pinch_factor)

            points.append((center_x + x, center_y + y))

        draw.polygon(points, fill=self.config.cytoplasm_color,
                     outline=self.config.cell_membrane_color)

    def _draw_nucleus(self, draw: ImageDraw.Draw, stage: CellStage, params: dict):
        """Draw the nucleus/nuclear envelope."""
        if not params["nucleus_visible"]:
            return

        opacity = params["nucleus_opacity"]

        if stage == CellStage.TELOPHASE:
            # Draw two nuclei reforming at poles
            pole_offset = self.cell_height * 0.35
            radius = int(self.nucleus_radius * 0.6)

            for y_offset in [-pole_offset, pole_offset]:
                cx = self.center_x
                cy = int(self.center_y + y_offset)
                self._draw_single_nucleus(draw, cx, cy, radius, opacity)
        else:
            # Draw single central nucleus
            self._draw_single_nucleus(draw, self.center_x, self.center_y,
                                      self.nucleus_radius, opacity)

    def _draw_single_nucleus(self, draw: ImageDraw.Draw, cx: int, cy: int,
                             radius: int, opacity: float):
        """Draw a single nucleus."""
        left = cx - radius
        top = cy - radius
        right = cx + radius
        bottom = cy + radius

        # Adjust colors based on opacity (simulating transparency)
        fill_color = self._blend_color(self.config.nucleus_fill_color,
                                        self.config.cytoplasm_color, opacity)
        outline_color = self._blend_color(self.config.nucleus_color,
                                           self.config.cytoplasm_color, opacity)

        draw.ellipse([left, top, right, bottom], fill=fill_color,
                     outline=outline_color, width=2)

        # Draw chromatin dots in Interphase
        if opacity > 0.9:
            self._draw_chromatin(draw, cx, cy, radius)

    def _draw_chromatin(self, draw: ImageDraw.Draw, cx: int, cy: int, radius: int):
        """Draw diffuse chromatin dots inside nucleus (Interphase)."""
        num_dots = 15
        for _ in range(num_dots):
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0.2, 0.8) * radius
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            dot_size = random.randint(2, 5)
            draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size],
                         fill=self.config.chromatin_color)

    def _draw_chromosomes(self, draw: ImageDraw.Draw, stage: CellStage, params: dict):
        """Draw chromosomes at their positions."""
        if not params["chromosomes_visible"]:
            return

        positions = params["chromosome_positions"]
        is_split = params.get("chromosomes_split", False)
        condensed = params["chromosomes_condensed"]

        if is_split:
            # Draw V-shaped chromatids (after separation)
            for i, (x, y) in enumerate(positions):
                # Alternate direction for top vs bottom
                going_up = i < self.chromosome_count
                self._draw_chromatid(draw, x, y, going_up, condensed)
        else:
            # Draw X-shaped chromosomes
            for x, y in positions:
                self._draw_chromosome(draw, x, y, condensed)

    def _draw_chromosome(self, draw: ImageDraw.Draw, x: float, y: float, condensed: bool):
        """Draw an X-shaped chromosome."""
        size = self.chromosome_size if condensed else self.chromosome_size * 0.7
        thickness = 4 if condensed else 2

        # Draw X shape
        draw.line([(x - size, y - size), (x + size, y + size)],
                  fill=self.config.chromosome_color, width=thickness)
        draw.line([(x - size, y + size), (x + size, y - size)],
                  fill=self.config.chromosome_color, width=thickness)

        # Draw centromere (center circle)
        centromere_size = 4
        draw.ellipse([x - centromere_size, y - centromere_size,
                      x + centromere_size, y + centromere_size],
                     fill=self.config.chromosome_color)

    def _draw_chromatid(self, draw: ImageDraw.Draw, x: float, y: float,
                        going_up: bool, condensed: bool):
        """Draw a V-shaped chromatid (half of a chromosome)."""
        size = self.chromosome_size * 0.8 if condensed else self.chromosome_size * 0.5
        thickness = 4 if condensed else 2

        # V pointing up or down
        if going_up:
            draw.line([(x - size * 0.5, y + size), (x, y)],
                      fill=self.config.chromosome_color, width=thickness)
            draw.line([(x + size * 0.5, y + size), (x, y)],
                      fill=self.config.chromosome_color, width=thickness)
        else:
            draw.line([(x - size * 0.5, y - size), (x, y)],
                      fill=self.config.chromosome_color, width=thickness)
            draw.line([(x + size * 0.5, y - size), (x, y)],
                      fill=self.config.chromosome_color, width=thickness)

    def _draw_spindle_fibers(self, draw: ImageDraw.Draw, stage: CellStage, params: dict):
        """Draw spindle fibers connecting poles to chromosomes."""
        if not params["spindle_visible"]:
            return

        # Pole positions
        pole_offset = self.cell_height * 0.45 * params["cell_elongation"]
        top_pole = (self.center_x, int(self.center_y - pole_offset))
        bottom_pole = (self.center_x, int(self.center_y + pole_offset))

        positions = params["chromosome_positions"]
        is_split = params.get("chromosomes_split", False)

        if is_split:
            # Connect each chromatid to its nearest pole
            for i, (x, y) in enumerate(positions):
                if i < self.chromosome_count:
                    # Top group connects to top pole
                    draw.line([top_pole, (x, y)], fill=self.config.spindle_color, width=1)
                else:
                    # Bottom group connects to bottom pole
                    draw.line([bottom_pole, (x, y)], fill=self.config.spindle_color, width=1)
        else:
            # Connect each chromosome to both poles
            for x, y in positions:
                draw.line([top_pole, (x, y)], fill=self.config.spindle_color, width=1)
                draw.line([bottom_pole, (x, y)], fill=self.config.spindle_color, width=1)

    def _draw_centrosomes(self, draw: ImageDraw.Draw, stage: CellStage, params: dict):
        """Draw centrosomes (spindle poles)."""
        if not params["spindle_visible"] and stage != CellStage.PROPHASE:
            return

        pole_offset = self.cell_height * 0.45 * params["cell_elongation"]
        size = 8

        # Top pole
        cx, cy = self.center_x, int(self.center_y - pole_offset)
        draw.ellipse([cx - size, cy - size, cx + size, cy + size],
                     fill=self.config.centrosome_color)

        # Bottom pole
        cy = int(self.center_y + pole_offset)
        draw.ellipse([cx - size, cy - size, cx + size, cy + size],
                     fill=self.config.centrosome_color)

    def _draw_labels(self, draw: ImageDraw.Draw, stage: CellStage, show_question: bool):
        """Draw stage label and question indicator."""
        font = self._get_font(size=20)
        small_font = self._get_font(size=16)

        # Stage name label (top left)
        stage_name = get_stage_name(stage.value)
        draw.text((20, 20), stage_name, fill=self.config.label_color, font=font)

        if show_question:
            # "What's next?" indicator (top right)
            question_text = "What's next? →"
            bbox = draw.textbbox((0, 0), question_text, font=small_font)
            text_width = bbox[2] - bbox[0]
            draw.text((self.width - text_width - 20, 20), question_text,
                      fill=(200, 0, 0), font=small_font)

            # Arrow at bottom
            arrow_y = self.height - 40
            draw.text((self.width // 2 - 10, arrow_y), "?",
                      fill=(200, 0, 0), font=font)

    def _get_font(self, size: int = 16) -> ImageFont.FreeTypeFont:
        """Get a font for labels."""
        font_names = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()

    def _blend_color(self, color1: Tuple[int, int, int],
                     color2: Tuple[int, int, int], alpha: float) -> Tuple[int, int, int]:
        """Blend two colors based on alpha value."""
        return tuple(int(c1 * alpha + c2 * (1 - alpha)) for c1, c2 in zip(color1, color2))

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, from_stage: CellStage, to_stage: CellStage,
                        task_id: str) -> Optional[str]:
        """Generate ground truth video showing the transition."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_transition_frames(from_stage, to_stage)

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_transition_frames(self, from_stage: CellStage, to_stage: CellStage,
                                   hold_frames: int = 10,
                                   transition_frames: int = 30) -> List[Image.Image]:
        """Create animation frames for stage transition."""
        frames = []

        # Hold initial stage
        initial_frame = self._render_cell(from_stage, show_question=True)
        for _ in range(hold_frames):
            frames.append(initial_frame)

        # Get parameters for interpolation
        from_params = self._get_stage_params(from_stage)
        to_params = self._get_stage_params(to_stage)

        # Create transition frames
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0
            frame = self._render_interpolated_frame(from_stage, to_stage,
                                                     from_params, to_params, progress)
            frames.append(frame)

        # Hold final stage
        final_frame = self._render_cell(to_stage, show_question=False)
        for _ in range(hold_frames):
            frames.append(final_frame)

        return frames

    def _render_interpolated_frame(self, from_stage: CellStage, to_stage: CellStage,
                                    from_params: dict, to_params: dict,
                                    progress: float) -> Image.Image:
        """Render a frame at an intermediate point in the transition."""
        img = Image.new("RGB", (self.width, self.height), self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Interpolate parameters
        params = self._interpolate_params(from_params, to_params, progress)

        # Draw components
        self._draw_spindle_fibers(draw, to_stage if progress > 0.5 else from_stage, params)
        self._draw_cell_membrane(draw, to_stage if progress > 0.5 else from_stage, params)
        self._draw_interpolated_nucleus(draw, from_params, to_params, progress)
        self._draw_interpolated_chromosomes(draw, from_params, to_params, progress)
        self._draw_centrosomes(draw, to_stage if progress > 0.5 else from_stage, params)

        # Transition label
        if progress < 0.5:
            self._draw_labels(draw, from_stage, show_question=False)
        else:
            self._draw_labels(draw, to_stage, show_question=False)

        return img

    def _interpolate_params(self, from_params: dict, to_params: dict,
                            progress: float) -> dict:
        """Interpolate numeric parameters between stages."""
        params = {}
        for key in from_params:
            from_val = from_params[key]
            to_val = to_params[key]

            if isinstance(from_val, (int, float)) and isinstance(to_val, (int, float)):
                params[key] = from_val + (to_val - from_val) * progress
            else:
                # For non-numeric, switch at midpoint
                params[key] = to_val if progress > 0.5 else from_val

        return params

    def _draw_interpolated_nucleus(self, draw: ImageDraw.Draw,
                                    from_params: dict, to_params: dict,
                                    progress: float):
        """Draw nucleus with interpolated opacity."""
        from_visible = from_params["nucleus_visible"]
        to_visible = to_params["nucleus_visible"]
        from_opacity = from_params["nucleus_opacity"] if from_visible else 0
        to_opacity = to_params["nucleus_opacity"] if to_visible else 0

        opacity = from_opacity + (to_opacity - from_opacity) * progress

        if opacity < 0.1:
            return

        # Handle Telophase special case (two nuclei)
        if to_params.get("pinch_amount", 0) > 0 and progress > 0.5:
            pole_offset = self.cell_height * 0.35
            radius = int(self.nucleus_radius * 0.6 * (progress - 0.5) * 2)
            if radius > 5:
                for y_offset in [-pole_offset, pole_offset]:
                    self._draw_single_nucleus(draw, self.center_x,
                                              int(self.center_y + y_offset), radius, opacity)
        else:
            self._draw_single_nucleus(draw, self.center_x, self.center_y,
                                      self.nucleus_radius, opacity)

    def _draw_interpolated_chromosomes(self, draw: ImageDraw.Draw,
                                        from_params: dict, to_params: dict,
                                        progress: float):
        """Draw chromosomes with interpolated positions."""
        from_visible = from_params["chromosomes_visible"]
        to_visible = to_params["chromosomes_visible"]

        if not from_visible and not to_visible:
            return

        from_positions = from_params["chromosome_positions"]
        to_positions = to_params["chromosome_positions"]

        from_split = from_params.get("chromosomes_split", False)
        to_split = to_params.get("chromosomes_split", False)

        # Handle appearing/disappearing
        if not from_visible:
            # Chromosomes appearing (Interphase -> Prophase)
            alpha = progress
            positions = to_positions
            is_split = to_split
        elif not to_visible:
            # Chromosomes disappearing
            alpha = 1 - progress
            positions = from_positions
            is_split = from_split
        else:
            alpha = 1.0
            # Interpolate positions
            if len(from_positions) == len(to_positions):
                positions = [
                    (
                        from_pos[0] + (to_pos[0] - from_pos[0]) * progress,
                        from_pos[1] + (to_pos[1] - from_pos[1]) * progress
                    )
                    for from_pos, to_pos in zip(from_positions, to_positions)
                ]
                is_split = to_split if progress > 0.3 else from_split
            elif len(to_positions) > len(from_positions):
                # Splitting (Metaphase -> Anaphase)
                positions = self._interpolate_split(from_positions, to_positions, progress)
                is_split = progress > 0.3
            else:
                # Merging (shouldn't happen in normal cycle)
                positions = to_positions if progress > 0.5 else from_positions
                is_split = to_split if progress > 0.5 else from_split

        # Draw chromosomes/chromatids
        condensed = to_params["chromosomes_condensed"] if progress > 0.5 else from_params["chromosomes_condensed"]

        if is_split:
            for i, (x, y) in enumerate(positions):
                going_up = i < self.chromosome_count
                self._draw_chromatid(draw, x, y, going_up, condensed)
        else:
            for x, y in positions:
                self._draw_chromosome(draw, x, y, condensed)

    def _interpolate_split(self, from_positions: List[Tuple[float, float]],
                           to_positions: List[Tuple[float, float]],
                           progress: float) -> List[Tuple[float, float]]:
        """Interpolate chromosome positions during splitting."""
        # from_positions has N chromosomes, to_positions has 2N chromatids
        positions = []
        n = len(from_positions)

        for i in range(n):
            # Each chromosome splits into two chromatids
            from_pos = from_positions[i]
            to_top = to_positions[i]  # Top chromatid
            to_bottom = to_positions[i + n]  # Bottom chromatid

            # Interpolate to both positions
            top_x = from_pos[0] + (to_top[0] - from_pos[0]) * progress
            top_y = from_pos[1] + (to_top[1] - from_pos[1]) * progress
            positions.append((top_x, top_y))

        for i in range(n):
            from_pos = from_positions[i]
            to_bottom = to_positions[i + n]

            bottom_x = from_pos[0] + (to_bottom[0] - from_pos[0]) * progress
            bottom_y = from_pos[1] + (to_bottom[1] - from_pos[1]) * progress
            positions.append((bottom_x, bottom_y))

        return positions
