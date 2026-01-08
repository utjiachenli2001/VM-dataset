# Lever Balance Data Generator - Torque Reasoning Task Generator

A lever/torque balance reasoning task generator for training and evaluating video generation models on physics reasoning tasks. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/lever-balance-data-generator.git
cd lever-balance-data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate lever balance tasks
python examples/generate.py --num-samples 50
```

### Output

Generated lever tasks will be saved to `data/questions/lever_task/` with:
- **first_frame.png**: Balanced lever with weighted objects on both sides
- **final_frame.png**: Tilted lever showing which side tips down (with torque comparison)
- **prompt.txt**: Physics reasoning instructions
- **ground_truth.mp4**: Video showing lever tipping animation (optional)

---

## 📁 Structure

```
lever-balance-data-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # ⚖️ Lever-specific implementation
│   ├── generator.py        # Lever generator (torque calculation)
│   ├── prompts.py          # Physics reasoning prompts
│   └── config.py           # Lever configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── lever_task/
        └── lever_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each lever task produces:

```
data/questions/lever_task/lever_XXXX/
├── first_frame.png          # Balanced lever with objects placed
├── final_frame.png          # Tilted lever with result annotation
├── prompt.txt               # Physics reasoning instructions
└── ground_truth.mp4         # Lever tipping animation (optional)
```

### Visual Elements

- **Triangular fulcrum**: Gray pivot point at center of beam
- **Brown beam**: Lever arm with distance markers (1m, 2m, 3m)
- **Red boxes**: Objects on left side with weight labels (e.g., "5kg")
- **Blue boxes**: Objects on right side with weight labels (e.g., "3kg")
- **Calculation boxes**: Torque calculations shown at bottom (Weight × Distance = Torque)
- **Result annotation**: Shows which side tips down with torque comparison

---

## 🎨 Configuration

### Lever Physics Settings

Configure lever generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Image settings
    image_size: tuple[int, int] = Field(default=(640, 480))

    # Distance settings (in meters from fulcrum)
    max_distance: int = Field(default=3)  # Positions: 1m, 2m, 3m

    # Weight settings (in kg)
    min_weight: int = Field(default=1)    # Minimum object weight
    max_weight: int = Field(default=10)   # Maximum object weight

    # Object count settings
    min_objects_per_side: int = Field(default=1)  # Minimum objects per side
    max_objects_per_side: int = Field(default=3)  # Maximum objects per side

    # Animation settings
    tilt_angle: float = Field(default=22.0)  # Max tilt in degrees

    # Balanced cases
    include_balanced: bool = Field(default=True)      # Include equilibrium cases
    balanced_probability: float = Field(default=0.15) # 15% balanced cases

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=15)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_levers

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Physics Principles

### Torque Calculation

The lever arm principle determines which side tips:

```
Torque (τ) = Weight × Distance from fulcrum

Left Torque  = Σ (Weight_i × Distance_i) for all left objects
Right Torque = Σ (Weight_j × Distance_j) for all right objects

If Left Torque > Right Torque → Left side tips down
If Right Torque > Left Torque → Right side tips down
If Left Torque = Right Torque → Lever stays balanced
```

### Example Calculation

```
Left side:  5kg at 2m → 5 × 2 = 10 N·m
Right side: 3kg at 3m → 3 × 3 = 9 N·m

Total: Left (10 N·m) > Right (9 N·m)
Result: Left side tips down
```

### Task Types

1. **Standard**: One side clearly has greater torque
2. **Counterintuitive**: Lighter total weight wins due to greater distance
3. **Balanced**: Equal torques on both sides (lever stays horizontal)

---

## 🎥 Video Generation

Ground truth videos show the lever tipping animation:
- Initial state: Lever balanced horizontally
- Transition: Smooth rotation toward heavier torque side
- Final state: Tilted lever with result annotation
- Linear interpolation for smooth animation
- Configurable FPS (default: 15)
- MP4 format with H.264 codec

### Animation Sequence

```
Frames 0-15:   Hold balanced state (setup visible)
Frames 16-45:  Linear rotation to final tilt angle
Frames 46-60:  Hold final tilted state (result shown)
```

---

## 📊 Prompt Categories

Different prompts are selected based on the task outcome:

| Category | Description | Example |
|----------|-------------|---------|
| `default` | General torque calculation | "Calculate torque on each side..." |
| `tips_left` | Left side tips down | "The left side has greater torque..." |
| `tips_right` | Right side tips down | "The right side has greater torque..." |
| `balanced` | Equal torques | "This lever is perfectly balanced..." |
| `counterintuitive` | Lighter side wins | "A lighter weight far from fulcrum..." |

---

## 🎯 Educational Value

This generator creates physics reasoning tasks that demonstrate:

1. **Torque depends on BOTH weight AND distance** - Not just total weight
2. **Lever arm principle** - τ = F × d
3. **Equilibrium conditions** - When torques balance
4. **Counterintuitive physics** - Small weight at large distance can beat heavy weight at small distance

---

## 📚 References

- **Lever Arm Principle**: [Wikipedia - Torque](https://en.wikipedia.org/wiki/Torque)
- **Simple Machines**: [Wikipedia - Lever](https://en.wikipedia.org/wiki/Lever)
- **Physics Education**: [HyperPhysics - Torque](http://hyperphysics.phy-astr.gsu.edu/hbase/torq.html)
