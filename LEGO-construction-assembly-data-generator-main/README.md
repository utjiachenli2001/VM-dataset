# LEGO Construction Assembly Generator

A LEGO instruction step generator for training and evaluating video generation models on construction assembly tasks. Based on the template-data-generator framework.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/lego-data-generator.git
cd lego-data-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate LEGO tasks
python examples/generate.py --num-samples 50
```

### Output

Generated LEGO instruction steps will be saved to `data/questions/lego_task/` with:
- **first_frame.png**: Instruction layout with callout, arrow, and partial model
- **final_frame.png**: Completed step with new brick placed on model
- **prompt.txt**: Assembly instructions
- **ground_truth.mp4**: Video showing piece placement animation (optional)

---

## Structure

```
lego-data-generator/
├── core/                    # Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # LEGO-specific implementation
│   ├── generator.py        # LEGO generator (isometric rendering)
│   ├── prompts.py          # Assembly instruction prompts
│   └── config.py           # LEGO configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── lego_task/
        └── lego_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## Output Format

Each LEGO task produces:

```
data/questions/lego_task/lego_XXXX/
├── first_frame.png          # Instruction frame (before placement)
├── final_frame.png          # Completed step (after placement)
├── prompt.txt               # Assembly instructions
└── ground_truth.mp4         # Piece placement video (optional)
```

### Visual Elements

- **Step number**: Displayed in circle (top-left)
- **Parts callout**: Shows brick to add with quantity (×1) and type label
- **Curved arrow**: Indicates attachment position on model
- **Isometric model**: 3D-style view of partially-built model
- **Highlight glow**: Yellow outline on newly placed brick

### Instruction Layout

```
┌─────────────────────────────────────┐
│  (3)                                │  <- Step number
│                                     │
│   ┌─────────┐                       │
│   │ [brick] │                       │
│   │  2x4    │  ───────>  [model]   │  <- Arrow to placement
│   │   ×1    │            with      │
│   └─────────┘            bricks    │
│    callout                         │
└─────────────────────────────────────┘
```

---

## Configuration

### LEGO Generation Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Domain
    domain: str = Field(default="lego")
    image_size: tuple[int, int] = Field(default=(512, 512))

    # Brick rendering
    stud_size: int = Field(default=20)       # Size of one stud in pixels
    brick_height_px: int = Field(default=24) # Height of standard brick

    # Available colors
    available_colors: list[str] = Field(
        default=["red", "blue", "yellow", "green", "white", "orange"]
    )

    # Available brick types
    available_brick_types: list[str] = Field(
        default=["1x1", "1x2", "2x2", "2x4"]
    )

    # Instruction layout
    show_arrows: bool = Field(default=True)

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=15)
    animation_hold_frames: int = Field(default=8)
    animation_move_frames: int = Field(default=20)
    animation_snap_frames: int = Field(default=6)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_lego

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## Model Templates

Six hand-designed LEGO models are included:

| Model | Bricks | Type | Description |
|-------|--------|------|-------------|
| Simple Tower | 5 | tower | Vertical stack of 2x2 bricks |
| L-Wall | 6 | wall | L-shaped wall structure |
| Car Base | 7 | car | Basic vehicle chassis |
| Staircase | 6 | stairs | Ascending step pattern |
| Bridge | 8 | bridge | Two pillars with span |
| Mini House | 10 | wall | Simple house with roof |

Each model defines a build sequence where each step adds one brick.

---

## Brick Types

Four basic brick types supported:

| Type | Dimensions (studs) | Height (plates) |
|------|-------------------|-----------------|
| 1x1 | 1 × 1 | 3 |
| 1x2 | 1 × 2 | 3 |
| 2x2 | 2 × 2 | 3 |
| 2x4 | 2 × 4 | 3 |

Standard LEGO brick height = 3 plates.

---

## Color Palette

LEGO-style colors available:

| Color | RGB Value |
|-------|-----------|
| Red | (201, 26, 9) |
| Blue | (0, 85, 191) |
| Yellow | (245, 205, 47) |
| Green | (0, 146, 71) |
| White | (255, 255, 255) |
| Black | (30, 30, 30) |
| Orange | (254, 138, 24) |
| Lime | (166, 202, 85) |
| Light Gray | (180, 180, 180) |
| Dark Gray | (100, 100, 100) |

---

## Video Generation

Optional ground truth videos show the assembly animation:

1. **Hold**: Display instruction frame
2. **Highlight**: Piece pulses in callout
3. **Move**: Piece lifts and travels toward model (eased motion)
4. **Descend**: Piece lowers to attachment point
5. **Snap**: Bounce effect simulating connection
6. **Flash**: Confirmation highlight on placed brick
7. **Hold**: Display completed step

- Configurable FPS (default: 15)
- MP4 format with H.264 codec
- Smooth easing curves for natural motion

---

## Rendering

### Isometric Projection

Bricks are rendered in 2D isometric view:
- No external 3D libraries required (pure PIL/Pillow)
- Proper depth sorting (painter's algorithm)
- Three visible faces per brick (top, left side, right side)
- Elliptical studs on top face

### Isometric Math

```python
# Convert 3D grid coordinates to 2D screen coordinates
iso_x = (x - y) * stud_px * 0.866  # cos(30°)
iso_y = (x + y) * stud_px * 0.5 - z * brick_height_px
```

---

## Task Description

**Construction_Assembly_1: LEGO Steps**

- **Scene**: LEGO instruction booklet style showing current partially-built model, specific piece(s) to add (shown separately with quantity), and arrow indicator showing attachment point. Step number displayed.

- **Core Idea**: Take the indicated piece(s), understand attachment point from visual instruction arrows, place correctly on existing model to complete construction step.

- **Control/Process**:
  1. Highlight new piece(s) to add
  2. Piece lifts and moves toward model
  3. Follow arrow indicator to attachment point
  4. Rotate piece to correct orientation (studs align)
  5. Lower piece toward attachment point
  6. Snap piece into place with click animation
  7. Flash/highlight to confirm correct placement
  8. Repeat for multiple pieces if needed

- **Success**: All pieces for step correctly attached. Model matches 'after' state. Ready for next step.

---

## Dependencies

Core requirements (see `requirements.txt`):
- `numpy` - Array operations
- `Pillow` - Image rendering
- `pydantic` - Configuration models
- `opencv-python` - Video generation

---

## Extending

### Adding New Models

Add templates in `src/generator.py`:

```python
templates.append(LegoModel(
    name="My Model",
    model_type="custom",
    bricks=[
        Brick("2x4", "red", 0, 0, 0),    # First brick
        Brick("2x2", "blue", 0, 0, 3),   # Second brick (on top)
        # ... more bricks in build order
    ]
))
```

### Adding New Prompts

Add prompts in `src/prompts.py`:

```python
PROMPTS["custom"] = [
    "Your custom instruction prompt here.",
    "Another variant of the prompt.",
]
```

---

## License

See [LICENSE](LICENSE) file.
