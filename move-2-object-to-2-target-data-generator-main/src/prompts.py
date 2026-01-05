"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK PROMPTS                                   ║
║                                                                               ║
║  CUSTOMIZE THIS FILE to define prompts/instructions for your task.            ║
║  Task: Move 2 objects (circles) to their corresponding target ring positions. ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Move both balls to their matching target rings. Each object should slide smoothly in a straight line until it reaches its corresponding dashed circle.",
        "Animate both objects moving to their destinations. Each ball should travel directly to its matching target ring and stop inside it.",
        "Show both spheres moving to their target positions. They should glide smoothly from their starting points to their corresponding dashed rings.",
        "Guide both balls to their collection zones. Each object should move in a straight path until it aligns with its matching target ring.",
        "Animate both balls sliding into their target areas. The movements should be smooth and direct, with each ball ending inside its corresponding dashed circle.",
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


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
