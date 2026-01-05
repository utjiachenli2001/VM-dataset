# Logic Gate Data Generator

A logic circuit puzzle generator for training and evaluating video generation models on logical reasoning tasks. Based on the template-data-generator framework.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/logic-gate-data-generator.git
cd logic-gate-data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate logic gate tasks
python examples/generate.py --num-samples 50
```

### Output

Generated logic circuit puzzles will be saved to `data/questions/logic_gate_task/` with:
- **first_frame.png**: Circuit diagram with input values and "?" at output
- **final_frame.png**: Circuit diagram with solved output value
- **prompt.txt**: Instructions for tracing the circuit
- **ground_truth.mp4**: Video showing signal propagation (optional)

---

## Structure

```
logic-gate-data-generator/
├── core/                    # Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # Logic gate implementation
│   ├── generator.py        # Circuit generator and renderer
│   ├── prompts.py          # Logic gate prompts and rules
│   └── config.py           # Task configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── logic_gate_task/
        └── logic_gate_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## Output Format

Each logic gate task produces:

```
data/questions/logic_gate_task/logic_gate_XXXX/
├── first_frame.png          # Circuit with "?" at output
├── final_frame.png          # Circuit with solved output
├── prompt.txt               # Tracing instructions
└── ground_truth.mp4         # Signal propagation video (optional)
```

### Visual Elements

- **Blue circle (0)**: Signal value 0 (Royal Blue: `#4169E1`)
- **Red circle (1)**: Signal value 1 (Crimson: `#DC143C`)
- **Gray circle (?)**: Unknown output value
- **Rectangles**: Logic gates with type labels (AND, OR, NOT, etc.)
- **Dark lines**: Wires connecting components

---

## Configuration

### Logic Gate Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Gate types to include
    gate_types: List[str] = Field(
        default=["AND", "OR", "NOT", "XOR", "NAND", "NOR"]
    )

    # Circuit complexity
    min_gates: int = Field(default=1)   # Minimum gates per circuit
    max_gates: int = Field(default=4)   # Maximum gates per circuit
    min_inputs: int = Field(default=2)  # Minimum input wires
    max_inputs: int = Field(default=4)  # Maximum input wires

    # Colors
    color_zero: tuple = Field(default=(65, 105, 225))   # Blue
    color_one: tuple = Field(default=(220, 20, 60))     # Red
    color_unknown: tuple = Field(default=(128, 128, 128)) # Gray

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
    hold_frames: int = Field(default=5)
    propagation_frames: int = Field(default=15)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_circuits

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## Supported Logic Gates

| Gate | Symbol | Rule | Example |
|------|--------|------|---------|
| **AND** | ∧ | Output 1 only if ALL inputs are 1 | 1∧1=1, 1∧0=0 |
| **OR** | ∨ | Output 1 if AT LEAST ONE input is 1 | 0∨1=1, 0∨0=0 |
| **NOT** | ¬ | Flip the input value | ¬0=1, ¬1=0 |
| **XOR** | ⊕ | Output 1 if inputs are DIFFERENT | 0⊕1=1, 1⊕1=0 |
| **NAND** | ¬∧ | NOT of AND | ¬(1∧1)=0 |
| **NOR** | ¬∨ | NOT of OR | ¬(0∨0)=1 |

---

## Video Generation

Optional ground truth videos show signal propagation:
1. **Initial state**: All inputs displayed with values
2. **Input highlighting**: Input wires light up with colors (Blue=0, Red=1)
3. **Gate processing**: Each gate highlights, shows rule text (e.g., "AND: 1∧0=0")
4. **Output propagation**: Result flows through to next gate or final output
5. **Final state**: Output value revealed, full path highlighted

### Animation Settings

- `hold_frames`: Frames to pause at start/end of each phase (default: 5)
- `propagation_frames`: Frames for each gate's processing animation (default: 15)
- `video_fps`: Frame rate (default: 10)

---

## Circuit Generation Algorithm

1. **Determine complexity**: Random number of gates (1-4) and inputs (2-4)
2. **Generate inputs**: Assign random values (0 or 1) to input wires A, B, C, ...
3. **Build gates**: For each gate:
   - Select random gate type from allowed types
   - Choose input wires from available wires (inputs + previous gate outputs)
   - Compute output value using gate logic
   - Add output wire to available wires for subsequent gates
4. **Final output**: Last gate's output becomes circuit output

---

## Example Circuit

```
     A ──1──┐
            ├──[AND]──W1──┐
     B ──0──┘             ├──[OR]── ? (output)
                          │
     C ──1────────────────┘

Solution: AND(1,0)=0, then OR(0,1)=1
Output: 1
```

---

## References

- **Boolean Algebra**: [Wikipedia](https://en.wikipedia.org/wiki/Boolean_algebra)
- **Logic Gates**: [Wikipedia](https://en.wikipedia.org/wiki/Logic_gate)
- **Digital Circuit Design**: [All About Circuits](https://www.allaboutcircuits.com/textbook/digital/)
