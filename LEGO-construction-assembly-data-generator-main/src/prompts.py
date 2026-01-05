"""
LEGO Construction Assembly Task Prompts

Defines instruction-style prompts for LEGO building steps.
"""

import random


# Prompts organized by context
PROMPTS = {
    "default": [
        "Follow this LEGO instruction step: take the highlighted piece and attach it to the model at the indicated position. The piece should move smoothly to its destination, rotate to align correctly, and snap into place.",
        "Complete this building step by placing the shown brick onto the partially-built model. Follow the arrow indicator to find the correct attachment point, then connect the piece securely.",
        "Animate this LEGO construction step. Pick up the highlighted piece, move it toward the model following the arrow guide, and snap it into the correct position to continue the build.",
    ],

    "single_piece": [
        "Place the single brick shown in the callout onto the model. Follow the arrow to the attachment point, align the studs, and snap the piece into place.",
        "Attach the highlighted brick to complete this step. Move the piece to where the arrow indicates and connect it to the existing structure.",
        "This step adds one brick. Take the piece from the parts area, follow the placement arrow, and click it into position on the model.",
    ],

    "multiple_pieces": [
        "This step requires multiple pieces. Add each highlighted brick one at a time, following the arrows to their respective attachment points on the model.",
        "Place all shown pieces onto the model. Pick up each brick, move it to the indicated position, and snap it into place before proceeding to the next piece.",
        "Complete this multi-piece step by attaching all highlighted bricks. Follow the visual guides for each piece's destination and orientation.",
    ],

    "tower": [
        "Continue building the tower by stacking the next brick. Align the studs with the brick below and press down to connect.",
        "Add the next layer to the tower structure. The new brick should stack directly on top of the previous one.",
    ],

    "wall": [
        "Extend the wall by placing the brick at the indicated position. Ensure proper alignment with adjacent bricks.",
        "Add this brick to continue the wall construction. Follow the arrow to see where it connects to the existing structure.",
    ],

    "car": [
        "Attach this piece to the vehicle. Follow the arrow to see where it connects - this could be part of the body, wheels, or cabin.",
        "Continue building the car by adding the highlighted piece. Snap it into the correct position on the chassis or body.",
    ],

    "stairs": [
        "Add the next step to the staircase structure. Each brick should be offset to create the ascending pattern.",
        "Place this brick to extend the stairs. It should connect at the correct height to maintain the stepping pattern.",
    ],

    "bridge": [
        "Add this piece to the bridge structure. Follow the arrow to see where it connects to support the span.",
        "Continue the bridge construction by placing the brick at the indicated position.",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.

    Args:
        task_type: Type of task (key in PROMPTS dict)

    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
