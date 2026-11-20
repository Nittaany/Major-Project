# Jarvis-EcoSign: Dual-Mode Hand Gesture Interface & Indian Sign Language (ISL) Recognition

> Real-time touchless virtual mouse + continuous Indian Sign Language (ISL) translation from a single standard webcam—running at a locked **30 FPS** on consumer CPU hardware (Apple Silicon ARM64) with no depth sensors or GPUs.

**Publication Status:** Research paper accepted for publication (Springer) · **First Author:** Satyam Chaudhary ([ORCID: 0009-0004-0677-1495](https://orcid.org/0009-0004-0677-1495))

---

## Live System Preview

![Jarvis-EcoSign Eel Web GUI and Live Pipeline](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/ui_demo.jpeg?vercel-blob-valid-until=1795200301402&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=kdV14K9U4RhKaamPvFju7b0mggbPWu01OZyl4A9BRac)

---

## The Problem

Existing assistive gesture systems force a functional split: they provide either deterministic OS navigation (virtual mouse) or probabilistic sign language recognition—rarely both on a standard laptop. Running MediaPipe landmark tracking alongside deep learning inference in a single Python loop hits the Global Interpreter Lock (GIL), dropping throughput to **14 FPS** and causing severe cursor stutter.

---

## Key Engineering Contributions

- **Zero-Copy Multiprocessing (GIL Bypass):** Decouples webcam capture (`vision_backend.py`) from the HCI and ISL consumer processes via `multiprocessing.shared_memory` (`numpy.copyto()`), eliminating ~27.6 MB/s of pipe-and-pickle serialization overhead and restoring a locked **30 FPS** (17–24 ms Vision+HCI loop, well within the 33.3 ms frame budget).
- **Deterministic Virtual Mouse (Mode 1):** 21-point hand heuristics paired with a velocity-adaptive **One Euro Filter** and **Sigmoid ballistic controller** for jitter-free relative cursor navigation without "Gorilla Arm" fatigue. Validated via ISO 9241-9 Fitts' Law pilot testing (n = 1): **0% error rate, 418.7 ms movement time** on standard 1.0 cm GUI targets at 4 cm distance.
- **Scale-Invariant Bi-LSTM ISL Recognition (Mode 2):** Extracts a 201-dimensional upper-body + dual-hand spatial vector via MediaPipe Holistic, applies **Shoulder-Invariant Normalization** (centered on the thoracic midpoint and scaled by inter-acromion distance), and runs a TFLite (Float32) Bi-LSTM across 30-frame interpolated windows.
- **Continuous Sign Language (CSLR) & Temporal Intelligence Engine:** Solves transition noise and UI flickering using a leaky `deque` prediction buffer (`popleft`), 0.85 confidence gate, 0.5s word-hold confirmation, 2.0s cooldown, dynamic 3.0s–6.0s timeouts, and a 10-frame Idle commit trigger.
- **Hybrid Edge + Cloud LLM Bridge:** Routes complex multi-word gloss arrays to a local 4-bit **Apple MLX (`Qwen1.5-1.8B-Chat-4bit`)** model for offline inference or a **Groq (`llama-3.1-8b-instant`)** failsafe in a non-blocking background thread with a 5.0s `ThreadPoolExecutor` timeout.

---

## System Architecture

![System Architecture](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/architecture.png?vercel-blob-valid-until=1795200343735&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=PdKlNr2BDP911ap_x-GSRIjKhgop4bhKqxkRR2WiG58)

| Module                          | Responsibility                                                                                   |
| :------------------------------ | :----------------------------------------------------------------------------------------------- |
| `src/Jarvis.py`                 | Main orchestrator, process lifecycle (`daemon=True`), Eel Web GUI, voice/text fallback           |
| `src/vision_backend.py`         | 30 FPS webcam producer, zero-copy shared memory writer, wake/mode-switch heuristics              |
| `src/HCI_Controller.py`         | 21-point hand heuristics, One Euro Filter, Sigmoid controller, OS actions                        |
| `src/ISL_Controller.py`         | 201-point Holistic extraction, shoulder-invariant normalization, TFLite Bi-LSTM, temporal buffer |
| `src/controllers/llm_engine.py` | Non-blocking Hybrid LLM worker (Apple MLX 4-bit local + Groq API failsafe)                       |

---

## Benchmarks & Evaluation

### 1. Throughput: GIL-Blocked vs. Zero-Copy Multiprocessing

![FPS Benchmark](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/fps_benchmark.jpg?vercel-blob-valid-until=1795200372118&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=quU1IN_BNmXpahOHRtpsGG71jNhMa0MvpGW4RUpNKLc)

### 2. Ablation Study (11-Class ISL Vocabulary, 532 Curated Sequences)

Evaluated on **532 video sequences** merging INCLUDE-50 subsets with custom webcam captures across 11 classes (`Hello`, `Thank You`, `Good Morning`, `Good`, `Happy`, `Time`, `Father`, `Teacher`, `I`, `You (plural)`, and 101 `Idle` negative-control clips) using a stratified 90/10 split:

| Configuration                               | Real-World Accuracy | UI Stability                 |
| :------------------------------------------ | :-----------------: | :--------------------------- |
| Baseline (Raw coordinates, no Idle class)   |       ~12.5%        | Severe flickering            |
| Shoulder-Invariant Normalization (no Idle)  |        59.3%        | Moderate flickering          |
| **Final (Shoulder-Invariant + Idle Class)** |     **96.65%**      | **Substantially stabilized** |

![11-Class Normalized Confusion Matrix](https://YOUR-VERCEL-BLOB-URL/major-project/confusion_matrix.png)

<details>
<summary><strong>View Dataset Distribution & Training Curves (150 Epochs)</strong></summary>

#### Dataset Class Distribution (532 Curated Sequences)

![ISL Dataset Class Distribution](hhttps://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/dataset.jpg?vercel-blob-valid-until=1795200386152&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=lwOBv5XXwLb9Y8rdLppM20c4iSJmG9L6KTbD1ro5sdc)

#### Training & Validation Convergence

|                                                                                                                                                                                                                                         Accuracy Convergence                                                                                                                                                                                                                                          |                                                                                                                                                                                                                                       Loss Convergence                                                                                                                                                                                                                                       |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| ![Model Accuracy](hhttps://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/accuracy.png?vercel-blob-valid-until=1795200402668&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=jIO2yhXrWCCK-mcosPle5i9FWoVs-xu_D7QWG23Eyy0) | ![Model Loss](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/Loss.png?vercel-blob-valid-until=1795200411102&vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNDEzNzc0LCJpYXQiOjE3OTUyMDAyMTM5Mjd9.-W6rXpNuFYMA-DzHfN6_q6B12P_p3YukxJQtvzalDO0&vercel-blob-signature=rmqHdCVqeb-cslqSOwLT8JVQfEdZEQNgFPva36LNl_U) |

</details>

### 3. Temporal Intelligence & Hybrid LLM Output

|                                                                                                                                                                                                            Temporal State Machine (Idle Commit & Cooldown)                                                                                                                                                                                                             |                                                                                                                                                                                                                  Local Apple MLX + Groq LLM Bridge                                                                                                                                                                                                                   |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| ![Temporal Engine](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/temporal_engine.png?vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNjc4ODg5LCJpYXQiOjE3OTUyMDA0NzkwMzl9.DnBk-45fWg1j3HrDcgbA_hi4Piu9zfX1E230UtsodRM&vercel-blob-signature=rnuLXKTtT4BMUDtT-NAiwVEQwyVucwTP7M-_mRRIuIg) | ![MLX LLM Test](https://0j0ljm5uoqzqkt2q.private.blob.vercel-storage.com/mlx_llm_test.png.png?vercel-blob-delegation=eyJzdG9yZUlkIjoic3RvcmVfMGowbEpNNXVPcXpxa1QycSIsIm93bmVySWQiOiJ0ZWFtX2szbnZYdFExb3l3ZkFQb2piVmo2d1VueCIsInBhdGhuYW1lIjoiKiIsIm9wZXJhdGlvbnMiOlsiZ2V0IiwiaGVhZCJdLCJ2YWxpZFVudGlsIjoxNzk1MjQzNjI2MTE2LCJpYXQiOjE3OTUyMDA0MjYyNzh9.MunJlyujXFHEFTdERz8wFCYF0GdZd49i8Dx35puHGzY&vercel-blob-signature=B5SB9EqNtrFTBq2pKq5Y64ptpXP67reELZ88IqB3kNo) |

---

## Design Decisions, Limitations & Tradeoffs

- **Why 11 classes instead of 50+?** Initial training on unconstrained INCLUDE-50 suffered data starvation (~15 samples/class) and studio-to-webcam domain shift. Injecting 101 `Idle` clips prioritized zero false positives during everyday computer use over vocabulary breadth.
- **Known failure modes:** In the 11-class confusion matrix, `Time` showed cross-class confusion, `Teacher` overlapped 33% with `Idle`, and `Good Morning` leaked 20% each into `Good` and `Hello`. In Fitts' Law testing, 0.25 cm targets hit the 640×480 webcam sub-pixel precision floor.
- **Platform scope:** OS bindings (`osascript`) and Apple MLX are built for macOS Apple Silicon (ARM64). Porting to Linux/Windows requires swapping OS bindings (`xdotool`/`pywin32`) and using the Groq/CPU LLM backend.

---

## Quick Start (macOS Apple Silicon)

```bash
git clone [https://github.com/Nittaany/Major-Project.git](https://github.com/Nittaany/Major-Project.git)
cd Major-Project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 src/Jarvis.py
```

- **Wake gesture:** Hold **Thumbs-Up** for 2.0s · **Mode toggle (HCI ↔ ISL):** Hold **Open Palm** for 3.5s.
- **Dataset note:** Raw INCLUDE-50 clips and custom signer recordings (`data/`, ~12 GB locally) are excluded from git due to size and dataset licensing.

---

## Citation

> S. Chaudhary, A. Goyal, and C. Venkatesh, _"Webcam-Based Dual-Mode Hand Gesture Interface for Computer Control and Indian Sign Language,"_ Department of Computing Technologies, SRM Institute of Science and Technology (Accepted for publication, Springer).
