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


class CellGrid:
    """
    Fixed 8x8 grid for cell positioning.
    All cells have fixed positions and sizes.
    Cells fill the grid from center outward in a deterministic pattern.
    """

    GRID_SIZE = 8  # 8x8 grid = 64 max cells
    CELL_RADIUS = 22.0  # Fixed cell size

    def __init__(self, image_size: tuple[int, int]):
        self.image_size = image_size
        width, height = image_size

        # Calculate grid bounds (accounting for header/footer)
        header_height = 60
        footer_height = 50
        margin = 20

        self.grid_left = margin
        self.grid_right = width - margin
        self.grid_top = header_height + 10
        self.grid_bottom = height - footer_height - 10

        self.grid_width = self.grid_right - self.grid_left
        self.grid_height = self.grid_bottom - self.grid_top

        self.cell_spacing_x = self.grid_width / self.GRID_SIZE
        self.cell_spacing_y = self.grid_height / self.GRID_SIZE

    def get_slot_position(self, row: int, col: int) -> tuple[float, float]:
        """Get pixel position for a grid slot (0-indexed)."""
        x = self.grid_left + (col + 0.5) * self.cell_spacing_x
        y = self.grid_top + (row + 0.5) * self.cell_spacing_y
        return x, y

    def get_slots_for_count(self, num_cells: int) -> List[tuple[int, int]]:
        """
        Get grid slots for a specific number of cells.
        Cells are arranged in a centered rectangular pattern.

        Supported counts: 1, 2, 4, 8, 16, 32, 64
        """
        # Calculate dimensions based on cell count
        # Pattern: cells fill a centered rectangle that doubles alternating H/V
        if num_cells == 1:
            return [(4, 4)]
        elif num_cells == 2:
            return [(4, 3), (4, 4)]
        elif num_cells == 4:
            return [(3, 3), (3, 4), (4, 3), (4, 4)]
        elif num_cells == 8:
            return [(3, 2), (3, 3), (3, 4), (3, 5),
                    (4, 2), (4, 3), (4, 4), (4, 5)]
        elif num_cells == 16:
            slots = []
            for row in range(2, 6):
                for col in range(2, 6):
                    slots.append((row, col))
            return slots
        elif num_cells == 32:
            slots = []
            for row in range(2, 6):
                for col in range(0, 8):
                    slots.append((row, col))
            return slots
        elif num_cells == 64:
            slots = []
            for row in range(0, 8):
                for col in range(0, 8):
                    slots.append((row, col))
            return slots
        else:
            # For non-standard counts, approximate with nearest pattern
            return self._get_slots_approximate(num_cells)

    def _get_slots_approximate(self, num_cells: int) -> List[tuple[int, int]]:
        """Generate slots for non-power-of-2 counts (e.g., 3 initial cells)."""
        # Find dimensions that fit
        import math
        cols = math.ceil(math.sqrt(num_cells))
        rows = math.ceil(num_cells / cols)

        # Center the grid
        start_col = (self.GRID_SIZE - cols) // 2
        start_row = (self.GRID_SIZE - rows) // 2

        slots = []
        for i in range(num_cells):
            r = i // cols
            c = i % cols
            slots.append((start_row + r, start_col + c))
        return slots

    def get_center_slots(self, num_cells: int) -> List[tuple[int, int]]:
        """Get centered grid slots for initial cells."""
        return self.get_slots_for_count(num_cells)


class Cell:
    """Represents a single cell with position and state."""

    def __init__(self, x: float, y: float, radius: float, generation: int = 0, slot: tuple[int, int] = None):
        self.x = x
        self.y = y
        self.radius = radius
        self.generation = generation
        self.slot = slot  # (row, col) grid position
        # For division animation
        self.elongation = 1.0  # 1.0 = circle, >1.0 = elongated
        self.pinch = 0.0  # 0.0 = no pinch, 1.0 = fully pinched

    def copy(self) -> "Cell":
        """Create a copy of this cell."""
        cell = Cell(self.x, self.y, self.radius, self.generation, self.slot)
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

        # Initialize fixed grid for cell positioning
        self.grid = CellGrid(config.image_size)

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

    def _create_cells_from_slots(self, slots: List[tuple[int, int]], generation: int) -> List[Cell]:
        """Create Cell objects from grid slot positions."""
        cells = []
        radius = CellGrid.CELL_RADIUS

        for slot in slots:
            row, col = slot
            x, y = self.grid.get_slot_position(row, col)
            cells.append(Cell(x, y, radius, generation=generation, slot=slot))

        return cells

    def _create_initial_cells(self, num_cells: int) -> List[Cell]:
        """Create initial cells at center grid slots."""
        slots = self.grid.get_center_slots(num_cells)
        return self._create_cells_from_slots(slots, generation=0)

    def _get_slots_for_cell_count(self, num_cells: int) -> List[tuple[int, int]]:
        """Get grid slots for a given number of cells."""
        return self.grid.get_slots_for_count(num_cells)

    def _get_cells_after_divisions(self, initial_count: int, num_divisions: int) -> List[Cell]:
        """Get the final cell layout after N divisions."""
        final_count = initial_count * (2 ** num_divisions)
        slots = self._get_slots_for_cell_count(final_count)
        return self._create_cells_from_slots(slots, generation=num_divisions)

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

        # Process each division cycle
        current_count = initial_cells_count

        for cycle in range(1, num_divisions + 1):
            generation = cycle - 1  # Generation before this division
            next_count = current_count * 2

            # Get slots for before and after this division
            slots_before = self._get_slots_for_cell_count(current_count)
            slots_after = self._get_slots_for_cell_count(next_count)

            # Create cells for animation
            cells_before = self._create_cells_from_slots(slots_before, generation)
            cells_after = self._create_cells_from_slots(slots_after, cycle)

            # Division animation for this cycle
            division_frames = self._animate_division_cycle(
                cells_before,
                cells_after,
                cycle,
                num_divisions
            )
            frames.extend(division_frames)

            # Update count for next cycle
            current_count = next_count

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
        cells_after: List[Cell],
        cycle: int,
        total_cycles: int
    ) -> List[Image.Image]:
        """Create frames for one division cycle (all cells divide simultaneously)."""
        frames = []
        division_frames = self.config.division_frames
        reorganize_frames = self.config.reorganize_frames

        cell_count = len(cells_before)
        new_count = len(cells_after)

        # Make copies so we don't modify originals
        cells_before = [cell.copy() for cell in cells_before]

        # Map each parent cell to its two daughter cells
        # Each parent at index i produces daughters at indices i*2 and i*2+1
        daughter_pairs = []
        for i in range(cell_count):
            d1 = cells_after[i * 2]
            d2 = cells_after[i * 2 + 1]
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
                    cell.radius,  # Fixed size in grid mode
                    d1.generation
                )
                temp_cell1.elongation = 1.8 - progress * 0.8  # Return to circle
                self._draw_single_cell(draw, temp_cell1)

                # Second daughter cell
                temp_cell2 = Cell(
                    cell.x + (d2.x - cell.x) * progress,
                    cell.y + (d2.y - cell.y) * progress,
                    cell.radius,  # Fixed size in grid mode
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
        for i in range(reorganize_frames):
            img = self._create_background()
            draw = ImageDraw.Draw(img)

            self._draw_cells(img, cells_after)
            self._draw_header(draw, f"Cycle {cycle}/{total_cycles} complete")
            self._draw_counter(draw, new_count)
            frames.append(img)

        return frames
