# Plant Growth Stage Generator 🌱

A plant growth stage prediction task generator for training and evaluating video generation models on biological reasoning tasks. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bio-growth-generator.git
cd bio-growth-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate plant growth tasks
python examples/generate.py --num-samples 50
```

### Output

Generated tasks will be saved to `data/questions/bio_growth_task/` with:
- **first_frame.png**: Plant at current growth stage with "What's next?" indicator
- **final_frame.png**: Plant at next growth stage
- **prompt.txt**: Stage-specific growth transition instructions
- **ground_truth.mp4**: Time-lapse video showing growth animation (optional)

---

## 📁 Structure

```
bio-growth-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🌱 Plant growth implementation
│   ├── generator.py        # Plant growth stage generator
│   ├── prompts.py          # Growth transition prompts
│   └── config.py           # Plant growth configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── bio_growth_task/
        └── bio_growth_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each plant growth task produces:

```
data/questions/bio_growth_task/bio_growth_XXXX/
├── first_frame.png          # Plant at current stage with "What's next?"
├── final_frame.png          # Plant at next stage
├── prompt.txt               # Growth transition instructions
└── ground_truth.mp4         # Time-lapse growth video (optional)
```

### Visual Elements

- **Cross-section view**: Shows both above-ground plant and underground roots
- **Sky background**: Light blue (`#87CEEB`)
- **Soil layer**: Brown (`#8B5A2B`) with texture
- **Grass line**: Green divider at ground level
- **Stage label**: Bottom-left corner showing current stage name
- **Question indicator**: Bottom-right "What's next? →" prompt

---

## 🌿 Growth Stages

The generator supports 8 sequential growth stages:

| Stage | Index | Visual Features |
|-------|-------|-----------------|
| **Seed** | 0 | Brown seed buried in soil |
| **Germination** | 1 | Seed cracking, small root emerging downward |
| **Sprout** | 2 | Stem breaking through soil, cotyledons visible |
| **Seedling** | 3 | Short stem, cotyledons + 2 small true leaves |
| **Vegetative** | 4 | Taller stem, 3 larger leaves, branching roots |
| **Flowering** | 5 | Full plant with colorful 5-petal flower |
| **Fruiting** | 6 | Flower fades, fruit developing |
| **Mature** | 7 | Full-size ripe fruit, complete root system |

Each task randomly selects a current stage (0-6) and generates the transition to the next stage.

---

## 🎨 Configuration

### Plant Growth Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Domain
    domain: str = Field(default="bio_growth")
    image_size: Tuple[int, int] = Field(default=(512, 512))

    # Layout
    ground_level: float = Field(default=0.45)  # 45% from top

    # Plant colors
    stem_color: Tuple[int, int, int] = Field(default=(34, 139, 34))   # Forest green
    leaf_color: Tuple[int, int, int] = Field(default=(50, 205, 50))   # Lime green
    root_color: Tuple[int, int, int] = Field(default=(210, 180, 140)) # Tan
    flower_color: Optional[Tuple[int, int, int]] = Field(default=None) # Random if None
    fruit_color: Optional[Tuple[int, int, int]] = Field(default=None)  # Random if None

    # Background colors
    sky_color: Tuple[int, int, int] = Field(default=(135, 206, 235))  # Light blue
    soil_color: Tuple[int, int, int] = Field(default=(139, 90, 43))   # Brown
    grass_color: Tuple[int, int, int] = Field(default=(34, 139, 34))  # Green

    # Animation settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=10)
    transition_frames: int = Field(default=30)
    hold_frames: int = Field(default=8)
    show_time_indicator: bool = Field(default=True)  # Moving sun
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_plants

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🎥 Video Generation

Optional ground truth videos show the growth transition:
- **Time-lapse animation**: Smooth interpolation between stages
- **Moving sun**: Indicates time passing (arcs across sky)
- **Growth components**: Roots extend, stem grows, leaves emerge, flowers bloom, fruits develop
- **Configurable**: FPS, transition frames, hold duration
- **Format**: MP4 with H.264 codec

### Animation Details

1. Hold initial stage (8 frames)
2. Interpolate all plant parameters over 30 frames:
   - Root depth and branching
   - Stem height and thickness
   - Leaf size and count
   - Flower bloom level
   - Fruit size
3. Hold final stage (8 frames)

---

## 🔧 Plant Rendering

### Component Drawing

Each plant component is rendered based on stage-specific parameters:

| Component | Parameters | Stages Present |
|-----------|------------|----------------|
| **Seed** | visibility, cracked | 0-3 (fades) |
| **Roots** | length, branch count | 1-7 |
| **Stem** | height, thickness | 2-7 |
| **Cotyledons** | size | 2-4 (shrinks) |
| **True Leaves** | size, count (max 3) | 3-7 |
| **Flower** | bloom level (bud→full) | 5-6 |
| **Fruit** | size | 6-7 |

### Color Variations

- **Flower colors**: Pink, Orange, Violet, Yellow, Red, Purple (random per sample)
- **Fruit colors**: Red, Orange, Gold, Purple, Green (random per sample)

---

## 📋 Prompts

Stage-specific prompts are defined in `src/prompts.py`:

```python
PROMPTS = {
    "seed_to_germination": [
        "Animate the seed beginning to germinate. A small root should emerge...",
    ],
    "germination_to_sprout": [
        "Show the sprout breaking through the soil surface...",
    ],
    "sprout_to_seedling": [
        "Animate the sprout growing into a seedling with true leaves...",
    ],
    # ... and so on for each transition
}
```

---

## 🧪 Task Design

### Core Idea

The task tests a model's understanding of:
- **Biological sequences**: What comes after each growth stage
- **Visual prediction**: How the plant should change visually
- **Temporal reasoning**: Growth is a gradual, continuous process

### Success Criteria

A generated video is successful when:
1. Plant transforms to the correct next stage
2. Appropriate biological features appear/change
3. Each stage is clearly distinguishable
4. Transition appears natural and continuous

---

## 📚 References

- **Plant Development**: [Wikipedia - Plant Development](https://en.wikipedia.org/wiki/Plant_development)
- **Growth Stages**: [BBCH Scale](https://en.wikipedia.org/wiki/BBCH-scale)
- **Template Framework**: Based on template-data-generator architecture
