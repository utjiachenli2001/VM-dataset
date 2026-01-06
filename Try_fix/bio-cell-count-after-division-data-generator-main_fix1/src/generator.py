"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BIO_CELL TASK GENERATOR                                 ║
║                                                                              ║
║  Generates cell division counting tasks.                                     ║
║  Simulates exponential cell growth: Final = Initial × 2^N                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class Cell:
    """Represents a single cell with position and state."""

    # Constants for hierarchical layout
    INITIAL_RADIUS = 30.0
    INITIAL_SPLIT_DISTANCE = 70.0
    SHRINK_FACTOR = 0.75

    def __init__(self, x: float, y: float, radius: float, generation: int = 0):
        self.x = x
        self.y = y
        self.radius = radius
        self.generation = generation
        # For division animation
        self.elongation = 1.0  # 1.0 = circle, >1.0 = elongated
        self.pinch = 0.0  # 0.0 = no pinch, 1.0 = fully pinched

    def divide(self) -> tuple["Cell", "Cell"]:
        """
        Divide this cell into two daughter cells.
        Split direction alternates: H (gen 0→1), V (gen 1→2), H (gen 2→3), ...
        """
        new_gen = self.generation + 1
        new_radius = Cell.INITIAL_RADIUS * (Cell.SHRINK_FACTOR ** new_gen)
        split_dist = Cell.INITIAL_SPLIT_DISTANCE * (Cell.SHRINK_FACTOR ** new_gen)

        # Alternate split direction based on generation
        if self.generation % 2 == 0:
            # Horizontal split (left-right)
            daughter1 = Cell(self.x - split_dist, self.y, new_radius, new_gen)
            daughter2 = Cell(self.x + split_dist, self.y, new_radius, new_gen)
        else:
            # Vertical split (up-down)
            daughter1 = Cell(self.x, self.y - split_dist, new_radius, new_gen)
            daughter2 = Cell(self.x, self.y + split_dist, new_radius, new_gen)

        return daughter1, daughter2

    def copy(self) -> "Cell":
        """Create a copy of this cell."""
        cell = Cell(self.x, self.y, self.radius, self.generation)
        cell.elongation = self.elongation
        cell.pinch = self.pinch
        return cell


class TaskGenerator(BaseGenerator):
    """
    Cell division task generator.

    Generates visual tasks showing cell division with exponential growth.
    Each task shows initial cells dividing N times, with formula display.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.config: TaskConfig = config
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one cell division task."""

        # Generate random parameters
        initial_cells = random.randint(
            self.config.min_initial_cells,
            self.config.max_initial_cells
        )
        num_divisions = random.randint(
            self.config.min_divisions,
            self.config.max_divisions
        )
        final_cells = initial_cells * (2 ** num_divisions)

        task_data = {
            "initial_cells": initial_cells,
            "num_divisions": num_divisions,
            "final_cells": final_cells,
        }

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_id, task_data)

        # Select prompt
        prompt = get_prompt(
            initial_cells=initial_cells,
            num_divisions=num_divisions
        )

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING METHODS
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render the initial state with starting cells."""
        initial_cells = task_data["initial_cells"]
        num_divisions = task_data["num_divisions"]

        img = self._create_background()
        draw = ImageDraw.Draw(img)

        # Create initial cells using hierarchical layout
        cells = self._create_initial_cells(initial_cells)

        # Draw cells
        self._draw_cells(img, cells)

        # Draw header text
        self._draw_header(draw, f"N = {num_divisions} division{'s' if num_divisions > 1 else ''}")

        # Draw counter
        self._draw_counter(draw, initial_cells, label="Initial")

        return img

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render the final state with all divided cells."""
        initial_cells = task_data["initial_cells"]
        num_divisions = task_data["num_divisions"]
        final_cells = task_data["final_cells"]

        img = self._create_background()
        draw = ImageDraw.Draw(img)

        # Get cells after all divisions using hierarchical layout
        cells = self._get_cells_after_divisions(initial_cells, num_divisions)

        # Draw cells
        self._draw_cells(img, cells)

        # Draw formula header
        formula = self._format_formula(initial_cells, num_divisions, final_cells)
        self._draw_header(draw, formula)

        # Draw final counter
        self._draw_counter(draw, final_cells, label="Final Count")

        return img

    def _render_intermediate_state(
        self,
        initial_cells: int,
        divisions_completed: int,
        total_divisions: int
    ) -> Image.Image:
        """Render an intermediate state during division."""
        img = self._create_background()
        draw = ImageDraw.Draw(img)

        # Get cells after completed divisions using hierarchical layout
        cells = self._get_cells_after_divisions(initial_cells, divisions_completed)
        cell_count = len(cells)

        # Draw cells
        self._draw_cells(img, cells)

        # Draw header showing progress
        self._draw_header(draw, f"Cycle {divisions_completed}/{total_divisions}")

        # Draw counter
        self._draw_counter(draw, cell_count)

        return img

    def _create_background(self) -> Image.Image:
        """Create background image."""
        return Image.new('RGB', self.config.image_size, self.config.background_color)

    def _create_initial_cells(self, num_cells: int) -> List[Cell]:
        """
        Create initial cells in a deterministic layout.

        1 cell: center
        2 cells: horizontal pair
        3 cells: triangle (2 top, 1 bottom)
        4 cells: 2x2 grid
        """
        width, height = self.config.image_size

        # Center of usable area (accounting for header/footer)
        header_height = 60
        footer_height = 50
        center_x = width / 2
        center_y = header_height + (height - header_height - footer_height) / 2

        radius = Cell.INITIAL_RADIUS
        spacing = Cell.INITIAL_SPLIT_DISTANCE

        cells = []

        if num_cells == 1:
            cells.append(Cell(center_x, center_y, radius, generation=0))

        elif num_cells == 2:
            # Horizontal pair
            cells.append(Cell(center_x - spacing, center_y, radius, generation=0))
            cells.append(Cell(center_x + spacing, center_y, radius, generation=0))

        elif num_cells == 3:
            # Triangle: 2 top, 1 bottom center
            cells.append(Cell(center_x - spacing, center_y - spacing * 0.5, radius, generation=0))
            cells.append(Cell(center_x + spacing, center_y - spacing * 0.5, radius, generation=0))
            cells.append(Cell(center_x, center_y + spacing * 0.5, radius, generation=0))

        elif num_cells == 4:
            # 2x2 grid
            cells.append(Cell(center_x - spacing, center_y - spacing, radius, generation=0))
            cells.append(Cell(center_x + spacing, center_y - spacing, radius, generation=0))
            cells.append(Cell(center_x - spacing, center_y + spacing, radius, generation=0))
            cells.append(Cell(center_x + spacing, center_y + spacing, radius, generation=0))

        return cells

    def _divide_all_cells(self, cells: List[Cell]) -> List[Cell]:
        """Divide all cells once, returning the new generation."""
        new_cells = []
        for cell in cells:
            daughter1, daughter2 = cell.divide()
            new_cells.append(daughter1)
            new_cells.append(daughter2)
        return new_cells

    def _get_cells_after_divisions(self, initial_count: int, num_divisions: int) -> List[Cell]:
        """Get the final cell layout after N divisions."""
        cells = self._create_initial_cells(initial_count)

        for _ in range(num_divisions):
            cells = self._divide_all_cells(cells)

        return cells

    def _draw_cells(self, img: Image.Image, cells: List[Cell]) -> None:
        """Draw all cells on the image."""
        draw = ImageDraw.Draw(img)

        for cell in cells:
            self._draw_single_cell(draw, cell)

    def _draw_single_cell(self, draw: ImageDraw.Draw, cell: Cell) -> None:
        """Draw a single cell with nucleus."""
        x, y, r = cell.x, cell.y, cell.radius

        # Handle elongation for division animation
        rx = r * cell.elongation
        ry = r / cell.elongation

        # Draw cell body (ellipse)
        bbox = [x - rx, y - ry, x + rx, y + ry]
        draw.ellipse(bbox, fill=self.config.cell_color, outline=self.config.cell_outline_color, width=2)

        # Draw pinch effect if dividing
        if cell.pinch > 0:
            pinch_width = rx * 2 * cell.pinch * 0.3
            pinch_color = self.config.background_color
            # Draw pinch lines from top and bottom
            pinch_height = ry * cell.pinch * 0.8
            draw.rectangle(
                [x - pinch_width/2, y - pinch_height, x + pinch_width/2, y + pinch_height],
                fill=pinch_color
            )

        # Draw nucleus (or two nuclei if dividing)
        nucleus_r = r * 0.25
        if cell.pinch > 0.5:
            # Two nuclei separating
            separation = rx * (cell.pinch - 0.5) * 1.5
            draw.ellipse(
                [x - separation - nucleus_r, y - nucleus_r, x - separation + nucleus_r, y + nucleus_r],
                fill=self.config.nucleus_color
            )
            draw.ellipse(
                [x + separation - nucleus_r, y - nucleus_r, x + separation + nucleus_r, y + nucleus_r],
                fill=self.config.nucleus_color
            )
        else:
            # Single nucleus
            draw.ellipse(
                [x - nucleus_r, y - nucleus_r, x + nucleus_r, y + nucleus_r],
                fill=self.config.nucleus_color
            )

    def _draw_header(self, draw: ImageDraw.Draw, text: str) -> None:
        """Draw header text at top of image."""
        font = self._get_font(size=28)
        width = self.config.image_size[0]

        # Get text size for centering
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        y = 15

        draw.text((x, y), text, fill=self.config.text_color, font=font)

    def _draw_counter(self, draw: ImageDraw.Draw, count: int, label: str = "Count") -> None:
        """Draw counter at bottom of image."""
        font = self._get_font(size=24)
        width, height = self.config.image_size

        text = f"{label}: {count}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        y = height - 45

        draw.text((x, y), text, fill=self.config.text_color, font=font)

    def _format_formula(self, initial: int, divisions: int, final: int) -> str:
        """Format the formula string with superscript."""
        # Using Unicode superscript characters for exponent
        superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
                       '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
        exp_str = ''.join(superscripts.get(c, c) for c in str(divisions))
        return f"{initial} × 2{exp_str} = {final} cells"

    def _get_font(self, size: int = 24) -> ImageFont.FreeTypeFont:
        """Get a font for text rendering."""
        font_names = [
            "arial.ttf",
            "Arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:/Windows/Fonts/arial.ttf",
        ]

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue

        return ImageFont.load_default()

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, task_id: str, task_data: dict) -> Optional[str]:
        """Generate ground truth video showing cell division process."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_division_animation(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_division_animation(self, task_data: dict) -> List[Image.Image]:
        """Create animation frames for cell division."""
        initial_cells_count = task_data["initial_cells"]
        num_divisions = task_data["num_divisions"]

        frames = []

        # Initial hold - show starting state
        initial_frame = self._render_initial_state(task_data)
        for _ in range(self.config.hold_frames):
            frames.append(initial_frame)

        # Start with initial cells
        current_cells = self._create_initial_cells(initial_cells_count)

        # Process each division cycle
        for cycle in range(1, num_divisions + 1):
            # Division animation for this cycle
            division_frames = self._animate_division_cycle(
                current_cells,
                cycle,
                num_divisions
            )
            frames.extend(division_frames)

            # Update cells after division
            current_cells = self._divide_all_cells(current_cells)

            # Hold frame showing new count (unless last cycle)
            if cycle < num_divisions:
                hold_frame = self._render_intermediate_state(
                    initial_cells_count, cycle, num_divisions
                )
                for _ in range(self.config.hold_frames // 2):
                    frames.append(hold_frame)

        # Final hold - show end state with formula
        final_frame = self._render_final_state(task_data)
        for _ in range(self.config.hold_frames * 2):
            frames.append(final_frame)

        return frames

    def _animate_division_cycle(
        self,
        cells_before: List[Cell],
        cycle: int,
        total_cycles: int
    ) -> List[Image.Image]:
        """Create frames for one division cycle (all cells divide simultaneously)."""
        frames = []
        division_frames = self.config.division_frames
        reorganize_frames = self.config.reorganize_frames

        cell_count = len(cells_before)
        new_count = cell_count * 2

        # Make copies so we don't modify originals
        cells_before = [cell.copy() for cell in cells_before]

        # Pre-compute daughter cells for each parent
        daughter_pairs = []
        for cell in cells_before:
            d1, d2 = cell.divide()
            daughter_pairs.append((d1, d2))

        # Phase 1: Elongation (cells stretch in the direction they will split)
        elongation_frames = division_frames // 3
        for i in range(elongation_frames):
            progress = (i + 1) / elongation_frames
            img = self._create_background()
            draw = ImageDraw.Draw(img)

            for cell in cells_before:
                cell.elongation = 1.0 + progress * 0.8  # Elongate up to 1.8x
                cell.pinch = 0.0

            self._draw_cells(img, cells_before)
            self._draw_header(draw, f"Cycle {cycle}/{total_cycles} - Dividing...")
            self._draw_counter(draw, cell_count)
            frames.append(img)

        # Phase 2: Pinching (middle narrows, nuclei separate)
        pinch_frames = division_frames // 3
        for i in range(pinch_frames):
            progress = (i + 1) / pinch_frames
            img = self._create_background()
            draw = ImageDraw.Draw(img)

            for cell in cells_before:
                cell.elongation = 1.8
                cell.pinch = progress

            self._draw_cells(img, cells_before)
            self._draw_header(draw, f"Cycle {cycle}/{total_cycles} - Dividing...")
            self._draw_counter(draw, cell_count)
            frames.append(img)

        # Phase 3: Separation (cells split and move to daughter positions)
        separation_frames = division_frames // 3
        for i in range(separation_frames):
            progress = (i + 1) / separation_frames
            img = self._create_background()
            draw = ImageDraw.Draw(img)

            for j, cell in enumerate(cells_before):
                d1, d2 = daughter_pairs[j]

                # Interpolate from parent center to daughter positions
                # First daughter cell
                temp_cell1 = Cell(
                    cell.x + (d1.x - cell.x) * progress,
                    cell.y + (d1.y - cell.y) * progress,
                    cell.radius + (d1.radius - cell.radius) * progress,
                    d1.generation
                )
                temp_cell1.elongation = 1.8 - progress * 0.8  # Return to circle
                self._draw_single_cell(draw, temp_cell1)

                # Second daughter cell
                temp_cell2 = Cell(
                    cell.x + (d2.x - cell.x) * progress,
                    cell.y + (d2.y - cell.y) * progress,
                    cell.radius + (d2.radius - cell.radius) * progress,
                    d2.generation
                )
                temp_cell2.elongation = 1.8 - progress * 0.8  # Return to circle
                self._draw_single_cell(draw, temp_cell2)

            # Update counter during separation
            displayed_count = cell_count if progress < 0.5 else new_count
            self._draw_header(draw, f"Cycle {cycle}/{total_cycles}")
            self._draw_counter(draw, displayed_count)
            frames.append(img)

        # Phase 4: Settle (cells at final positions)
        cells_after = []
        for d1, d2 in daughter_pairs:
            cells_after.append(d1)
            cells_after.append(d2)

        for i in range(reorganize_frames):
            img = self._create_background()
            draw = ImageDraw.Draw(img)

            self._draw_cells(img, cells_after)
            self._draw_header(draw, f"Cycle {cycle}/{total_cycles} complete")
            self._draw_counter(draw, new_count)
            frames.append(img)

        return frames
