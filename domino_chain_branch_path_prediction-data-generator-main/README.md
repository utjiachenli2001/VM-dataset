# Domino Chain Branch Path Prediction Data Generator

A domino chain reasoning task generator for training and evaluating video generation models on spatial reasoning and chain reaction prediction tasks. Based on the template-data-generator framework.

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-org/domino-chain-data-generator.git
cd domino-chain-data-generator

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

Generated domino chains will be saved to `data/questions/domino_chain_task/` with:
- **first_frame.png**: Y-shaped domino arrangement with all dominos standing
- **final_frame.png**: Chain reaction result showing fallen and standing dominos
- **prompt.txt**: Task instructions for predicting which dominos fall
- **ground_truth.mp4**: Video showing the chain reaction animation (optional)

---

## 📁 Structure

```
domino-chain-data-generator/
├── core/                    # ✅ Framework utilities (don't modify)
│   ├── base_generator.py   # Abstract base class
│   ├── schemas.py          # Pydantic models
│   ├── image_utils.py      # Image helpers
│   ├── video_utils.py      # Video generation
│   └── output_writer.py    # File output
├── src/                     # 🎯 Domino chain implementation
│   ├── generator.py        # Domino chain generator (Y-shaped branching)
│   ├── prompts.py          # Chain reaction prediction prompts
│   └── config.py           # Domino chain configuration
├── examples/
│   └── generate.py         # Entry point
└── data/questions/         # Generated output
    └── domino_chain_task/
        └── domino_chain_XXXX/
            ├── first_frame.png
            ├── final_frame.png
            ├── prompt.txt
            └── ground_truth.mp4
```

---

## 📦 Output Format

Each domino chain task produces:

```
data/questions/domino_chain_task/domino_chain_XXXX/
├── first_frame.png          # All dominos standing upright
├── final_frame.png          # Fallen dominos rotated, standing ones upright
├── prompt.txt               # Chain reaction prediction instructions
└── ground_truth.mp4         # Chain reaction animation (optional)
```

### Visual Elements

- **Green rectangle (START)**: Starting domino that initiates the chain
- **Gray rectangles (T1, T2...)**: Trunk dominos leading to the junction
- **Red rectangles (A1, A2...)**: Branch A dominos (left branch)
- **Blue rectangles (B1, B2...)**: Branch B dominos (right branch)
- **Red X mark**: Gap indicator showing where a branch is blocked
- **Rotated dominos**: Fallen state (80° rotation in fall direction)

### Y-Shaped Structure

```
        [START]          ← Green (initiates chain)
           |
          [T1]           ← Gray (trunk)
           |
          [T2]           ← Junction point
         /    \
       /        \
     [A1]      [B1]      ← Red (Branch A) / Blue (Branch B)
      |          |
     [A2]      [B2]
      |          |
     [A3]      [B3]
```

---

## 🎨 Configuration

### Domino Chain Generation Settings

Configure generation in `src/config.py`:

```python
class TaskConfig(GenerationConfig):
    # Structure settings
    trunk_length_min: int = Field(default=1)    # 1-3 dominos before junction
    trunk_length_max: int = Field(default=3)
    branch_length_min: int = Field(default=2)   # 2-4 dominos per branch
    branch_length_max: int = Field(default=4)

    # Block settings
    block_probability: float = Field(default=0.3)  # 30% chance of blocked branch

    # Visual settings
    domino_width: int = Field(default=20)       # Domino rectangle width
    domino_height: int = Field(default=50)      # Domino rectangle height
    domino_spacing: int = Field(default=60)     # Space between dominos
    branch_angle: float = Field(default=35.0)   # Branch angle from vertical

    # Colors (RGB tuples)
    trunk_color: tuple = Field(default=(100, 100, 100))    # Gray
    branch_a_color: tuple = Field(default=(220, 60, 60))   # Red
    branch_b_color: tuple = Field(default=(60, 120, 220))  # Blue
    start_color: tuple = Field(default=(60, 180, 60))      # Green
    background_color: tuple = Field(default=(245, 245, 240))

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

## 🔧 Task Logic

### Chain Reaction Rules

1. **Push START**: The chain reaction begins when START domino is pushed
2. **Sequential Propagation**: Each falling domino knocks over the next in sequence
3. **Junction Split**: At the junction, the reaction splits into two parallel branches
4. **Parallel Execution**: Both branches (A and B) fall simultaneously
5. **Gap Blocking**: If a gap exists in a branch, dominos after the gap remain standing

### Task Types

| Type | Description | Probability |
|------|-------------|-------------|
| Complete | All dominos fall in both branches | 70% |
| Blocked | One branch has a gap, some dominos remain standing | 30% |

### Blocked Branch Example

```
        [START]  ← Falls
           |
          [T1]   ← Falls
           |
          [T2]   ← Falls (junction)
         /    \
       /        \
     [A1]      [B1]   ← Both fall
      |          |
     [A2]      [B2]   ← Both fall
      |        ~~X~~  ← Gap in Branch B
     [A3]      [B3]   ← A3 falls, B3 STANDS
```

**Result**: Fallen = [START, T1, T2, A1, A2, A3, B1, B2], Standing = [B3]

---

## 🎥 Video Generation

Optional ground truth videos show the chain reaction:
- **Initial hold**: All dominos standing (10 frames)
- **Trunk animation**: Sequential falling from START to junction
- **Branch animation**: Parallel falling of both branches simultaneously
- **Blocked handling**: Animation stops at gap, remaining dominos stay upright
- **Final hold**: End state displayed (20 frames)
- **Format**: MP4 with H.264 codec, configurable FPS (default: 15)

---

## 📝 Prompt Types

Three prompt categories based on task type:

### Default Prompts
General chain reaction prediction without specifying if blocked.

### Blocked Prompts
Explicitly mention that one branch has a gap and some dominos won't fall.

### Complete Prompts
Indicate that all dominos are connected and will fall completely.

---

## 🎯 Core Reasoning Challenge

The task tests spatial reasoning abilities:

1. **Chain Propagation Understanding**: Knowing that dominos fall sequentially
2. **Branch Split Comprehension**: Understanding that one junction triggers two parallel paths
3. **Gap Detection**: Identifying blocked branches and predicting which dominos remain standing
4. **State Prediction**: Accurately determining the final state of all dominos

---

## 📚 References

- **Template Data Generator**: Base framework for task generation
- **Domino Physics**: Simplified 2D representation of domino chain reactions
- **Branch Path Prediction**: Spatial reasoning task for video generation models
