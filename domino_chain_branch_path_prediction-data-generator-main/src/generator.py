"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN GENERATOR                              ║
║                                                                               ║
║  Generates Domino Chain Branch Path Prediction tasks.                         ║
║  Creates Y-shaped domino arrangements with optional blocked branches.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import math
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


# ══════════════════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Domino:
    """Represents a single domino in the chain."""
    id: str                          # "START", "T1", "A1", "B1", etc.
    x: float                         # X position (center)
    y: float                         # Y position (center)
    angle: float                     # Rotation angle in degrees (0 = upright)
    branch: str                      # "trunk", "A", "B"
    color: Tuple[int, int, int]      # RGB color
    fallen: bool = False             # Whether this domino has fallen
    fall_angle: float = 0.0          # Current fall angle during animation


@dataclass
class DominoChain:
    """Represents the complete Y-shaped domino chain."""
    trunk: List[Domino] = field(default_factory=list)
    branch_a: List[Domino] = field(default_factory=list)
    branch_b: List[Domino] = field(default_factory=list)
    blocked_branch: Optional[str] = None   # None, "A", or "B"
    block_after_index: int = -1            # Index after which the gap occurs

    def get_all_dominos(self) -> List[Domino]:
        """Get all dominos in order: trunk, branch_a, branch_b."""
        return self.trunk + self.branch_a + self.branch_b

    def get_fallen_dominos(self) -> List[str]:
        """Get IDs of all dominos that will fall."""
        fallen = [d.id for d in self.trunk]  # Trunk always falls

        if self.blocked_branch == "A":
            # Branch A is blocked
            fallen += [d.id for d in self.branch_a[:self.block_after_index + 1]]
            fallen += [d.id for d in self.branch_b]  # B falls completely
        elif self.blocked_branch == "B":
            # Branch B is blocked
            fallen += [d.id for d in self.branch_a]  # A falls completely
            fallen += [d.id for d in self.branch_b[:self.block_after_index + 1]]
        else:
            # No block - all fall
            fallen += [d.id for d in self.branch_a]
            fallen += [d.id for d in self.branch_b]

        return fallen

    def get_standing_dominos(self) -> List[str]:
        """Get IDs of dominos that remain standing."""
        fallen_set = set(self.get_fallen_dominos())
        all_ids = [d.id for d in self.get_all_dominos()]
        return [id for id in all_ids if id not in fallen_set]


# ══════════════════════════════════════════════════════════════════════════════
#  GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

class TaskGenerator(BaseGenerator):
    """
    Domino Chain Branch Path Prediction generator.

    Generates Y-shaped domino arrangements where pushing START causes
    a chain reaction that splits at a junction into two branches.
    Some puzzles have blocked branches where the chain stops.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one domino chain task pair."""

        # Generate the domino chain structure
        chain = self._generate_chain()

        # Determine task type for prompt selection
        task_type = "blocked" if chain.blocked_branch else "complete"

        # Render images
        first_image = self._render_chain(chain, show_fallen=False)
        final_image = self._render_chain(chain, show_fallen=True)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(chain, task_id)

        # Select prompt
        prompt = get_prompt(task_type)

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

    def _generate_chain(self) -> DominoChain:
        """Generate a random Y-shaped domino chain."""
        config = self.config

        # Determine structure sizes
        trunk_length = random.randint(config.trunk_length_min, config.trunk_length_max)
        branch_a_length = random.randint(config.branch_length_min, config.branch_length_max)
        branch_b_length = random.randint(config.branch_length_min, config.branch_length_max)

        # Determine if there's a blocked branch
        has_block = random.random() < config.block_probability
        blocked_branch = None
        block_after_index = -1

        if has_block:
            blocked_branch = random.choice(["A", "B"])
            branch_len = branch_a_length if blocked_branch == "A" else branch_b_length
            # Block somewhere in the middle (not first, not last)
            if branch_len > 2:
                block_after_index = random.randint(0, branch_len - 2)
            else:
                block_after_index = 0

        # Calculate positions
        canvas_w, canvas_h = config.image_size
        center_x = canvas_w // 2
        start_y = 60  # Top margin

        spacing = config.domino_spacing
        branch_angle_rad = math.radians(config.branch_angle)

        # Create trunk dominos
        trunk = []
        y = start_y

        # START domino
        trunk.append(Domino(
            id="START",
            x=center_x,
            y=y,
            angle=0,
            branch="trunk",
            color=config.start_color
        ))
        y += spacing

        # Additional trunk dominos
        for i in range(trunk_length):
            trunk.append(Domino(
                id=f"T{i + 1}",
                x=center_x,
                y=y,
                angle=0,
                branch="trunk",
                color=config.trunk_color
            ))
            y += spacing

        # Junction point (last trunk domino position)
        junction_x = center_x
        junction_y = y - spacing  # Back up to last trunk position

        # Create branch A (left)
        branch_a = []
        bx = junction_x
        by = junction_y + spacing

        for i in range(branch_a_length):
            # Move left and down
            bx -= spacing * math.sin(branch_angle_rad)
            by += spacing * math.cos(branch_angle_rad)

            branch_a.append(Domino(
                id=f"A{i + 1}",
                x=bx,
                y=by,
                angle=-config.branch_angle,  # Tilted left
                branch="A",
                color=config.branch_a_color
            ))

        # Create branch B (right)
        branch_b = []
        bx = junction_x
        by = junction_y + spacing

        for i in range(branch_b_length):
            # Move right and down
            bx += spacing * math.sin(branch_angle_rad)
            by += spacing * math.cos(branch_angle_rad)

            branch_b.append(Domino(
                id=f"B{i + 1}",
                x=bx,
                y=by,
                angle=config.branch_angle,  # Tilted right
                branch="B",
                color=config.branch_b_color
            ))

        return DominoChain(
            trunk=trunk,
            branch_a=branch_a,
            branch_b=branch_b,
            blocked_branch=blocked_branch,
            block_after_index=block_after_index
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_chain(
        self,
        chain: DominoChain,
        show_fallen: bool = False,
        animation_progress: Optional[dict] = None
    ) -> Image.Image:
        """
        Render the domino chain.

        Args:
            chain: The domino chain structure
            show_fallen: If True, show dominos in fallen state
            animation_progress: Optional dict mapping domino ID to fall progress (0-1)
        """
        config = self.config
        img = Image.new("RGB", config.image_size, config.background_color)
        draw = ImageDraw.Draw(img)

        # Get font for labels
        font = self._get_font(size=12)
        small_font = self._get_font(size=10)

        fallen_ids = set(chain.get_fallen_dominos()) if show_fallen else set()

        # Draw gap indicator if blocked
        if chain.blocked_branch:
            self._draw_gap_indicator(draw, chain, config)

        # Draw all dominos
        for domino in chain.get_all_dominos():
            is_fallen = domino.id in fallen_ids

            # Determine fall angle
            if animation_progress and domino.id in animation_progress:
                fall_progress = animation_progress[domino.id]
                fall_angle = fall_progress * 80  # Fall to 80 degrees
            elif is_fallen:
                fall_angle = 80  # Fully fallen
            else:
                fall_angle = 0  # Standing

            # Determine fall direction based on branch
            if domino.branch == "A":
                fall_direction = -1  # Fall left
            elif domino.branch == "B":
                fall_direction = 1   # Fall right
            else:
                fall_direction = 1   # Trunk falls forward (right)

            self._draw_domino(
                draw, domino, fall_angle * fall_direction,
                is_fallen, font, config
            )

        # Draw legend
        self._draw_legend(draw, chain, config, small_font)

        return img

    def _draw_domino(
        self,
        draw: ImageDraw.Draw,
        domino: Domino,
        fall_angle: float,
        is_fallen: bool,
        font: ImageFont.FreeTypeFont,
        config: TaskConfig
    ):
        """Draw a single domino."""
        w = config.domino_width
        h = config.domino_height

        # Calculate rotation
        total_angle = domino.angle + fall_angle
        angle_rad = math.radians(total_angle)

        # Rectangle corners before rotation (centered at origin)
        corners = [
            (-w / 2, -h / 2),
            (w / 2, -h / 2),
            (w / 2, h / 2),
            (-w / 2, h / 2)
        ]

        # Rotate and translate corners
        rotated_corners = []
        for cx, cy in corners:
            rx = cx * math.cos(angle_rad) - cy * math.sin(angle_rad)
            ry = cx * math.sin(angle_rad) + cy * math.cos(angle_rad)
            rotated_corners.append((domino.x + rx, domino.y + ry))

        # Determine color (dim if fallen)
        color = domino.color
        if is_fallen:
            # Darken the color slightly for fallen dominos
            color = tuple(int(c * config.fallen_alpha) for c in color)

        # Draw filled polygon
        draw.polygon(rotated_corners, fill=color, outline=(50, 50, 50), width=2)

        # Draw label
        label = domino.id
        bbox = draw.textbbox((0, 0), label, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Position label at center of domino
        text_x = domino.x - text_w / 2
        text_y = domino.y - text_h / 2

        # Text color (white for dark dominos, black for light)
        brightness = sum(color) / 3
        text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)

        draw.text((text_x, text_y), label, fill=text_color, font=font)

    def _draw_gap_indicator(
        self,
        draw: ImageDraw.Draw,
        chain: DominoChain,
        config: TaskConfig
    ):
        """Draw an indicator showing where the gap is."""
        if not chain.blocked_branch:
            return

        # Get the domino before the gap
        if chain.blocked_branch == "A" and chain.block_after_index < len(chain.branch_a) - 1:
            before = chain.branch_a[chain.block_after_index]
            after = chain.branch_a[chain.block_after_index + 1]
        elif chain.blocked_branch == "B" and chain.block_after_index < len(chain.branch_b) - 1:
            before = chain.branch_b[chain.block_after_index]
            after = chain.branch_b[chain.block_after_index + 1]
        else:
            return

        # Draw X mark between the two dominos
        mid_x = (before.x + after.x) / 2
        mid_y = (before.y + after.y) / 2
        size = 15

        draw.line(
            [(mid_x - size, mid_y - size), (mid_x + size, mid_y + size)],
            fill=(200, 50, 50), width=3
        )
        draw.line(
            [(mid_x - size, mid_y + size), (mid_x + size, mid_y - size)],
            fill=(200, 50, 50), width=3
        )

    def _draw_legend(
        self,
        draw: ImageDraw.Draw,
        chain: DominoChain,
        config: TaskConfig,
        font: ImageFont.FreeTypeFont
    ):
        """Draw a legend showing branch colors and fallen/standing info."""
        x = 10
        y = config.image_size[1] - 80

        # Branch A indicator
        draw.rectangle([x, y, x + 15, y + 15], fill=config.branch_a_color, outline=(0, 0, 0))
        draw.text((x + 20, y), "Branch A", fill=(0, 0, 0), font=font)

        # Branch B indicator
        y += 20
        draw.rectangle([x, y, x + 15, y + 15], fill=config.branch_b_color, outline=(0, 0, 0))
        draw.text((x + 20, y), "Branch B", fill=(0, 0, 0), font=font)

        # Block indicator if present
        if chain.blocked_branch:
            y += 20
            draw.text((x, y), f"Gap in Branch {chain.blocked_branch}", fill=(200, 50, 50), font=font)

    def _get_font(self, size: int = 12) -> ImageFont.FreeTypeFont:
        """Get a font for rendering text."""
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

    def _generate_video(self, chain: DominoChain, task_id: str) -> Optional[str]:
        """Generate animation video of the chain reaction."""
        if not self.video_generator:
            return None

        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(chain)

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_animation_frames(
        self,
        chain: DominoChain,
        hold_frames: int = 10,
        fall_frames_per_domino: int = 4
    ) -> List[Image.Image]:
        """Create animation frames showing the chain reaction."""
        frames = []

        # Get the order of falling dominos
        fallen_ids = chain.get_fallen_dominos()

        # Build the fall sequence
        # Trunk falls first, then branches fall in parallel
        trunk_ids = [d.id for d in chain.trunk]
        branch_a_ids = [d.id for d in chain.branch_a if d.id in fallen_ids]
        branch_b_ids = [d.id for d in chain.branch_b if d.id in fallen_ids]

        # Hold initial state
        initial_frame = self._render_chain(chain, show_fallen=False)
        for _ in range(hold_frames):
            frames.append(initial_frame)

        # Animate trunk falling
        animation_state = {}  # domino_id -> fall progress (0-1)

        for domino_id in trunk_ids:
            for f in range(fall_frames_per_domino):
                progress = (f + 1) / fall_frames_per_domino
                animation_state[domino_id] = progress
                frame = self._render_chain(chain, show_fallen=False, animation_progress=animation_state)
                frames.append(frame)

        # Animate branches falling in parallel
        max_branch_len = max(len(branch_a_ids), len(branch_b_ids))

        for i in range(max_branch_len):
            # Get dominos falling at this step
            falling_now = []
            if i < len(branch_a_ids):
                falling_now.append(branch_a_ids[i])
            if i < len(branch_b_ids):
                falling_now.append(branch_b_ids[i])

            # Animate these dominos falling together
            for f in range(fall_frames_per_domino):
                progress = (f + 1) / fall_frames_per_domino
                for domino_id in falling_now:
                    animation_state[domino_id] = progress
                frame = self._render_chain(chain, show_fallen=False, animation_progress=animation_state)
                frames.append(frame)

        # Hold final state
        final_frame = self._render_chain(chain, show_fallen=True)
        for _ in range(hold_frames * 2):
            frames.append(final_frame)

        return frames
