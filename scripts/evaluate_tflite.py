#!/usr/bin/env python3
"""
Held-out evaluation of models/ISL_Model.tflite.

Reproduces the training-time split exactly:
    X = nan_to_num(X); X = clip(X, -5.0, 5.0)
    train_test_split(X, y, test_size=0.1, stratify=y, random_state=42)

Usage (from repo root):
    python scripts/evaluate_tflite.py
"""
import os
import sys
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data", "processed")  # where data_extractor.py writes
MODEL_PATH = os.path.join(ROOT, "models", "ISL_Model.tflite")


def load_interpreter(path):
    try:
        import tensorflow as tf
        return tf.lite.Interpreter(model_path=path)
    except ImportError:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter(model_path=path)


def main():
    paths = {n: os.path.join(DATA_DIR, n) for n in ("X.npy", "y.npy", "labels.npy")}
    missing = [p for p in paths.values() if not os.path.exists(p)]
    if missing or not os.path.exists(MODEL_PATH):
        print("[ERROR] Required files not found:")
        for p in missing + ([MODEL_PATH] if not os.path.exists(MODEL_PATH) else []):
            print("   -", p)
        print("Run src/ml_tools/data_extractor.py first (writes data/processed/*.npy).")
        return 2

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, f1_score, classification_report

    X = np.load(paths["X.npy"])
    y = np.load(paths["y.npy"])
    label_map = np.load(paths["labels.npy"], allow_pickle=True).item()
    names = [k for k, _ in sorted(label_map.items(), key=lambda kv: kv[1])]

    # Identical sanitization to training
    X = np.nan_to_num(X)
    X = np.clip(X, -5.0, 5.0)

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.1, stratify=y, random_state=42
    )

    interp = load_interpreter(MODEL_PATH)
    interp.allocate_tensors()
    inp, out = interp.get_input_details()[0], interp.get_output_details()[0]

    preds = []
    for clip in X_test:
        interp.set_tensor(inp["index"], clip[np.newaxis].astype(np.float32))
        interp.invoke()
        preds.append(int(np.argmax(interp.get_tensor(out["index"])[0])))
    preds = np.array(preds)

    print("=" * 70)
    print("HELD-OUT EVALUATION: models/ISL_Model.tflite")
    print("=" * 70)
    print(f"Input tensor shape     : {tuple(inp['shape'])}")
    print(f"Total clips            : {len(X)}")
    print(f"Held-out test clips    : {len(X_test)}")
    print(f"Accuracy               : {accuracy_score(y_test, preds):.4f}")
    print(f"Macro-F1               : {f1_score(y_test, preds, average='macro', zero_division=0):.4f}")
    print(f"Weighted-F1            : {f1_score(y_test, preds, average='weighted', zero_division=0):.4f}")
    print()
    labels = list(range(len(names)))
    print(classification_report(y_test, preds, labels=labels, target_names=names,
                                digits=4, zero_division=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
