"""
データ読み込み・dtypes 最適化（630k 行用）。
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

from src.config import DATA_DIR, ID_COL, TARGET_COL, FEATURE_NAMES


def _optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """メモリ節約のため int8/int16/float32 に変換。"""
    out = df.copy()
    for c in out.columns:
        if c in (ID_COL,):
            continue
        if out[c].dtype == "int64":
            mx, mn = out[c].max(), out[c].min()
            if -128 <= mn and mx <= 127:
                out[c] = out[c].astype("int8")
            elif -32768 <= mn and mx <= 32767:
                out[c] = out[c].astype("int16")
        elif out[c].dtype == "float64":
            out[c] = out[c].astype("float32")
    return out


def load_train_test(
    data_dir: Path | str | None = None,
    optimize: bool = True,
) -> tuple:
    """
    train.csv / test.csv / sample_submission.csv を読み込む。
    Returns:
        train_df, test_df, sample_submission_df
    """
    base = Path(data_dir or DATA_DIR)
    train = pd.read_csv(base / "train.csv")
    test = pd.read_csv(base / "test.csv")
    sub = pd.read_csv(base / "sample_submission.csv")
    if optimize:
        train = _optimize_dtypes(train)
        test = _optimize_dtypes(test)
    return train, test, sub


def get_feature_columns(train_df: pd.DataFrame) -> list[str]:
    """id と target を除いた特徴量カラムのリスト。"""
    drop = {ID_COL, TARGET_COL}
    return [c for c in train_df.columns if c not in drop]
