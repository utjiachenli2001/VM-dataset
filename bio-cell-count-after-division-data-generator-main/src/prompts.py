"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      BIO_CELL TASK PROMPTS                                   ║
║                                                                              ║
║  Educational prompts for cell division counting task.                        ║
║  Focuses on exponential growth formula: Final = Initial × 2^N               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Watch the cells divide {n} time{s}. Starting with {initial} cell{s_init}, calculate the final count using the formula: Initial × 2^N.",
        "Observe {initial} cell{s_init} undergoing {n} division cycle{s}. Each cell divides into 2. What is the final cell count?",
        "Animate the cell division process: {initial} cell{s_init} will divide {n} time{s}. Show the exponential growth and display the final count.",
        "Simulate mitosis: Starting with {initial} cell{s_init}, each divides into 2 daughter cells. After {n} cycle{s}, how many cells are there?",
    ],

    "educational": [
        "Cell Division Challenge: {initial} cell{s_init} × 2^{n} = ? Watch the division process and verify the exponential growth formula.",
        "Biology Reasoning: If {initial} cell{s_init} undergo{s_verb} {n} rounds of mitosis, and each division doubles the count, what is the final population?",
        "Exponential Growth Demo: Observe how {initial} starting cell{s_init} become{s_verb2} many more after {n} division{s}. Calculate: {initial} × 2^{n}.",
    ],

    "simple": [
        "Count the cells after {n} division{s}. Start: {initial} cell{s_init}.",
        "{initial} cell{s_init} divide{s_verb} {n} time{s}. Final count = ?",
        "Division cycles: {n}. Initial cells: {initial}. Calculate the result.",
    ],
}


def get_prompt(initial_cells: int = 1, num_divisions: int = 1, prompt_type: str = None) -> str:
    """
    Generate a prompt for the cell division task.

    Args:
        initial_cells: Number of starting cells
        num_divisions: Number of division cycles (N)
        prompt_type: Optional prompt category ("default", "educational", "simple")

    Returns:
        Formatted prompt string
    """
    # Select prompt type
    if prompt_type is None:
        prompt_type = random.choice(list(PROMPTS.keys()))

    prompts = PROMPTS.get(prompt_type, PROMPTS["default"])
    template = random.choice(prompts)

    # Format placeholders
    formatted = template.format(
        initial=initial_cells,
        n=num_divisions,
        s="" if num_divisions == 1 else "s",
        s_init="" if initial_cells == 1 else "s",
        s_verb="s" if initial_cells == 1 else "",
        s_verb2="s" if initial_cells == 1 else "",
    )

    return formatted


def get_all_prompts() -> dict[str, list[str]]:
    """Get all prompt templates organized by type."""
    return PROMPTS.copy()
