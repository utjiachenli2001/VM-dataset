"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK GENERATOR                                 ║
║                                                                               ║
║  Construction Blueprint - Missing Piece Task                                  ║
║  Generate structures with gaps and candidate pieces to fill them              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
from pathlib import Path
from typing import List, Tuple, Set, Optional
from PIL import Image, ImageDraw

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt


# Standard tetromino shapes (relative coordinates from anchor point)
TETROMINOES = {
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "L": [(0, 0), (0, 1), (0, 2), (1, 2)],
    "J": [(1, 0), (1, 1), (1, 2), (0, 2)],
}

# Simple shapes for variety
SIMPLE_SHAPES = {
    "single": [(0, 0)],
    "domino_h": [(0, 0), (1, 0)],
    "domino_v": [(0, 0), (0, 1)],
    "tromino_l": [(0, 0), (1, 0), (0, 1)],
    "tromino_i": [(0, 0), (1, 0), (2, 0)],
}


class TaskGenerator(BaseGenerator):
    """
    Generator for Construction Blueprint - Missing Piece task.

    Creates structures with one missing piece and 4 candidate pieces.
    Only one candidate correctly fits the gap.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Colors
        self.bg_color = (245, 245, 245)  # Light gray background
        self.structure_color = (70, 130, 180)  # Steel blue for structure
        self.gap_color = (255, 255, 255)  # White for gap area
        self.gap_outline_color = (255, 100, 100)  # Red dashed outline
        self.candidate_bg_color = (230, 230, 230)  # Candidate area background
        self.correct_color = (100, 200, 100)  # Green for correct
        self.incorrect_color = (200, 100, 100)  # Red for incorrect
        self.highlight_color = (255, 200, 100)  # Orange for scanning

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one task pair."""

        # Generate task data
        task_data = self._generate_task_data()

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
    #  TASK DATA GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_task_data(self) -> dict:
        """Generate structure with gap and candidate pieces."""

        grid_size = self.config.grid_size

        # Generate a connected structure
        structure = self._generate_structure()

        # Select a piece to remove (the gap)
        gap_piece = self._select_removable_piece(structure)

        # Remove the gap piece from structure
        structure_with_gap = structure - gap_piece

        # Generate candidate pieces (1 correct + 3 distractors)
        candidates, correct_index = self._generate_candidates(gap_piece)

        return {
            "structure": structure_with_gap,
            "gap_piece": gap_piece,
            "candidates": candidates,
            "correct_index": correct_index,
            "grid_size": grid_size,
        }

    def _generate_structure(self) -> Set[Tuple[int, int]]:
        """Generate a connected structure using random block placement."""

        grid_size = self.config.grid_size
        min_blocks = self.config.min_structure_blocks
        max_blocks = self.config.max_structure_blocks

        target_blocks = random.randint(min_blocks, max_blocks)

        # Start with a seed block near center
        center = grid_size // 2
        structure = {(center, center)}

        # Grow structure by adding adjacent blocks
        attempts = 0
        max_attempts = target_blocks * 10

        while len(structure) < target_blocks and attempts < max_attempts:
            attempts += 1

            # Pick a random existing block
            existing = random.choice(list(structure))

            # Try to add an adjacent block
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                new_x = existing[0] + dx
                new_y = existing[1] + dy

                # Check bounds (leave margin for candidates display)
                if 1 <= new_x < grid_size - 1 and 1 <= new_y < grid_size - 2:
                    if (new_x, new_y) not in structure:
                        structure.add((new_x, new_y))
                        break

        return structure

    def _select_removable_piece(self, structure: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Select a contiguous piece to remove from the structure."""

        # Try to select a tetromino-shaped piece first
        structure_list = list(structure)
        random.shuffle(structure_list)

        # Try different shape sizes (prefer 2-4 blocks)
        for target_size in [3, 4, 2, 1]:
            for start_block in structure_list:
                piece = self._grow_piece(structure, start_block, target_size)
                if len(piece) == target_size:
                    # Verify removing this piece doesn't disconnect the structure
                    remaining = structure - piece
                    if self._is_connected(remaining):
                        return piece

        # Fallback: just remove one block
        for block in structure_list:
            remaining = structure - {block}
            if self._is_connected(remaining):
                return {block}

        # Last resort: return any block
        return {structure_list[0]}

    def _grow_piece(self, structure: Set[Tuple[int, int]],
                    start: Tuple[int, int], target_size: int) -> Set[Tuple[int, int]]:
        """Grow a contiguous piece starting from a block."""

        piece = {start}
        frontier = [start]

        while len(piece) < target_size and frontier:
            current = frontier.pop(0)

            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            random.shuffle(directions)

            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor in structure and neighbor not in piece:
                    piece.add(neighbor)
                    frontier.append(neighbor)
                    if len(piece) >= target_size:
                        break

        return piece

    def _is_connected(self, blocks: Set[Tuple[int, int]]) -> bool:
        """Check if a set of blocks forms a connected component."""

        if not blocks:
            return True

        blocks_list = list(blocks)
        visited = {blocks_list[0]}
        queue = [blocks_list[0]]

        while queue:
            current = queue.pop(0)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor in blocks and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return len(visited) == len(blocks)

    def _generate_candidates(self, correct_piece: Set[Tuple[int, int]]) -> Tuple[List[Set[Tuple[int, int]]], int]:
        """Generate 4 candidate pieces: 1 correct + 3 distractors."""

        candidates = []

        # Normalize the correct piece (translate to origin)
        correct_normalized = self._normalize_piece(correct_piece)
        candidates.append(correct_normalized)

        # Generate 3 distractors
        distractors = self._generate_distractors(correct_normalized)
        candidates.extend(distractors[:3])

        # Shuffle and track correct index
        indices = list(range(len(candidates)))
        random.shuffle(indices)

        shuffled_candidates = [candidates[i] for i in indices]
        correct_index = indices.index(0)  # Original correct was at index 0

        return shuffled_candidates, correct_index

    def _normalize_piece(self, piece: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Translate piece so its bounding box starts at (0, 0)."""

        if not piece:
            return piece

        min_x = min(p[0] for p in piece)
        min_y = min(p[1] for p in piece)

        return {(p[0] - min_x, p[1] - min_y) for p in piece}

    def _generate_distractors(self, correct: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
        """Generate distractor pieces that are similar but wrong."""

        distractors = []
        correct_size = len(correct)

        # Distractor 1: Different size (add or remove a block)
        if correct_size > 1:
            # Remove a block
            smaller = set(list(correct)[:-1])
            distractors.append(self._normalize_piece(smaller))
        else:
            # Add a block
            bigger = correct | {(1, 0)}
            distractors.append(self._normalize_piece(bigger))

        # Distractor 2: Rotated version (90 degrees)
        rotated = {(-p[1], p[0]) for p in correct}
        rotated_normalized = self._normalize_piece(rotated)
        if rotated_normalized != correct:
            distractors.append(rotated_normalized)
        else:
            # If rotation gives same shape, use a different shape
            distractors.append(self._get_random_shape(correct_size))

        # Distractor 3: Different shape entirely
        different = self._get_random_shape(correct_size)
        while different == correct or different in distractors:
            different = self._get_random_shape(max(1, correct_size + random.choice([-1, 0, 1])))
        distractors.append(different)

        return distractors

    def _get_random_shape(self, target_size: int) -> Set[Tuple[int, int]]:
        """Get a random shape of approximately the target size."""

        # Try tetrominoes first
        if target_size == 4:
            shape_name = random.choice(list(TETROMINOES.keys()))
            return set(TETROMINOES[shape_name])

        # Try simple shapes
        if target_size <= 3:
            matching = [s for s, coords in SIMPLE_SHAPES.items() if len(coords) == target_size]
            if matching:
                shape_name = random.choice(matching)
                return set(SIMPLE_SHAPES[shape_name])

        # Generate random connected shape
        shape = {(0, 0)}
        while len(shape) < target_size:
            block = random.choice(list(shape))
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            shape.add((block[0] + dx, block[1] + dy))

        return self._normalize_piece(shape)

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render the structure with gap and candidates below."""

        return self._render_scene(
            task_data,
            show_gap_highlight=True,
            show_candidates=True,
            candidate_states=None,  # No selection yet
            placed_piece=False
        )

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render the completed structure with piece in place."""

        return self._render_scene(
            task_data,
            show_gap_highlight=False,
            show_candidates=True,
            candidate_states={task_data["correct_index"]: "correct"},
            placed_piece=True
        )

    def _render_scene(
        self,
        task_data: dict,
        show_gap_highlight: bool = True,
        show_candidates: bool = True,
        candidate_states: Optional[dict] = None,
        placed_piece: bool = False,
        scanning_index: Optional[int] = None,
        ghost_preview: Optional[int] = None,
        piece_animation_progress: Optional[float] = None
    ) -> Image.Image:
        """
        Render the complete scene.

        Args:
            task_data: The task data dict
            show_gap_highlight: Whether to show dashed outline on gap
            show_candidates: Whether to show candidate pieces
            candidate_states: Dict mapping index to state ("correct", "incorrect", "scanning")
            placed_piece: Whether the correct piece is placed in the gap
            scanning_index: Index of currently scanning candidate
            ghost_preview: Index of candidate being previewed as ghost
            piece_animation_progress: 0.0-1.0 for piece movement animation
        """

        img_size = self.config.image_size[0]
        grid_size = task_data["grid_size"]

        # Layout: structure takes upper 70%, candidates take lower 30%
        structure_height = int(img_size * 0.70)
        candidate_height = img_size - structure_height

        # Calculate block size for structure area
        block_size = min(structure_height, img_size) // (grid_size + 2)

        # Create image
        img = Image.new("RGB", (img_size, img_size), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Draw structure area background
        structure_area = (0, 0, img_size, structure_height)

        # Calculate structure offset to center it
        structure_width = grid_size * block_size
        structure_offset_x = (img_size - structure_width) // 2
        structure_offset_y = (structure_height - grid_size * block_size) // 2

        # Draw structure blocks
        for block in task_data["structure"]:
            x = structure_offset_x + block[0] * block_size
            y = structure_offset_y + block[1] * block_size
            draw.rectangle(
                [x, y, x + block_size - 2, y + block_size - 2],
                fill=self.structure_color,
                outline=(50, 100, 140)
            )

        # Draw gap area
        gap_piece = task_data["gap_piece"]
        if placed_piece:
            # Draw the piece in place
            for block in gap_piece:
                x = structure_offset_x + block[0] * block_size
                y = structure_offset_y + block[1] * block_size
                draw.rectangle(
                    [x, y, x + block_size - 2, y + block_size - 2],
                    fill=self.correct_color,
                    outline=(70, 150, 70)
                )
        elif show_gap_highlight:
            # Draw dashed outline for gap
            for block in gap_piece:
                x = structure_offset_x + block[0] * block_size
                y = structure_offset_y + block[1] * block_size
                self._draw_dashed_rect(draw, x, y, block_size - 2, block_size - 2, self.gap_outline_color)

        # Draw ghost preview if active
        if ghost_preview is not None and piece_animation_progress is None:
            candidate = task_data["candidates"][ghost_preview]
            gap_min_x = min(b[0] for b in gap_piece)
            gap_min_y = min(b[1] for b in gap_piece)

            for block in candidate:
                x = structure_offset_x + (gap_min_x + block[0]) * block_size
                y = structure_offset_y + (gap_min_y + block[1]) * block_size

                # Semi-transparent ghost
                ghost_color = (150, 150, 200, 128)
                # Draw as slightly transparent
                draw.rectangle(
                    [x + 2, y + 2, x + block_size - 4, y + block_size - 4],
                    fill=(180, 180, 220),
                    outline=(100, 100, 150)
                )

        # Draw piece animation
        if piece_animation_progress is not None:
            self._draw_animated_piece(
                draw, task_data, structure_offset_x, structure_offset_y,
                block_size, structure_height, img_size, piece_animation_progress
            )

        # Draw separator line
        draw.line([(0, structure_height), (img_size, structure_height)], fill=(200, 200, 200), width=2)

        # Draw candidates area
        if show_candidates:
            self._draw_candidates(
                draw, task_data, structure_height, candidate_height,
                img_size, candidate_states, scanning_index
            )

        return img

    def _draw_dashed_rect(self, draw: ImageDraw.Draw, x: int, y: int,
                          width: int, height: int, color: Tuple[int, int, int]):
        """Draw a dashed rectangle."""

        dash_length = 5
        gap_length = 3

        # Top edge
        self._draw_dashed_line(draw, x, y, x + width, y, color, dash_length, gap_length)
        # Bottom edge
        self._draw_dashed_line(draw, x, y + height, x + width, y + height, color, dash_length, gap_length)
        # Left edge
        self._draw_dashed_line(draw, x, y, x, y + height, color, dash_length, gap_length)
        # Right edge
        self._draw_dashed_line(draw, x + width, y, x + width, y + height, color, dash_length, gap_length)

    def _draw_dashed_line(self, draw: ImageDraw.Draw, x1: int, y1: int,
                          x2: int, y2: int, color: Tuple[int, int, int],
                          dash_length: int, gap_length: int):
        """Draw a dashed line."""

        import math

        total_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        if total_length == 0:
            return

        dx = (x2 - x1) / total_length
        dy = (y2 - y1) / total_length

        pos = 0
        drawing = True

        while pos < total_length:
            if drawing:
                end_pos = min(pos + dash_length, total_length)
                draw.line([
                    (x1 + dx * pos, y1 + dy * pos),
                    (x1 + dx * end_pos, y1 + dy * end_pos)
                ], fill=color, width=2)
                pos = end_pos + gap_length
            else:
                pos += gap_length
            drawing = not drawing

    def _draw_candidates(
        self,
        draw: ImageDraw.Draw,
        task_data: dict,
        y_offset: int,
        height: int,
        img_width: int,
        candidate_states: Optional[dict],
        scanning_index: Optional[int]
    ):
        """Draw the candidate pieces area."""

        candidates = task_data["candidates"]
        num_candidates = len(candidates)

        # Calculate candidate box sizes
        margin = 20
        available_width = img_width - 2 * margin
        box_width = available_width // num_candidates
        box_size = min(box_width - 10, height - 20)

        # Calculate block size within candidate box
        max_piece_size = max(
            max(max(b[0] for b in c) + 1, max(b[1] for b in c) + 1) if c else 1
            for c in candidates
        )
        candidate_block_size = (box_size - 20) // max(max_piece_size, 2)

        for i, candidate in enumerate(candidates):
            # Calculate box position
            box_x = margin + i * box_width + (box_width - box_size) // 2
            box_y = y_offset + (height - box_size) // 2

            # Determine box state
            bg_color = self.candidate_bg_color
            outline_color = (180, 180, 180)
            outline_width = 1

            if candidate_states and i in candidate_states:
                state = candidate_states[i]
                if state == "correct":
                    bg_color = (200, 255, 200)
                    outline_color = self.correct_color
                    outline_width = 3
                elif state == "incorrect":
                    bg_color = (255, 220, 220)
                    outline_color = self.incorrect_color
                    outline_width = 2

            if scanning_index == i:
                outline_color = self.highlight_color
                outline_width = 3

            # Draw candidate box
            draw.rectangle(
                [box_x, box_y, box_x + box_size, box_y + box_size],
                fill=bg_color,
                outline=outline_color,
                width=outline_width
            )

            # Draw candidate piece centered in box
            if candidate:
                piece_width = (max(b[0] for b in candidate) + 1) * candidate_block_size
                piece_height = (max(b[1] for b in candidate) + 1) * candidate_block_size
                piece_offset_x = box_x + (box_size - piece_width) // 2
                piece_offset_y = box_y + (box_size - piece_height) // 2

                for block in candidate:
                    bx = piece_offset_x + block[0] * candidate_block_size
                    by = piece_offset_y + block[1] * candidate_block_size
                    draw.rectangle(
                        [bx, by, bx + candidate_block_size - 2, by + candidate_block_size - 2],
                        fill=self.structure_color,
                        outline=(50, 100, 140)
                    )

            # Draw X or checkmark based on state
            if candidate_states and i in candidate_states:
                state = candidate_states[i]
                mark_size = 20
                mark_x = box_x + box_size - mark_size - 5
                mark_y = box_y + 5

                if state == "correct":
                    # Green checkmark
                    self._draw_checkmark(draw, mark_x, mark_y, mark_size, self.correct_color)
                elif state == "incorrect":
                    # Red X
                    self._draw_x_mark(draw, mark_x, mark_y, mark_size, self.incorrect_color)

            # Draw candidate number
            label = str(i + 1)
            draw.text((box_x + 5, box_y + 5), label, fill=(100, 100, 100))

    def _draw_checkmark(self, draw: ImageDraw.Draw, x: int, y: int,
                        size: int, color: Tuple[int, int, int]):
        """Draw a checkmark."""

        points = [
            (x, y + size * 0.5),
            (x + size * 0.35, y + size * 0.8),
            (x + size, y + size * 0.2)
        ]
        draw.line(points, fill=color, width=3)

    def _draw_x_mark(self, draw: ImageDraw.Draw, x: int, y: int,
                     size: int, color: Tuple[int, int, int]):
        """Draw an X mark."""

        draw.line([(x, y), (x + size, y + size)], fill=color, width=3)
        draw.line([(x + size, y), (x, y + size)], fill=color, width=3)

    def _draw_animated_piece(
        self,
        draw: ImageDraw.Draw,
        task_data: dict,
        structure_offset_x: int,
        structure_offset_y: int,
        block_size: int,
        structure_height: int,
        img_size: int,
        progress: float
    ):
        """Draw the piece being animated from candidate area to gap."""

        correct_index = task_data["correct_index"]
        candidate = task_data["candidates"][correct_index]
        gap_piece = task_data["gap_piece"]

        # Calculate start position (in candidate area)
        num_candidates = len(task_data["candidates"])
        margin = 20
        available_width = img_size - 2 * margin
        box_width = available_width // num_candidates
        candidate_height = img_size - structure_height
        box_size = min(box_width - 10, candidate_height - 20)

        max_piece_size = max(
            max(max(b[0] for b in c) + 1, max(b[1] for b in c) + 1) if c else 1
            for c in task_data["candidates"]
        )
        candidate_block_size = (box_size - 20) // max(max_piece_size, 2)

        box_x = margin + correct_index * box_width + (box_width - box_size) // 2
        box_y = structure_height + (candidate_height - box_size) // 2

        piece_width = (max(b[0] for b in candidate) + 1) * candidate_block_size
        piece_height = (max(b[1] for b in candidate) + 1) * candidate_block_size
        start_x = box_x + (box_size - piece_width) // 2
        start_y = box_y + (box_size - piece_height) // 2

        # Calculate end position (in gap)
        gap_min_x = min(b[0] for b in gap_piece)
        gap_min_y = min(b[1] for b in gap_piece)
        end_x = structure_offset_x + gap_min_x * block_size
        end_y = structure_offset_y + gap_min_y * block_size

        # Interpolate position
        current_x = start_x + (end_x - start_x) * progress
        current_y = start_y + (end_y - start_y) * progress

        # Interpolate block size
        current_block_size = candidate_block_size + (block_size - candidate_block_size) * progress

        # Draw piece at current position
        for block in candidate:
            bx = current_x + block[0] * current_block_size
            by = current_y + block[1] * current_block_size

            color = self.structure_color
            if progress > 0.8:
                # Transition to green as it approaches destination
                blend = (progress - 0.8) / 0.2
                color = (
                    int(self.structure_color[0] + (self.correct_color[0] - self.structure_color[0]) * blend),
                    int(self.structure_color[1] + (self.correct_color[1] - self.structure_color[1]) * blend),
                    int(self.structure_color[2] + (self.correct_color[2] - self.structure_color[2]) * blend),
                )

            draw.rectangle(
                [bx, by, bx + current_block_size - 2, by + current_block_size - 2],
                fill=color,
                outline=(50, 100, 140)
            )

    # ══════════════════════════════════════════════════════════════════════════
    #  VIDEO GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_video(self, task_data: dict, task_id: str) -> Optional[str]:
        """Generate ground truth video showing the selection process."""

        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)

        return str(result) if result else None

    def _create_animation_frames(self, task_data: dict) -> List[Image.Image]:
        """Create animation frames for the selection process."""

        frames = []
        correct_index = task_data["correct_index"]
        num_candidates = len(task_data["candidates"])

        # Phase 1: Initial state with gap highlighted (hold)
        hold_frames = 10
        for _ in range(hold_frames):
            frame = self._render_scene(task_data, show_gap_highlight=True, show_candidates=True)
            frames.append(frame)

        # Phase 2: Scan through candidates
        candidate_states = {}

        for i in range(num_candidates):
            # Scanning indicator on current candidate
            scan_frames = 5
            for _ in range(scan_frames):
                frame = self._render_scene(
                    task_data,
                    show_gap_highlight=True,
                    show_candidates=True,
                    candidate_states=candidate_states.copy(),
                    scanning_index=i
                )
                frames.append(frame)

            # Ghost preview
            preview_frames = 8
            for _ in range(preview_frames):
                frame = self._render_scene(
                    task_data,
                    show_gap_highlight=True,
                    show_candidates=True,
                    candidate_states=candidate_states.copy(),
                    scanning_index=i,
                    ghost_preview=i
                )
                frames.append(frame)

            # Mark as correct or incorrect
            if i == correct_index:
                candidate_states[i] = "correct"
                # Show correct state
                for _ in range(10):
                    frame = self._render_scene(
                        task_data,
                        show_gap_highlight=True,
                        show_candidates=True,
                        candidate_states=candidate_states.copy()
                    )
                    frames.append(frame)
                break  # Stop scanning once correct is found
            else:
                candidate_states[i] = "incorrect"
                # Show incorrect briefly
                for _ in range(5):
                    frame = self._render_scene(
                        task_data,
                        show_gap_highlight=True,
                        show_candidates=True,
                        candidate_states=candidate_states.copy()
                    )
                    frames.append(frame)

        # Phase 3: Animate piece moving to gap
        move_frames = 20
        for i in range(move_frames):
            progress = i / (move_frames - 1)
            frame = self._render_scene(
                task_data,
                show_gap_highlight=False,
                show_candidates=True,
                candidate_states=candidate_states,
                piece_animation_progress=progress
            )
            frames.append(frame)

        # Phase 4: Final state (hold)
        final_hold = 15
        for _ in range(final_hold):
            frame = self._render_scene(
                task_data,
                show_gap_highlight=False,
                show_candidates=True,
                candidate_states=candidate_states,
                placed_piece=True
            )
            frames.append(frame)

        return frames
