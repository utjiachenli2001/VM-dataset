"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN PROMPTS                                ║
║                                                                               ║
║  Prompts for Domino Chain Gap Analysis task.                                  ║
║  Prompts are selected based on task type and returned to the model.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Analyze the domino chain and determine which domino is the last to fall. "
        "Look for gaps in the spacing that would stop the chain reaction. "
        "Push the first domino and show the chain reaction stopping at the gap.",

        "Push the first domino and predict where the chain reaction stops. "
        "Identify the gap that prevents the chain from continuing. "
        "Animate the dominos falling until they reach the break point.",

        "Find the break point in this domino chain. Which domino falls last before "
        "the gap stops the reaction? Show the chain reaction and highlight where it ends.",

        "Examine the spacing between dominos to find where the chain will break. "
        "Animate the first domino being pushed and show each domino falling in sequence "
        "until the gap prevents further progress.",
    ],

    "analysis": [
        "Study the domino arrangement carefully. One gap is too wide for the chain "
        "reaction to continue. Push the first domino and show exactly where the "
        "chain stops, highlighting the problematic gap.",

        "This domino chain has a hidden break point. Analyze the distances between "
        "dominos, push the first one, and demonstrate which domino is the last to fall "
        "before the chain reaction fails.",
    ],

    "prediction": [
        "Before pushing the first domino, identify which domino will be the last to fall. "
        "Then animate the chain reaction to verify your prediction, showing the gap "
        "that stops the chain.",

        "Predict the stopping point of this domino chain by examining the spacing. "
        "Show the animation of dominos falling and confirm where the chain breaks "
        "due to excessive distance between dominos.",
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
