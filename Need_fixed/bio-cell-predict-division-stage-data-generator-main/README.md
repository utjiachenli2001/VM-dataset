# Bio_Cell_1: Predict Division Stage Data Generator

A cell division (mitosis) task generator for training and evaluating video generation models on biological reasoning tasks. The task requires predicting what a cell will look like in the next stage of mitosis. Based on the template-data-generator framework.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bio-cell-data-generator.git
cd bio-cell-data-generator

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
- **first_frame.png**: Cell at current mitosis stage with "What's next?" indicator
- **final_frame.png**: Cell at the next stage of division
- **prompt.txt**: Stage transition instructions
- **ground_truth.mp4**: Video showing the biological transition (optional)

---

## Structure

```
bio-cell-data-generator/
├── core/                    # Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # Cell division implementation
│   ├── generator.py        # Cell division generator
│   ├── prompts.py          # Stage-specific prompts
│   └── config.py           # Cell configuration
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

## Output Format

Each cell division task produces:

```
data/questions/bio_cell_task/bio_cell_XXXX/
├── first_frame.png          # Cell at current stage (with question indicator)
├── final_frame.png          # Cell at next stage
├── prompt.txt               # Transition instructions
└── ground_truth.mp4         # Animated transition video (optional)
```

### Visual Elements

- **Cell membrane**: Light green oval (elongates and pinches during division)
- **Nucleus**: Peach/tan circle (visible in Interphase, dissolves, reforms in Telophase)
- **Chromosomes**: Steel blue X-shapes (condense, align, split into V-shaped chromatids)
- **Spindle fibers**: Gray lines connecting poles to chromosomes
- **Centrosomes**: Brown dots at cell poles
- **Labels**: Stage name (top-left), "What's next?" indicator (top-right)

---

## The Mitotic Cycle

The generator covers all 5 stages of mitosis:

| Stage | Visual Characteristics |
|-------|----------------------|
| **Interphase** | Intact nucleus with diffuse chromatin dots, no visible chromosomes |
| **Prophase** | Chromosomes condense (X-shapes visible), nuclear envelope fading, spindle forming |
| **Metaphase** | Chromosomes aligned at cell equator (metaphase plate), spindle fibers attached |
| **Anaphase** | Sister chromatids separate (V-shapes), move to opposite poles, cell elongates |
| **Telophase** | Chromatids at poles, nuclear envelopes reforming, cell pinching (cytokinesis) |

**Cycle progression**: Interphase → Prophase → Metaphase → Anaphase → Telophase → Interphase

---

## Configuration

### Cell Division Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Domain
    domain: str = Field(default="bio_cell")
    image_size: tuple[int, int] = Field(default=(512, 512))

    # Chromosome settings
    chromosome_count: int = Field(default=4)  # Fixed at 4 for simplicity

    # Color scheme (classic biology textbook colors)
    cell_membrane_color: tuple = Field(default=(144, 238, 144))  # Light green
    cytoplasm_color: tuple = Field(default=(220, 255, 220))      # Very light green
    nucleus_color: tuple = Field(default=(255, 218, 185))        # Peach/tan
    chromosome_color: tuple = Field(default=(70, 130, 180))      # Steel blue
    spindle_color: tuple = Field(default=(169, 169, 169))        # Gray
    centrosome_color: tuple = Field(default=(139, 69, 19))       # Brown

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

## Stage Transitions & Animations

### Transition Details

Each stage transition animates specific biological changes:

| Transition | Animation |
|------------|-----------|
| Interphase → Prophase | Chromatin condenses into visible X-shaped chromosomes, nuclear envelope fades |
| Prophase → Metaphase | Chromosomes move to center, align on metaphase plate |
| Metaphase → Anaphase | Chromosomes split at centromere, V-shaped chromatids move to poles, cell elongates |
| Anaphase → Telophase | Chromatids reach poles, nuclear envelopes reform, cell pinches |
| Telophase → Interphase | Chromosomes decondense, division completes (cycle restarts) |

### Video Generation

Ground truth videos show smooth biological transitions:
- Chromosome position interpolation
- Nuclear envelope dissolving/reforming
- Cell membrane shape morphing (elongation, pinching)
- Stage label updates at transition midpoint
- Configurable FPS (default: 10)
- MP4 format with H.264 codec

---

## Task Design

### Core Concept

The task tests understanding of the mitotic cell cycle:
1. **Recognition**: Identify current stage from visual cues
2. **Prediction**: Determine the next stage in the cycle
3. **Visualization**: Understand how cellular structures transform

### Prompt Examples

```text
# Metaphase → Anaphase
"The cell is in Metaphase with chromosomes aligned at the center.
Animate the transition to Anaphase, showing sister chromatids
separating and moving toward opposite poles."

# Telophase → Interphase
"The cell is in Telophase with chromosomes at poles and the cell pinching.
Animate the completion of division and return to Interphase,
showing the chromosomes decondensing within the new nuclei."
```

---

## Dependencies

Core requirements (see `requirements.txt`):
- `numpy` - Numerical operations
- `Pillow` - Image rendering
- `pydantic` - Configuration models
- `opencv-python` - Video generation

---

## References

- **Mitosis Overview**: [Wikipedia - Mitosis](https://en.wikipedia.org/wiki/Mitosis)
- **Cell Cycle Phases**: [Khan Academy - Cell Division](https://www.khanacademy.org/science/biology/cellular-molecular-biology/mitosis/a/phases-of-mitosis)
- **Biology Textbook Style**: Classic educational diagrams from Campbell Biology
