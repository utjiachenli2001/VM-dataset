# Bio_Cell_2: Count After Division Data Generator 🧬

A cell division counting task generator for training and evaluating video generation models on biological/mathematical reasoning tasks. Based on the template-data-generator framework, simulating exponential cell growth through mitosis.

**Core Formula:** `Final = Initial × 2^N`


A task variant focused on counting cells after the division process completes. Given the initial cell count and number of division cycles, the model must predict the final cell count using exponential growth principles.

**Task Format:**
- **Input:** Initial number of cells + number of division cycles (N)
- **Output:** Final cell count after all divisions complete
- **Formula:** `Final Count = Initial × 2^N`

**Example:**
- Start with 3 cells, undergo 2 division cycles
- Each division doubles all cells: 3 → 6 → 12
- Answer: 12 cells (3 × 2² = 12)

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bio-cell-generator.git
cd bio-cell-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate cell division tasks
python examples/generate.py --num-samples 50
```

### Output

Generated tasks will be saved to `data/questions/bio_cell_task/` with:
- **first_frame.png**: Initial cells with "N = X divisions" label
- **final_frame.png**: Final cells with formula display (e.g., "2 × 2³ = 16 cells")
- **prompt.txt**: Educational instructions
- **ground_truth.mp4**: Video showing division animation (optional)

---

## 📁 Structure

```
bio-cell-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🧬 Cell division implementation
│   ├── generator.py        # Cell renderer & division animation
│   ├── prompts.py          # Educational prompts
│   └── config.py           # Task configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── bio_cell_task/
        └── bio_cell_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each cell division task produces:

```
data/questions/bio_cell_task/bio_cell_XXXX/
├── first_frame.png          # Initial cells with division count label
├── final_frame.png          # Final cells with formula result
├── prompt.txt               # Educational instructions
└── ground_truth.mp4         # Division animation video (optional)
```

### Visual Elements

- **Green circles (●)**: Cell bodies (Light green: `#90EE90`)
- **Dark green dots**: Nuclei (Forest green: `#228B22`)
- **Header text**: Shows "N = X divisions" or formula result
- **Counter**: Displays current/final cell count

### Example Scenarios

| Initial | N | Formula | Final |
|---------|---|---------|-------|
| 1 | 1 | 1 × 2¹ | 2 |
| 2 | 2 | 2 × 2² | 8 |
| 3 | 3 | 3 × 2³ | 24 |
| 4 | 2 | 4 × 2² | 16 |

---

## 🎨 Configuration

### Cell Division Settings

Configure task generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Cell count parameters
    min_initial_cells: int = Field(default=1)   # 1-4 starting cells
    max_initial_cells: int = Field(default=4)
    min_divisions: int = Field(default=1)       # 1-3 division cycles
    max_divisions: int = Field(default=3)

    # Cell appearance
    cell_color: tuple = Field(default=(144, 238, 144))       # Light green
    nucleus_color: tuple = Field(default=(34, 139, 34))      # Dark green
    cell_outline_color: tuple = Field(default=(60, 179, 113)) # Medium sea green

    # Layout settings
    background_color: tuple = Field(default=(240, 248, 255)) # Alice blue
    text_color: tuple = Field(default=(30, 30, 30))          # Dark gray

    # Animation settings
    hold_frames: int = Field(default=8)         # Frames to hold at start/end
    division_frames: int = Field(default=20)    # Frames per division cycle
    reorganize_frames: int = Field(default=10)  # Frames for cell repositioning

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_cells

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Division Animation

### Animation Phases

The ground truth video shows a 4-phase division process for each cycle:

1. **Elongation Phase**
   - Cells stretch horizontally
   - Simulates cell preparing for division

2. **Pinching Phase**
   - Middle of cell narrows
   - Two nuclei become visible and separate

3. **Separation Phase**
   - Cell splits into two daughter cells
   - Cells move apart from parent position

4. **Reorganization Phase**
   - Daughter cells move to grid positions
   - Counter updates to new cell count

### Animation Flow

```
Initial (2 cells) → Cycle 1 → 4 cells → Cycle 2 → 8 cells → Cycle 3 → 16 cells (Final)
     ↓                ↓           ↓         ↓          ↓         ↓
   Hold          Elongate     Hold     Elongate    Hold    Show Formula
                 Pinch                 Pinch
                 Separate              Separate
                 Reorganize            Reorganize
```

---

## 🎥 Video Generation

Optional ground truth videos show the complete division process:
- All cells divide simultaneously per cycle
- Smooth transitions between phases
- Counter updates after each division
- Final frame displays the exponential formula
- Configurable FPS (default: 10)
- MP4 format with mp4v codec

---

## 📝 Prompt Types

Three prompt categories available in `src/prompts.py`:

### Default
> "Watch the cells divide 3 times. Starting with 2 cells, calculate the final count using the formula: Initial × 2^N."

### Educational
> "Cell Division Challenge: 2 cells × 2³ = ? Watch the division process and verify the exponential growth formula."

### Simple
> "Count the cells after 3 divisions. Start: 2 cells."

---

## 🧪 Task Variety

The generator creates diverse scenarios by randomizing:

| Parameter | Range | Effect |
|-----------|-------|--------|
| Initial cells | 1-4 | Starting population |
| Division cycles (N) | 1-3 | Exponential factor |
| Final cells | 2-32 | Result complexity |

This provides training data for:
- Exponential growth understanding
- Visual counting at different scales
- Formula verification (Initial × 2^N)

---

## 📚 References

- **Cell Division (Mitosis)**: [Wikipedia](https://en.wikipedia.org/wiki/Mitosis)
- **Template Framework**: Based on template-data-generator architecture

---

## 📋 Requirements

- Python >= 3.8
- numpy >= 1.26.0
- Pillow >= 10.0.0
- pydantic >= 2.0.0
- opencv-python >= 4.8.0 (for video generation)
