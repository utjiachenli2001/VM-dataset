"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           CELL DIVISION TASK PROMPTS                         ║
║                                                                              ║
║  Bio_Cell_1: Predict Division Stage                                          ║
║  Prompts for mitosis cell division prediction tasks.                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Predict what the cell will look like in the next stage of mitosis. "
        "Animate the transition showing how chromosomes and cellular structures "
        "change as the cell progresses through division.",

        "Show the cell transitioning to the next phase of cell division. "
        "The animation should accurately depict the movement of chromosomes "
        "and changes in cellular structures.",

        "Animate the progression of this cell to the next mitotic stage. "
        "Show how the chromosomes, spindle fibers, and cell membrane change "
        "during the transition.",
    ],

    "interphase": [
        "The cell is in Interphase with intact nucleus and diffuse chromatin. "
        "Animate the transition to Prophase, showing chromosomes condensing "
        "and becoming visible as distinct structures.",

        "Show the cell leaving Interphase and entering Prophase. "
        "The chromatin should condense into visible chromosomes and the "
        "nuclear envelope should begin to break down.",
    ],

    "prophase": [
        "The cell is in Prophase with condensed chromosomes visible. "
        "Animate the transition to Metaphase, showing chromosomes aligning "
        "at the cell's equator (metaphase plate).",

        "Show the cell progressing from Prophase to Metaphase. "
        "The chromosomes should move toward the center and line up "
        "along the middle of the cell, attached to spindle fibers.",
    ],

    "metaphase": [
        "The cell is in Metaphase with chromosomes aligned at the center. "
        "Animate the transition to Anaphase, showing sister chromatids "
        "separating and moving toward opposite poles.",

        "Show the dramatic transition from Metaphase to Anaphase. "
        "The chromosomes should split at their centromeres, with each "
        "half moving toward opposite ends of the cell.",
    ],

    "anaphase": [
        "The cell is in Anaphase with separated chromatids moving to poles. "
        "Animate the transition to Telophase, showing chromatids reaching "
        "the poles and nuclear envelopes beginning to reform.",

        "Show the cell completing Anaphase and entering Telophase. "
        "The chromosomes should reach the poles, nuclear membranes should "
        "reform, and the cell should begin to pinch in the middle.",
    ],

    "telophase": [
        "The cell is in Telophase with chromosomes at poles and the cell pinching. "
        "Animate the completion of division and return to Interphase, "
        "showing the chromosomes decondensing within the new nuclei.",

        "Show the cell completing Telophase and cytokinesis, transitioning "
        "back to Interphase. The chromosomes should decondense and the "
        "nuclear envelopes should fully reform.",
    ],
}


# Stage display names for labels
STAGE_NAMES = {
    "interphase": "INTERPHASE",
    "prophase": "PROPHASE",
    "metaphase": "METAPHASE",
    "anaphase": "ANAPHASE",
    "telophase": "TELOPHASE",
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.

    Args:
        task_type: Type of task (key in PROMPTS dict, typically the stage name)

    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type.lower(), PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type.lower(), PROMPTS["default"])


def get_stage_name(stage: str) -> str:
    """Get display name for a stage."""
    return STAGE_NAMES.get(stage.lower(), stage.upper())
