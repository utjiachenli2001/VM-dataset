"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK PROMPTS                                   ║
║                                                                               ║
║  Prompts for Construction_Stack_1: Block Rearrangement Task                   ║
║  Prompts are selected based on task type and returned to the model.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Rearrange the colored blocks from the CURRENT state to match the TARGET state. "
        "Only the topmost block of any stack can be moved at a time. "
        "Move blocks one by one: lift up, move horizontally, then lower onto the destination stack. "
        "Minimize the total number of moves.",

        "Transform the left stack arrangement into the target arrangement shown on the right. "
        "You can only move the top block from any stack. "
        "Each move consists of lifting a block, moving it to another stack, and placing it on top. "
        "Complete the rearrangement in as few moves as possible.",

        "Solve this block stacking puzzle by moving blocks from CURRENT to match TARGET. "
        "Rules: Only the top block of a stack can be moved. "
        "Blocks can be placed on any stack or empty position. "
        "Show each move clearly: lift, translate, and lower the block.",
    ],

    "easy": [
        "Simple block rearrangement: Move the blocks to match the target configuration. "
        "Only move one block at a time from the top of any stack. "
        "This puzzle requires just a few moves to solve.",

        "Rearrange these blocks to match the target. "
        "Pick up the top block, move it to another stack, and place it down. "
        "Find the shortest sequence of moves.",
    ],

    "medium": [
        "Rearrange the block stacks to match the target state. "
        "Only the topmost block can be moved at any time. "
        "Use the available stacks strategically to minimize moves. "
        "Plan your moves carefully before starting.",

        "Transform the current block arrangement into the target. "
        "Move one block at a time, always from the top of a stack. "
        "You may need to temporarily move blocks to intermediate stacks.",
    ],

    "hard": [
        "Solve this challenging block rearrangement puzzle. "
        "The current state must be transformed to match the target exactly. "
        "Only top blocks can be moved, one at a time. "
        "Optimal solving requires careful planning and minimal moves.",

        "Complex block stacking challenge: Rearrange all blocks to match the target. "
        "Use the Tower of Hanoi principle - only move top blocks. "
        "Find the most efficient sequence of moves to solve this puzzle.",
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
