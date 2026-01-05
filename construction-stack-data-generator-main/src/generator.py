"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK GENERATOR                                 ║
║                                                                               ║
║  Construction_Stack_1: Block Rearrangement Task Generator                     ║
║  Generates block stacking puzzles with optimal solutions.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
from pathlib import Path
from typing import Optional
from collections import deque
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


# Type aliases for clarity
Block = int  # Block is represented by its color index
Stack = list[Block]  # Stack is a list of blocks (bottom to top)
State = tuple[tuple[Block, ...], ...]  # Immutable state for hashing
Move = tuple[int, int]  # (from_stack_idx, to_stack_idx)


class TaskGenerator(BaseGenerator):
    """
    Block Stacking Task Generator.

    Generates puzzles where colored blocks must be rearranged from
    an initial configuration to a target configuration using
    Tower of Hanoi-style rules (only move top block).
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Parse colors
        self.colors = [self._hex_to_rgb(c) for c in config.block_colors]
        self.color_names = config.block_color_names

        # Layout constants
        self._calculate_layout()

    def _calculate_layout(self):
        """Calculate layout dimensions based on config."""
        width, height = self.config.image_size

        # We show CURRENT on left, TARGET on right
        # Each section has num_stacks stacks
        self.section_width = width // 2
        self.stack_spacing = self.section_width // (self.config.num_stacks + 1)

        # Ground level (where blocks sit)
        self.ground_y = height - 80

        # Lift height (above all blocks)
        max_stack_height = self.config.max_blocks * self.config.block_height
        self.lift_y = self.ground_y - max_stack_height - 60

        # Label positions
        self.label_y = 30

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one block stacking task pair."""

        # Generate task data
        task_data = self._generate_task_data()

        # Render images
        first_image = self._render_state(
            task_data["initial_state"],
            task_data["target_state"],
            move_count=0,
            optimal_moves=task_data["optimal_moves"]
        )
        final_image = self._render_state(
            task_data["target_state"],  # Final state matches target
            task_data["target_state"],
            move_count=task_data["optimal_moves"],
            optimal_moves=task_data["optimal_moves"],
            is_solved=True
        )

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(task_data, task_id)

        # Select prompt based on difficulty
        difficulty = task_data.get("difficulty", "default")
        prompt = get_prompt(difficulty)

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  TASK GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_task_data(self) -> dict:
        """Generate a block stacking puzzle with solution."""

        num_blocks = random.randint(self.config.min_blocks, self.config.max_blocks)
        num_stacks = self.config.num_stacks

        # Select colors for blocks
        block_colors = random.sample(range(len(self.colors)), num_blocks)

        # Generate initial and target states
        # Ensure they are different and solvable
        for _ in range(100):  # Max attempts
            initial_state = self._generate_random_state(block_colors, num_stacks)
            target_state = self._generate_random_state(block_colors, num_stacks)

            # Ensure states are different
            if initial_state == target_state:
                continue

            # Find optimal solution
            solution = self._solve_puzzle(initial_state, target_state, num_stacks)

            if solution is not None:
                # Determine difficulty based on move count
                num_moves = len(solution)
                if num_moves <= 3:
                    difficulty = "easy"
                elif num_moves <= 6:
                    difficulty = "medium"
                else:
                    difficulty = "hard"

                return {
                    "initial_state": initial_state,
                    "target_state": target_state,
                    "solution": solution,
                    "optimal_moves": num_moves,
                    "difficulty": difficulty,
                    "block_colors": block_colors,
                    "num_stacks": num_stacks,
                }

        # Fallback: simple swap puzzle
        return self._generate_fallback_puzzle(num_blocks, num_stacks)

    def _generate_random_state(self, blocks: list[int], num_stacks: int) -> State:
        """Generate a random valid state with given blocks distributed across stacks."""
        stacks = [[] for _ in range(num_stacks)]

        # Randomly distribute blocks across stacks
        shuffled_blocks = blocks.copy()
        random.shuffle(shuffled_blocks)

        for block in shuffled_blocks:
            stack_idx = random.randint(0, num_stacks - 1)
            stacks[stack_idx].append(block)

        return tuple(tuple(s) for s in stacks)

    def _generate_fallback_puzzle(self, num_blocks: int, num_stacks: int) -> dict:
        """Generate a simple fallback puzzle."""
        blocks = list(range(num_blocks))

        # Initial: all blocks in first stack
        initial_stacks = [blocks.copy()] + [[] for _ in range(num_stacks - 1)]
        initial_state = tuple(tuple(s) for s in initial_stacks)

        # Target: all blocks in last stack (reversed)
        target_stacks = [[] for _ in range(num_stacks - 1)] + [list(reversed(blocks))]
        target_state = tuple(tuple(s) for s in target_stacks)

        solution = self._solve_puzzle(initial_state, target_state, num_stacks)

        return {
            "initial_state": initial_state,
            "target_state": target_state,
            "solution": solution or [],
            "optimal_moves": len(solution) if solution else 0,
            "difficulty": "medium",
            "block_colors": blocks,
            "num_stacks": num_stacks,
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  PUZZLE SOLVER (BFS for optimal solution)
    # ══════════════════════════════════════════════════════════════════════════

    def _solve_puzzle(
        self,
        initial: State,
        target: State,
        num_stacks: int,
        max_moves: int = 20
    ) -> Optional[list[Move]]:
        """
        Find optimal solution using BFS.

        Returns list of moves (from_stack, to_stack) or None if unsolvable.
        """
        if initial == target:
            return []

        # BFS
        queue = deque([(initial, [])])
        visited = {initial}

        while queue:
            current_state, moves = queue.popleft()

            if len(moves) >= max_moves:
                continue

            # Try all possible moves
            for from_idx in range(num_stacks):
                if not current_state[from_idx]:  # Empty stack
                    continue

                for to_idx in range(num_stacks):
                    if from_idx == to_idx:
                        continue

                    # Make move
                    new_state = self._apply_move(current_state, from_idx, to_idx)

                    if new_state == target:
                        return moves + [(from_idx, to_idx)]

                    if new_state not in visited:
                        visited.add(new_state)
                        queue.append((new_state, moves + [(from_idx, to_idx)]))

        return None  # No solution found within max_moves

    def _apply_move(self, state: State, from_idx: int, to_idx: int) -> State:
        """Apply a move and return new state."""
        stacks = [list(s) for s in state]

        if stacks[from_idx]:
            block = stacks[from_idx].pop()
            stacks[to_idx].append(block)

        return tuple(tuple(s) for s in stacks)

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_state(
        self,
        current_state: State,
        target_state: State,
        move_count: int = 0,
        optimal_moves: int = 0,
        is_solved: bool = False,
        moving_block: Optional[dict] = None
    ) -> Image.Image:
        """
        Render the current puzzle state.

        Args:
            current_state: Current arrangement of blocks
            target_state: Target arrangement to achieve
            move_count: Current move counter
            optimal_moves: Optimal number of moves
            is_solved: Whether puzzle is solved
            moving_block: Optional dict with block animation info
        """
        width, height = self.config.image_size
        img = Image.new("RGB", (width, height), color=(245, 245, 250))
        draw = ImageDraw.Draw(img)

        # Draw divider line
        mid_x = width // 2
        draw.line([(mid_x, 50), (mid_x, height - 50)], fill=(200, 200, 200), width=2)

        # Draw labels
        font = self._get_font(24)
        small_font = self._get_font(16)

        # CURRENT label
        draw.text((mid_x // 2, self.label_y), "CURRENT", fill=(50, 50, 50),
                  font=font, anchor="mm")

        # TARGET label
        draw.text((mid_x + mid_x // 2, self.label_y), "TARGET", fill=(50, 50, 50),
                  font=font, anchor="mm")

        # Draw ground lines
        self._draw_ground(draw, 0, self.section_width)
        self._draw_ground(draw, mid_x, width)

        # Draw current state (left side)
        self._draw_stacks(draw, current_state, x_offset=0)

        # Draw target state (right side)
        self._draw_stacks(draw, target_state, x_offset=mid_x)

        # Draw moving block if present
        if moving_block:
            self._draw_block(
                draw,
                moving_block["color_idx"],
                moving_block["x"],
                moving_block["y"]
            )

        # Draw move counter
        counter_text = f"Moves: {move_count}"
        if is_solved:
            counter_text = f"Solved in {move_count} moves (Optimal: {optimal_moves})"
            draw.text((width // 2, height - 30), counter_text,
                      fill=(34, 139, 34), font=font, anchor="mm")
        else:
            draw.text((width // 2, height - 30), counter_text,
                      fill=(50, 50, 50), font=small_font, anchor="mm")

        return img

    def _draw_ground(self, draw: ImageDraw.Draw, x_start: int, x_end: int):
        """Draw ground lines for stacks."""
        y = self.ground_y + 5
        padding = 20

        for i in range(self.config.num_stacks):
            x_center = x_start + self.stack_spacing * (i + 1)
            half_width = self.config.block_width // 2 + 10

            # Draw platform
            draw.rectangle(
                [x_center - half_width, y, x_center + half_width, y + 8],
                fill=(120, 120, 130)
            )

    def _draw_stacks(self, draw: ImageDraw.Draw, state: State, x_offset: int):
        """Draw all stacks in a state."""
        for stack_idx, stack in enumerate(state):
            x_center = x_offset + self.stack_spacing * (stack_idx + 1)

            for block_idx, color_idx in enumerate(stack):
                y = self.ground_y - (block_idx + 1) * self.config.block_height
                self._draw_block(draw, color_idx, x_center, y)

    def _draw_block(
        self,
        draw: ImageDraw.Draw,
        color_idx: int,
        x_center: int,
        y_top: int
    ):
        """Draw a single block."""
        half_width = self.config.block_width // 2
        block_height = self.config.block_height

        # Block rectangle
        x0 = x_center - half_width
        y0 = y_top
        x1 = x_center + half_width
        y1 = y_top + block_height

        color = self.colors[color_idx]

        # Draw block with slight 3D effect
        # Main block
        draw.rectangle([x0, y0, x1, y1], fill=color, outline=(50, 50, 50), width=2)

        # Highlight (top edge)
        highlight = tuple(min(255, c + 40) for c in color)
        draw.line([(x0 + 2, y0 + 2), (x1 - 2, y0 + 2)], fill=highlight, width=2)

        # Shadow (bottom edge)
        shadow = tuple(max(0, c - 40) for c in color)
        draw.line([(x0 + 2, y1 - 2), (x1 - 2, y1 - 2)], fill=shadow, width=2)

        # Draw color initial in center
        font = self._get_font(18)
        label = self.color_names[color_idx][0]  # First letter
        text_color = (255, 255, 255) if sum(color) < 400 else (30, 30, 30)
        draw.text(
            (x_center, y_top + block_height // 2),
            label,
            fill=text_color,
            font=font,
            anchor="mm"
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, task_data: dict, task_id: str) -> Optional[str]:
        """Generate ground truth video showing the solution."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        if not frames:
            return None

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_animation_frames(self, task_data: dict) -> list[Image.Image]:
        """Create all animation frames for the solution."""
        frames = []

        initial_state = task_data["initial_state"]
        target_state = task_data["target_state"]
        solution = task_data["solution"]
        optimal_moves = task_data["optimal_moves"]

        current_state = initial_state
        move_count = 0

        # Hold initial state
        initial_frame = self._render_state(
            current_state, target_state,
            move_count=0, optimal_moves=optimal_moves
        )
        for _ in range(self.config.hold_frames):
            frames.append(initial_frame)

        # Animate each move
        for move_idx, (from_idx, to_idx) in enumerate(solution):
            # Get the block being moved
            stacks = [list(s) for s in current_state]
            moving_block_color = stacks[from_idx][-1]

            # Calculate positions
            from_x = self.stack_spacing * (from_idx + 1)
            to_x = self.stack_spacing * (to_idx + 1)

            from_stack_height = len(stacks[from_idx])
            to_stack_height = len(stacks[to_idx])

            from_y = self.ground_y - from_stack_height * self.config.block_height
            to_y = self.ground_y - (to_stack_height + 1) * self.config.block_height

            # Remove block from source (for rendering)
            stacks[from_idx].pop()
            state_without_moving = tuple(tuple(s) for s in stacks)

            # Phase 1: Lift
            for i in range(self.config.lift_frames):
                progress = i / max(1, self.config.lift_frames - 1)
                y = from_y + (self.lift_y - from_y) * progress

                frame = self._render_state(
                    state_without_moving, target_state,
                    move_count=move_count, optimal_moves=optimal_moves,
                    moving_block={
                        "color_idx": moving_block_color,
                        "x": from_x,
                        "y": y
                    }
                )
                frames.append(frame)

            # Phase 2: Move horizontally
            for i in range(self.config.move_frames):
                progress = i / max(1, self.config.move_frames - 1)
                x = from_x + (to_x - from_x) * progress

                frame = self._render_state(
                    state_without_moving, target_state,
                    move_count=move_count, optimal_moves=optimal_moves,
                    moving_block={
                        "color_idx": moving_block_color,
                        "x": x,
                        "y": self.lift_y
                    }
                )
                frames.append(frame)

            # Phase 3: Lower
            for i in range(self.config.lower_frames):
                progress = i / max(1, self.config.lower_frames - 1)
                y = self.lift_y + (to_y - self.lift_y) * progress

                frame = self._render_state(
                    state_without_moving, target_state,
                    move_count=move_count, optimal_moves=optimal_moves,
                    moving_block={
                        "color_idx": moving_block_color,
                        "x": to_x,
                        "y": y
                    }
                )
                frames.append(frame)

            # Update state and move count
            stacks[to_idx].append(moving_block_color)
            current_state = tuple(tuple(s) for s in stacks)
            move_count += 1

            # Pause between moves (show settled state)
            settled_frame = self._render_state(
                current_state, target_state,
                move_count=move_count, optimal_moves=optimal_moves
            )
            for _ in range(self.config.pause_between_moves):
                frames.append(settled_frame)

        # Hold final state (solved)
        final_frame = self._render_state(
            current_state, target_state,
            move_count=move_count, optimal_moves=optimal_moves,
            is_solved=True
        )
        for _ in range(self.config.hold_frames * 2):
            frames.append(final_frame)

        return frames

    # ══════════════════════════════════════════════════════════════════════════
    #  UTILITIES
    # ══════════════════════════════════════════════════════════════════════════

    def _hex_to_rgb(self, hex_color: str) -> tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Get a font of specified size."""
        font_names = [
            "arial.ttf",
            "Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "DejaVuSans.ttf",
        ]

        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size)
            except (OSError, IOError):
                continue

        return ImageFont.load_default()
