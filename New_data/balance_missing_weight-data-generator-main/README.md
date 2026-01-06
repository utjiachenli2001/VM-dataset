# Balance Scale Missing Weight Data Generator ⚖️

A balance scale puzzle generator for training and evaluating video generation models on mathematical reasoning tasks. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/balance-scale-data-generator.git
cd balance-scale-data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate balance scale tasks
python examples/generate.py --num-samples 50
```

### Output

Generated puzzles will be saved to `data/questions/balance_scale_task/` with:
- **first_frame.png**: Tilted scale with unknown weight marked "?"
- **final_frame.png**: Balanced horizontal scale with solved weight
- **prompt.txt**: Problem-solving instructions
- **ground_truth.mp4**: Video showing step-by-step solution (optional)

---

## 📁 Structure

```
balance-scale-data-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # ⚖️ Balance scale implementation
│   ├── generator.py        # Puzzle generator & renderer
│   ├── prompts.py          # Balance scale prompts
│   └── config.py           # Puzzle configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── balance_scale_task/
        └── balance_scale_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each balance scale task produces:

```
data/questions/balance_scale_task/balance_scale_XXXX/
├── first_frame.png          # Tilted scale with "?" weight
├── final_frame.png          # Balanced scale with solution
├── prompt.txt               # Problem-solving instructions
└── ground_truth.mp4         # Step-by-step solution video (optional)
```

### Visual Elements

- **Blue boxes**: Known weight values (e.g., "5kg", "3kg")
- **Orange box with "?"**: Unknown weight to solve for
- **Green box**: Solved weight value (in final frame)
- **Tilted beam**: Unbalanced state (heavy side down)
- **Horizontal beam**: Balanced state (both sides equal)
- **Gray fulcrum**: Triangle pivot point at center

---

## 🎨 Configuration

### Puzzle Generation Settings

Configure puzzle generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Puzzle parameters
    min_total_weight: int = Field(default=5)    # Minimum balanced weight
    max_total_weight: int = Field(default=20)   # Maximum balanced weight
    min_objects_per_side: int = Field(default=2)  # Min weights per side
    max_objects_per_side: int = Field(default=4)  # Max weights per side

    # Visual settings
    image_size: tuple[int, int] = Field(default=(600, 400))
    tilt_angle: float = Field(default=12.0)     # Degrees when unbalanced

    # Animation settings
    show_steps: bool = Field(default=True)      # Show equation steps
    step_display_frames: int = Field(default=15)  # Frames per step

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_puzzles

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Puzzle Generation Algorithm

### Weight Distribution

1. **Total weight selection**: Random integer from configured range (5-20kg)
2. **Heavy side partition**: Randomly split total into 2-4 positive integers
3. **Light side known weights**: Generate weights summing to less than total
4. **Unknown weight calculation**: `? = total - sum(known_light_weights)`

### Validation Rules

- All weights are positive integers (≥ 1kg)
- Unknown weight must be positive
- Heavy side always displayed on left
- Light side (with "?") always on right

### Example Puzzle

```
Heavy side: [5kg, 5kg] = 10kg total
Light side: [3kg, ?]
Equation: 3 + ? = 10
Solution: ? = 7kg
```

---

## 🎥 Video Animation Sequence

Ground truth videos show the complete solution process:

| Phase | Duration | Description |
|-------|----------|-------------|
| 1. Initial hold | 10 frames | Show tilted scale with "?" |
| 2. Step 1 | 15 frames | "Heavy side: 5 + 5 = 10kg" |
| 3. Step 2 | 15 frames | "Light side: 3 + ?" |
| 4. Step 3 | 15 frames | "3 + ? = 10" |
| 5. Step 4 | 15 frames | "? = 10 - 3" |
| 6. Step 5 | 15 frames | "? = 7kg" |
| 7. Transform | 10 frames | "?" changes to "7kg" |
| 8. Balance | 20 frames | Scale animates to horizontal |
| 9. Final hold | 10 frames | Show balanced state + "Balanced!" |

- Configurable FPS (default: 10)
- MP4 format with H.264 codec
- Ease-out animation for smooth balancing motion

---

## 🎯 Task Description

### Scene Setup
A balance scale is shown in a tilted position (one side down). The lower/heavy side contains objects with known weight labels. The higher/light side contains some objects with known weights PLUS one object marked with "?" indicating unknown weight.

### Goal
Determine what weight value would balance the scale by:
1. Calculating the total weight on the heavy side
2. Identifying known weights on the light side
3. Setting up the balance equation
4. Solving for the unknown weight

### Success Criteria
- Correct weight value replaces the "?"
- Scale becomes perfectly balanced (horizontal beam)
- Equation solution is displayed

---

## 🎨 Color Scheme

| Element | Color | Hex Code |
|---------|-------|----------|
| Background | White | `#FFFFFF` |
| Beam/Fulcrum | Dark Gray | `#444444` |
| Scale Pans | Light Gray | `#C8C8C8` |
| Known Weights | Blue | `#4A90D9` |
| Unknown Weight (?) | Orange | `#E67E22` |
| Solved Weight | Green | `#27AE60` |
| Text on Boxes | White | `#FFFFFF` |

---

## 📚 References

- **Template Data Generator**: Base framework for task generation
- **Pydantic**: Configuration and data validation
- **Pillow (PIL)**: Image rendering and manipulation
- **OpenCV**: Video generation (optional dependency)
