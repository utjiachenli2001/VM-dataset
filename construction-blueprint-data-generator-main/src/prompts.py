"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK PROMPTS                                   ║
║                                                                               ║
║  Construction Blueprint - Missing Piece Task                                  ║
║  Prompts for selecting the correct piece to fill the gap in a structure       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Examine the structure with the missing piece. Compare each candidate piece to the gap and select the one that fits perfectly. Animate the correct piece moving into place to complete the structure.",
        "A structure is shown with one piece missing (indicated by dashed outline). Four candidate pieces are displayed below. Find the piece that exactly matches the gap shape and size, then show it fitting into place.",
        "Identify which of the four candidate pieces correctly fills the highlighted gap in the structure. The correct piece should match the gap's exact shape. Animate the selection process and final placement.",
        "Look at the incomplete structure with the marked gap. Analyze each candidate piece below and determine which one will complete the structure. Show the matching piece sliding into the gap.",
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
