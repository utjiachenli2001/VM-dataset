# Construction Stack Data Generator 🧱

A block stacking/rearrangement task generator for training and evaluating video generation models on spatial reasoning tasks. Based on the template-data-generator framework with Tower of Hanoi-style puzzle mechanics.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/construction-stack-generator.git
cd construction-stack-generator

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Generate block stacking tasks
python examples/generate.py --num-samples 50
```

### Output

Generated tasks will be saved to `data/questions/construction_stack_task/` with:
- **first_frame.png**: Current state vs Target state side-by-side
- **final_frame.png**: Solved state (current matches target)
- **prompt.txt**: Rearrangement instructions
- **ground_truth.mp4**: Video showing solution with move counter

---

## 📁 Structure

```
construction-stack-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🧱 Block stacking implementation
│   ├── generator.py        # Block stacking generator (BFS solver)
│   ├── prompts.py          # Task prompts by difficulty
│   └── config.py           # Block stacking configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── construction_stack_task/
        └── construction_stack_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each block stacking task produces:

```
data/questions/construction_stack_task/construction_stack_XXXX/
├── first_frame.png          # CURRENT vs TARGET side-by-side
├── final_frame.png          # Solved state with move count
├── prompt.txt               # Rearrangement instructions
└── ground_truth.mp4         # Solution animation (optional)
```

### Visual Elements

- **Colored blocks**: Red, Blue, Green, Yellow, Purple, Orange (with letter labels)
- **CURRENT section**: Left side showing initial block arrangement
- **TARGET section**: Right side showing goal arrangement
- **Platforms**: Gray base platforms for each stack position
- **Move counter**: Displayed at bottom, shows "Solved in X moves (Optimal: Y)" when complete

---

## 🎨 Configuration

### Block Stacking Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Stack configuration
    num_stacks: int = Field(default=3)      # 2-3 stacks (Hanoi-style)
    min_blocks: int = Field(default=3)      # Minimum blocks per puzzle
    max_blocks: int = Field(default=5)      # Maximum blocks per puzzle

    # Visual styling
    block_width: int = Field(default=60)    # Block width in pixels
    block_height: int = Field(default=40)   # Block height in pixels
    image_size: tuple = Field(default=(640, 480))

    # Colors (hex)
    block_colors: list = Field(default=[
        "#E74C3C",  # Red
        "#3498DB",  # Blue
        "#2ECC71",  # Green
        "#F1C40F",  # Yellow
        "#9B59B6",  # Purple
        "#E67E22",  # Orange
    ])

    # Animation settings
    lift_frames: int = Field(default=8)     # Frames for lifting block
    move_frames: int = Field(default=12)    # Frames for horizontal movement
    lower_frames: int = Field(default=8)    # Frames for lowering block
    hold_frames: int = Field(default=10)    # Frames to hold at start/end
    pause_between_moves: int = Field(default=5)

    # Video settings
    generate_videos: bool = Field(default=True)
    video_fps: int = Field(default=15)
```

### Command-Line Usage

```bash
# Basic generation
python examples/generate.py --num-samples 50

# Custom output directory
python examples/generate.py --num-samples 100 --output data/my_stacks

# Reproducible generation with seed
python examples/generate.py --num-samples 50 --seed 42

# Without videos (faster)
python examples/generate.py --num-samples 50 --no-videos
```

---

## 🔧 Algorithms

### Puzzle Generation

1. **Random State Generation**
   - Select 3-5 blocks from color palette
   - Distribute randomly across 2-3 stacks
   - Generate different random target state
   - Verify states are different and solvable

2. **Difficulty Classification**
   - **Easy**: 1-3 moves required
   - **Medium**: 4-6 moves required
   - **Hard**: 7+ moves required

### Solver (BFS)

- Uses **Breadth-First Search** for optimal solution
- Guarantees minimum number of moves
- Explores all possible moves level by level
- Limited to 20 moves max (sufficient for 5 blocks)

### Move Rules (Tower of Hanoi-style)

- Only the **topmost block** of any stack can be moved
- Blocks can be placed on **any stack** (unlimited capacity)
- Goal: Transform CURRENT state to match TARGET state

---

## 🎥 Video Generation

Ground truth videos show the complete solution:

1. **Hold**: Initial state displayed for 10 frames
2. **For each move**:
   - **Lift**: Block rises vertically (8 frames)
   - **Translate**: Block moves horizontally (12 frames)
   - **Lower**: Block descends to destination (8 frames)
   - **Pause**: Settled state shown (5 frames)
3. **Hold**: Final solved state with "Solved in X moves (Optimal: Y)" message

- MP4 format with mp4v codec
- Configurable FPS (default: 15)
- Move counter overlaid on every frame

---

## 🎯 Task Description

### Scene Layout

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│      CURRENT              │         TARGET          │
│                           │                         │
│   ┌───┐                   │                 ┌───┐   │
│   │ R │                   │                 │ G │   │
│   ├───┤     ┌───┐         │   ┌───┐         ├───┤   │
│   │ B │     │ G │         │   │ R │         │ B │   │
│   ═════     ═════   ═════ │   ═════   ═════ ═════   │
│                           │                         │
│              Moves: 0                               │
└─────────────────────────────────────────────────────┘
```

### Core Mechanics

- **Objective**: Rearrange blocks from CURRENT to match TARGET
- **Constraint**: Only move top block of any stack
- **Goal**: Minimize total number of moves
- **Success**: Display "Solved in X moves (Optimal: Y)"

---

## 📚 References

- **Tower of Hanoi**: [Wikipedia](https://en.wikipedia.org/wiki/Tower_of_Hanoi)
- **Blocks World**: [AI Planning Domain](https://en.wikipedia.org/wiki/Blocks_world)
- **BFS Algorithm**: [Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
