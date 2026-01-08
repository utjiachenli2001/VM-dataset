"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           LEVER TASK PROMPTS                                  ║
║                                                                               ║
║  Prompts for lever/torque balance reasoning tasks.                            ║
║  Prompts are selected based on task type and returned to the model.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Calculate the torque on each side of the lever using the formula: Torque = Weight × Distance. Compare the total torques and animate the lever tipping toward the side with greater torque.",
        "Using the lever arm principle, determine which side has greater torque. Show the lever rotating to its final position based on the torque imbalance.",
        "Analyze the balance of this lever system. Calculate Weight × Distance for each object, sum the torques on each side, and animate the result.",
    ],

    "tips_left": [
        "The left side has greater total torque. Animate the lever tipping down on the left side, showing how the combined effect of weight and distance determines the outcome.",
        "Calculate the torques: the left side's Weight × Distance sum exceeds the right. Show the lever rotating counterclockwise until the left side is down.",
        "Demonstrate the lever arm principle: despite potentially lighter weights, the left side tips down due to greater total torque (Weight × Distance).",
    ],

    "tips_right": [
        "The right side has greater total torque. Animate the lever tipping down on the right side, demonstrating the lever arm principle in action.",
        "Calculate the torques: the right side's Weight × Distance sum exceeds the left. Show the lever rotating clockwise until the right side is down.",
        "Demonstrate how distance amplifies force: the right side tips down because its total torque (Weight × Distance) is greater.",
    ],

    "balanced": [
        "This lever is perfectly balanced! The total torque on the left equals the total torque on the right. Show the lever remaining horizontal, demonstrating equilibrium.",
        "Calculate the torques on both sides - they are equal! Animate the lever staying balanced, as the Weight × Distance products cancel out.",
        "A balanced lever: the left and right torques are equal. The lever remains horizontal, showing that balance depends on BOTH weight AND distance.",
    ],

    "counterintuitive": [
        "This problem demonstrates a key physics principle: a lighter weight far from the fulcrum can balance or outweigh a heavier weight close to the fulcrum. Calculate the torques and show the result.",
        "Distance matters! Even though one side may have heavier objects, the torque depends on Weight × Distance. Calculate both sides and animate accordingly.",
        "The lever arm principle in action: observe how position affects balance. A small weight at a large distance creates significant torque.",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.

    Args:
        task_type: Type of task (key in PROMPTS dict)
            - "default": General torque calculation prompts
            - "tips_left": When left side tips down
            - "tips_right": When right side tips down
            - "balanced": When torques are equal
            - "counterintuitive": When lighter side tips down

    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
