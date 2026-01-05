"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK GENERATOR                                 ║
║                                                                               ║
║  CUSTOMIZE THIS FILE to implement your data generation logic.                 ║
║  Task: Move 2 objects (circles) to their corresponding target ring positions. ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import random
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


class TaskGenerator(BaseGenerator):
    """
    Move-to-Target task generator (2 objects).

    Generates tasks where 2 objects (circles) must move to their corresponding
    target ring positions.

    Required:
        - generate_task_pair(task_id) -> TaskPair

    The base class provides:
        - self.config: Your TaskConfig instance
        - generate_dataset(): Loops and calls generate_task_pair() for each sample
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one task pair."""

        # Generate task data (positions for 2 objects and 2 targets)
        task_data = self._generate_task_data()

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)

        # Select prompt
        prompt = get_prompt()

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  TASK DATA GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_task_data(self) -> dict:
        """Generate random positions for 2 objects and 2 targets."""
        width, height = self.config.image_size
        margin = self.config.margin
        min_dist = self.config.min_distance
        max_dist = self.config.max_distance
        min_sep = self.config.min_separation

        # Valid placement area
        min_x = margin
        max_x = width - margin
        min_y = margin
        max_y = height - margin

        def distance(p1, p2):
            return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

        def is_valid_placement(positions, new_pos):
            """Check if new position is far enough from existing positions."""
            for pos in positions:
                if distance(pos, new_pos) < min_sep:
                    return False
            return True

        # Try to find valid positions
        for _ in range(200):
            # Generate positions for object 1
            obj1_x = random.randint(min_x, max_x)
            obj1_y = random.randint(min_y, max_y)
            obj1_pos = (obj1_x, obj1_y)

            # Generate target 1 position (within distance range from obj1)
            target1_x = random.randint(min_x, max_x)
            target1_y = random.randint(min_y, max_y)
            target1_pos = (target1_x, target1_y)

            dist1 = distance(obj1_pos, target1_pos)
            if not (min_dist <= dist1 <= max_dist):
                continue

            # Generate object 2 position (separated from obj1 and target1)
            obj2_x = random.randint(min_x, max_x)
            obj2_y = random.randint(min_y, max_y)
            obj2_pos = (obj2_x, obj2_y)

            if not is_valid_placement([obj1_pos, target1_pos], obj2_pos):
                continue

            # Generate target 2 position (separated from all others, within range of obj2)
            target2_x = random.randint(min_x, max_x)
            target2_y = random.randint(min_y, max_y)
            target2_pos = (target2_x, target2_y)

            dist2 = distance(obj2_pos, target2_pos)
            if not (min_dist <= dist2 <= max_dist):
                continue

            if not is_valid_placement([obj1_pos, target1_pos, obj2_pos], target2_pos):
                continue

            # All constraints satisfied
            return {
                "object_starts": [obj1_pos, obj2_pos],
                "target_positions": [target1_pos, target2_pos],
                "distances": [dist1, dist2]
            }

        # Fallback: place objects in corners
        obj1_pos = (margin + 60, margin + 60)
        target1_pos = (width - margin - 60, margin + 60)
        obj2_pos = (margin + 60, height - margin - 60)
        target2_pos = (width - margin - 60, height - margin - 60)

        return {
            "object_starts": [obj1_pos, obj2_pos],
            "target_positions": [target1_pos, target2_pos],
            "distances": [distance(obj1_pos, target1_pos), distance(obj2_pos, target2_pos)]
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render initial state: 2 objects at start, 2 target rings at destinations."""
        img = self._create_background()
        draw = ImageDraw.Draw(img)

        obj_positions = task_data["object_starts"]
        target_positions = task_data["target_positions"]

        # Draw target rings (dashed circles)
        for i, target_pos in enumerate(target_positions):
            ring_color = self.config.ring_colors[i]
            self._draw_dashed_circle(draw, target_pos, self.config.target_ring_radius, ring_color)

        # Draw objects (solid circles with gradient effect)
        for i, obj_pos in enumerate(obj_positions):
            obj_color = self.config.object_colors[i]
            self._draw_object(draw, obj_pos, obj_color)

        return img

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render final state: 2 objects at their target positions."""
        img = self._create_background()
        draw = ImageDraw.Draw(img)

        target_positions = task_data["target_positions"]

        # Draw target rings (dashed circles)
        for i, target_pos in enumerate(target_positions):
            ring_color = self.config.ring_colors[i]
            self._draw_dashed_circle(draw, target_pos, self.config.target_ring_radius, ring_color)

        # Draw objects at target positions
        for i, target_pos in enumerate(target_positions):
            obj_color = self.config.object_colors[i]
            self._draw_object(draw, target_pos, obj_color)

        return img

    def _create_background(self) -> Image.Image:
        """Create background image."""
        return Image.new('RGB', self.config.image_size, self.config.bg_color)

    def _draw_object(self, draw: ImageDraw.Draw, center: tuple[int, int], color: tuple[int, int, int]) -> None:
        """Draw the movable object (solid circle with simple 3D effect)."""
        cx, cy = center
        r = self.config.object_radius

        # Draw main circle
        outline_color = (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30))
        draw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=color,
            outline=outline_color,
            width=2
        )

        # Add highlight for 3D effect (small white ellipse offset)
        highlight_r = r // 3
        highlight_offset = r // 3
        highlight_color = (
            min(255, color[0] + 60),
            min(255, color[1] + 60),
            min(255, color[2] + 60)
        )
        draw.ellipse(
            [cx - highlight_offset - highlight_r // 2,
             cy - highlight_offset - highlight_r // 2,
             cx - highlight_offset + highlight_r // 2,
             cy - highlight_offset + highlight_r // 2],
            fill=highlight_color
        )

    def _draw_dashed_circle(
        self,
        draw: ImageDraw.Draw,
        center: tuple[int, int],
        radius: int,
        color: tuple[int, int, int]
    ) -> None:
        """Draw a dashed circle (target ring)."""
        cx, cy = center
        dash_len = self.config.ring_dash_length
        gap_len = self.config.ring_gap_length

        # Calculate circumference and number of segments
        circumference = 2 * math.pi * radius
        segment_len = dash_len + gap_len
        num_segments = int(circumference / segment_len)

        # Draw dashes
        for i in range(num_segments):
            # Start and end angles for this dash
            start_angle = (i * segment_len / circumference) * 360
            end_angle = ((i * segment_len + dash_len) / circumference) * 360

            # Convert to radians
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)

            # Calculate start and end points
            x1 = cx + radius * math.cos(start_rad)
            y1 = cy + radius * math.sin(start_rad)
            x2 = cx + radius * math.cos(end_rad)
            y2 = cy + radius * math.sin(end_rad)

            # Draw line segment (approximation of arc)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=3)

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
        """Generate ground truth video with both objects moving to targets."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        # Create animation frames
        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(
            frames,
            video_path
        )

        return str(result) if result else None

    def _create_animation_frames(
        self,
        task_data: dict,
        hold_frames: int = 5,
        transition_frames: int = 25
    ) -> list:
        """
        Create animation frames where both objects move from start to target simultaneously.

        Args:
            task_data: Contains object_starts and target_positions
            hold_frames: Frames to hold at start and end
            transition_frames: Frames for the movement animation
        """
        frames = []

        start_positions = task_data["object_starts"]
        end_positions = task_data["target_positions"]

        # Hold initial position
        initial_frame = self._render_frame_at_positions(start_positions, end_positions)
        for _ in range(hold_frames):
            frames.append(initial_frame)

        # Transition frames (linear interpolation for both objects)
        for i in range(transition_frames):
            progress = i / (transition_frames - 1) if transition_frames > 1 else 1.0

            # Interpolate both objects
            current_positions = []
            for j in range(2):
                start_pos = start_positions[j]
                end_pos = end_positions[j]
                current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
                current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
                current_positions.append((int(current_x), int(current_y)))

            frame = self._render_frame_at_positions(current_positions, end_positions)
            frames.append(frame)

        # Hold final position
        final_frame = self._render_frame_at_positions(end_positions, end_positions)
        for _ in range(hold_frames):
            frames.append(final_frame)

        return frames

    def _render_frame_at_positions(
        self,
        object_positions: list[tuple[int, int]],
        target_positions: list[tuple[int, int]]
    ) -> Image.Image:
        """Render a single frame with objects at given positions."""
        img = self._create_background()
        draw = ImageDraw.Draw(img)

        # Draw target rings (always at target positions)
        for i, target_pos in enumerate(target_positions):
            ring_color = self.config.ring_colors[i]
            self._draw_dashed_circle(draw, target_pos, self.config.target_ring_radius, ring_color)

        # Draw objects at current positions
        for i, obj_pos in enumerate(object_positions):
            obj_color = self.config.object_colors[i]
            self._draw_object(draw, obj_pos, obj_color)

        return img
