"""
LEGO Construction Assembly Task Generator

Generates LEGO instruction step images and animations showing:
- Current partially-built model
- New piece(s) to add (shown separately)
- Arrow indicators for attachment points
- Step number display
- Animation of piece placement
"""

import random
import tempfile
import math
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig, LEGO_COLORS, BRICK_TYPES
from .prompts import get_prompt


@dataclass
class Brick:
    """Represents a single LEGO brick."""
    brick_type: str  # "1x1", "1x2", "2x2", "2x4"
    color: str  # Color name from LEGO_COLORS
    x: int  # Grid position (studs)
    y: int  # Grid position (studs)
    z: int  # Height in plates (1 brick = 3 plates)
    rotation: int = 0  # 0 or 90 degrees

    @property
    def size(self) -> Tuple[int, int, int]:
        """Get brick dimensions (width, depth, height) in studs/plates."""
        w, d, h = BRICK_TYPES[self.brick_type]
        if self.rotation == 90:
            return (d, w, h)
        return (w, d, h)


@dataclass
class LegoModel:
    """A LEGO model defined as a sequence of brick placements."""
    name: str
    model_type: str  # "tower", "wall", "car", etc.
    bricks: List[Brick]  # Build sequence (order matters)

    def get_bricks_up_to_step(self, step: int) -> List[Brick]:
        """Get all bricks placed up to (but not including) the given step."""
        return self.bricks[:step]

    def get_brick_at_step(self, step: int) -> Optional[Brick]:
        """Get the brick placed at this step (0-indexed)."""
        if 0 <= step < len(self.bricks):
            return self.bricks[step]
        return None

    @property
    def total_steps(self) -> int:
        return len(self.bricks)


class TaskGenerator(BaseGenerator):
    """
    LEGO Construction Assembly task generator.

    Generates instruction-style images showing a construction step,
    with the current model state, new piece callout, and placement arrows.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Load hand-designed model templates
        self.templates = self._get_model_templates()

        # Isometric rendering settings
        self.stud_px = config.stud_size
        self.brick_h_px = config.brick_height_px

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one LEGO instruction step task."""

        # Select a random model and step
        model = random.choice(self.templates)
        step = random.randint(1, model.total_steps - 1)  # At least 1 brick placed

        # Get task data
        task_data = {
            "model": model,
            "step": step,
            "new_brick": model.get_brick_at_step(step),
            "existing_bricks": model.get_bricks_up_to_step(step),
            "type": model.model_type,
        }

        # Render images
        first_image = self._render_instruction_frame(task_data, show_new_brick_on_model=False)
        final_image = self._render_instruction_frame(task_data, show_new_brick_on_model=True)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_data, task_id)

        # Select prompt based on model type
        prompt = get_prompt(model.model_type)

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  ISOMETRIC RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _iso_project(self, x: float, y: float, z: float, origin: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert 3D grid coordinates to 2D isometric screen coordinates.

        Args:
            x, y: Horizontal grid position (in studs)
            z: Vertical position (in plates, 3 plates = 1 brick height)
            origin: Screen origin point (x, y)

        Returns:
            (screen_x, screen_y)
        """
        # Isometric projection
        iso_x = (x - y) * self.stud_px * 0.866  # cos(30°) ≈ 0.866
        iso_y = (x + y) * self.stud_px * 0.5 - z * (self.brick_h_px / 3)

        return (int(origin[0] + iso_x), int(origin[1] + iso_y))

    def _draw_brick(
        self,
        draw: ImageDraw.Draw,
        brick: Brick,
        origin: Tuple[int, int],
        highlight: bool = False,
        alpha: float = 1.0,
        offset: Tuple[float, float, float] = (0, 0, 0)
    ) -> None:
        """
        Draw a single LEGO brick in isometric view.

        Args:
            draw: PIL ImageDraw object
            brick: Brick to draw
            origin: Screen origin for isometric projection
            highlight: Whether to draw highlight effect
            alpha: Opacity (for animation)
            offset: Position offset for animation (x, y, z)
        """
        w, d, h = brick.size
        base_color = LEGO_COLORS.get(brick.color, (200, 200, 200))

        # Apply offset for animation
        bx = brick.x + offset[0]
        by = brick.y + offset[1]
        bz = brick.z + offset[2]

        # Calculate color variants for shading
        top_color = base_color
        left_color = tuple(max(0, int(c * 0.7)) for c in base_color)
        right_color = tuple(max(0, int(c * 0.85)) for c in base_color)

        if highlight:
            # Brighten for highlight
            top_color = tuple(min(255, int(c * 1.2)) for c in base_color)

        # Get corner points of the brick
        # Bottom face corners
        p0 = self._iso_project(bx, by, bz, origin)
        p1 = self._iso_project(bx + w, by, bz, origin)
        p2 = self._iso_project(bx + w, by + d, bz, origin)
        p3 = self._iso_project(bx, by + d, bz, origin)

        # Top face corners
        p4 = self._iso_project(bx, by, bz + h, origin)
        p5 = self._iso_project(bx + w, by, bz + h, origin)
        p6 = self._iso_project(bx + w, by + d, bz + h, origin)
        p7 = self._iso_project(bx, by + d, bz + h, origin)

        # Draw faces (back to front for proper occlusion)
        # Left face (visible from left)
        draw.polygon([p3, p7, p4, p0], fill=left_color, outline=(50, 50, 50))

        # Right face (visible from right)
        draw.polygon([p1, p5, p6, p2], fill=right_color, outline=(50, 50, 50))

        # Top face
        draw.polygon([p4, p5, p6, p7], fill=top_color, outline=(50, 50, 50))

        # Draw studs on top
        self._draw_studs(draw, brick, origin, offset, top_color)

        # Draw highlight glow if needed
        if highlight:
            self._draw_highlight_glow(draw, brick, origin, offset)

    def _draw_studs(
        self,
        draw: ImageDraw.Draw,
        brick: Brick,
        origin: Tuple[int, int],
        offset: Tuple[float, float, float],
        top_color: Tuple[int, int, int]
    ) -> None:
        """Draw the studs on top of a brick."""
        w, d, h = brick.size
        bx = brick.x + offset[0]
        by = brick.y + offset[1]
        bz = brick.z + offset[2]

        stud_radius = self.stud_px * 0.25

        for sx in range(w):
            for sy in range(d):
                # Stud center position
                cx = bx + sx + 0.5
                cy = by + sy + 0.5
                cz = bz + h

                screen_pos = self._iso_project(cx, cy, cz, origin)

                # Draw ellipse for isometric stud
                ellipse_w = stud_radius * 1.5
                ellipse_h = stud_radius * 0.8

                bbox = [
                    screen_pos[0] - ellipse_w,
                    screen_pos[1] - ellipse_h,
                    screen_pos[0] + ellipse_w,
                    screen_pos[1] + ellipse_h
                ]

                # Stud color (slightly lighter than top)
                stud_color = tuple(min(255, int(c * 1.1)) for c in top_color)
                draw.ellipse(bbox, fill=stud_color, outline=(50, 50, 50))

    def _draw_highlight_glow(
        self,
        draw: ImageDraw.Draw,
        brick: Brick,
        origin: Tuple[int, int],
        offset: Tuple[float, float, float]
    ) -> None:
        """Draw a highlight glow around a brick."""
        w, d, h = brick.size
        bx = brick.x + offset[0]
        by = brick.y + offset[1]
        bz = brick.z + offset[2]

        # Get top face center for glow
        cx = bx + w / 2
        cy = by + d / 2
        cz = bz + h

        center = self._iso_project(cx, cy, cz, origin)

        # Draw glow circles (yellow highlight)
        for r in range(3, 0, -1):
            glow_color = (255, 255, 100, 50 * r)
            radius = self.stud_px * (w + d) / 2 + r * 3
            bbox = [
                center[0] - radius,
                center[1] - radius * 0.5,
                center[0] + radius,
                center[1] + radius * 0.5
            ]
            # Note: PIL doesn't support alpha in polygon, so we just use outline
            draw.ellipse(bbox, outline=(255, 255, 100), width=2)

    def _draw_model(
        self,
        image: Image.Image,
        bricks: List[Brick],
        origin: Tuple[int, int],
        highlight_brick: Optional[Brick] = None,
        highlight_offset: Tuple[float, float, float] = (0, 0, 0)
    ) -> Image.Image:
        """
        Draw a complete model (list of bricks) in isometric view.

        Uses painter's algorithm: sort bricks by depth and draw back-to-front.
        """
        draw = ImageDraw.Draw(image)

        # Sort bricks by depth (back to front)
        # In isometric, further = higher x + y, lower z
        sorted_bricks = sorted(bricks, key=lambda b: (b.x + b.y, b.z))

        for brick in sorted_bricks:
            is_highlight = (highlight_brick is not None and
                           brick.x == highlight_brick.x and
                           brick.y == highlight_brick.y and
                           brick.z == highlight_brick.z)

            offset = highlight_offset if is_highlight else (0, 0, 0)
            self._draw_brick(draw, brick, origin, highlight=is_highlight, offset=offset)

        return image

    # ══════════════════════════════════════════════════════════════════════════
    #  INSTRUCTION LAYOUT
    # ══════════════════════════════════════════════════════════════════════════

    def _render_instruction_frame(
        self,
        task_data: Dict,
        show_new_brick_on_model: bool = False
    ) -> Image.Image:
        """
        Render a complete instruction frame with:
        - Step number
        - Parts callout (new brick)
        - Model view
        - Arrow indicator
        """
        width, height = self.config.image_size
        image = Image.new('RGB', (width, height), color=(245, 245, 240))
        draw = ImageDraw.Draw(image)

        step = task_data["step"]
        new_brick = task_data["new_brick"]
        existing_bricks = task_data["existing_bricks"]

        # Draw step number
        self._draw_step_number(draw, step + 1, (30, 20))

        # Draw parts callout (left side)
        callout_origin = (80, height // 3)
        self._draw_parts_callout(draw, new_brick, callout_origin)

        # Draw model (right side)
        model_origin = (width * 2 // 3, height * 2 // 3)

        if show_new_brick_on_model:
            # Final state: all bricks including new one
            all_bricks = existing_bricks + [new_brick]
            self._draw_model(image, all_bricks, model_origin, highlight_brick=new_brick)
        else:
            # Initial state: only existing bricks + arrow
            self._draw_model(image, existing_bricks, model_origin)

            # Draw arrow from callout to placement position
            if self.config.show_arrows:
                self._draw_placement_arrow(draw, new_brick, callout_origin, model_origin)

        # Draw border/frame
        draw.rectangle([5, 5, width - 6, height - 6], outline=(200, 200, 200), width=2)

        return image

    def _draw_step_number(
        self,
        draw: ImageDraw.Draw,
        step: int,
        position: Tuple[int, int]
    ) -> None:
        """Draw the step number in a circle."""
        x, y = position
        radius = 25

        # Draw circle background
        draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                     fill=(70, 70, 70), outline=(50, 50, 50), width=2)

        # Draw step number
        font = self._get_font(24)
        text = str(step)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        draw.text((x - tw // 2, y - th // 2 - 2), text, fill=(255, 255, 255), font=font)

    def _draw_parts_callout(
        self,
        draw: ImageDraw.Draw,
        brick: Brick,
        origin: Tuple[int, int]
    ) -> None:
        """Draw the parts callout showing the piece to add."""
        x, y = origin

        # Draw callout box background
        box_w, box_h = 100, 120
        draw.rectangle([x - 10, y - 10, x + box_w, y + box_h],
                       fill=(255, 255, 255), outline=(180, 180, 180), width=2)

        # Draw the brick (at origin, z=0)
        temp_brick = Brick(
            brick_type=brick.brick_type,
            color=brick.color,
            x=0, y=0, z=0,
            rotation=brick.rotation
        )

        callout_center = (x + box_w // 2, y + box_h // 2 - 10)
        self._draw_brick(draw, temp_brick, callout_center)

        # Draw quantity "×1"
        font = self._get_font(18)
        draw.text((x + box_w - 30, y + box_h - 25), "×1", fill=(50, 50, 50), font=font)

        # Draw brick type label
        font_small = self._get_font(12)
        draw.text((x + 5, y + box_h - 25), brick.brick_type, fill=(100, 100, 100), font=font_small)

    def _draw_placement_arrow(
        self,
        draw: ImageDraw.Draw,
        brick: Brick,
        callout_origin: Tuple[int, int],
        model_origin: Tuple[int, int]
    ) -> None:
        """Draw an arrow from callout to placement position."""
        # Arrow start (from callout)
        start_x = callout_origin[0] + 100
        start_y = callout_origin[1] + 50

        # Arrow end (to brick placement position)
        w, d, h = brick.size
        target = self._iso_project(
            brick.x + w / 2,
            brick.y + d / 2,
            brick.z + h + 2,  # Slightly above placement
            model_origin
        )

        # Draw curved arrow
        self._draw_curved_arrow(draw, (start_x, start_y), target)

    def _draw_curved_arrow(
        self,
        draw: ImageDraw.Draw,
        start: Tuple[int, int],
        end: Tuple[int, int],
        color: Tuple[int, int, int] = (50, 50, 50)
    ) -> None:
        """Draw a curved arrow from start to end."""
        # Control point for bezier curve
        mid_x = (start[0] + end[0]) // 2
        mid_y = min(start[1], end[1]) - 30

        # Draw curve as line segments
        points = []
        for t in range(21):
            t_norm = t / 20
            # Quadratic bezier
            x = (1 - t_norm) ** 2 * start[0] + 2 * (1 - t_norm) * t_norm * mid_x + t_norm ** 2 * end[0]
            y = (1 - t_norm) ** 2 * start[1] + 2 * (1 - t_norm) * t_norm * mid_y + t_norm ** 2 * end[1]
            points.append((int(x), int(y)))

        # Draw the curve
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=3)

        # Draw arrowhead
        self._draw_arrowhead(draw, points[-2], points[-1], color)

    def _draw_arrowhead(
        self,
        draw: ImageDraw.Draw,
        from_pt: Tuple[int, int],
        to_pt: Tuple[int, int],
        color: Tuple[int, int, int]
    ) -> None:
        """Draw an arrowhead at the end of a line."""
        angle = math.atan2(to_pt[1] - from_pt[1], to_pt[0] - from_pt[0])
        arrow_len = 15
        arrow_angle = math.pi / 6  # 30 degrees

        # Calculate arrowhead points
        p1 = (
            int(to_pt[0] - arrow_len * math.cos(angle - arrow_angle)),
            int(to_pt[1] - arrow_len * math.sin(angle - arrow_angle))
        )
        p2 = (
            int(to_pt[0] - arrow_len * math.cos(angle + arrow_angle)),
            int(to_pt[1] - arrow_len * math.sin(angle + arrow_angle))
        )

        draw.polygon([to_pt, p1, p2], fill=color)

    # ══════════════════════════════════════════════════════════════════════════
    #  ANIMATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, task_data: Dict, task_id: str) -> Optional[str]:
        """Generate ground truth video showing piece placement animation."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_animation_frames(self, task_data: Dict) -> List[Image.Image]:
        """
        Create animation frames for brick placement:
        1. Hold instruction layout
        2. Highlight piece
        3. Piece lifts and moves toward model
        4. Piece descends to attachment point
        5. Snap effect
        6. Confirmation flash
        7. Hold final state
        """
        frames = []

        step = task_data["step"]
        new_brick = task_data["new_brick"]
        existing_bricks = task_data["existing_bricks"]

        hold_frames = self.config.animation_hold_frames
        move_frames = self.config.animation_move_frames
        snap_frames = self.config.animation_snap_frames

        width, height = self.config.image_size
        model_origin = (width * 2 // 3, height * 2 // 3)
        callout_origin = (80, height // 3)

        # Phase 1: Hold initial instruction frame
        initial_frame = self._render_instruction_frame(task_data, show_new_brick_on_model=False)
        for _ in range(hold_frames):
            frames.append(initial_frame.copy())

        # Phase 2: Piece lifts from callout and moves to model
        # Calculate start and end positions
        start_pos = self._iso_project(0, 0, 3, (callout_origin[0] + 50, callout_origin[1] + 50))
        end_pos = self._iso_project(
            new_brick.x + new_brick.size[0] / 2,
            new_brick.y + new_brick.size[1] / 2,
            new_brick.z + new_brick.size[2] + 3,  # Above final position
            model_origin
        )

        for i in range(move_frames):
            progress = i / (move_frames - 1)
            # Ease in-out curve
            eased = 0.5 - 0.5 * math.cos(progress * math.pi)

            frame = self._render_animation_frame(
                task_data,
                progress=eased,
                phase="moving",
                model_origin=model_origin,
                callout_origin=callout_origin
            )
            frames.append(frame)

        # Phase 3: Piece descends to attachment point
        for i in range(snap_frames):
            progress = i / (snap_frames - 1)

            frame = self._render_animation_frame(
                task_data,
                progress=progress,
                phase="descending",
                model_origin=model_origin,
                callout_origin=callout_origin
            )
            frames.append(frame)

        # Phase 4: Snap effect (slight bounce)
        for i in range(snap_frames):
            progress = i / (snap_frames - 1)
            # Bounce: goes slightly down then back
            bounce = math.sin(progress * math.pi) * 0.1

            frame = self._render_animation_frame(
                task_data,
                progress=1.0,
                phase="snapping",
                bounce_offset=bounce,
                model_origin=model_origin,
                callout_origin=callout_origin
            )
            frames.append(frame)

        # Phase 5: Flash confirmation
        for i in range(4):
            highlight = (i % 2 == 0)
            frame = self._render_final_frame(task_data, model_origin, highlight=highlight)
            frames.append(frame)

        # Phase 6: Hold final state
        final_frame = self._render_final_frame(task_data, model_origin, highlight=False)
        for _ in range(hold_frames):
            frames.append(final_frame.copy())

        return frames

    def _render_animation_frame(
        self,
        task_data: Dict,
        progress: float,
        phase: str,
        model_origin: Tuple[int, int],
        callout_origin: Tuple[int, int],
        bounce_offset: float = 0
    ) -> Image.Image:
        """Render a single animation frame."""
        width, height = self.config.image_size
        image = Image.new('RGB', (width, height), color=(245, 245, 240))
        draw = ImageDraw.Draw(image)

        step = task_data["step"]
        new_brick = task_data["new_brick"]
        existing_bricks = task_data["existing_bricks"]

        # Draw step number
        self._draw_step_number(draw, step + 1, (30, 20))

        # Draw empty callout box (piece has left)
        if phase != "moving" or progress > 0.1:
            box_w, box_h = 100, 120
            x, y = callout_origin
            draw.rectangle([x - 10, y - 10, x + box_w, y + box_h],
                           fill=(255, 255, 255), outline=(180, 180, 180), width=2)

        # Draw existing model
        self._draw_model(image, existing_bricks, model_origin)

        # Draw moving piece based on phase
        if phase == "moving":
            # Interpolate position from callout to above model
            start_offset = (
                -new_brick.x + (callout_origin[0] - model_origin[0]) / self.stud_px,
                -new_brick.y + (callout_origin[1] - model_origin[1]) / self.stud_px * 2,
                5  # Start height
            )
            end_offset = (0, 0, 3)  # Above final position

            current_offset = (
                start_offset[0] + (end_offset[0] - start_offset[0]) * progress,
                start_offset[1] + (end_offset[1] - start_offset[1]) * progress,
                start_offset[2] + (end_offset[2] - start_offset[2]) * progress
            )

            self._draw_brick(draw, new_brick, model_origin, highlight=True, offset=current_offset)

        elif phase == "descending":
            # Move from above to final position
            z_offset = 3 * (1 - progress)
            self._draw_brick(draw, new_brick, model_origin, highlight=True, offset=(0, 0, z_offset))

        elif phase == "snapping":
            # Slight bounce effect
            z_offset = -bounce_offset * self.brick_h_px / self.stud_px
            self._draw_brick(draw, new_brick, model_origin, highlight=True, offset=(0, 0, z_offset))

        # Draw border
        draw.rectangle([5, 5, width - 6, height - 6], outline=(200, 200, 200), width=2)

        return image

    def _render_final_frame(
        self,
        task_data: Dict,
        model_origin: Tuple[int, int],
        highlight: bool = False
    ) -> Image.Image:
        """Render the final frame with completed step."""
        width, height = self.config.image_size
        image = Image.new('RGB', (width, height), color=(245, 245, 240))
        draw = ImageDraw.Draw(image)

        step = task_data["step"]
        new_brick = task_data["new_brick"]
        existing_bricks = task_data["existing_bricks"]

        # Draw step number with checkmark
        self._draw_step_number(draw, step + 1, (30, 20))

        # Draw complete model
        all_bricks = existing_bricks + [new_brick]
        highlight_brick = new_brick if highlight else None
        self._draw_model(image, all_bricks, model_origin, highlight_brick=highlight_brick)

        # Draw border
        draw.rectangle([5, 5, width - 6, height - 6], outline=(200, 200, 200), width=2)

        return image

    # ══════════════════════════════════════════════════════════════════════════
    #  UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font for text rendering."""
        font_names = [
            "arial.ttf",
            "Arial.ttf",
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
    #  MODEL TEMPLATES
    # ══════════════════════════════════════════════════════════════════════════

    def _get_model_templates(self) -> List[LegoModel]:
        """Define hand-designed LEGO model templates."""
        templates = []

        # Template 1: Simple Tower (5 bricks)
        templates.append(LegoModel(
            name="Simple Tower",
            model_type="tower",
            bricks=[
                Brick("2x2", "red", 0, 0, 0),
                Brick("2x2", "blue", 0, 0, 3),
                Brick("2x2", "yellow", 0, 0, 6),
                Brick("2x2", "green", 0, 0, 9),
                Brick("2x2", "orange", 0, 0, 12),
            ]
        ))

        # Template 2: L-shaped Wall (6 bricks)
        templates.append(LegoModel(
            name="L-Wall",
            model_type="wall",
            bricks=[
                Brick("2x4", "red", 0, 0, 0),
                Brick("2x4", "red", 0, 4, 0),
                Brick("2x2", "red", 0, 8, 0),
                Brick("2x4", "blue", 0, 0, 3),
                Brick("2x4", "blue", 0, 4, 3),
                Brick("2x2", "blue", 0, 8, 3),
            ]
        ))

        # Template 3: Simple Car Base (7 bricks)
        templates.append(LegoModel(
            name="Car Base",
            model_type="car",
            bricks=[
                Brick("2x4", "blue", 0, 0, 0),  # Base front
                Brick("2x4", "blue", 0, 4, 0),  # Base back
                Brick("1x2", "black", 0, 0, 3),  # Wheel area front-left
                Brick("1x2", "black", 0, 6, 3),  # Wheel area back-left
                Brick("1x2", "black", 1, 0, 3),  # Wheel area front-right
                Brick("1x2", "black", 1, 6, 3),  # Wheel area back-right
                Brick("2x2", "yellow", 0, 3, 3),  # Cabin
            ]
        ))

        # Template 4: Staircase (6 bricks)
        templates.append(LegoModel(
            name="Staircase",
            model_type="stairs",
            bricks=[
                Brick("2x4", "white", 0, 0, 0),
                Brick("2x4", "white", 0, 2, 3),
                Brick("2x4", "white", 0, 4, 6),
                Brick("2x2", "red", 0, 6, 9),
                Brick("2x2", "red", 0, 8, 12),
                Brick("1x2", "red", 0, 10, 15),
            ]
        ))

        # Template 5: Simple Bridge (8 bricks)
        templates.append(LegoModel(
            name="Bridge",
            model_type="bridge",
            bricks=[
                Brick("2x2", "green", 0, 0, 0),  # Left pillar base
                Brick("2x2", "green", 0, 0, 3),  # Left pillar top
                Brick("2x2", "green", 0, 6, 0),  # Right pillar base
                Brick("2x2", "green", 0, 6, 3),  # Right pillar top
                Brick("2x4", "yellow", 0, 1, 6),  # Span left
                Brick("2x4", "yellow", 0, 4, 6),  # Span right
                Brick("1x2", "orange", 0, 0, 6),  # Rail left
                Brick("1x2", "orange", 0, 7, 6),  # Rail right
            ]
        ))

        # Template 6: Mini House (10 bricks)
        templates.append(LegoModel(
            name="Mini House",
            model_type="wall",
            bricks=[
                Brick("2x4", "white", 0, 0, 0),  # Front wall base
                Brick("2x4", "white", 2, 0, 0),  # Back wall base
                Brick("2x4", "white", 0, 0, 3),  # Front wall top
                Brick("2x4", "white", 2, 0, 3),  # Back wall top
                Brick("1x2", "blue", 0, 1, 6),  # Window left
                Brick("1x2", "blue", 0, 3, 6),  # Window right
                Brick("2x2", "red", 1, 0, 6),  # Roof front-left
                Brick("2x2", "red", 1, 2, 6),  # Roof front-right
                Brick("1x2", "red", 1, 0, 9),  # Roof peak left
                Brick("1x2", "red", 1, 2, 9),  # Roof peak right
            ]
        ))

        return templates
