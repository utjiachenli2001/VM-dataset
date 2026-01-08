"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        DOMINO CHAIN GAP GENERATOR                             ║
║                                                                               ║
║  Generates domino chain gap analysis tasks.                                   ║
║  Task: Find where the chain reaction stops due to a gap.                      ║
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


class TaskGenerator(BaseGenerator):
    """
    Domino Chain Gap Analysis generator.

    Generates tasks where a chain of dominos has one gap that's too wide,
    stopping the chain reaction. The task is to identify which domino
    is the last to fall.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Calculate fall reach threshold
        self.fall_reach = config.domino_height * config.fall_reach_ratio

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one domino chain gap analysis task."""

        # Generate domino chain data
        task_data = self._generate_chain_data()

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_data, task_id)

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
    #  CHAIN GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_chain_data(self) -> dict:
        """Generate domino chain with one gap."""
        # Random number of dominos
        num_dominos = random.randint(self.config.min_dominos, self.config.max_dominos)

        # Choose gap position (not first, not last - somewhere in middle)
        # Gap is AFTER this domino index (0-indexed)
        gap_after = random.randint(1, num_dominos - 3)

        # Generate spacings
        spacings = []
        for i in range(num_dominos - 1):
            if i == gap_after:
                # This is the gap - too far
                spacing = random.randint(
                    self.config.gap_spacing_min,
                    self.config.gap_spacing_max
                )
            else:
                # Normal spacing
                spacing = random.randint(
                    self.config.normal_spacing_min,
                    self.config.normal_spacing_max
                )
            spacings.append(spacing)

        # Calculate x positions
        positions = []
        x = self.config.margin_left
        for i in range(num_dominos):
            positions.append(x)
            if i < len(spacings):
                x += spacings[i]

        # The answer is the domino index (1-indexed for display) that falls last
        # Gap is after index gap_after (0-indexed), so last fallen = gap_after + 1 (1-indexed)
        last_fallen_index = gap_after  # 0-indexed
        answer = last_fallen_index + 1  # 1-indexed for display

        return {
            "num_dominos": num_dominos,
            "positions": positions,
            "spacings": spacings,
            "gap_after": gap_after,  # 0-indexed
            "answer": answer,  # 1-indexed (domino number)
            "last_fallen_index": last_fallen_index,  # 0-indexed
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render initial state with all dominos standing."""
        img = Image.new('RGB', self.config.image_size, self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Draw ground
        self._draw_ground(draw)

        # Draw all dominos standing
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]
            self._draw_domino_standing(draw, x, i + 1, self.config.domino_color)

        # Draw "PUSH" arrow at first domino
        self._draw_push_indicator(draw, task_data["positions"][0])

        # Draw "?" question marker
        self._draw_question_marker(draw)

        # Draw title
        self._draw_title(draw, "Where does the chain stop?")

        return img

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render final state with fallen and standing dominos."""
        img = Image.new('RGB', self.config.image_size, self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Draw ground
        self._draw_ground(draw)

        # Draw dominos - fallen up to and including last_fallen_index, rest standing
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]
            if i <= task_data["last_fallen_index"]:
                # Fallen domino
                self._draw_domino_fallen(draw, x, i + 1, self.config.fallen_domino_color)
            else:
                # Standing domino
                self._draw_domino_standing(draw, x, i + 1, self.config.domino_color)

        # Draw gap indicator
        gap_x1 = task_data["positions"][task_data["gap_after"]]
        gap_x2 = task_data["positions"][task_data["gap_after"] + 1]
        self._draw_gap_indicator(draw, gap_x1, gap_x2)

        # Circle the last fallen domino
        last_x = task_data["positions"][task_data["last_fallen_index"]]
        self._draw_answer_circle(draw, last_x, task_data["answer"])

        # Draw answer title
        self._draw_title(draw, f"Chain stopped at Domino #{task_data['answer']}")

        return img

    def _draw_ground(self, draw: ImageDraw.Draw) -> None:
        """Draw ground line."""
        y = self.config.ground_y
        width = self.config.image_size[0]
        draw.line([(0, y), (width, y)], fill=self.config.ground_color, width=4)

        # Draw some texture lines
        for i in range(0, width, 40):
            draw.line([(i, y + 2), (i + 20, y + 2)], fill=self.config.ground_color, width=2)

    def _draw_domino_standing(
        self,
        draw: ImageDraw.Draw,
        x: int,
        number: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a standing domino at position x."""
        w = self.config.domino_width
        h = self.config.domino_height
        ground_y = self.config.ground_y

        # Rectangle from ground up
        left = x - w // 2
        top = ground_y - h
        right = x + w // 2
        bottom = ground_y

        # Draw domino body
        draw.rectangle([left, top, right, bottom], fill=color, outline=(20, 20, 20), width=2)

        # Draw number
        font = self._get_font(14)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = x - text_w // 2
        text_y = ground_y - h // 2 - text_h // 2
        draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)

    def _draw_domino_fallen(
        self,
        draw: ImageDraw.Draw,
        x: int,
        number: int,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a fallen domino (tilted to the right)."""
        w = self.config.domino_width
        h = self.config.domino_height
        ground_y = self.config.ground_y

        # Fallen domino tilted ~75 degrees to the right
        angle = 75  # degrees from vertical
        angle_rad = math.radians(angle)

        # Base point (bottom-left corner stays on ground)
        base_x = x - w // 2
        base_y = ground_y

        # Calculate corners of tilted rectangle
        # The domino pivots from its bottom-left corner
        dx = h * math.sin(angle_rad)
        dy = h * math.cos(angle_rad)

        # Four corners
        p1 = (base_x, base_y)  # bottom-left
        p2 = (base_x + dx, base_y - dy)  # top-left
        p3 = (base_x + dx + w * math.cos(angle_rad), base_y - dy + w * math.sin(angle_rad))  # top-right
        p4 = (base_x + w * math.cos(angle_rad), base_y + w * math.sin(angle_rad))  # bottom-right

        # Draw as polygon
        draw.polygon([p1, p2, p3, p4], fill=color, outline=(20, 20, 20))

        # Draw number at center of fallen domino
        center_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
        center_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
        font = self._get_font(12)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2), text, fill=(255, 255, 255), font=font)

    def _draw_push_indicator(self, draw: ImageDraw.Draw, x: int) -> None:
        """Draw PUSH arrow pointing at first domino."""
        arrow_y = self.config.ground_y - self.config.domino_height - 40
        arrow_start_x = x - 60
        arrow_end_x = x - self.config.domino_width // 2 - 5

        # Draw arrow line
        draw.line(
            [(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)],
            fill=self.config.text_color,
            width=3
        )

        # Draw arrowhead
        draw.polygon([
            (arrow_end_x, arrow_y),
            (arrow_end_x - 10, arrow_y - 6),
            (arrow_end_x - 10, arrow_y + 6)
        ], fill=self.config.text_color)

        # Draw "PUSH" text
        font = self._get_font(16)
        text = "PUSH"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            (arrow_start_x - text_w - 10, arrow_y - 10),
            text,
            fill=self.config.text_color,
            font=font
        )

    def _draw_question_marker(self, draw: ImageDraw.Draw) -> None:
        """Draw prominent ? marker."""
        # Position in upper right area
        x = self.config.image_size[0] - 80
        y = 60

        # Draw circle background
        radius = 30
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(255, 193, 7),  # Yellow
            outline=self.config.text_color,
            width=3
        )

        # Draw ?
        font = self._get_font(36)
        text = "?"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            (x - text_w // 2, y - text_h // 2 - 2),
            text,
            fill=self.config.text_color,
            font=font
        )

    def _draw_gap_indicator(self, draw: ImageDraw.Draw, x1: int, x2: int) -> None:
        """Draw TOO FAR indicator between two positions."""
        y = self.config.ground_y + 25

        # Draw bracket
        bracket_top = y - 5
        bracket_bottom = y + 5

        # Left bracket
        draw.line([(x1, bracket_top), (x1, bracket_bottom)], fill=self.config.gap_indicator_color, width=2)
        # Right bracket
        draw.line([(x2, bracket_top), (x2, bracket_bottom)], fill=self.config.gap_indicator_color, width=2)
        # Connecting line
        draw.line([(x1, y), (x2, y)], fill=self.config.gap_indicator_color, width=2)

        # Draw "TOO FAR!" text
        font = self._get_font(14)
        text = "TOO FAR!"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        center_x = (x1 + x2) // 2
        draw.text(
            (center_x - text_w // 2, y + 8),
            text,
            fill=self.config.gap_indicator_color,
            font=font
        )

    def _draw_answer_circle(self, draw: ImageDraw.Draw, x: int, answer: int) -> None:
        """Draw circle around the answer domino."""
        # Circle around the fallen domino area
        center_y = self.config.ground_y - 20
        radius = 45

        draw.ellipse(
            [x - radius, center_y - radius, x + radius + 30, center_y + radius],
            outline=self.config.highlight_color,
            width=4
        )

    def _draw_title(self, draw: ImageDraw.Draw, text: str) -> None:
        """Draw title text at top of image."""
        font = self._get_font(20)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (self.config.image_size[0] - text_w) // 2
        y = 20
        draw.text((x, y), text, fill=self.config.text_color, font=font)

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font of specified size."""
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

    def _generate_video(self, task_data: dict, task_id: str) -> Optional[str]:
        """Generate animation video showing chain reaction."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)

        return str(result) if result else None

    def _create_animation_frames(self, task_data: dict) -> List[Image.Image]:
        """Create animation frames for domino chain reaction."""
        frames = []

        # Phase 1: Hold initial state
        initial_frame = self._render_initial_state(task_data)
        for _ in range(15):
            frames.append(initial_frame)

        # Phase 2: Animate each domino falling up to the gap
        # Each domino has multiple frames showing it tilting
        fall_angles = [0, 15, 30, 45, 60, 75]  # Degrees from vertical

        for domino_idx in range(task_data["last_fallen_index"] + 1):
            # Animate this domino falling
            for angle in fall_angles:
                frame = self._render_animation_frame(task_data, domino_idx, angle)
                frames.append(frame)

            # Brief pause after each domino falls
            frames.append(frame)

        # Phase 3: Show gap measurement / approaching gap
        # Hold on the last fallen state
        last_fallen_frame = self._render_animation_frame(
            task_data,
            task_data["last_fallen_index"],
            75,
            show_measurement=True
        )
        for _ in range(20):
            frames.append(last_fallen_frame)

        # Phase 4: Show "TOO FAR" indicator
        gap_frame = self._render_animation_frame(
            task_data,
            task_data["last_fallen_index"],
            75,
            show_gap_indicator=True
        )
        for _ in range(20):
            frames.append(gap_frame)

        # Phase 5: Show final answer
        final_frame = self._render_final_state(task_data)
        for _ in range(30):
            frames.append(final_frame)

        return frames

    def _render_animation_frame(
        self,
        task_data: dict,
        falling_up_to: int,
        current_angle: float,
        show_measurement: bool = False,
        show_gap_indicator: bool = False
    ) -> Image.Image:
        """Render a single animation frame."""
        img = Image.new('RGB', self.config.image_size, self.config.background_color)
        draw = ImageDraw.Draw(img)

        # Draw ground
        self._draw_ground(draw)

        # Draw dominos
        for i in range(task_data["num_dominos"]):
            x = task_data["positions"][i]

            if i < falling_up_to:
                # Already fully fallen
                self._draw_domino_fallen(draw, x, i + 1, self.config.fallen_domino_color)
            elif i == falling_up_to:
                # Currently falling - draw at current angle
                self._draw_domino_at_angle(draw, x, i + 1, current_angle, self.config.fallen_domino_color)
            else:
                # Still standing
                self._draw_domino_standing(draw, x, i + 1, self.config.domino_color)

        # Show measurement if requested
        if show_measurement:
            self._draw_distance_measurement(draw, task_data)

        # Show gap indicator if requested
        if show_gap_indicator:
            gap_x1 = task_data["positions"][task_data["gap_after"]]
            gap_x2 = task_data["positions"][task_data["gap_after"] + 1]
            self._draw_gap_indicator(draw, gap_x1, gap_x2)

        # Draw title based on state
        if show_gap_indicator:
            self._draw_title(draw, "Gap detected - Chain stops!")
        elif show_measurement:
            self._draw_title(draw, "Measuring distance to next domino...")
        else:
            self._draw_title(draw, "Chain reaction in progress...")

        return img

    def _draw_domino_at_angle(
        self,
        draw: ImageDraw.Draw,
        x: int,
        number: int,
        angle: float,
        color: Tuple[int, int, int]
    ) -> None:
        """Draw a domino at a specific angle (0 = standing, 90 = flat)."""
        if angle <= 0:
            self._draw_domino_standing(draw, x, number, color)
            return
        if angle >= 75:
            self._draw_domino_fallen(draw, x, number, color)
            return

        w = self.config.domino_width
        h = self.config.domino_height
        ground_y = self.config.ground_y

        angle_rad = math.radians(angle)

        # Base point (bottom-left corner stays on ground)
        base_x = x - w // 2
        base_y = ground_y

        # Calculate corners of tilted rectangle
        dx = h * math.sin(angle_rad)
        dy = h * math.cos(angle_rad)

        p1 = (base_x, base_y)
        p2 = (base_x + dx, base_y - dy)
        p3 = (base_x + dx + w * math.cos(angle_rad), base_y - dy + w * math.sin(angle_rad))
        p4 = (base_x + w * math.cos(angle_rad), base_y + w * math.sin(angle_rad))

        draw.polygon([p1, p2, p3, p4], fill=color, outline=(20, 20, 20))

        # Draw number
        center_x = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
        center_y = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
        font = self._get_font(12)
        text = str(number)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text((center_x - text_w // 2, center_y - text_h // 2), text, fill=(255, 255, 255), font=font)

    def _draw_distance_measurement(self, draw: ImageDraw.Draw, task_data: dict) -> None:
        """Draw distance measurement between last fallen and next domino."""
        gap_idx = task_data["gap_after"]
        x1 = task_data["positions"][gap_idx]
        x2 = task_data["positions"][gap_idx + 1]

        # For fallen domino, tip is further right
        angle_rad = math.radians(75)
        tip_x = x1 - self.config.domino_width // 2 + self.config.domino_height * math.sin(angle_rad)

        y = self.config.ground_y - self.config.domino_height // 2

        # Draw measurement line
        draw.line([(tip_x, y), (x2, y)], fill=(255, 165, 0), width=2)

        # Draw end markers
        draw.line([(tip_x, y - 10), (tip_x, y + 10)], fill=(255, 165, 0), width=2)
        draw.line([(x2, y - 10), (x2, y + 10)], fill=(255, 165, 0), width=2)

        # Draw distance text
        distance = x2 - tip_x
        font = self._get_font(12)
        text = f"{distance}px"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        center_x = (tip_x + x2) // 2
        draw.text((center_x - text_w // 2, y - 25), text, fill=(255, 165, 0), font=font)
