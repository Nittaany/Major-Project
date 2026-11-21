#!/usr/bin/env python3
"""
Stratified K-fold cross-validation of the Bi-LSTM training recipe.

Why: one 54-clip test split has a +/-~9-point 95% interval. Averaging over K folds
(every clip is tested exactly once, never used for selecting epochs) gives a far
more credible number. Architecture/optimizer match the Colab notebook exactly.
Note: this measures the RECIPE, not the specific shipped .tflite file.

Run from repo root:
    python scripts/cross_validate.py                       # 5 folds x 150 epochs (slow)
    python scripts/cross_validate.py --folds 2 --epochs 20 # quick smoke test
"""
import argparse
import os
import sys
import time
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "data", "processed")


def build_model(n_classes, input_shape):
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Bidirectional, BatchNormalization
    model = Sequential([
        Input(shape=input_shape),
        Bidirectional(LSTM(64, return_sequences=True, unroll=True)),
        BatchNormalization(), Dropout(0.3),
        LSTM(32, return_sequences=False, unroll=True),
        BatchNormalization(), Dropout(0.3),
        Dense(32, activation="relu"),
        Dense(n_classes, activation="softmax"),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005, clipnorm=1.0),
                  loss="sparse_categorical_crossentropy",
                  metrics=["sparse_categorical_accuracy"])
    return model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    xp, yp, lp = (os.path.join(DATA_DIR, n) for n in ("X.npy", "y.npy", "labels.npy"))
    if not all(os.path.exists(p) for p in (xp, yp, lp)):
        print("[ERROR] Need data/processed/{X,y,labels}.npy"); return 2

    import tensorflow as tf
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import f1_score, classification_report

    X = np.load(xp); y = np.load(yp)
    label_map = np.load(lp, allow_pickle=True).item()
    names = [k for k, _ in sorted(label_map.items(), key=lambda kv: kv[1])]
    X = np.clip(np.nan_to_num(X, nan=0.0, posinf=5.0, neginf=-5.0), -5.0, 5.0)

    skf = StratifiedKFold(n_splits=a.folds, shuffle=True, random_state=a.seed)
    accs, f1s, all_true, all_pred = [], [], [], []
    for k, (tr, te) in enumerate(skf.split(X, y), 1):
        tf.keras.backend.clear_session()
        tf.keras.utils.set_random_seed(a.seed + k)
        t0 = time.time()
        model = build_model(len(names), X.shape[1:])
        model.fit(X[tr], y[tr], epochs=a.epochs, batch_size=a.batch_size, verbose=0)  # no val, no early stop
        pred = np.argmax(model.predict(X[te], verbose=0), axis=1)   # final-epoch weights, never selected on test
        acc = float(np.mean(pred == y[te]))
        f1 = f1_score(y[te], pred, average="macro", zero_division=0)
        accs.append(acc); f1s.append(f1); all_true.extend(y[te]); all_pred.extend(pred)
        print(f"[fold {k}/{a.folds}] test={len(te):3d}  acc={acc:.4f}  macro-F1={f1:.4f}  ({time.time()-t0:.0f}s)")

    print("\n" + "=" * 60)
    print(f"{a.folds}-fold CV  (epochs={a.epochs}, batch={a.batch_size}, seed={a.seed}, clips={len(X)})")
    print(f"Accuracy : {np.mean(accs):.4f} +/- {np.std(accs, ddof=1) if len(accs) > 1 else 0:.4f} (std over folds)")
    print(f"Macro-F1 : {np.mean(f1s):.4f} +/- {np.std(f1s, ddof=1) if len(f1s) > 1 else 0:.4f}")
    print("=" * 60 + "\nPooled per-class report (every clip tested once):\n")
    print(classification_report(all_true, all_pred, labels=list(range(len(names))),
                                target_names=names, digits=4, zero_division=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
