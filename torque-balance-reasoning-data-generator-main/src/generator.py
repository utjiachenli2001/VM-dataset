"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LEVER TASK GENERATOR                                ║
║                                                                               ║
║  Generates lever/torque balance reasoning tasks.                              ║
║  Creates problems where users must calculate torques and predict tip direction║
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
    Lever/torque balance task generator.

    Generates physics problems where:
    - Objects with weights are placed at distances from a fulcrum
    - Torque = Weight × Distance
    - The side with greater total torque tips down
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Colors
        self.colors = {
            "background": (245, 245, 240),      # Light cream
            "beam": (139, 90, 43),              # Brown wood color
            "beam_outline": (101, 67, 33),      # Darker brown
            "fulcrum": (80, 80, 80),            # Dark gray
            "fulcrum_outline": (50, 50, 50),    # Darker gray
            "left_object": (220, 60, 60),       # Red
            "right_object": (60, 100, 220),     # Blue
            "text": (30, 30, 30),               # Dark text
            "label_bg": (255, 255, 255),        # White background for labels
            "distance_marker": (120, 120, 120), # Gray for tick marks
            "calc_left_bg": (255, 230, 230),    # Light red for left calc box
            "calc_right_bg": (230, 230, 255),   # Light blue for right calc box
        }

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one lever balance task."""

        # Generate task data
        task_data = self._generate_task_data()

        # Render images
        first_image = self._render_initial_state(task_data)
        final_image = self._render_final_state(task_data)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(first_image, final_image, task_id, task_data)

        # Select prompt based on task type
        prompt = get_prompt(task_data.get("prompt_type", "default"))

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
        """Generate a lever balance problem."""

        # Decide if this should be a balanced case
        force_balanced = (
            self.config.include_balanced and
            random.random() < self.config.balanced_probability
        )

        if force_balanced:
            return self._generate_balanced_problem()
        else:
            return self._generate_unbalanced_problem()

    def _generate_unbalanced_problem(self) -> dict:
        """Generate a problem where one side tips."""

        # Generate left side objects
        num_left = random.randint(
            self.config.min_objects_per_side,
            self.config.max_objects_per_side
        )
        left_objects = self._generate_objects(num_left, "left")

        # Generate right side objects
        num_right = random.randint(
            self.config.min_objects_per_side,
            self.config.max_objects_per_side
        )
        right_objects = self._generate_objects(num_right, "right")

        # Calculate torques
        left_torque = sum(obj["weight"] * obj["distance"] for obj in left_objects)
        right_torque = sum(obj["weight"] * obj["distance"] for obj in right_objects)

        # Ensure not accidentally balanced
        if left_torque == right_torque:
            # Adjust one weight slightly
            if left_objects:
                left_objects[0]["weight"] += 1
                left_torque = sum(obj["weight"] * obj["distance"] for obj in left_objects)

        # Determine tip direction
        if left_torque > right_torque:
            tips_to = "left"
        else:
            tips_to = "right"

        # Check if counterintuitive (lighter total weight wins)
        left_total_weight = sum(obj["weight"] for obj in left_objects)
        right_total_weight = sum(obj["weight"] for obj in right_objects)

        is_counterintuitive = (
            (tips_to == "left" and left_total_weight < right_total_weight) or
            (tips_to == "right" and right_total_weight < left_total_weight)
        )

        # Select prompt type
        if is_counterintuitive:
            prompt_type = "counterintuitive"
        elif tips_to == "left":
            prompt_type = "tips_left"
        else:
            prompt_type = "tips_right"

        return {
            "left_objects": left_objects,
            "right_objects": right_objects,
            "left_torque": left_torque,
            "right_torque": right_torque,
            "tips_to": tips_to,
            "prompt_type": prompt_type,
            "is_balanced": False,
        }

    def _generate_balanced_problem(self) -> dict:
        """Generate a perfectly balanced problem."""

        # Start with one side
        num_left = random.randint(1, 2)
        left_objects = self._generate_objects(num_left, "left")
        left_torque = sum(obj["weight"] * obj["distance"] for obj in left_objects)

        # Generate right side to match torque
        right_objects = self._generate_matching_objects(left_torque)
        right_torque = sum(obj["weight"] * obj["distance"] for obj in right_objects)

        return {
            "left_objects": left_objects,
            "right_objects": right_objects,
            "left_torque": left_torque,
            "right_torque": right_torque,
            "tips_to": "none",
            "prompt_type": "balanced",
            "is_balanced": True,
        }

    def _generate_objects(self, count: int, side: str) -> List[dict]:
        """Generate random objects for one side."""
        objects = []
        used_distances = set()

        for _ in range(count):
            # Pick unique distance
            available_distances = [
                d for d in range(1, self.config.max_distance + 1)
                if d not in used_distances
            ]
            if not available_distances:
                break

            distance = random.choice(available_distances)
            used_distances.add(distance)

            weight = random.randint(self.config.min_weight, self.config.max_weight)

            objects.append({
                "weight": weight,
                "distance": distance,
                "side": side,
            })

        return objects

    def _generate_matching_objects(self, target_torque: int) -> List[dict]:
        """Generate objects that sum to target torque."""
        objects = []

        # Try to find a combination that matches
        remaining_torque = target_torque

        for distance in range(self.config.max_distance, 0, -1):
            if remaining_torque <= 0:
                break

            # Check if this distance can contribute
            if remaining_torque >= distance:
                weight = remaining_torque // distance
                if weight >= self.config.min_weight and weight <= self.config.max_weight:
                    if remaining_torque % distance == 0:
                        objects.append({
                            "weight": weight,
                            "distance": distance,
                            "side": "right",
                        })
                        remaining_torque = 0
                        break

        # Fallback: just create one object that matches
        if remaining_torque > 0 or not objects:
            # Find a factor pair
            for d in range(1, self.config.max_distance + 1):
                if target_torque % d == 0:
                    w = target_torque // d
                    if self.config.min_weight <= w <= self.config.max_weight:
                        objects = [{
                            "weight": w,
                            "distance": d,
                            "side": "right",
                        }]
                        break

        return objects

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_initial_state(self, task_data: dict) -> Image.Image:
        """Render the initial balanced lever state."""
        return self._render_lever(task_data, tilt_angle=0.0, show_result=False)

    def _render_final_state(self, task_data: dict) -> Image.Image:
        """Render the final tilted lever state."""
        if task_data["is_balanced"]:
            tilt_angle = 0.0
        elif task_data["tips_to"] == "left":
            tilt_angle = -self.config.tilt_angle
        else:
            tilt_angle = self.config.tilt_angle

        return self._render_lever(task_data, tilt_angle=tilt_angle, show_result=True)

    def _render_lever(
        self,
        task_data: dict,
        tilt_angle: float = 0.0,
        show_result: bool = False
    ) -> Image.Image:
        """
        Render the lever scene.

        Args:
            task_data: Problem data with objects and torques
            tilt_angle: Rotation angle in degrees (negative = left down)
            show_result: Whether to show the result text
        """
        width, height = self.config.image_size
        img = Image.new("RGB", (width, height), self.colors["background"])
        draw = ImageDraw.Draw(img)

        # Layout parameters
        fulcrum_x = width // 2
        fulcrum_y = int(height * 0.55)
        beam_length = int(width * 0.85)
        beam_height = 16
        fulcrum_size = 40

        # Get font
        font = self._get_font(16)
        font_small = self._get_font(13)
        font_large = self._get_font(18)

        # Draw title
        title = "Lever Balance - Torque Calculation"
        title_bbox = draw.textbbox((0, 0), title, font=font_large)
        title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, 15), title, fill=self.colors["text"], font=font_large)

        # Draw fulcrum (triangle)
        self._draw_fulcrum(draw, fulcrum_x, fulcrum_y, fulcrum_size)

        # Calculate beam endpoints based on tilt
        angle_rad = math.radians(tilt_angle)
        half_length = beam_length // 2

        left_x = fulcrum_x - half_length * math.cos(angle_rad)
        left_y = fulcrum_y - half_length * math.sin(angle_rad)
        right_x = fulcrum_x + half_length * math.cos(angle_rad)
        right_y = fulcrum_y + half_length * math.sin(angle_rad)

        # Draw beam
        self._draw_beam(draw, left_x, left_y, right_x, right_y, beam_height, angle_rad)

        # Draw distance markers on beam
        self._draw_distance_markers(
            draw, fulcrum_x, fulcrum_y, half_length, angle_rad, font_small
        )

        # Draw objects
        self._draw_objects(
            draw, task_data["left_objects"], fulcrum_x, fulcrum_y,
            half_length, angle_rad, font, is_left=True
        )
        self._draw_objects(
            draw, task_data["right_objects"], fulcrum_x, fulcrum_y,
            half_length, angle_rad, font, is_left=False
        )

        # Draw calculation boxes
        self._draw_calculation_boxes(draw, task_data, width, height, font_small, show_result)

        return img

    def _draw_fulcrum(self, draw: ImageDraw.Draw, x: int, y: int, size: int):
        """Draw the triangular fulcrum."""
        # Triangle points
        top = (x, y)
        bottom_left = (x - size // 2, y + size)
        bottom_right = (x + size // 2, y + size)

        # Draw filled triangle
        draw.polygon([top, bottom_left, bottom_right], fill=self.colors["fulcrum"])
        draw.polygon([top, bottom_left, bottom_right], outline=self.colors["fulcrum_outline"], width=2)

    def _draw_beam(
        self,
        draw: ImageDraw.Draw,
        x1: float, y1: float,
        x2: float, y2: float,
        height: int,
        angle_rad: float
    ):
        """Draw the lever beam as a rotated rectangle."""
        # Calculate perpendicular offset for beam height
        perp_x = -math.sin(angle_rad) * height / 2
        perp_y = math.cos(angle_rad) * height / 2

        # Four corners of the beam
        corners = [
            (x1 - perp_x, y1 - perp_y),
            (x1 + perp_x, y1 + perp_y),
            (x2 + perp_x, y2 + perp_y),
            (x2 - perp_x, y2 - perp_y),
        ]

        draw.polygon(corners, fill=self.colors["beam"], outline=self.colors["beam_outline"], width=2)

    def _draw_distance_markers(
        self,
        draw: ImageDraw.Draw,
        fulcrum_x: int,
        fulcrum_y: int,
        half_length: int,
        angle_rad: float,
        font: ImageFont.FreeTypeFont
    ):
        """Draw distance markers on the beam."""
        # Calculate pixels per meter
        pixels_per_meter = half_length / self.config.max_distance

        for d in range(1, self.config.max_distance + 1):
            # Left side marker
            dist_px = d * pixels_per_meter
            left_marker_x = fulcrum_x - dist_px * math.cos(angle_rad)
            left_marker_y = fulcrum_y - dist_px * math.sin(angle_rad)

            # Draw tick mark
            tick_length = 8
            perp_x = -math.sin(angle_rad) * tick_length
            perp_y = math.cos(angle_rad) * tick_length

            draw.line(
                [(left_marker_x - perp_x, left_marker_y - perp_y),
                 (left_marker_x + perp_x, left_marker_y + perp_y)],
                fill=self.colors["distance_marker"], width=2
            )

            # Draw distance label below beam
            label = f"{d}m"
            label_x = left_marker_x - 10
            label_y = left_marker_y + 20
            draw.text((label_x, label_y), label, fill=self.colors["distance_marker"], font=font)

            # Right side marker
            right_marker_x = fulcrum_x + dist_px * math.cos(angle_rad)
            right_marker_y = fulcrum_y + dist_px * math.sin(angle_rad)

            draw.line(
                [(right_marker_x - perp_x, right_marker_y - perp_y),
                 (right_marker_x + perp_x, right_marker_y + perp_y)],
                fill=self.colors["distance_marker"], width=2
            )

            label_x = right_marker_x - 10
            label_y = right_marker_y + 20
            draw.text((label_x, label_y), label, fill=self.colors["distance_marker"], font=font)

    def _draw_objects(
        self,
        draw: ImageDraw.Draw,
        objects: List[dict],
        fulcrum_x: int,
        fulcrum_y: int,
        half_length: int,
        angle_rad: float,
        font: ImageFont.FreeTypeFont,
        is_left: bool
    ):
        """Draw weight objects on the beam."""
        pixels_per_meter = half_length / self.config.max_distance
        color = self.colors["left_object"] if is_left else self.colors["right_object"]

        for obj in objects:
            dist_px = obj["distance"] * pixels_per_meter

            if is_left:
                obj_x = fulcrum_x - dist_px * math.cos(angle_rad)
                obj_y = fulcrum_y - dist_px * math.sin(angle_rad)
            else:
                obj_x = fulcrum_x + dist_px * math.cos(angle_rad)
                obj_y = fulcrum_y + dist_px * math.sin(angle_rad)

            # Draw object (box) above beam
            box_size = 35
            box_offset = 30  # Distance above beam

            # Offset perpendicular to beam (upward)
            perp_x = math.sin(angle_rad) * box_offset
            perp_y = -math.cos(angle_rad) * box_offset

            box_center_x = obj_x + perp_x
            box_center_y = obj_y + perp_y

            # Draw box
            box_coords = [
                box_center_x - box_size // 2,
                box_center_y - box_size // 2,
                box_center_x + box_size // 2,
                box_center_y + box_size // 2,
            ]
            draw.rectangle(box_coords, fill=color, outline=(0, 0, 0), width=2)

            # Draw weight label
            label = f"{obj['weight']}kg"
            bbox = draw.textbbox((0, 0), label, font=font)
            label_w = bbox[2] - bbox[0]
            label_h = bbox[3] - bbox[1]
            label_x = box_center_x - label_w // 2
            label_y = box_center_y - label_h // 2
            draw.text((label_x, label_y), label, fill=(255, 255, 255), font=font)

    def _draw_calculation_boxes(
        self,
        draw: ImageDraw.Draw,
        task_data: dict,
        width: int,
        height: int,
        font: ImageFont.FreeTypeFont,
        show_result: bool
    ):
        """Draw torque calculation boxes at the bottom."""
        box_width = 180
        box_height = 90
        box_y = height - box_height - 20
        margin = 30

        # Left calculation box
        left_box = [margin, box_y, margin + box_width, box_y + box_height]
        draw.rectangle(left_box, fill=self.colors["calc_left_bg"], outline=(0, 0, 0), width=2)

        # Left torque calculation text
        y_offset = box_y + 8
        draw.text((margin + 10, y_offset), "LEFT TORQUE", fill=self.colors["text"], font=font)
        y_offset += 18

        for obj in task_data["left_objects"]:
            calc_text = f"{obj['weight']}kg × {obj['distance']}m = {obj['weight'] * obj['distance']}"
            draw.text((margin + 10, y_offset), calc_text, fill=self.colors["text"], font=font)
            y_offset += 16

        total_text = f"Total: {task_data['left_torque']} N·m"
        draw.text((margin + 10, y_offset), total_text, fill=self.colors["left_object"], font=font)

        # Right calculation box
        right_box = [width - margin - box_width, box_y, width - margin, box_y + box_height]
        draw.rectangle(right_box, fill=self.colors["calc_right_bg"], outline=(0, 0, 0), width=2)

        # Right torque calculation text
        y_offset = box_y + 8
        draw.text((width - margin - box_width + 10, y_offset), "RIGHT TORQUE", fill=self.colors["text"], font=font)
        y_offset += 18

        for obj in task_data["right_objects"]:
            calc_text = f"{obj['weight']}kg × {obj['distance']}m = {obj['weight'] * obj['distance']}"
            draw.text((width - margin - box_width + 10, y_offset), calc_text, fill=self.colors["text"], font=font)
            y_offset += 16

        total_text = f"Total: {task_data['right_torque']} N·m"
        draw.text((width - margin - box_width + 10, y_offset), total_text, fill=self.colors["right_object"], font=font)

        # Result text in center
        if show_result:
            if task_data["is_balanced"]:
                result_text = f"BALANCED ({task_data['left_torque']} = {task_data['right_torque']})"
                result_color = (0, 128, 0)  # Green
            elif task_data["tips_to"] == "left":
                result_text = f"LEFT TIPS DOWN ({task_data['left_torque']} > {task_data['right_torque']})"
                result_color = self.colors["left_object"]
            else:
                result_text = f"RIGHT TIPS DOWN ({task_data['right_torque']} > {task_data['left_torque']})"
                result_color = self.colors["right_object"]

            bbox = draw.textbbox((0, 0), result_text, font=font)
            text_w = bbox[2] - bbox[0]
            result_x = (width - text_w) // 2
            result_y = box_y + box_height // 2 - 8

            # Draw background for result text
            padding = 8
            result_bg = [
                result_x - padding,
                result_y - padding,
                result_x + text_w + padding,
                result_y + 20 + padding
            ]
            draw.rectangle(result_bg, fill=(255, 255, 255), outline=(0, 0, 0), width=2)
            draw.text((result_x, result_y), result_text, fill=result_color, font=font)

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
    ) -> Optional[str]:
        """Generate animation video of lever tipping."""
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        # Create animation frames
        frames = self._create_lever_animation_frames(task_data)

        result = self.video_generator.create_video_from_frames(frames, video_path)

        return str(result) if result else None

    def _create_lever_animation_frames(
        self,
        task_data: dict,
        hold_frames: int = 15,
        transition_frames: int = 30
    ) -> List[Image.Image]:
        """
        Create animation frames for lever tipping.

        Animation sequence:
        1. Hold initial balanced state
        2. Smoothly rotate to final tilted state
        3. Hold final state
        """
        frames = []

        # Determine final tilt angle
        if task_data["is_balanced"]:
            final_angle = 0.0
        elif task_data["tips_to"] == "left":
            final_angle = -self.config.tilt_angle
        else:
            final_angle = self.config.tilt_angle

        # Hold initial state (show_result=False)
        initial_frame = self._render_lever(task_data, tilt_angle=0.0, show_result=False)
        for _ in range(hold_frames):
            frames.append(initial_frame)

        # Transition frames (linear interpolation)
        for i in range(transition_frames):
            progress = (i + 1) / transition_frames
            current_angle = final_angle * progress

            # Show result text only in the last few frames of transition
            show_result = progress > 0.8

            frame = self._render_lever(task_data, tilt_angle=current_angle, show_result=show_result)
            frames.append(frame)

        # Hold final state (show_result=True)
        final_frame = self._render_lever(task_data, tilt_angle=final_angle, show_result=True)
        for _ in range(hold_frames):
            frames.append(final_frame)

        return frames
