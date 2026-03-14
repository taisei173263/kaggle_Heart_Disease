"""
便利関数（シード固定・難例分析など）。
"""
import os
import random
import argparse
import numpy as np


def set_seed(seed: int = 42) -> None:
    """再現性のためのシード固定（numpy / random / sklearn / lightgbm / xgb）。"""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    try:
        import sklearn
        sklearn.utils.check_random_state(seed)
    except Exception:
        pass
    try:
        import lightgbm as lgb
        # lightgbm は fit の random_state で固定
    except ImportError:
        pass
    try:
        import xgboost as xgb
        # xgb は fit の random_state で固定
    except ImportError:
        pass


def analyze_hard_cases(
    oof_pred: np.ndarray,
    y_true: np.ndarray,
    X=None,
    top_k: int = 500,
    out_path: str | None = None,
):
    """
    OOF で |pred - y| が大きい上位 k 件を抽出し、難例として返す。
    学習データの「掃除」はせず分析のみ。out_path があれば CSV 保存。
    """
    import pandas as pd
    err = np.abs(oof_pred - y_true.ravel())
    idx = np.argsort(err)[::-1][:top_k]
    hard = pd.DataFrame({
        "index": idx,
        "oof_pred": oof_pred[idx],
        "y_true": y_true.ravel()[idx],
        "error": err[idx],
    })
    if X is not None and hasattr(X, "iloc"):
        hard_df = pd.concat([hard.reset_index(drop=True), X.iloc[idx].reset_index(drop=True)], axis=1)
    else:
        hard_df = hard
    if out_path:
        hard_df.to_csv(out_path, index=False)
    return hard_df


def main_analyze_hard_cases():
    """CLI: python -m src.utils --analyze_hard_cases"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze_hard_cases", action="store_true", help="Analyze hard cases from OOF")
    parser.add_argument("--oof", type=str, default=None, help="Path to oof_*.npy (e.g. outputs/oof/oof_lr.npy)")
    parser.add_argument("--train", type=str, default=None, help="Path to train.csv")
    parser.add_argument("--top_k", type=int, default=500)
    parser.add_argument("--out", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()
    if not args.analyze_hard_cases or not args.oof or not args.train:
        print("Usage: python -m src.utils --analyze_hard_cases --oof outputs/oof/oof_lr.npy --train data/raw/train.csv [--top_k 500] [--out hard_cases.csv]")
        return
    import pandas as pd
    from pathlib import Path
    from src.config import TARGET_COL, DATA_DIR
    oof = np.load(args.oof)
    train_path = args.train or str(Path(DATA_DIR) / "train.csv")
    train = pd.read_csv(train_path, nrows=None)
    y = train[TARGET_COL].values
    X = train.drop(columns=[TARGET_COL, "id"], errors="ignore")
    df = analyze_hard_cases(oof, y, X, top_k=args.top_k, out_path=args.out)
    print(f"Hard cases (top {args.top_k}):")
    print(df.head(20))
    if args.out:
        print(f"Saved to {args.out}")


if __name__ == "__main__":
    main_analyze_hard_cases()
