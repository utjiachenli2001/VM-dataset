"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK GENERATOR                                 ║
║                                                                               ║
║  Logic Gate Output Task Generator                                             ║
║  Generates logic circuit puzzles with signal propagation animations.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont

from core import BaseGenerator, TaskPair, ImageRenderer
from core.video_utils import VideoGenerator
from .config import TaskConfig
from .prompts import get_prompt, get_gate_rule


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIC GATE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def gate_and(inputs: List[int]) -> int:
    """AND gate: outputs 1 only if all inputs are 1."""
    return 1 if all(i == 1 for i in inputs) else 0


def gate_or(inputs: List[int]) -> int:
    """OR gate: outputs 1 if at least one input is 1."""
    return 1 if any(i == 1 for i in inputs) else 0


def gate_not(inputs: List[int]) -> int:
    """NOT gate: flips single input."""
    return 1 - inputs[0]


def gate_xor(inputs: List[int]) -> int:
    """XOR gate: outputs 1 if exactly one input is 1 (for 2 inputs: different)."""
    return sum(inputs) % 2


def gate_nand(inputs: List[int]) -> int:
    """NAND gate: NOT of AND."""
    return 1 - gate_and(inputs)


def gate_nor(inputs: List[int]) -> int:
    """NOR gate: NOT of OR."""
    return 1 - gate_or(inputs)


GATE_FUNCTIONS = {
    "AND": gate_and,
    "OR": gate_or,
    "NOT": gate_not,
    "XOR": gate_xor,
    "NAND": gate_nand,
    "NOR": gate_nor,
}

# Number of inputs each gate type accepts
GATE_INPUT_COUNT = {
    "AND": 2,
    "OR": 2,
    "NOT": 1,
    "XOR": 2,
    "NAND": 2,
    "NOR": 2,
}


class TaskGenerator(BaseGenerator):
    """
    Logic Gate Output task generator.

    Generates circuit diagrams with input values, logic gates, and unknown output.
    Creates animations showing signal propagation through the circuit.
    """

    def __init__(self, config: TaskConfig):
        super().__init__(config)
        self.renderer = ImageRenderer(image_size=config.image_size)

        # Initialize video generator if enabled
        self.video_generator = None
        if config.generate_videos and VideoGenerator.is_available():
            self.video_generator = VideoGenerator(fps=config.video_fps, output_format="mp4")

        # Visual settings
        self.color_zero = config.color_zero
        self.color_one = config.color_one
        self.color_unknown = config.color_unknown
        self.wire_color = (60, 60, 60)  # Dark gray for wires
        self.gate_fill = (240, 240, 240)  # Light gray for gate boxes
        self.gate_border = (40, 40, 40)  # Dark border
        self.bg_color = (255, 255, 255)  # White background

    def generate_task_pair(self, task_id: str) -> TaskPair:
        """Generate one logic gate task pair."""

        # Generate circuit data
        circuit = self._generate_circuit()

        # Render images
        first_image = self._render_circuit(circuit, show_output=False)
        final_image = self._render_circuit(circuit, show_output=True)

        # Generate video (optional)
        video_path = None
        if self.config.generate_videos and self.video_generator:
            video_path = self._generate_video(circuit, task_id)

        # Select prompt based on circuit complexity
        num_gates = len(circuit["gates"])
        if num_gates == 1:
            prompt_type = "single_gate"
        else:
            prompt_type = "multi_gate"
        prompt = get_prompt(prompt_type)

        return TaskPair(
            task_id=task_id,
            domain=self.config.domain,
            prompt=prompt,
            first_image=first_image,
            final_image=final_image,
            ground_truth_video=video_path
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  CIRCUIT GENERATION
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_circuit(self) -> Dict[str, Any]:
        """
        Generate a random logic circuit.

        Returns:
            Circuit dictionary with inputs, gates, and solution.
        """
        # Determine circuit complexity
        num_gates = random.randint(self.config.min_gates, self.config.max_gates)
        num_inputs = random.randint(self.config.min_inputs, self.config.max_inputs)

        # Generate input values
        input_names = [chr(ord('A') + i) for i in range(num_inputs)]
        inputs = {name: random.randint(0, 1) for name in input_names}

        # Generate gates
        gates = []
        available_wires = list(input_names)  # Wires available as inputs to gates
        wire_values = dict(inputs)  # Track computed values

        for i in range(num_gates):
            gate_id = f"G{i + 1}"

            # Choose gate type
            gate_type = random.choice(self.config.gate_types)
            num_gate_inputs = GATE_INPUT_COUNT[gate_type]

            # Select input wires for this gate
            if len(available_wires) < num_gate_inputs:
                # Not enough wires, use what we have (with possible duplicates for 2-input gates)
                gate_inputs = random.choices(available_wires, k=num_gate_inputs)
            else:
                gate_inputs = random.sample(available_wires, num_gate_inputs)

            # Determine output wire name
            if i == num_gates - 1:
                output_wire = "OUT"
            else:
                output_wire = f"W{i + 1}"

            # Compute gate output
            input_values = [wire_values[w] for w in gate_inputs]
            output_value = GATE_FUNCTIONS[gate_type](input_values)
            wire_values[output_wire] = output_value

            gates.append({
                "id": gate_id,
                "type": gate_type,
                "inputs": gate_inputs,
                "output": output_wire,
                "input_values": input_values,
                "output_value": output_value,
            })

            # Add output wire to available wires for next gates
            available_wires.append(output_wire)

        return {
            "inputs": inputs,
            "gates": gates,
            "output_wire": "OUT",
            "solution": wire_values["OUT"],
            "wire_values": wire_values,
        }

    # ══════════════════════════════════════════════════════════════════════════
    #  CIRCUIT RENDERING
    # ══════════════════════════════════════════════════════════════════════════

    def _render_circuit(
        self,
        circuit: Dict[str, Any],
        show_output: bool = False,
        highlighted_wires: Optional[set] = None,
        active_gate: Optional[str] = None,
        gate_rule_text: Optional[str] = None,
    ) -> Image.Image:
        """
        Render the circuit diagram.

        Args:
            circuit: Circuit data dictionary
            show_output: Whether to show the solution or "?"
            highlighted_wires: Set of wire names to highlight with signal colors
            active_gate: ID of gate currently being computed (for highlighting)
            gate_rule_text: Rule text to display near active gate
        """
        width, height = self.config.image_size
        img = Image.new('RGB', (width, height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # Get font
        font = self._get_font(size=16)
        small_font = self._get_font(size=14)
        large_font = self._get_font(size=20)

        # Layout parameters
        margin = 40
        input_x = margin
        output_x = width - margin - 30
        gate_width = 60
        gate_height = 40

        inputs = circuit["inputs"]
        gates = circuit["gates"]
        num_inputs = len(inputs)
        num_gates = len(gates)

        # Calculate positions
        input_spacing = (height - 2 * margin) // (num_inputs + 1)
        input_positions = {}
        for i, name in enumerate(inputs.keys()):
            y = margin + (i + 1) * input_spacing
            input_positions[name] = (input_x, y)

        # Calculate gate positions (spread horizontally)
        gate_region_start = input_x + 80
        gate_region_end = output_x - 80
        gate_spacing = (gate_region_end - gate_region_start) // (num_gates + 1) if num_gates > 0 else 0

        gate_positions = {}
        for i, gate in enumerate(gates):
            x = gate_region_start + (i + 1) * gate_spacing
            # Center gate vertically based on its inputs
            gate_input_wires = gate["inputs"]
            y_positions = []
            for wire in gate_input_wires:
                if wire in input_positions:
                    y_positions.append(input_positions[wire][1])
                elif wire in gate_positions:
                    y_positions.append(gate_positions[wire][1])
            y = sum(y_positions) // len(y_positions) if y_positions else height // 2
            gate_positions[gate["id"]] = (x, y)
            # Also store output wire position
            gate_positions[gate["output"]] = (x + gate_width, y)

        # Output position
        output_y = height // 2
        if gates:
            last_gate = gates[-1]
            if last_gate["output"] in gate_positions:
                output_y = gate_positions[last_gate["output"]][1]

        # Draw title
        draw.text((width // 2, 15), "Logic Circuit", font=large_font, fill=(0, 0, 0), anchor="mm")

        # Draw input wires and labels
        for name, value in inputs.items():
            x, y = input_positions[name]

            # Determine wire color
            if highlighted_wires and name in highlighted_wires:
                wire_color = self.color_one if value == 1 else self.color_zero
            else:
                wire_color = self.wire_color

            # Draw input label (name)
            draw.text((x - 5, y), name, font=font, fill=(0, 0, 0), anchor="rm")

            # Draw input value circle
            circle_r = 12
            circle_color = self.color_one if value == 1 else self.color_zero
            draw.ellipse(
                [x, y - circle_r, x + circle_r * 2, y + circle_r],
                fill=circle_color, outline=(0, 0, 0), width=2
            )
            draw.text((x + circle_r, y), str(value), font=font, fill=(255, 255, 255), anchor="mm")

            # Draw wire extending from input
            wire_start_x = x + circle_r * 2 + 5
            draw.line([(wire_start_x, y), (wire_start_x + 30, y)], fill=wire_color, width=3)

        # Draw gates and connecting wires
        for gate in gates:
            gate_id = gate["id"]
            gate_type = gate["type"]
            gate_x, gate_y = gate_positions[gate_id]

            # Draw input wires to gate
            for i, input_wire in enumerate(gate["inputs"]):
                # Find source position
                if input_wire in input_positions:
                    src_x = input_positions[input_wire][0] + 24 + 35  # After input circle and wire
                    src_y = input_positions[input_wire][1]
                else:
                    # From another gate's output
                    src_x, src_y = gate_positions.get(input_wire, (gate_x - 50, gate_y))

                # Input connection point on gate
                num_gate_inputs = len(gate["inputs"])
                if num_gate_inputs == 1:
                    input_y = gate_y
                else:
                    input_y = gate_y - gate_height // 4 + i * (gate_height // 2)

                # Determine wire color
                wire_value = circuit["wire_values"].get(input_wire, 0)
                if highlighted_wires and input_wire in highlighted_wires:
                    wire_color = self.color_one if wire_value == 1 else self.color_zero
                else:
                    wire_color = self.wire_color

                # Draw wire with right-angle routing
                mid_x = (src_x + gate_x) // 2
                points = [
                    (src_x, src_y),
                    (mid_x, src_y),
                    (mid_x, input_y),
                    (gate_x, input_y)
                ]
                for j in range(len(points) - 1):
                    draw.line([points[j], points[j + 1]], fill=wire_color, width=3)

            # Draw gate box
            is_active = (active_gate == gate_id)
            box_fill = (255, 255, 200) if is_active else self.gate_fill
            border_width = 3 if is_active else 2

            draw.rectangle(
                [gate_x, gate_y - gate_height // 2, gate_x + gate_width, gate_y + gate_height // 2],
                fill=box_fill, outline=self.gate_border, width=border_width
            )

            # Draw gate label
            draw.text(
                (gate_x + gate_width // 2, gate_y),
                gate_type, font=font, fill=(0, 0, 0), anchor="mm"
            )

            # Draw output wire from gate
            output_wire = gate["output"]
            out_x = gate_x + gate_width

            if output_wire == "OUT":
                # Connect to final output
                wire_end_x = output_x - 30
            else:
                # Intermediate wire
                wire_end_x = out_x + 30

            # Determine output wire color
            output_value = gate["output_value"]
            if highlighted_wires and output_wire in highlighted_wires:
                wire_color = self.color_one if output_value == 1 else self.color_zero
            else:
                wire_color = self.wire_color

            draw.line([(out_x, gate_y), (wire_end_x, gate_y)], fill=wire_color, width=3)

            # Draw rule text if this is the active gate
            if is_active and gate_rule_text:
                rule_y = gate_y + gate_height // 2 + 20
                draw.text(
                    (gate_x + gate_width // 2, rule_y),
                    gate_rule_text, font=small_font, fill=(0, 100, 0), anchor="mm"
                )

        # Draw output section
        # Draw wire to output
        if gates:
            last_gate = gates[-1]
            last_gate_x, last_gate_y = gate_positions[last_gate["id"]]
            wire_start_x = last_gate_x + gate_width + 30
            wire_start_y = last_gate_y
        else:
            wire_start_x = input_x + 100
            wire_start_y = height // 2

        # Output wire
        output_value = circuit["solution"]
        if highlighted_wires and "OUT" in highlighted_wires:
            wire_color = self.color_one if output_value == 1 else self.color_zero
        else:
            wire_color = self.wire_color

        draw.line([(wire_start_x, wire_start_y), (output_x - 25, output_y)], fill=wire_color, width=3)

        # Draw output circle with value or "?"
        circle_r = 15
        if show_output:
            circle_color = self.color_one if output_value == 1 else self.color_zero
            display_value = str(output_value)
        else:
            circle_color = self.color_unknown
            display_value = "?"

        draw.ellipse(
            [output_x - circle_r, output_y - circle_r, output_x + circle_r, output_y + circle_r],
            fill=circle_color, outline=(0, 0, 0), width=2
        )
        draw.text((output_x, output_y), display_value, font=large_font, fill=(255, 255, 255), anchor="mm")

        # Draw "Output" label
        draw.text((output_x, output_y + circle_r + 15), "OUT", font=font, fill=(0, 0, 0), anchor="mm")

        return img

    def _get_font(self, size: int = 16) -> ImageFont.FreeTypeFont:
        """Get a font for rendering text."""
        font_names = [
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "Arial.ttf",
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

    def _generate_video(self, circuit: Dict[str, Any], task_id: str) -> Optional[str]:
        """
        Generate animation video showing signal propagation.

        The animation shows:
        1. Initial state with inputs highlighted
        2. Signal propagation through each gate
        3. Final output revealed
        """
        temp_dir = Path(tempfile.gettempdir()) / f"{self.config.domain}_videos"
        temp_dir.mkdir(parents=True, exist_ok=True)
        video_path = temp_dir / f"{task_id}_ground_truth.mp4"

        frames = self._create_animation_frames(circuit)

        result = self.video_generator.create_video_from_frames(frames, video_path)
        return str(result) if result else None

    def _create_animation_frames(self, circuit: Dict[str, Any]) -> List[Image.Image]:
        """
        Create animation frames for signal propagation.
        """
        frames = []
        hold_frames = self.config.hold_frames
        propagation_frames = self.config.propagation_frames

        inputs = circuit["inputs"]
        gates = circuit["gates"]

        # Phase 1: Initial state (inputs not highlighted yet)
        for _ in range(hold_frames):
            frame = self._render_circuit(circuit, show_output=False)
            frames.append(frame)

        # Phase 2: Highlight inputs
        highlighted = set(inputs.keys())
        for _ in range(hold_frames):
            frame = self._render_circuit(circuit, show_output=False, highlighted_wires=highlighted)
            frames.append(frame)

        # Phase 3: Process each gate
        for gate in gates:
            gate_id = gate["id"]
            gate_type = gate["type"]
            input_values = tuple(gate["input_values"])
            output_wire = gate["output"]

            # Get rule text
            rule_text = get_gate_rule(gate_type, input_values)

            # Show gate active with rule
            for _ in range(propagation_frames):
                frame = self._render_circuit(
                    circuit,
                    show_output=False,
                    highlighted_wires=highlighted,
                    active_gate=gate_id,
                    gate_rule_text=rule_text
                )
                frames.append(frame)

            # Add output wire to highlighted set
            highlighted.add(output_wire)

            # Show result propagating
            for _ in range(hold_frames):
                frame = self._render_circuit(
                    circuit,
                    show_output=(output_wire == "OUT"),
                    highlighted_wires=highlighted
                )
                frames.append(frame)

        # Phase 4: Final state with output revealed
        for _ in range(hold_frames * 2):
            frame = self._render_circuit(circuit, show_output=True, highlighted_wires=highlighted)
            frames.append(frame)

        return frames
