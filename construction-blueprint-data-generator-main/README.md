# Construction Blueprint Data Generator 🧩

A missing piece puzzle task generator for training and evaluating video generation models on spatial reasoning tasks. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/construction-blueprint-generator.git
cd construction-blueprint-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate missing piece tasks
python examples/generate.py --num-samples 50
```

### Output

Generated puzzles will be saved to `data/questions/construction_blueprint_task/` with:
- **first_frame.png**: Structure with gap (dashed outline) + 4 candidate pieces
- **final_frame.png**: Completed structure with correct piece placed
- **prompt.txt**: Selection instructions
- **ground_truth.mp4**: Video showing selection process (optional)

---

## 📁 Structure

```
construction-blueprint-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🧩 Missing piece implementation
│   ├── generator.py        # Structure & candidate generation
│   ├── prompts.py          # Task prompts
│   └── config.py           # Task configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── construction_blueprint_task/
        └── construction_blueprint_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each puzzle task produces:

```
data/questions/construction_blueprint_task/construction_blueprint_XXXX/
├── first_frame.png          # Structure with gap + candidates
├── final_frame.png          # Completed structure
├── prompt.txt               # Selection instructions
└── ground_truth.mp4         # Selection process video (optional)
```

### Visual Elements

- **Steel blue blocks**: Structure blocks (RGB: 70, 130, 180)
- **Red dashed outline**: Missing piece gap indicator
- **4 candidate boxes**: Pieces to choose from (numbered 1-4)
- **Green checkmark (✓)**: Correct piece indicator
- **Red X mark (✗)**: Incorrect piece indicator
- **Green blocks**: Placed correct piece (RGB: 100, 200, 100)

---

## 🎨 Configuration

### Task Generation Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Grid settings
    grid_size: int = Field(default=8)  # 8x8 grid

    # Structure size
    min_structure_blocks: int = Field(default=12)
    max_structure_blocks: int = Field(default=20)

    # Candidate pieces
    num_candidates: int = Field(default=4)  # Fixed at 4

    # Visual settings
    image_size: tuple[int, int] = Field(default=(512, 512))

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

## 🔧 How It Works

### Structure Generation

1. Start with a seed block at grid center
2. Grow connected structure by adding adjacent blocks
3. Target size: 12-20 blocks (configurable)
4. Result: Random connected tetromino-like structure

### Gap Selection

1. Find a contiguous 2-4 block piece within structure
2. Verify removing it doesn't disconnect the structure
3. Mark as the "missing piece" with dashed outline

### Candidate Generation

4 pieces are generated:
1. **Correct piece**: Exact shape of the gap (normalized to origin)
2. **Distractor 1**: Different size (one block added or removed)
3. **Distractor 2**: Rotated 90° (if different from original)
4. **Distractor 3**: Completely different shape

Candidates are shuffled randomly.

### Video Animation Phases

1. **Initial hold**: Show structure with highlighted gap
2. **Scanning**: Orange highlight scans each candidate
3. **Ghost preview**: Semi-transparent piece attempts to fit gap
4. **Marking**: Red X for wrong pieces, green ✓ for correct
5. **Movement**: Correct piece animates from candidate area to gap
6. **Final hold**: Show completed structure

---

## 🎥 Video Generation

Optional ground truth videos show the selection process:
- Scans through candidates sequentially
- Ghost preview shows piece fitting attempt
- X marks for wrong pieces, checkmark for correct
- Smooth animation of piece moving to gap
- Color transition to green on placement
- MP4 format with configurable FPS

---

## 📊 Task Difficulty

Current implementation uses single difficulty level:
- Gap pieces: 2-4 blocks (tetromino-like shapes)
- Distractors: Similar but distinguishable
- Structure: 12-20 connected blocks

Future difficulty levels could include:
- **Easy**: Larger shape differences, fewer candidates
- **Medium**: Current implementation
- **Hard**: Subtle differences, rotations, mirror images

---

## 🔗 References

- **Template Data Generator**: Base framework for task generation
- **Tetromino Shapes**: Standard I, O, T, S, Z, L, J pieces used for variety
