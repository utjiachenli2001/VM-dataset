"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BIO_GROWTH TASK GENERATOR                           ║
║                                                                               ║
║  Generates plant growth stage prediction tasks.                               ║
║  Each task shows a plant at one stage and asks "What's next?"                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
import math
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import (
    STAGES,
    get_prompt_for_transition,
    get_next_stage,
    get_stage_index,
)


class TaskGenerator(BaseGenerator):
    """
    Plant growth stage prediction task generator.

    Generates cross-section views of plants at different growth stages.
    The task is to predict/animate the transition to the next stage.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Pre-compute layout values
        self.width, self.height = config.image_size
        self.ground_y = int(self.height * config.ground_level)

        # Random colors for flowers/fruits (if not specified)
        self.flower_colors = [
            (255, 105, 180),  # Pink
            (255, 165, 0),    # Orange
            (238, 130, 238),  # Violet
            (255, 255, 0),    # Yellow
            (255, 0, 0),      # Red
            (148, 0, 211),    # Purple
        ]

        self.fruit_colors = [
            (255, 0, 0),      # Red (tomato/apple)
            (255, 165, 0),    # Orange
            (255, 215, 0),    # Gold
            (128, 0, 128),    # Purple (grape/plum)
            (0, 128, 0),      # Green (unripe)
        ]

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one plant growth task pair."""

        # Select a random current stage (0-6, not 7 since mature has no next)
        current_stage_idx = random.randint(0, len(STAGES) - 2)
        current_stage = STAGES[current_stage_idx]
        next_stage = STAGES[current_stage_idx + 1]

        # Generate plant parameters for this sample
        plant_params = self._generate_plant_params()

        # Render images
        first_image = self._render_stage(current_stage, plant_params, show_question=True)
        final_image = self._render_stage(next_stage, plant_params, show_question=False)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(
                current_stage, next_stage, plant_params, task_id
            )

        # Select prompt for this transition
        prompt = get_prompt_for_transition(current_stage, next_stage)

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path,
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  PLANT PARAMETER GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_plant_params(self) -> Dict[str, Any]:
        """Generate random parameters for a plant instance."""
        # Pick colors
        flower_color = self.config.flower_color or random.choice(self.flower_colors)
        fruit_color = self.config.fruit_color or random.choice(self.fruit_colors)

        return {
            "flower_color": flower_color,
            "fruit_color": fruit_color,
            "seed_x": self.width // 2,  # Center of image
            "variation": random.uniform(0.9, 1.1),  # Slight size variation
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_stage(
        self,
        stage: str,
        params: Dict[str, Any],
        show_question: bool = False
    ) -> Image.Image:
        """Render a plant at a specific growth stage."""
        img = Image.new("RGB", (self.width, self.height), self.config.sky_color)
        draw = ImageDraw.Draw(img)

        # Draw background layers
        self._draw_background(draw)

        # Draw plant at this stage
        stage_idx = get_stage_index(stage)
        self._draw_plant_at_stage(draw, stage_idx, params)

        # Draw labels
        self._draw_labels(draw, stage, show_question)

        return img

    def _draw_background(self, draw: ImageDraw.Draw) -> None:
        """Draw sky, grass line, and soil cross-section."""
        # Soil (underground)
        draw.rectangle(
            [0, self.ground_y, self.width, self.height],
            fill=self.config.soil_color
        )

        # Grass line on top of soil
        grass_height = 6
        draw.rectangle(
            [0, self.ground_y - grass_height // 2, self.width, self.ground_y + grass_height // 2],
            fill=self.config.grass_color
        )

        # Add some soil texture (dots)
        for _ in range(50):
            x = random.randint(0, self.width)
            y = random.randint(self.ground_y + 10, self.height - 10)
            r = random.randint(2, 4)
            darker_soil = tuple(max(0, c - 30) for c in self.config.soil_color)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=darker_soil)

    def _draw_plant_at_stage(
        self,
        draw: ImageDraw.Draw,
        stage_idx: int,
        params: Dict[str, Any]
    ) -> None:
        """Draw the plant based on growth stage index (0-7)."""
        center_x = params["seed_x"]
        variation = params["variation"]

        # Stage-specific parameters (normalized 0-1 progress values)
        stage_params = self._get_stage_params(stage_idx)

        # Draw components based on stage
        if stage_idx >= 0:  # Seed and above
            self._draw_seed(draw, center_x, stage_params)

        if stage_idx >= 1:  # Germination and above - roots
            self._draw_roots(draw, center_x, stage_params, variation)

        if stage_idx >= 2:  # Sprout and above - stem
            self._draw_stem(draw, center_x, stage_params, variation)

        if stage_idx >= 2:  # Sprout and above - cotyledons
            self._draw_cotyledons(draw, center_x, stage_params, variation)

        if stage_idx >= 3:  # Seedling and above - true leaves
            self._draw_leaves(draw, center_x, stage_params, variation)

        if stage_idx >= 5:  # Flowering and above - flowers
            self._draw_flowers(draw, center_x, stage_params, params["flower_color"], variation)

        if stage_idx >= 6:  # Fruiting and above - fruits
            self._draw_fruits(draw, center_x, stage_params, params["fruit_color"], variation)

    def _get_stage_params(self, stage_idx: int) -> Dict[str, float]:
        """Get normalized parameters for each growth stage."""
        # Parameters progress from 0.0 to 1.0 across stages
        params = {
            # 0: seed, 1: germination, 2: sprout, 3: seedling, 4: vegetative, 5: flowering, 6: fruiting, 7: mature
            "seed_visible": 1.0 if stage_idx <= 2 else max(0, 1.0 - (stage_idx - 2) * 0.5),
            "seed_cracked": 1.0 if stage_idx >= 1 else 0.0,
            "root_length": [0, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0][stage_idx],
            "root_branches": [0, 1, 2, 3, 4, 5, 5, 6][stage_idx],
            "stem_height": [0, 0, 0.15, 0.3, 0.5, 0.7, 0.8, 1.0][stage_idx],
            "stem_thickness": [0, 0, 2, 3, 5, 6, 7, 8][stage_idx],
            "cotyledon_size": [0, 0, 0.8, 0.6, 0.3, 0.1, 0, 0][stage_idx],
            "leaf_size": [0, 0, 0, 0.4, 0.7, 0.85, 0.95, 1.0][stage_idx],
            "leaf_count": [0, 0, 0, 2, 3, 3, 3, 3][stage_idx],
            "flower_bloom": [0, 0, 0, 0, 0, 1.0, 0.3, 0][stage_idx],
            "fruit_size": [0, 0, 0, 0, 0, 0, 0.6, 1.0][stage_idx],
        }
        return params

    # ══════════════════════════════════════════════════════════════════════════
    #  PLANT COMPONENT DRAWING
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_seed(self, draw: ImageDraw.Draw, center_x: int, params: Dict) -> None:
        """Draw the seed in the soil."""
        if params["seed_visible"] <= 0:
            return

        seed_y = self.ground_y + 30
        seed_w = int(20 * params["seed_visible"])
        seed_h = int(12 * params["seed_visible"])

        # Seed body (brown oval)
        seed_color = (139, 69, 19)  # Saddle brown
        draw.ellipse(
            [center_x - seed_w, seed_y - seed_h, center_x + seed_w, seed_y + seed_h],
            fill=seed_color,
            outline=(100, 50, 10),
            width=2
        )

        # Crack if germinating
        if params["seed_cracked"] > 0:
            crack_len = int(seed_w * params["seed_cracked"])
            draw.line(
                [center_x - crack_len, seed_y, center_x + crack_len, seed_y],
                fill=(60, 30, 5),
                width=2
            )

    def _draw_roots(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        variation: float
    ) -> None:
        """Draw the root system."""
        if params["root_length"] <= 0:
            return

        root_start_y = self.ground_y + 35
        max_root_depth = int(150 * variation)
        root_depth = int(max_root_depth * params["root_length"])

        root_color = self.config.root_color

        # Main taproot
        draw.line(
            [center_x, root_start_y, center_x, root_start_y + root_depth],
            fill=root_color,
            width=3
        )

        # Branch roots
        num_branches = int(params["root_branches"])
        for i in range(num_branches):
            branch_y = root_start_y + (root_depth * (i + 1)) // (num_branches + 1)
            branch_len = int(30 * params["root_length"] * variation * (1 - i * 0.1))

            # Left branch
            draw.line(
                [center_x, branch_y, center_x - branch_len, branch_y + branch_len // 2],
                fill=root_color,
                width=2
            )
            # Right branch
            draw.line(
                [center_x, branch_y, center_x + branch_len, branch_y + branch_len // 2],
                fill=root_color,
                width=2
            )

    def _draw_stem(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        variation: float
    ) -> None:
        """Draw the plant stem."""
        if params["stem_height"] <= 0:
            return

        max_stem_height = int(180 * variation)
        stem_height = int(max_stem_height * params["stem_height"])
        stem_thickness = max(2, int(params["stem_thickness"]))

        stem_top = self.ground_y - stem_height
        stem_bottom = self.ground_y

        # Draw stem as rectangle
        draw.rectangle(
            [
                center_x - stem_thickness // 2,
                stem_top,
                center_x + stem_thickness // 2,
                stem_bottom
            ],
            fill=self.config.stem_color
        )

    def _draw_cotyledons(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        variation: float
    ) -> None:
        """Draw seed leaves (cotyledons)."""
        if params["cotyledon_size"] <= 0 or params["stem_height"] <= 0:
            return

        max_stem_height = int(180 * variation)
        stem_height = int(max_stem_height * params["stem_height"])
        stem_top = self.ground_y - stem_height

        cot_size = int(15 * params["cotyledon_size"])
        cot_y = stem_top + 10

        # Two round cotyledons
        cot_color = (144, 238, 144)  # Light green
        # Left cotyledon
        draw.ellipse(
            [center_x - cot_size - 10, cot_y - cot_size // 2,
             center_x - 5, cot_y + cot_size // 2],
            fill=cot_color,
            outline=self.config.stem_color
        )
        # Right cotyledon
        draw.ellipse(
            [center_x + 5, cot_y - cot_size // 2,
             center_x + cot_size + 10, cot_y + cot_size // 2],
            fill=cot_color,
            outline=self.config.stem_color
        )

    def _draw_leaves(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        variation: float
    ) -> None:
        """Draw true leaves (simple 3-leaf pattern)."""
        if params["leaf_size"] <= 0:
            return

        max_stem_height = int(180 * variation)
        stem_height = int(max_stem_height * params["stem_height"])
        stem_top = self.ground_y - stem_height

        leaf_size = int(35 * params["leaf_size"] * variation)
        num_leaves = int(params["leaf_count"])

        leaf_color = self.config.leaf_color
        leaf_outline = tuple(max(0, c - 40) for c in leaf_color)

        # Position leaves along stem
        leaf_positions = []
        if num_leaves >= 1:
            leaf_positions.append((stem_top + 5, -1))  # Top left
        if num_leaves >= 2:
            leaf_positions.append((stem_top + 5, 1))   # Top right
        if num_leaves >= 3:
            leaf_positions.append((stem_top + 40, -1))  # Lower left

        for leaf_y, direction in leaf_positions:
            self._draw_single_leaf(
                draw, center_x, leaf_y, leaf_size, direction, leaf_color, leaf_outline
            )

    def _draw_single_leaf(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        leaf_y: int,
        size: int,
        direction: int,  # -1 for left, 1 for right
        fill_color: Tuple[int, int, int],
        outline_color: Tuple[int, int, int]
    ) -> None:
        """Draw a single leaf shape."""
        # Simple pointed oval leaf
        leaf_width = size
        leaf_height = int(size * 0.5)

        offset_x = direction * (size // 2 + 5)

        # Leaf body (ellipse)
        draw.ellipse(
            [
                center_x + offset_x - leaf_width // 2,
                leaf_y - leaf_height // 2,
                center_x + offset_x + leaf_width // 2,
                leaf_y + leaf_height // 2
            ],
            fill=fill_color,
            outline=outline_color,
            width=2
        )

        # Leaf stem connecting to main stem
        draw.line(
            [center_x, leaf_y, center_x + offset_x - direction * leaf_width // 2, leaf_y],
            fill=self.config.stem_color,
            width=2
        )

        # Center vein
        draw.line(
            [
                center_x + offset_x - direction * leaf_width // 3,
                leaf_y,
                center_x + offset_x + direction * leaf_width // 3,
                leaf_y
            ],
            fill=outline_color,
            width=1
        )

    def _draw_flowers(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        flower_color: Tuple[int, int, int],
        variation: float
    ) -> None:
        """Draw flowers at the top of the plant."""
        if params["flower_bloom"] <= 0:
            return

        max_stem_height = int(180 * variation)
        stem_height = int(max_stem_height * params["stem_height"])
        flower_y = self.ground_y - stem_height - 10

        bloom = params["flower_bloom"]
        flower_size = int(20 * bloom)

        if bloom > 0.5:
            # Full flower with petals
            num_petals = 5
            petal_size = flower_size

            for i in range(num_petals):
                angle = (2 * math.pi * i) / num_petals - math.pi / 2
                petal_x = center_x + int(petal_size * 0.7 * math.cos(angle))
                petal_y = flower_y + int(petal_size * 0.7 * math.sin(angle))

                draw.ellipse(
                    [
                        petal_x - petal_size // 2,
                        petal_y - petal_size // 2,
                        petal_x + petal_size // 2,
                        petal_y + petal_size // 2
                    ],
                    fill=flower_color,
                    outline=tuple(max(0, c - 50) for c in flower_color)
                )

            # Flower center
            center_size = flower_size // 3
            draw.ellipse(
                [
                    center_x - center_size,
                    flower_y - center_size,
                    center_x + center_size,
                    flower_y + center_size
                ],
                fill=(255, 223, 0),  # Gold center
                outline=(200, 150, 0)
            )
        else:
            # Bud (not fully opened)
            bud_h = int(15 * bloom * 2)
            bud_w = int(8 * bloom * 2)
            draw.ellipse(
                [center_x - bud_w, flower_y - bud_h, center_x + bud_w, flower_y],
                fill=flower_color,
                outline=tuple(max(0, c - 50) for c in flower_color)
            )

    def _draw_fruits(
        self,
        draw: ImageDraw.Draw,
        center_x: int,
        params: Dict,
        fruit_color: Tuple[int, int, int],
        variation: float
    ) -> None:
        """Draw fruits on the plant."""
        if params["fruit_size"] <= 0:
            return

        max_stem_height = int(180 * variation)
        stem_height = int(max_stem_height * params["stem_height"])
        fruit_y = self.ground_y - stem_height - 5

        fruit_size = int(25 * params["fruit_size"])

        # Main fruit
        draw.ellipse(
            [
                center_x - fruit_size,
                fruit_y - fruit_size,
                center_x + fruit_size,
                fruit_y + fruit_size
            ],
            fill=fruit_color,
            outline=tuple(max(0, c - 40) for c in fruit_color),
            width=2
        )

        # Highlight
        highlight_size = fruit_size // 3
        draw.ellipse(
            [
                center_x - fruit_size // 2,
                fruit_y - fruit_size // 2,
                center_x - fruit_size // 2 + highlight_size,
                fruit_y - fruit_size // 2 + highlight_size
            ],
            fill=(255, 255, 255, 128)
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  LABELS
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_labels(
        self,
        draw: ImageDraw.Draw,
        stage: str,
        show_question: bool
    ) -> None:
        """Draw stage label and question indicator."""
        font = self._get_font(20)
        small_font = self._get_font(16)

        # Stage label in bottom-left corner
        stage_text = f"Stage: {stage.capitalize()}"
        padding = 10
        text_bbox = draw.textbbox((0, 0), stage_text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        # Background box
        box_x = padding
        box_y = self.height - text_h - padding * 3
        draw.rectangle(
            [box_x, box_y, box_x + text_w + padding * 2, self.height - padding],
            fill=(255, 255, 255, 200),
            outline=(0, 0, 0)
        )
        draw.text(
            (box_x + padding, box_y + padding // 2),
            stage_text,
            fill=(0, 0, 0),
            font=font
        )

        # "What's next?" indicator in bottom-right corner
        if show_question:
            question_text = "What's next? →"
            q_bbox = draw.textbbox((0, 0), question_text, font=small_font)
            q_w = q_bbox[2] - q_bbox[0]
            q_h = q_bbox[3] - q_bbox[1]

            q_x = self.width - q_w - padding * 3
            q_y = self.height - q_h - padding * 3

            draw.rectangle(
                [q_x, q_y, self.width - padding, self.height - padding],
                fill=(255, 255, 200),
                outline=(200, 150, 0),
                width=2
            )
            draw.text(
                (q_x + padding, q_y + padding // 2),
                question_text,
                fill=(100, 80, 0),
                font=small_font
            )

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font at the specified size."""
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

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(
        self,
        current_stage: str,
        next_stage: str,
        params: Dict[str, Any],
        task_id: str
    ) -> Optional[str]:
        """Generate growth animation video."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_growth_animation_frames(current_stage, next_stage, params)

        result = self.video_generator.create_video_from_frames(frames, video_path)

        return str(result) if result else None

    def _create_growth_animation_frames(
        self,
        current_stage: str,
        next_stage: str,
        params: Dict[str, Any]
    ) -> List[Image.Image]:
        """Create frames showing growth transition between stages."""
        frames = []
        current_idx = get_stage_index(current_stage)
        next_idx = get_stage_index(next_stage)

        hold_frames = self.config.hold_frames
        transition_frames = self.config.transition_frames

        # Get stage parameters for interpolation
        current_params = self._get_stage_params(current_idx)
        next_params = self._get_stage_params(next_idx)

        # Hold initial frame
        first_frame = self._render_stage(current_stage, params, show_question=True)
        for _ in range(hold_frames):
            frames.append(first_frame)

        # Transition frames (interpolate between stages)
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0

            # Interpolate all parameters
            interp_params = {}
            for key in current_params:
                start_val = current_params[key]
                end_val = next_params[key]
                interp_params[key] = start_val + (end_val - start_val) * progress

            # Render frame with interpolated parameters
            frame = self._render_interpolated_frame(interp_params, params, progress)
            frames.append(frame)

        # Hold final frame
        final_frame = self._render_stage(next_stage, params, show_question=False)
        for _ in range(hold_frames):
            frames.append(final_frame)

        return frames

    def _render_interpolated_frame(
        self,
        stage_params: Dict[str, float],
        plant_params: Dict[str, Any],
        progress: float
    ) -> Image.Image:
        """Render a frame with interpolated stage parameters."""
        img = Image.new("RGB", (self.width, self.height), self.config.sky_color)
        draw = ImageDraw.Draw(img)

        # Draw background
        self._draw_background(draw)

        # Draw sun indicator if enabled (shows time passing)
        if self.config.show_time_indicator:
            self._draw_sun(draw, progress)

        # Draw plant components with interpolated parameters
        center_x = plant_params["seed_x"]
        variation = plant_params["variation"]

        # Use stage_params directly (already interpolated)
        if stage_params["seed_visible"] > 0:
            self._draw_seed(draw, center_x, stage_params)

        if stage_params["root_length"] > 0:
            self._draw_roots(draw, center_x, stage_params, variation)

        if stage_params["stem_height"] > 0:
            self._draw_stem(draw, center_x, stage_params, variation)
            self._draw_cotyledons(draw, center_x, stage_params, variation)

        if stage_params["leaf_size"] > 0:
            self._draw_leaves(draw, center_x, stage_params, variation)

        if stage_params["flower_bloom"] > 0:
            self._draw_flowers(
                draw, center_x, stage_params,
                plant_params["flower_color"], variation
            )

        if stage_params["fruit_size"] > 0:
            self._draw_fruits(
                draw, center_x, stage_params,
                plant_params["fruit_color"], variation
            )

        return img

    def _draw_sun(self, draw: ImageDraw.Draw, progress: float) -> None:
        """Draw a sun that moves across the sky to indicate time passing."""
        # Sun moves in an arc from left to right
        sun_radius = 25
        arc_height = 80

        # Calculate sun position along arc
        start_x = 60
        end_x = self.width - 60
        sun_x = start_x + (end_x - start_x) * progress

        # Parabolic arc for y position
        normalized_x = (progress - 0.5) * 2  # -1 to 1
        sun_y = 50 + arc_height * (normalized_x ** 2)

        # Sun body
        sun_color = (255, 223, 0)
        draw.ellipse(
            [sun_x - sun_radius, sun_y - sun_radius,
             sun_x + sun_radius, sun_y + sun_radius],
            fill=sun_color,
            outline=(255, 180, 0),
            width=2
        )

        # Sun rays
        ray_length = 15
        num_rays = 8
        for i in range(num_rays):
            angle = (2 * math.pi * i) / num_rays
            inner_x = sun_x + int((sun_radius + 3) * math.cos(angle))
            inner_y = sun_y + int((sun_radius + 3) * math.sin(angle))
            outer_x = sun_x + int((sun_radius + ray_length) * math.cos(angle))
            outer_y = sun_y + int((sun_radius + ray_length) * math.sin(angle))

            draw.line(
                [inner_x, inner_y, outer_x, outer_y],
                fill=sun_color,
                width=3
            )
