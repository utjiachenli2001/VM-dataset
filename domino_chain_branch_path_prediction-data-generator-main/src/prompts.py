"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           DOMINO CHAIN PROMPTS                                ║
║                                                                               ║
║  Prompts for the Domino Chain Branch Path Prediction task.                    ║
║  Focused on predicting which dominos will fall.                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Push the START domino to begin the chain reaction. The dominos will fall in sequence, splitting at the junction point into two branches. Predict and show which dominos will fall and which will remain standing.",
        "Initiate the chain reaction by pushing the START domino. Watch as the falling dominos reach the junction and split into two parallel paths. Show the final state with all fallen dominos.",
        "Begin the domino chain by toppling START. The reaction will propagate through the trunk and branch into two directions at the junction. Animate which dominos fall and identify any that remain standing.",
    ],

    "blocked": [
        "Push the START domino. The chain reaction will split at the junction, but one branch has a gap that will stop the chain. Show which dominos fall and which remain standing due to the blocked path.",
        "Initiate the chain from START. As the dominos fall and split at the junction, notice that one branch is incomplete. Predict and display which dominos will fall and which will be left standing.",
        "Start the chain reaction. The dominos will propagate and branch, but a gap in one path will prevent some dominos from falling. Show the final state with fallen and standing dominos clearly marked.",
    ],

    "complete": [
        "Push START to begin the chain. Both branches will complete successfully as all dominos are properly connected. Show the full chain reaction with all dominos falling.",
        "Initiate the complete chain reaction from START. Watch both branches fall in parallel as the reaction splits at the junction. All dominos will fall - animate the full sequence.",
        "Begin the domino chain by pushing START. The reaction propagates through the trunk, splits at the junction, and completes both branches. Show all dominos falling in sequence.",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.

    Args:
        task_type: Type of task - "default", "blocked", or "complete"

    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
