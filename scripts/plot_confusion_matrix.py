#!/usr/bin/env python3
"""
Regenerate the confusion matrix from the SHIPPED models/ISL_Model.tflite
on the exact held-out split used in training (test_size=0.1, stratify, seed 42).

Output: docs/assets/confusion_matrix.png   (cells show row-% and raw counts)
Run from repo root:  python scripts/plot_confusion_matrix.py
"""
import os
import sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data", "processed")
MODEL_PATH = os.path.join(ROOT, "models", "ISL_Model.tflite")
OUT_PATH = os.path.join(ROOT, "docs", "assets", "confusion_matrix.png")


def load_interpreter(path):
    try:
        import tensorflow as tf
        return tf.lite.Interpreter(model_path=path)
    except ImportError:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter(model_path=path)


def main():
    need = [os.path.join(DATA_DIR, n) for n in ("X.npy", "y.npy", "labels.npy")] + [MODEL_PATH]
    missing = [p for p in need if not os.path.exists(p)]
    if missing:
        print("[ERROR] Missing:", *missing, sep="\n   - ")
        return 2

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import confusion_matrix

    X = np.load(os.path.join(DATA_DIR, "X.npy"))
    y = np.load(os.path.join(DATA_DIR, "y.npy"))
    label_map = np.load(os.path.join(DATA_DIR, "labels.npy"), allow_pickle=True).item()
    names = [k for k, _ in sorted(label_map.items(), key=lambda kv: kv[1])]

    X = np.clip(np.nan_to_num(X, nan=0.0, posinf=5.0, neginf=-5.0), -5.0, 5.0)  # same as training
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)

    interp = load_interpreter(MODEL_PATH)
    interp.allocate_tensors()
    inp, out = interp.get_input_details()[0], interp.get_output_details()[0]
    preds = []
    for clip in X_test:
        interp.set_tensor(inp["index"], clip[np.newaxis].astype(np.float32))
        interp.invoke()
        preds.append(int(np.argmax(interp.get_tensor(out["index"])[0])))
    preds = np.array(preds)

    n = len(names)
    cm = confusion_matrix(y_test, preds, labels=list(range(n)))
    norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    acc = np.trace(cm) / cm.sum()

    fig, ax = plt.subplots(figsize=(9.5, 8))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{norm[i, j]:.2f}\n({cm[i, j]})", ha="center", va="center",
                    fontsize=8, color="white" if norm[i, j] > 0.5 else "black")
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels(names, rotation=45, ha="right"); ax.set_yticklabels(names)
    ax.set_xlabel("Predicted class"); ax.set_ylabel("True class")
    ax.set_title(f"ISL_Model.tflite - held-out confusion matrix "
                 f"(accuracy {acc:.1%}, n={cm.sum()})", pad=12)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fig.savefig(OUT_PATH, dpi=200)
    print(f"[OK] accuracy {acc:.4f} on {cm.sum()} clips -> {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
