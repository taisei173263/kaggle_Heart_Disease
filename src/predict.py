"""
推論 + submission 生成。
実行: python -m src.predict --checkpoint outputs/models [--model lr]
または: python -m src.predict --checkpoint outputs/submissions --submission submission_lr.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

from src.config import DATA_DIR, DATA_OUTPUT_DIR, MODELS_DIR, TARGET_COL, ID_COL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default=None, help="e.g. models (default)")
    parser.add_argument("--model", type=str, default=None, help="e.g. lr, gbdt -> use test_{model}.npy")
    parser.add_argument("--submission", type=str, default=None, help="e.g. submission_lr.csv in data/output")
    parser.add_argument("--data_dir", type=str, default=None, help="Path to data dir for sample_submission.csv")
    parser.add_argument("--out", type=str, default=None, help="Output path for submission.csv")
    args = parser.parse_args()

    base = Path(args.checkpoint or str(MODELS_DIR))
    data_dir = Path(args.data_dir or str(DATA_DIR))
    sub_template = pd.read_csv(data_dir / "sample_submission.csv")

    if args.submission:
        src = base / args.submission
        if not src.is_file():
            src = DATA_OUTPUT_DIR / args.submission
        if not src.is_file():
            raise FileNotFoundError(f"Submission file not found: {args.submission}")
        pred_df = pd.read_csv(src)
    else:
        model = args.model or "lr"
        npy_path = base / f"test_{model}.npy"
        if not npy_path.is_file():
            npy_path = MODELS_DIR / f"test_{model}.npy"
        if not npy_path.is_file():
            raise FileNotFoundError(f"Checkpoint not found: test_{model}.npy in {base}")
        test_preds = np.load(npy_path)
        pred_df = sub_template.copy()
        pred_df[TARGET_COL] = test_preds.astype(np.float32)

    if list(pred_df.columns) != list(sub_template.columns) and all(c in pred_df.columns for c in sub_template.columns):
        pred_df = pred_df[sub_template.columns]
    out_path = Path(args.out or str(DATA_OUTPUT_DIR / "submission.csv"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(out_path, index=False)
    print(f"Saved: {out_path} (rows={len(pred_df)})")


if __name__ == "__main__":
    main()
