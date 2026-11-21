# Jarvis-EcoSign — Engineering Deep Dive (source material for README + résumé)

> Everything below is derived from the actual source files. Items marked **⚠ VERIFY** are
> claims in the current README that the code you shared does not (or cannot) back up.
> Fix or soften those before a recruiter reads them; an interviewer who opens the code will find them.

---

## 1. One-paragraph pitch (README top / LinkedIn)

Jarvis-EcoSign is a real-time, CPU-only assistive interface that turns a single 640×480 webcam
into (a) a touchless virtual mouse and (b) a continuous Indian Sign Language (ISL) translator.
A producer process captures frames into OS shared memory; two isolated consumer processes
(HCI and ISL) read them zero-copy, bypassing the Python GIL. ISL frames pass through
MediaPipe Holistic, a shoulder-invariant normalizer, and a Bi-LSTM exported to TFLite; a
temporal state machine converts noisy per-window predictions into stable words, and a hybrid
rule-engine → LLM (Apple MLX local / Groq cloud) layer turns gloss sequences into English.

## 2. Résumé bullets (pick 3–4)

- Architected a 3-process real-time vision pipeline (capture → HCI / ISL) using `multiprocessing.shared_memory`
  with zero-copy NumPy views, eliminating ~27.6 MB/s of frame pickling and GIL contention; throughput 14 → 30 FPS *(author-measured)*.
- Designed a shoulder-invariant landmark normalization (centroid + inter-shoulder scaling) over 201 MediaPipe Holistic
  features, fixing studio-to-webcam domain shift; added an `Idle` negative-control class (101 clips) to suppress false positives.
- Trained and exported a Bi-LSTM (~159 K parameters) to TensorFlow Lite for CPU inference on Apple Silicon; evaluated with
  5-fold stratified cross-validation (**72.7 % ± 4.1 accuracy, macro-F1 0.73**, 532 clips, 11 classes) plus a reproducible
  held-out script (85.2 %, 46/54, on the single 10 % split of the shipped model).
- Built a temporal-intelligence engine (leaky 5-vote buffer, hysteresis confidence gate, 0.5 s hold confirmation,
  2.0 s cooldown, context-aware 3–6 s timeouts, 10-frame idle commit) converting flickering frame predictions into sentences.
- Implemented a 3-tier hybrid translation path: deterministic rule parser → local 4-bit Qwen1.5-1.8B (MLX) → Groq Llama-3.1-8B,
  with 5 s `ThreadPoolExecutor` timeout, retry, result cache and raw-gloss fallback.
- Built a virtual-mouse gesture engine (One Euro Filter, relative-motion cursor, 6 gestures) and evaluated it with an
  ISO 9241-9-style Fitts' Law pilot (n = 1).
- Added a 52-test hardware-free `pytest` suite (normalization invariances, filter stability, gain bounds, intent routing,
  train/serve parity check between two normalizer copies).

## 3. System architecture

```
 Webcam ──► vision_backend.py (producer, flips frame, wake/mode gestures)
                │  np.copyto → SharedMemory('jarvis_shm', 921,600 B) + frame_ready Event
                ├──► HCI process  (HCI_Controller.run_hci)   mode_flag == 0
                └──► ISL process  (ISL_Controller.run_isl)   mode_flag == 1
                         │ result_queue (sentence, glosses, rule_matched)
                         ▼
                 llm_worker thread (HybridLLM) ──► Eel web UI ──► Jarvis.py (voice/text, bridge file watcher)
```

| Concern | Mechanism | File |
|---|---|---|
| Frame transport | `SharedMemory` + `numpy.copyto`, 640×480×3 uint8 = 921,600 B/frame (27.6 MB/s @30 FPS) | `vision_backend.py` |
| Synchronisation | `multiprocessing.Event` (frame_ready, stop_event), shared `Value` mode flag | `vision_backend.py` |
| Mode switching | Thumbs-up 2.0 s = wake; open-palm 3.5 s = toggle HCI/ISL (hot-corner ROI 150 px) | `vision_backend.py` |
| Buffer hygiene | ISL clears all buffers when mode ≠ 1 (no stale sentences across switches) | `ISL_Controller.py` |
| IPC to UI | `data/isl_live.txt` bridge file polled at 10 Hz (mtime) + Eel websocket | `Jarvis.py`, `app.py` |
| LLM routing | `data/llm_mode.txt` written by UI toggle, read per request | `app.py`, `llm_engine.py` |

## 4. Mathematics

### 4.1 Shoulder-invariant normalization (`normalize_features`)
Let `S_L, S_R ∈ ℝ³` be pose landmarks 11/12.

```
c = (S_L + S_R) / 2                    (thoracic centre)
D = ‖S_L − S_R‖₂   (D := 1 if D < 0.01)
x̂ᵢ = (xᵢ − c) / D        for all 25 pose + 21 left-hand + 21 right-hand points (x, y, z)
feature vector ∈ ℝ²⁰¹ = 25·3 + 21·3 + 21·3
```
Properties (each proven by a unit test): invariant to uniform scale `s` and translation `t`
(`(s·x+t − (s·c+t)) / (s·D) = (x−c)/D`); shoulders map to ±0.5 on the x-axis (`‖Ŝ_L − Ŝ_R‖ = 1`).

### 4.2 Temporal resampling (`data_extractor.resize_sequence`)
Each clip of `T` frames is linearly interpolated per feature to `T' = 30`:
`X'[:, j] = interp(linspace(0, T, 30), arange(T), X[:, j])` → input tensor `(1, 30, 201)`.

### 4.3 One Euro Filter (`math_utils.OneEuroFilter`, HCI copy in `HCI_Controller.py`)
```
α(f_c, Δt) = 2π f_c Δt / (2π f_c Δt + 1)
dx̂  = α(f_d, Δt)·(Δx/Δt) + (1 − α)·dx̂_prev           (smoothed velocity, f_d = 1 Hz)
f_c = f_min + β·|dx̂|                                  (speed-adaptive cutoff)
x̂   = α(f_c, Δt)·x + (1 − α)·x̂_prev
```
Slow hand → low cutoff → heavy smoothing (kills tremor). Fast hand → cutoff rises → low lag.
HCI settings in code: `min_cutoff = 0.01`, `β = 1.0`, `d_cutoff = 1.0`.

### 4.4 Sigmoid ballistic gain (`math_utils.SigmoidController`)
```
G(v) = G_min + (G_max − G_min) / (1 + e^{−k (v − v_inf)}),   G_min=1, G_max=15, v_inf=25, k=0.2
```
Bounded in `[1, 15]`, equals 8.0 at `v = v_inf`, monotonic (all tested).
**⚠ VERIFY:** the `HCI_Controller.py` you shared does **not** import `SigmoidController`; it moves the cursor with a constant
`SENSITIVITY = 1.3`. Either wire it in (`dx *= gain.get_gain(speed)`) or remove "sigmoid ballistics" from README/résumé.

### 4.5 Fitts' Law (pilot)
`ID = log₂(D/W + 1)`, throughput `TP = ID / MT`. Reported: W = 1.0 cm, D = 4.0 cm → MT = 418.7 ms, 0 % errors (n = 1).
Sub-pixel targets (W = 0.25 cm) fail at 60–90 % — a webcam resolution floor, which is a useful honest limitation.

## 5. ML model & data

| Item | Value |
|---|---|
| Source data | INCLUDE-50 (train/val/test lists included) + custom webcam recordings (`record_custom_data.py`, 3 s clips, mp4v) |
| Classes | 11: Hello, Thank you, Good morning, Good, Happy, Time, Father, Teacher, I, You (plural), **Idle** |
| Extraction | MediaPipe Holistic (complexity 1, conf 0.5) → `normalize_features` → 30-frame resample; clips ≤ 5 frames discarded |
| Whitelist | `WHITELIST_DIRS` in `data_extractor.py` restricts to 11 folders (targeted extraction) |
| Architecture | `Bi-LSTM(64, return_sequences) → BN → Dropout .3 → LSTM(32) → BN → Dropout .3 → Dense(32, ReLU) → Dense(11, softmax)` |
| Parameters (analytic) | Bi-LSTM 136,192 + BN 512 + LSTM 20,608 + BN 128 + Dense 1,056 + Dense 363 ≈ **158,859** (confirm with `model.summary()`) |
| Training | Adam lr 5e-4, clipnorm 1.0, sparse CCE, 150 epochs, batch 8; `unroll=True` for TFLite on ARM64. EarlyStopping was set to `monitor='loss'` (training loss) so it never fired: all 150 epochs ran and the shipped weights are the final epoch's |
| Export | TFLite float32, builtin ops only |
| Split | `train_test_split(test_size=0.1, stratify=y, random_state=42)` on 532 clips |

**Ablation claims:** earlier README numbers (raw ≈ 12.5 % → normalised 59.3 %) are **not reproducible from any retained log** — present them as
"earlier informal experiments" or leave them out. What *is* supported: shoulder-invariant normalization is proven invariant by unit tests, and
the Idle class exists to give the softmax a null option.

### Verified results (use these)
| Evaluation | Result |
|---|---|
| 5-fold stratified CV (`scripts/cross_validate.py`, 150 epochs, no epoch selection) | **72.74 % ± 4.06** accuracy, macro-F1 **0.726 ± 0.041** (folds: 70.1, 76.6, 74.5, 67.0, 75.5) |
| Shipped `ISL_Model.tflite`, single stratified 10 % split (54 clips) | 85.19 % (46/54), macro-F1 0.859 — 95 % interval ≈ 73–92 % |
| Weakest classes (pooled CV F1) | good 0.57, you (plural) 0.63, hello 0.67, idle 0.68, good morning 0.69 |
| Strongest (pooled CV F1) | father 0.90, happy 0.88, thank you 0.79, teacher 0.79 |

Notes: the 85.2 % split is above every CV fold (max 76.6 %), so treat it as a favourable draw, not the expected accuracy.
`96.65 %` appears nowhere in the training log (best validation accuracy 92.6 %; nearest 96.x figures are *training* accuracy) — do not use it.
Colab trained with `validation_data=(X_test, y_test)`; because the shipped weights are the last epoch (not selected on that data) the
85.2 % is not checkpoint-selected, but epoch count/architecture were chosen while watching that split. Keep CV as the headline.
Training shows overfitting (train ≈ 96 %, val ≈ 85 %; val-loss minimum ≈ epoch 120, then rising).
Risks still to state: clip-level split (same signer/session may appear in train and test), your own recordings mixed with INCLUDE-50.

## 6. Temporal Intelligence Engine (`run_isl`)

Per frame: Holistic → normalize → append to 30-frame `deque` → TFLite inference (once the window is full).

| Stage | Parameter in code |
|---|---|
| Confidence gate (hysteresis) | **0.80** fresh start, **0.70** mid-sentence |
| Prediction smoothing | leaky `deque(maxlen=5)` majority vote (oldest drops; never `.clear()`) |
| Word-hold confirmation | 0.5 s stable before a word is committed |
| Cooldown | 2.0 s against re-adding same word |
| Post-word stability | 0.8 s no finalization after a word is added |
| Idle commit | 10 consecutive Idle frames (~0.33 s) |
| Dynamic timeout | `calculate_dynamic_timeout`: 3.0 empty · 6.0 lone subject · 5.0 subject+1 · 3.5 greeting · 4.0 default, + 1 s extension grace |
| Finalize iff | non-empty ∧ (idle ∨ timeout) ∧ min-buffer ∧ ¬post-word-window ∧ ¬hold-in-progress |

**⚠ VERIFY:** README says a "0.85 confidence gate". In the live code that value only appears in the old commented-out version;
the active gate is 0.80 / 0.70.

### Linguistic layer (`parse_intent`, returns `(sentence, rule_matched)`)
- Tier 0: ≥ 3 glosses → grammatical reorder (`normalize_gloss_order`: pronoun < noun < time < adjective < greeting) → `False` (LLM).
- Tier 1–3: ≤ 2 glosses with deterministic templates (I/YOU/TIME/greetings, TEACHER politeness variants) → `True`, bypasses LLM (zero latency, zero cost).
- Tier 4: anything else → ordered gloss string with `?`/`.` and `False`.
- Known quirk (pinned by a test): `["HELLO","HAPPY"]` → "Hello everyone." (second gloss dropped).

## 7. HCI gesture engine

| Gesture | Rule (MediaPipe 21-pt) |
|---|---|
| Move | index extended (`tip.y < pip.y`), cursor moved **relatively** from knuckle (lm 5) delta × 1.3 |
| Left click | thumb–index distance < 0.04 **and** thumb–middle > 0.06 |
| Right click | thumb–middle < 0.04 **and** thumb–index > 0.06 |
| Drag | all four fingers curled → `mouseDown`, release on any other gesture |
| App switch | index+middle+ring up, pinky down → ⌘-Tab (1 s cooldown) |
| Screenshot | pinky only → ⌘⇧3 (1 s cooldown) |
| Neutral / clutch | open hand → cursor stops (lets user reposition, like lifting a mouse) |

Design points worth stating: relative (trackpad-style) rather than absolute mapping, knuckle anchor instead of fingertip
(pinching doesn't move the pointer), mutual-exclusion margins (0.04 vs 0.06) to prevent click/fist ambiguity,
per-action cooldowns (0.3 s click / 1.0 s system actions).

## 8. Hybrid LLM subsystem (`llm_engine.HybridLLM`)

- Backends: Apple MLX `Qwen1.5-1.8B-Chat-4bit` (offline, ~1.2 GB) and Groq `llama-3.1-8b-instant` (temp 0.3, 50 tokens).
- Mode (`MLX | GROQ | AUTO`) read live from `data/llm_mode.txt`; AUTO tries MLX then Groq.
- Fault tolerance: 5 s `ThreadPoolExecutor` timeout, 2-attempt Groq retry (0.5 s back-off), tuple-keyed result cache,
  final fallback to capitalised raw gloss; ≤ 1 gloss never calls an LLM.
- Prompt engineering: strict-rules system prompt + 4 few-shot examples; output sanitiser strips chat-template tokens and truncates to one sentence.
- Latency is logged per request (ms).

## 9. Quality engineering

- `tests/test_core.py` — 52 tests, ~0.1 s, no hardware/network/TF/MediaPipe (heavy modules stubbed only during import).
- Notable test: `test_utils_and_isl_controller_implementations_agree` — `normalize_features` is **duplicated** in
  `utils/normalization.py` (training) and `ISL_Controller.py` (inference); the test is a train/serve-skew guard.
  Better long-term: have `ISL_Controller` import the utils version.
- `scripts/evaluate_tflite.py` — reproducible held-out evaluation (accuracy, macro/weighted F1, per-class report).
- `verify_system.py` — preflight checks (Python ≥ 3.10, venv, deps, camera, web assets, syntax).

## 10. Honest limitations / things a reviewer may probe

1. ~~**Train/serve preprocessing gap:**~~ **FIXED** (live loop now applies `nan_to_num` + `clip(-5, 5)` like training): training sanitises with `nan_to_num` + `clip(-5, 5)`; the live loop in `run_isl` feeds
   `normalize_features` output straight into TFLite with no clip. Add the same two lines before `np.expand_dims`.
   (The training script isn't in the repo tree — commit it; recruiters want to see it.)
2. **Possible mirror skew:** `vision_backend.py` does `cv2.flip(frame, 1)` before writing to shared memory; `data_extractor.py` ("No Flip")
   and the custom recorder (raw frames saved) use un-mirrored video. Check this affects hand labelling/left-right features.
3. **Missing-hand encoding:** a missing hand becomes zeros *before* centring, so after normalization it is `(0 − c)/D`
   — a position-dependent constant rather than a clean "absent" signal. Consistent between train and serve, but worth masking.
4. Small data (532 clips, 11 classes), 1 signer set for custom data, n = 1 HCI study. Report these as scope, not hide them.
5. macOS-only bindings (⌘ hotkeys, MLX); Gesture_Controller*.py are legacy files that can be moved to `archive/`.
6. Large commented-out legacy blocks in `Jarvis.py` / `vision_backend.py` / `ISL_Controller.py` — delete (git has history).
7. `record_custom_data.py` hard-codes `/Users/nitant/...`; make it relative to repo root.
8. **Frame handshake:** `vision_backend.py` calls `frame_ready.set()` every frame and only clears it on shutdown, so the HCI and ISL loops free-run
   on whatever frame is in shared memory (duplicates/skips; no read lock). Effective ISL window length depends on CPU speed.
9. **Training/inference time base:** training resamples a whole clip (≈2–3 s) to 30 frames; live inference uses the last 30 loop iterations.
10. **Training recipe:** EarlyStopping watches training loss (never stops); validation set == test set; no class weights or augmentation.
11. Idle recall in CV is ≈ 66 % (≈ 1 in 3 idle clips read as a sign) — the runtime confidence gate/hold-confirmation exists to absorb this, but its
    effect has not been measured separately.

## 11. Suggested README restructure (recruiter-first)

1. Title + 1-line value prop + demo GIF (record one: mouse mode → ISL mode → translated sentence).
2. "Results" table — only numbers you can reproduce with a command (`python scripts/evaluate_tflite.py`, `pytest`).
3. Architecture diagram + 3-sentence explanation of the shared-memory design.
4. "Key engineering decisions" (5 bullets: zero-copy IPC, shoulder-invariant normalization, Idle class, temporal engine, hybrid LLM with timeout).
5. "Limitations & next steps" (leakage, signer-disjoint split, vocabulary size, mirror/clip parity).
6. Quick start, tests, licence (MIT), citation.

## 12. Likely interview questions (with the answer the code supports)

- *Why shared memory over a Queue?* Queue pickles 0.92 MB frames 30×/s and serialises on the GIL; shared memory is a view — `O(1)` reads.
- *Why an Idle class?* Softmax must pick something; without a null class every frame is a false positive. Idle recall is ≈ 66 % in CV, so it reduces but does not eliminate false positives; the temporal gate handles the rest *(effect not separately measured)*.
- *Why normalise by shoulder width?* Removes camera distance/body size; proven invariant to scale + translation by test.
- *Why a leaky buffer instead of clearing?* Clearing on one low-confidence frame throws away evidence during hand transitions; majority-of-5 decays gracefully.
- *How do you guard the LLM path?* Rule parser first, 5 s timeout, retry, cache, raw fallback — the UI never blocks.
- *What would you do next?* Signer-disjoint evaluation, CTC/sequence model for true continuous signing, wire sigmoid gain into HCI, Windows/Linux backends.
