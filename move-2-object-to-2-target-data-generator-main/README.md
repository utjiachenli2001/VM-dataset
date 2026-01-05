# Move-2-Object-to-2-Target Data Generator 🎯

A spatial reasoning task generator for training and evaluating video generation models. Two objects (circles) must move to their two corresponding target rings. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/move-2-object-to-2-target-generator.git
cd move-2-object-to-2-target-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate tasks
python examples/generate.py --num-samples 50
```

### Output

Generated tasks will be saved to `data/questions/move_to_target_task/` with:
- **first_frame.png**: Two balls at starting positions, two target rings at destinations
- **final_frame.png**: Both balls inside their matching target rings
- **prompt.txt**: Movement instructions
- **ground_truth.mp4**: Video showing both balls sliding to targets (optional)

---

## 📁 Structure

```
move-2-object-to-2-target-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🎯 Task-specific implementation
│   ├── generator.py        # Move-2-object-to-2-target generator
│   ├── prompts.py          # Movement instruction prompts
│   └── config.py           # Task configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── move_to_target_task/
        └── move_to_target_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each task produces:

```
data/questions/move_to_target_task/move_to_target_XXXX/
├── first_frame.png          # Objects at start, rings at target
├── final_frame.png          # Objects inside target rings
├── prompt.txt               # Movement instructions
└── ground_truth.mp4         # Animation video (optional)
```

### Visual Elements

- **Pink ball (●)**: First movable object (`#f48fb1`)
- **Blue ball (●)**: Second movable object (`#8fbcf4`)
- **Pink dashed ring (◯)**: Target for pink ball (`#b46482`)
- **Blue dashed ring (◯)**: Target for blue ball (`#648cb4`)
- **Gray background**: Canvas (`#dcdcdc`)

---

## 🎨 Configuration

### Task Settings

Configure task generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Canvas settings
    image_size: tuple[int, int] = Field(default=(512, 512))
    bg_color: tuple[int, int, int] = Field(default=(220, 220, 220))

    # Object settings
    object_radius: int = Field(default=30)
    object_colors: tuple = Field(
        default=((244, 143, 177), (143, 188, 244))  # Pink, Blue
    )

    # Target ring settings
    target_ring_radius: int = Field(default=35)
    ring_colors: tuple = Field(
        default=((180, 100, 130), (100, 140, 180))  # Matching colors
    )
    ring_dash_length: int = Field(default=8)
    ring_gap_length: int = Field(default=6)

    # Placement constraints
    min_distance: int = Field(default=80)   # Min distance: object → target
    max_distance: int = Field(default=250)  # Max distance: object → target
    min_separation: int = Field(default=80) # Min separation between elements
    margin: int = Field(default=50)         # Canvas edge margin

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_tasks

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Task Logic

### Position Generation

1. **Object 1 start**: Random position within canvas margins
2. **Target 1**: Random position within `min_distance` to `max_distance` from Object 1
3. **Object 2 start**: Random position with `min_separation` from existing elements
4. **Target 2**: Random position within distance range from Object 2, separated from others

### Constraints

- All elements stay within `margin` pixels from canvas edges
- Objects and targets maintain `min_separation` distance from each other
- Each object's target is within `[min_distance, max_distance]` range

### Movement

- **Path type**: Straight line (linear interpolation)
- **Both objects move simultaneously**
- Objects slide from start position to target ring center

---

## 🎥 Video Generation

Ground truth videos show the solution animation:
- Both balls animate simultaneously from start to target
- Linear interpolation for smooth movement
- Hold frames at start and end positions
- Configurable FPS (default: 10)
- MP4 format with H.264 codec

### Animation Sequence

1. **Hold** (5 frames): Initial state
2. **Transition** (25 frames): Both objects slide to targets
3. **Hold** (5 frames): Final state

---

## 🎯 Task Description

This task tests a model's ability to:

1. **Spatial reasoning**: Understanding object-target correspondence by color
2. **Motion planning**: Moving objects in straight lines to destinations
3. **Multi-object tracking**: Handling two independent movements simultaneously
4. **Goal recognition**: Identifying dashed rings as target destinations

### Example Prompts

- "Move both balls to their matching target rings."
- "Animate both objects moving to their destinations."
- "Guide both balls to their collection zones."

---

## 📚 Dependencies

```
numpy==1.26.4
Pillow==10.4.0
pydantic==2.10.5
opencv-python==4.10.0.84  # For video generation
```

---

## 🔗 Related Projects

- **template-data-generator**: Base framework for task generators
- **VMEvalKit**: Video model evaluation toolkit
