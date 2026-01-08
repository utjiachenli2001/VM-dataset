"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        BALANCE SCALE TASK GENERATOR                           ║
║                                                                               ║
║  Generates "Find Missing Weight" puzzles with balance scales.                 ║
║  One side has known weights, other side has known weights + one unknown (?).  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import random
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


# ══════════════════════════════════════════════════════════════════════════════
#  COLOR SCHEME
# ══════════════════════════════════════════════════════════════════════════════

COLORS = {
    "background": (255, 255, 255),       # White
    "beam": (68, 68, 68),                # Dark gray
    "fulcrum": (68, 68, 68),             # Dark gray
    "pan": (200, 200, 200),              # Light gray
    "pan_outline": (100, 100, 100),      # Medium gray
    "known_weight": (74, 144, 217),      # Blue
    "unknown_weight": (230, 126, 34),    # Orange
    "solved_weight": (39, 174, 96),      # Green
    "text_light": (255, 255, 255),       # White text
    "text_dark": (0, 0, 0),              # Black text
    "step_bg": (240, 240, 240),          # Light gray for step overlay
    "step_border": (180, 180, 180),      # Border for step overlay
}


class TaskGenerator(BaseGenerator):
    """
    Balance Scale missing weight puzzle generator.

    Generates puzzles where:
    - Left side (heavy): has objects with known weights, totaling more
    - Right side (light): has known weights + one unknown weight marked '?'
    - Goal: Find what '?' must be to balance the scale
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
        """Generate one balance scale puzzle."""

        # Generate puzzle data
        task_data = self._generate_task_data()

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)

        # Select prompt
        prompt = get_prompt("default")

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  PUZZLE GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_task_data(self) -> dict:
        """Generate a valid balance scale puzzle."""

        for _ in range(100):  # Try up to 100 times to generate valid puzzle
            # Pick total weight
            total_weight = random.randint(
                self.config.min_total_weight,
                self.config.max_total_weight
            )

            # Generate heavy side (left) weights
            num_heavy = random.randint(
                self.config.min_objects_per_side,
                self.config.max_objects_per_side
            )
            heavy_side = self._random_partition(total_weight, num_heavy)

            if not heavy_side:
                continue

            # Generate light side (right) - one slot reserved for unknown
            num_light = random.randint(
                self.config.min_objects_per_side,
                self.config.max_objects_per_side
            )
            num_known_light = num_light - 1  # Reserve one for '?'

            if num_known_light <= 0:
                num_known_light = 1
                num_light = 2

            # Known weights on light side must sum to less than total
            max_known_sum = total_weight - 1  # Leave at least 1 for unknown

            # Generate known weights for light side
            known_sum = random.randint(1, max(1, max_known_sum - 1))
            light_side_known = self._random_partition(known_sum, num_known_light)

            if not light_side_known:
                continue

            # Calculate unknown weight
            unknown_weight = total_weight - sum(light_side_known)

            if unknown_weight < 1:
                continue

            # Build solution steps
            heavy_sum_str = " + ".join(str(w) for w in heavy_side)
            known_sum_str = " + ".join(str(w) for w in light_side_known)

            solution_steps = [
                f"Heavy side: {heavy_sum_str} = {total_weight}kg",
                f"Light side: {known_sum_str} + ?",
                f"{sum(light_side_known)} + ? = {total_weight}",
                f"? = {total_weight} - {sum(light_side_known)}",
                f"? = {unknown_weight}kg"
            ]

            return {
                "heavy_side": heavy_side,
                "light_side_known": light_side_known,
                "unknown_weight": unknown_weight,
                "total_weight": total_weight,
                "equation": f"{sum(light_side_known)} + ? = {total_weight}",
                "solution_steps": solution_steps,
            }

        # Fallback if generation fails
        return self._get_fallback_puzzle()

    def _random_partition(self, total: int, num_parts: int) -> Optional[List[int]]:
        """Randomly partition total into num_parts positive integers."""
        if total < num_parts:
            return None

        # Use stars and bars method with minimum 1 per part
        remaining = total - num_parts  # Give 1 to each part first
        parts = [1] * num_parts

        # Distribute remaining randomly
        for _ in range(remaining):
            idx = random.randint(0, num_parts - 1)
            parts[idx] += 1

        random.shuffle(parts)
        return parts

    def _get_fallback_puzzle(self) -> dict:
        """Fallback puzzle if random generation fails."""
        return {
            "heavy_side": [5, 5],
            "light_side_known": [3],
            "unknown_weight": 7,
            "total_weight": 10,
            "equation": "3 + ? = 10",
            "solution_steps": [
                "Heavy side: 5 + 5 = 10kg",
                "Light side: 3 + ?",
                "3 + ? = 10",
                "? = 10 - 3",
                "? = 7kg"
            ],
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render tilted scale with '?' on light side."""
        return self._render_scale(
            task_data,
            tilt_angle=self.config.tilt_angle,
            show_unknown=True,
            solved=False
        )

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render balanced scale with solved weight."""
        return self._render_scale(
            task_data,
            tilt_angle=0,
            show_unknown=False,
            solved=True
        )

    def _render_scale(
        self,
        task_data: dict,
        tilt_angle: float = 0,
        show_unknown: bool = True,
        solved: bool = False
    ) -> Image.Image:
        """
        Render the balance scale.

        Args:
            task_data: Puzzle data
            tilt_angle: Degrees of tilt (positive = left side down)
            show_unknown: If True, show '?' on light side; if False, show solved value
            solved: If True, use green color for solved weight
        """
        width, height = self.config.image_size
        img = Image.new('RGB', (width, height), COLORS["background"])
        draw = ImageDraw.Draw(img)

        # Scale dimensions
        center_x = width // 2
        fulcrum_y = height // 3
        beam_length = int(width * 0.7)
        beam_height = 8
        pan_width = int(width * 0.25)
        pan_height = 12
        pan_drop = 60  # Distance from beam to pan

        # Calculate beam endpoints with tilt
        angle_rad = math.radians(tilt_angle)
        half_beam = beam_length // 2

        left_x = center_x - int(half_beam * math.cos(angle_rad))
        left_y = fulcrum_y + int(half_beam * math.sin(angle_rad))
        right_x = center_x + int(half_beam * math.cos(angle_rad))
        right_y = fulcrum_y - int(half_beam * math.sin(angle_rad))

        # Draw fulcrum (triangle)
        fulcrum_size = 20
        fulcrum_points = [
            (center_x, fulcrum_y - 5),
            (center_x - fulcrum_size, fulcrum_y + fulcrum_size),
            (center_x + fulcrum_size, fulcrum_y + fulcrum_size),
        ]
        draw.polygon(fulcrum_points, fill=COLORS["fulcrum"])

        # Draw beam
        beam_points = [
            (left_x, left_y - beam_height // 2),
            (right_x, right_y - beam_height // 2),
            (right_x, right_y + beam_height // 2),
            (left_x, left_y + beam_height // 2),
        ]
        draw.polygon(beam_points, fill=COLORS["beam"])

        # Draw support strings/lines
        left_pan_y = left_y + pan_drop
        right_pan_y = right_y + pan_drop
        draw.line([(left_x, left_y), (left_x, left_pan_y)], fill=COLORS["beam"], width=2)
        draw.line([(right_x, right_y), (right_x, right_pan_y)], fill=COLORS["beam"], width=2)

        # Draw pans
        self._draw_pan(draw, left_x, left_pan_y, pan_width, pan_height)
        self._draw_pan(draw, right_x, right_pan_y, pan_width, pan_height)

        # Draw weights on left (heavy) side
        heavy_weights = task_data["heavy_side"]
        self._draw_weights(
            draw, img, left_x, left_pan_y - pan_height,
            heavy_weights, pan_width,
            is_known=True
        )

        # Draw weights on right (light) side
        light_known = task_data["light_side_known"]
        unknown = task_data["unknown_weight"]

        # Combine known and unknown for display
        if show_unknown:
            light_display = light_known + ["?"]
        else:
            light_display = light_known + [unknown]

        self._draw_weights(
            draw, img, right_x, right_pan_y - pan_height,
            light_display, pan_width,
            is_known=False,
            solved=solved
        )

        # Draw labels
        font = self._get_font(16)
        if solved:
            # Draw "Balanced!" text
            balanced_text = "Balanced!"
            bbox = draw.textbbox((0, 0), balanced_text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(
                (center_x - text_width // 2, height - 40),
                balanced_text,
                fill=COLORS["solved_weight"],
                font=font
            )

        return img

    def _draw_pan(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        top_y: int,
        width: int,
        height: int
    ):
        """Draw a scale pan."""
        left = center_x - width // 2
        right = center_x + width // 2
        draw.rectangle(
            [left, top_y, right, top_y + height],
            fill=COLORS["pan"],
            outline=COLORS["pan_outline"],
            width=2
        )

    def _draw_weights(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        center_x: int,
        bottom_y: int,
        weights: List,
        pan_width: int,
        is_known: bool = True,
        solved: bool = False
    ):
        """Draw weight boxes on a pan."""
        if not weights:
            return

        num_weights = len(weights)
        box_width = min(40, (pan_width - 10) // num_weights)
        box_height = 35
        spacing = 5
        total_width = num_weights * box_width + (num_weights - 1) * spacing
        start_x = center_x - total_width // 2

        font = self._get_font(14)

        for i, weight in enumerate(weights):
            box_x = start_x + i * (box_width + spacing)
            box_y = bottom_y - box_height - 5

            # Determine color
            if weight == "?":
                color = COLORS["unknown_weight"]
            elif not is_known and i == len(weights) - 1 and solved:
                # Last weight on light side, solved state
                color = COLORS["solved_weight"]
            else:
                color = COLORS["known_weight"]

            # Draw box
            draw.rectangle(
                [box_x, box_y, box_x + box_width, box_y + box_height],
                fill=color,
                outline=(0, 0, 0),
                width=1
            )

            # Draw label
            label = str(weight) if weight != "?" else "?"
            if weight != "?" and isinstance(weight, int):
                label = f"{weight}kg"

            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = box_x + (box_width - text_width) // 2
            text_y = box_y + (box_height - text_height) // 2

            draw.text((text_x, text_y), label, fill=COLORS["text_light"], font=font)

    def _draw_step_overlay(
        self,
        img: Image.Image,
        step_text: str,
        step_number: int,
        total_steps: int
    ) -> Image.Image:
        """Draw step-by-step overlay on image."""
        img = img.copy()
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Overlay box dimensions
        box_width = int(width * 0.8)
        box_height = 50
        box_x = (width - box_width) // 2
        box_y = height - box_height - 20

        # Draw overlay background
        draw.rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            fill=COLORS["step_bg"],
            outline=COLORS["step_border"],
            width=2
        )

        # Draw step text
        font = self._get_font(18)
        step_label = f"Step {step_number}/{total_steps}: {step_text}"

        bbox = draw.textbbox((0, 0), step_label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = box_x + (box_width - text_width) // 2
        text_y = box_y + (box_height - (bbox[3] - bbox[1])) // 2

        draw.text((text_x, text_y), step_label, fill=COLORS["text_dark"], font=font)

        return img

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font for rendering text."""
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

    def _generate_video(
        self,
        first_image: Image.Image,
        final_image: Image.Image,
        task_id: str,
        task_data: dict
    ) -> str:
        """Generate ground truth video with step-by-step animation."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(
            frames,
            video_path
        )

        return str(result) if result else None

    def _create_animation_frames(self, task_data: dict) -> List[Image.Image]:
        """Create animation frames for the solution process."""
        frames = []
        hold_frames = 10
        step_frames = self.config.step_display_frames
        transition_frames = 20

        # Phase 1: Hold initial tilted state
        initial_frame = self._render_scale(
            task_data,
            tilt_angle=self.config.tilt_angle,
            show_unknown=True,
            solved=False
        )
        for _ in range(hold_frames):
            frames.append(initial_frame)

        # Phase 2: Show step-by-step solution
        if self.config.show_steps:
            solution_steps = task_data["solution_steps"]
            for i, step in enumerate(solution_steps):
                step_frame = self._draw_step_overlay(
                    initial_frame, step, i + 1, len(solution_steps)
                )
                for _ in range(step_frames):
                    frames.append(step_frame)

        # Phase 3: Transform '?' to solved value (on tilted scale)
        transform_frames = 10
        for i in range(transform_frames):
            progress = i / (transform_frames - 1) if transform_frames > 1 else 1.0

            # Still tilted, but showing solved value
            if progress > 0.5:
                frame = self._render_scale(
                    task_data,
                    tilt_angle=self.config.tilt_angle,
                    show_unknown=False,
                    solved=False  # Not fully solved color yet
                )
            else:
                frame = self._render_scale(
                    task_data,
                    tilt_angle=self.config.tilt_angle,
                    show_unknown=True,
                    solved=False
                )
            frames.append(frame)

        # Phase 4: Animate scale balancing (tilt -> horizontal)
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0

            # Ease-out animation
            eased_progress = 1 - (1 - progress) ** 2

            current_tilt = self.config.tilt_angle * (1 - eased_progress)

            frame = self._render_scale(
                task_data,
                tilt_angle=current_tilt,
                show_unknown=False,
                solved=(progress > 0.8)  # Turn green near the end
            )
            frames.append(frame)

        # Phase 5: Hold final balanced state
        final_frame = self._render_scale(
            task_data,
            tilt_angle=0,
            show_unknown=False,
            solved=True
        )
        for _ in range(hold_frames):
            frames.append(final_frame)

        return frames
