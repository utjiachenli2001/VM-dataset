# Domino Chain Gap Analysis Data Generator 🎯

A domino chain reasoning task generator for training and evaluating video generation models on spatial and physical reasoning tasks. Based on the template-data-generator framework.

**Task**: Given a chain of dominos with one gap that's too wide, determine which domino is the last to fall before the chain reaction stops.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/domino-chain-gap-generator.git
cd domino-chain-gap-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate domino chain tasks
python examples/generate.py --num-samples 50
```

### Output

Generated tasks will be saved to `data/questions/domino_task/` with:
- **first_frame.png**: All dominos standing, "PUSH" arrow on first domino, "?" marker
- **final_frame.png**: Fallen dominos (red), standing dominos (blue), "TOO FAR!" gap indicator, answer circled
- **prompt.txt**: Chain analysis instructions
- **ground_truth.mp4**: Video showing chain reaction stopping at gap (optional)

---

## 📁 Structure

```
domino-chain-gap-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🎯 Domino-specific implementation
│   ├── generator.py        # Domino chain generator
│   ├── prompts.py          # Chain analysis prompts
│   └── config.py           # Domino configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── domino_task/
        └── domino_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each domino chain task produces:

```
data/questions/domino_task/domino_XXXX/
├── first_frame.png          # All dominos standing with PUSH indicator
├── final_frame.png          # Chain stopped, answer revealed
├── prompt.txt               # Analysis instructions
└── ground_truth.mp4         # Chain reaction animation (optional)
```

### Visual Elements

- **Blue rectangles**: Standing dominos (numbered 1, 2, 3...)
- **Red rectangles**: Fallen dominos (tilted 75° to the right)
- **"PUSH" arrow**: Points to first domino (chain start)
- **Yellow "?" marker**: Indicates the question to solve
- **"TOO FAR!" indicator**: Highlights the gap that breaks the chain
- **Green circle**: Marks the answer (last fallen domino)

---

## 🎨 Configuration

### Domino Chain Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Image dimensions (wider for side view)
    image_size: tuple[int, int] = Field(default=(800, 400))

    # Domino dimensions
    domino_width: int = Field(default=16)   # Width in pixels
    domino_height: int = Field(default=70)  # Height in pixels

    # Chain parameters
    min_dominos: int = Field(default=7)     # Minimum dominos in chain
    max_dominos: int = Field(default=12)    # Maximum dominos in chain

    # Spacing parameters
    normal_spacing_min: int = Field(default=30)   # Valid spacing (min)
    normal_spacing_max: int = Field(default=45)   # Valid spacing (max)
    gap_spacing_min: int = Field(default=90)      # Gap spacing (min)
    gap_spacing_max: int = Field(default=120)     # Gap spacing (max)

    # Physics threshold
    fall_reach_ratio: float = Field(default=0.9)  # Domino reach = 90% of height

    # Colors
    domino_color: tuple = Field(default=(41, 128, 185))      # Blue (standing)
    fallen_domino_color: tuple = Field(default=(231, 76, 60)) # Red (fallen)
    highlight_color: tuple = Field(default=(46, 204, 113))    # Green (answer)
    gap_indicator_color: tuple = Field(default=(192, 57, 43)) # Dark red (gap)

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=15)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_dominos

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Algorithm

### Chain Generation

1. **Random domino count**: Select N dominos (7-12 by default)
2. **Gap placement**: Randomly place one gap (not at start or end)
3. **Spacing assignment**:
   - Normal positions: 30-45px spacing (dominos can reach)
   - Gap position: 90-120px spacing (too far to reach)
4. **Answer calculation**: Domino before the gap = last to fall

### Physics Rule

A domino can knock over the next one if:
```
distance_to_next < domino_height × fall_reach_ratio
```

Default: `distance < 70px × 0.9 = 63px`

Normal spacing (30-45px) < 63px → Chain continues
Gap spacing (90-120px) > 63px → Chain stops

### Rendering

- **Side view**: Shows dominos as vertical rectangles
- **Falling animation**: Dominos rotate from 0° to 75° (tilted right)
- **Pivot point**: Bottom-left corner stays on ground during fall

---

## 🎥 Video Generation

Ground truth videos show the complete chain reaction:

| Phase | Duration | Description |
|-------|----------|-------------|
| 1. Initial | 15 frames | All dominos standing, PUSH indicator |
| 2. Chain Reaction | ~6 frames/domino | Each domino tilts through 6 angles (0°→75°) |
| 3. Measurement | 20 frames | Distance measurement shown at gap |
| 4. Gap Reveal | 20 frames | "TOO FAR!" indicator appears |
| 5. Answer | 30 frames | Final state with answer circled |

- **Format**: MP4 with H.264 codec
- **FPS**: 15 (configurable)
- **Resolution**: 800×400 pixels

---

## 🧩 Task Difficulty

Difficulty can be adjusted by modifying spacing parameters:

| Difficulty | Gap Visibility | Configuration |
|------------|----------------|---------------|
| Easy | Obvious gap | `gap_spacing_min=120, gap_spacing_max=150` |
| Medium | Subtle gap | `gap_spacing_min=90, gap_spacing_max=120` (default) |
| Hard | Very subtle | `gap_spacing_min=70, gap_spacing_max=90` |

Additional difficulty factors:
- More dominos = harder to track
- Gap in middle = harder than at edges
- Similar spacings = requires careful analysis

---

## 📚 References

- **Template Data Generator**: Base framework for synthetic task generation
- **Domino Physics**: Simplified model based on reach distance
- **PIL/Pillow**: Image rendering library
- **OpenCV**: Video generation (optional dependency)
