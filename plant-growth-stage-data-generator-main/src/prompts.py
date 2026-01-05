"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           BIO_GROWTH TASK PROMPTS                             ║
║                                                                               ║
║  Prompts for plant growth stage prediction task.                              ║
║  Each transition has specific prompts describing the expected growth.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  GROWTH STAGES (in order)
# ══════════════════════════════════════════════════════════════════════════════

STAGES = [
    "seed",
    "germination",
    "sprout",
    "seedling",
    "vegetative",
    "flowering",
    "fruiting",
    "mature",
]


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE PROMPTS FOR EACH STAGE TRANSITION
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Animate the plant growing to its next developmental stage. Show the natural progression with appropriate changes in roots, stem, and leaves.",
        "Show a time-lapse of the plant advancing to the next growth stage. The transition should display realistic biological development.",
    ],

    "seed_to_germination": [
        "Animate the seed beginning to germinate. A small root (radicle) should emerge from the seed and start growing downward into the soil.",
        "Show the seed cracking open as germination begins. The first root tip should appear and extend downward, anchoring into the soil.",
        "Display the germination process where the seed coat splits and a tiny root emerges, reaching down into the earth.",
    ],

    "germination_to_sprout": [
        "Animate the germinated seed developing into a sprout. The stem should push upward through the soil surface while roots continue to grow down.",
        "Show the sprout breaking through the soil surface. The stem emerges carrying the seed leaves (cotyledons) into the light.",
        "Display the transition from germination to sprout as the young plant pushes through the earth, with cotyledons beginning to unfold.",
    ],

    "sprout_to_seedling": [
        "Animate the sprout growing into a seedling. True leaves should develop while the stem grows taller and the root system expands.",
        "Show the sprout developing its first true leaves. The plant grows taller, cotyledons may wither, and proper leaves emerge.",
        "Display the seedling stage emerging as true leaves appear above the cotyledons and the root system branches underground.",
    ],

    "seedling_to_vegetative": [
        "Animate the seedling entering vigorous vegetative growth. The stem thickens, leaves grow larger, and the root system expands significantly.",
        "Show the plant transitioning to vegetative stage with rapid growth. More leaves develop, the stem strengthens, and roots spread deeper.",
        "Display the vegetative growth phase beginning. The plant becomes bushier with larger leaves and a more robust root network.",
    ],

    "vegetative_to_flowering": [
        "Animate the vegetative plant beginning to flower. Flower buds should form and gradually open into blossoms while the plant maintains its foliage.",
        "Show the transition to flowering stage. Buds appear at growing points and slowly open to reveal colorful flowers.",
        "Display the flowering process as the mature plant develops buds that unfurl into beautiful blooms, signaling reproductive maturity.",
    ],

    "flowering_to_fruiting": [
        "Animate the flowers transforming into fruits. Petals fall away as the flower base swells and develops into young fruit.",
        "Show the fruiting stage beginning as pollinated flowers develop into small fruits. The fruits should grow larger over time.",
        "Display the transition from flowering to fruiting. Flowers fade and fruits emerge, gradually increasing in size.",
    ],

    "fruiting_to_mature": [
        "Animate the plant reaching full maturity. Fruits ripen to their final color and size, representing a complete growth cycle.",
        "Show the final maturation stage. Fruits become fully ripe and the plant reaches its maximum development.",
        "Display the plant completing its growth cycle with mature, ripe fruits ready for harvest.",
    ],
}


def get_transition_key(current_stage: str, next_stage: str) -> str:
    """Get the prompt key for a stage transition."""
    return f"{current_stage}_to_{next_stage}"


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.

    Args:
        task_type: Type of task - either "default" or a transition key like "seed_to_germination"

    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_prompt_for_transition(current_stage: str, next_stage: str) -> str:
    """
    Get a prompt specifically for a stage transition.

    Args:
        current_stage: Current growth stage name
        next_stage: Next growth stage name

    Returns:
        Random prompt for this specific transition
    """
    key = get_transition_key(current_stage, next_stage)
    return get_prompt(key)


def get_all_prompts(task_type: str = "default") -> list:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])


def get_stage_index(stage_name: str) -> int:
    """Get the index of a stage (0-7)."""
    return STAGES.index(stage_name)


def get_stage_name(index: int) -> str:
    """Get stage name by index."""
    return STAGES[index]


def get_next_stage(current_stage: str) -> str:
    """Get the next stage after the current one. Returns None if at mature stage."""
    idx = get_stage_index(current_stage)
    if idx >= len(STAGES) - 1:
        return None
    return STAGES[idx + 1]
