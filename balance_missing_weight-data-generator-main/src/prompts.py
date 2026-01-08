"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        BALANCE SCALE TASK PROMPTS                             ║
║                                                                               ║
║  Prompts for the "Find Missing Weight" balance scale puzzle.                  ║
║  Prompts describe the task and expected solution process.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Calculate the missing weight marked '?' to balance the scale. Show the step-by-step solution: calculate the heavy side total, identify known weights on the light side, set up the equation, solve for the unknown, then animate the scale reaching equilibrium.",
        "Find the unknown weight that will make both sides equal. Display the arithmetic steps, reveal the answer by replacing '?' with the correct value, and animate the scale becoming perfectly horizontal.",
        "Solve for the missing weight on the balance scale. First calculate the total on the heavy side, then determine what value '?' must be to achieve balance. Show the equation and animate the final balanced state.",
        "Determine the unknown weight needed to balance the scale. Work through the problem step by step: sum the heavy side, identify the known light side weights, solve the equation, and show the scale leveling out when the correct weight is found.",
        "What weight should replace '?' to balance the scale? Calculate the difference between the heavy side total and the known weights on the light side. Animate the solution by showing '?' transform into the correct value and the scale becoming horizontal.",
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
