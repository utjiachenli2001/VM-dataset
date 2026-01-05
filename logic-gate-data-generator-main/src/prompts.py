"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           YOUR TASK PROMPTS                                   ║
║                                                                               ║
║  Logic Gate Output Task Prompts                                               ║
║  Prompts are selected based on task type and returned to the model.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random


# ══════════════════════════════════════════════════════════════════════════════
#  DEFINE YOUR PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "default": [
        "Trace the signal through the logic circuit to determine the output value. Follow each input through its gates, applying the correct logic operation, until you reach the final output.",
        "Analyze this logic circuit diagram. Starting from the input values (0 or 1), apply the logic gate rules to compute the final output that replaces the '?'.",
        "Determine the output of this logic circuit. Trace the signal flow from left to right, applying each gate's operation to find the result.",
    ],

    "single_gate": [
        "This circuit has a single logic gate. Apply the gate's rule to the input values to find the output.",
        "Compute the output of this single-gate circuit by applying the logic operation to the inputs.",
    ],

    "multi_gate": [
        "This circuit contains multiple logic gates. Trace the signals step by step through each gate to determine the final output.",
        "Follow the signal flow through this multi-gate circuit. Compute each intermediate result until you reach the final output.",
    ],

    "AND": [
        "This circuit uses AND gates. Remember: AND outputs 1 only when ALL inputs are 1.",
    ],

    "OR": [
        "This circuit uses OR gates. Remember: OR outputs 1 when AT LEAST ONE input is 1.",
    ],

    "NOT": [
        "This circuit uses NOT gates. Remember: NOT flips the input (0→1, 1→0).",
    ],

    "XOR": [
        "This circuit uses XOR gates. Remember: XOR outputs 1 when inputs are DIFFERENT.",
    ],

    "NAND": [
        "This circuit uses NAND gates. Remember: NAND is NOT-AND, outputs 0 only when ALL inputs are 1.",
    ],

    "NOR": [
        "This circuit uses NOR gates. Remember: NOR is NOT-OR, outputs 1 only when ALL inputs are 0.",
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIC GATE RULES (for display during animation)
# ══════════════════════════════════════════════════════════════════════════════

GATE_RULES = {
    "AND": {
        (0, 0): "AND: 0∧0=0",
        (0, 1): "AND: 0∧1=0",
        (1, 0): "AND: 1∧0=0",
        (1, 1): "AND: 1∧1=1",
    },
    "OR": {
        (0, 0): "OR: 0∨0=0",
        (0, 1): "OR: 0∨1=1",
        (1, 0): "OR: 1∨0=1",
        (1, 1): "OR: 1∨1=1",
    },
    "NOT": {
        (0,): "NOT: ¬0=1",
        (1,): "NOT: ¬1=0",
    },
    "XOR": {
        (0, 0): "XOR: 0⊕0=0",
        (0, 1): "XOR: 0⊕1=1",
        (1, 0): "XOR: 1⊕0=1",
        (1, 1): "XOR: 1⊕1=0",
    },
    "NAND": {
        (0, 0): "NAND: ¬(0∧0)=1",
        (0, 1): "NAND: ¬(0∧1)=1",
        (1, 0): "NAND: ¬(1∧0)=1",
        (1, 1): "NAND: ¬(1∧1)=0",
    },
    "NOR": {
        (0, 0): "NOR: ¬(0∨0)=1",
        (0, 1): "NOR: ¬(0∨1)=0",
        (1, 0): "NOR: ¬(1∨0)=0",
        (1, 1): "NOR: ¬(1∨1)=0",
    },
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


def get_gate_rule(gate_type: str, inputs: tuple) -> str:
    """
    Get the rule text for a specific gate operation.

    Args:
        gate_type: Type of gate (AND, OR, NOT, etc.)
        inputs: Tuple of input values

    Returns:
        Rule text string (e.g., "AND: 1∧1=1")
    """
    gate_rules = GATE_RULES.get(gate_type, {})
    return gate_rules.get(inputs, f"{gate_type}: {inputs}")
