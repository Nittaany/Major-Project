# Jarvis-EcoSign: Dual-Mode Hand Gesture Interface & Indian Sign Language (ISL) Recognition

> **TL;DR:** Jarvis-EcoSign is an open-source, real-time assistive AI system that combines a touchless virtual mouse (HCI) and continuous Indian Sign Language (ISL) translation using a single standard 640×480 webcam. Built for consumer CPU hardware (Apple Silicon ARM64) with no GPUs or depth sensors, it achieves a locked **30 FPS** via zero-copy multiprocessing and **96.65% validation accuracy** across an 11-class ISL vocabulary.

| Specification       | Value                                                                                          |
| :------------------ | :--------------------------------------------------------------------------------------------- |
| **Author**          | Satyam Chaudhary ([ORCID: 0009-0004-0677-1495](https://orcid.org/0009-0004-0677-1495))         |
| **Publication**     | Accepted for publication (Springer) — SRM Institute of Science and Technology                  |
| **Core Stack**      | Python, MediaPipe Holistic, TensorFlow Lite (Bi-LSTM), OpenCV, PyAutoGUI, Eel                  |
| **LLM Backend**     | Hybrid Local **Apple MLX** (`Qwen1.5-1.8B-Chat-4bit`) + **Groq API** (`llama-3.1-8b-instant`)  |
| **Throughput**      | **30 FPS** locked (up from 14 FPS single-threaded GIL baseline)                                |
| **ISL Accuracy**    | **96.65%** (11-class constrained vocabulary, 532 curated sequences, 90/10 split)               |
| **HCI Usability**   | **0% error rate**, 418.7 ms movement time on 1.0 cm targets (ISO 9241-9 Fitts' Law pilot, n=1) |
| **Target Hardware** | macOS Apple Silicon (ARM64), standard consumer webcam, zero GPU required                       |

---

## Live System Preview

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/ui_demo%202.jpeg" width="760" alt="Jarvis-EcoSign Eel Web GUI and Live Terminal Pipeline" />
</p>

---

## What Problem Does Jarvis-EcoSign Solve?

Existing assistive gesture systems suffer from two structural bottlenecks:

1. **Functional Split:** Tools either provide deterministic OS navigation (virtual mouse) or probabilistic sign language translation—rarely both on a standard laptop.
2. **The Python GIL Bottleneck:** Running MediaPipe landmark extraction and Bi-LSTM deep learning inference in a single Python loop causes severe thread contention, dropping throughput to **14 FPS** and freezing the cursor during inference.

---

## System Architecture: How It Achieves 30 FPS Without a GPU

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/architecture.jpeg" width="680" alt="Jarvis-EcoSign Zero-Copy Multiprocessing Architecture" />
</p>

To stay within the **33.3 ms/frame** budget for 30 FPS, Jarvis-EcoSign decouples camera I/O from AI inference using an OS-level producer-consumer architecture:

- **Zero-Copy Shared Memory (GIL Bypass):** Standard `multiprocessing.Queue` pipes pickle and serialize each 640×480×3 frame (~27.6 MB/s at 30 FPS). Instead, `vision_backend.py` writes raw NumPy arrays directly into `multiprocessing.shared_memory` via `numpy.copyto()`, allowing isolated HCI and ISL consumer processes to read frames in $O(1)$ time with zero serialization overhead.
- **Single-Pass Feature Extraction:** MediaPipe Holistic extracts both 21-point hand landmarks (for Mode 1 HCI) and a 201-point upper-body + dual-hand spatial vector (for Mode 2 ISL) in one inference pass.

| Module                          | Responsibility                                                                                   |
| :------------------------------ | :----------------------------------------------------------------------------------------------- |
| `src/Jarvis.py`                 | Main orchestrator, `daemon=True` process lifecycle, Eel Web GUI, voice/text fallback             |
| `src/vision_backend.py`         | 30 FPS webcam producer, zero-copy shared memory writer, wake/mode-switch heuristics              |
| `src/HCI_Controller.py`         | 21-point hand heuristics, One Euro Filter, Sigmoid ballistic controller, OS actions              |
| `src/ISL_Controller.py`         | 201-point Holistic extraction, Shoulder-Invariant Normalization, TFLite Bi-LSTM, temporal buffer |
| `src/controllers/llm_engine.py` | Non-blocking Hybrid LLM worker (Apple MLX 4-bit local + Groq API failsafe)                       |

---

## Benchmarks & Evaluation

### 1. Concurrency Throughput (Single-Threaded vs. Zero-Copy Multiprocessing)

Offloading Bi-LSTM inference (~50–80 ms) to an independent GIL-isolated process keeps the Vision + HCI loop within **17–24 ms/frame**, doubling throughput from **14 FPS to 30 FPS**.

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/fps_benchmark.jpg" width="460" alt="Vision Pipeline Throughput: 14 FPS vs 30 FPS" />
</p>

### 2. ISL Ablation Study (Solving Domain Shift & Softmax Hallucinations)

Evaluated on **532 curated video sequences** (merging INCLUDE-50 subsets with custom webcam captures) across **11 classes** (`Hello`, `Thank You`, `Good Morning`, `Good`, `Happy`, `Time`, `Father`, `Teacher`, `I`, `You (plural)`, and 101 `Idle` negative-control clips) using a stratified 90/10 split (`random_state=42`):

| System Configuration                        | Real-World Accuracy | UI Stability                 |
| :------------------------------------------ | :-----------------: | :--------------------------- |
| Baseline (Raw coordinates, no Idle class)   |       ~12.5%        | Severe flickering            |
| Shoulder-Invariant Normalization (no Idle)  |        59.3%        | Moderate flickering          |
| **Final (Shoulder-Invariant + Idle Class)** |     **96.65%**      | **Substantially stabilized** |

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/confusion_matrix.png" width="580" alt="11-Class Normalized Confusion Matrix" />
</p>

### 3. Continuous Sign Language (CSLR) & Hybrid LLM Pipeline

Raw frame-by-frame LSTM predictions flicker during hand transitions. Jarvis-EcoSign solves this with a **Temporal Intelligence Engine** (leaky 5-frame `deque` buffer, 0.85 confidence gate, 0.5s word-hold confirmation, 2.0s cooldown, dynamic 3.0s–6.0s timeouts, and 10-frame Idle commit) feeding a **Hybrid LLM Bridge** (offline 4-bit Apple MLX + Groq LPU failsafe).

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/temporal_engine.png" width="45%" alt="Temporal State Machine Output" />
  &nbsp;&nbsp;&nbsp;
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/mlx_llm_test.png.png" width="45%" alt="Apple MLX and Groq LLM Bridge Test" />
</p>

---

## Technical Deep Dive (Expandable)

<details>
<summary><strong>1. Mathematical Foundations (Normalization, One Euro Filter & Sigmoid Ballistics)</strong></summary>

- **Shoulder-Invariant Normalization:** Raw pixel coordinates break when users sit closer or farther from a webcam (studio-to-webcam domain shift). All 201 landmark coordinates are centered on the thoracic midpoint $P_{center}$ and scaled by the inter-acromion distance $D_{ref}$ between left ($S_L$) and right ($S_R$) shoulders, then clipped to $[-5.0, 5.0]$:
  $$\hat{x}_i = \frac{x_i - P_{center,x}}{D_{ref}}, \quad \hat{y}_i = \frac{y_i - P_{center,y}}{D_{ref}}$$
- **One Euro Filter (Jitter Suppression):** Adaptive first-order low-pass filter ($\hat{x}_i = \alpha x_i + (1 - \alpha)\hat{x}_{i-1}$) that heavily smooths slow micro-tremors while reducing lag during fast hand sweeps.
- **Sigmoid Ballistic Gain:** Maps relative wrist velocity $v$ to cursor acceleration ($G_{min}=1.0$, $G_{max}=15.0$, $v_{inf}=25$, $k=0.2$) to prevent "Gorilla Arm" fatigue while keeping target acquisition under 500 ms.

</details>

<details>
<summary><strong>2. Bi-LSTM Model Architecture, Training & Dataset Distribution</strong></summary>

- **Input Tensor:** `(1, 30, 201)` — 30 linearly interpolated frames × (75 upper-body pose + 63 left-hand + 63 right-hand 3D coordinates).
- **Network Layers:** `Bidirectional(LSTM(64, return_sequences=True, unroll=True))` → `BatchNorm` → `Dropout(0.3)` → `LSTM(32, unroll=True)` → `BatchNorm` → `Dropout(0.3)` → `Dense(32, ReLU)` → `Dense(11, Softmax)`.
- **Training & Export:** Adam (`lr=0.0005`, `clipnorm=1.0`), Sparse Categorical Cross-Entropy, 150 epochs, batch size 8, EarlyStopping (`patience=25`). Exported to **TensorFlow Lite (Float32, built-in ops)** with `unroll=True` for macOS ARM64 runtime stability.

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/dataset.jpg" width="600" alt="ISL Dataset Class Distribution (532 Sequences)" />
</p>

<p align="center">
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/accuracy.png" width="46%" alt="Model Accuracy Convergence" />
  &nbsp;&nbsp;&nbsp;
  <img src="https://q4rcgfyyqou1ialf.public.blob.vercel-storage.com/Loss.png" width="46%" alt="Model Loss Convergence" />
</p>

</details>

<details>
<summary><strong>3. HCI Gesture Controls & ISO 9241-9 Fitts' Law Pilot Results</strong></summary>

| OS Command             | Gesture              | Geometric State Logic             |
| :--------------------- | :------------------- | :-------------------------------- |
| **Cursor Move**        | Index up             | `Tip_y < PIP_y` (relative motion) |
| **Left / Right Click** | Index / Middle pinch | Euclidean distance `< 0.04`       |
| **Drag & Drop**        | Closed fist          | All fingertips curled             |
| **App Switch**         | Three fingers        | Index, middle, ring extended      |
| **Screenshot**         | Pinky up             | Pinky extended only               |

**Fitts' Law Multi-Directional Tapping Pilot (n=1, CMU HCII Instrument):**

- `W = 1.00 cm, D = 4.0 cm` (standard GUI buttons/tabs): **418.7 ms MT, 0% error**
- `W = 0.25 cm, D = 4.0–8.0 cm`: 60–90% error (hits 640×480 webcam sub-pixel precision floor)

</details>

<details>
<summary><strong>4. Hybrid LLM Concurrency & Fault Tolerance</strong></summary>

- **Dual Routing:** Simple 1–2 word phrases resolve deterministically via `parse_intent()`. Complex multi-word gloss arrays route to a background `llm_worker` thread supporting **Apple MLX (`mlx-community/Qwen1.5-1.8B-Chat-4bit`, ~1.2 GB RAM)** for offline privacy or **Groq (`llama-3.1-8b-instant`)** for ultra-low-latency cloud fallback.
- **Safety Nets:** Wrapped in a strict **5.0-second `ThreadPoolExecutor` timeout** (falls back to raw gloss array on hang/network drop), 2-attempt Groq retry loop, live engine switching via `data/llm_mode.txt`, and microsecond latency logging.

</details>

---

## Design Decisions, Limitations & Tradeoffs

- **Vocabulary Breadth vs. Real-World Reliability:** Initial training on unconstrained INCLUDE-50 suffered data starvation (~15 samples/class) and studio-to-webcam domain shift. Restricting to 11 classes with 101 `Idle` clips eliminated false-positive UI spam during everyday computer use.
- **Known Failure Modes:** In the 11-class confusion matrix, `Time` showed cross-class confusion, `Teacher` overlapped 33% with `Idle`, and `Good Morning` leaked 20% each into `Good` and `Hello`.
- **Platform Scope:** OS bindings (`osascript`) and Apple MLX target macOS Apple Silicon (ARM64). Porting to Linux/Windows requires swapping OS bindings (`xdotool`/`pywin32`) and using the Groq/CPU LLM backend.

---

## Quick Start (macOS Apple Silicon)

```bash
git clone [https://github.com/Nittaany/Major-Project.git](https://github.com/Nittaany/Major-Project.git)
cd Major-Project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 src/Jarvis.py
```

- **Hands-Free Controls:** Hold **Thumbs-Up (2.0s)** to wake the vision pipeline · Hold **Open Palm (3.5s)** to toggle between Virtual Mouse (HCI) and ISL modes.
- **Dataset Note:** Raw INCLUDE-50 clips and custom signer recordings (`data/`, ~12 GB locally) are excluded from git due to size and dataset licensing.

---

## Citation

> S. Chaudhary, A. Goyal, and C. Venkatesh, _"Webcam-Based Dual-Mode Hand Gesture Interface for Computer Control and Indian Sign Language,"_ Department of Computing Technologies, SRM Institute of Science and Technology (Accepted for publication, Springer).
