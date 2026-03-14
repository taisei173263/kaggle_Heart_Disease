"""
CV 設計。StratifiedKFold と extended strat（strat_key で層化）を提供。
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

from src.config import TARGET_COL, EXTENDED_STRAT_COLS


def get_stratified_kfold(
    y: np.ndarray,
    n_splits: int = 5,
    shuffle: bool = True,
    random_state: int = 42,
) -> StratifiedKFold:
    """StratifiedKFold を返す。"""
    return StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)


def get_extended_strat_key(df: pd.DataFrame) -> np.ndarray:
    """
    strat_key = concat(Thallium, Chest pain type, Number of vessels fluro, Heart Disease)
    を文字列結合 → LabelEncode して層化用の整数列を返す。
    """
    cols = [c for c in EXTENDED_STRAT_COLS if c in df.columns]
    if not cols:
        return df[TARGET_COL].values if TARGET_COL in df.columns else np.zeros(len(df), dtype=int)
    key = df[cols].astype(str).agg("_".join, axis=1)
    le = LabelEncoder()
    return le.fit_transform(key)


def get_extended_stratified_splits(
    X: pd.DataFrame,
    y: np.ndarray,
    n_splits: int = 5,
    shuffle: bool = True,
    random_state: int = 42,
):
    """
    Extended strat 用の層化キーで KFold 的に分割するイテレータ。
    sklearn の StratifiedKFold は strat_key を渡せるので、key で層化する。
    """
    strat_key = get_extended_strat_key(X.assign(**{TARGET_COL: y}))
    kf = StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
    for train_idx, val_idx in kf.split(X, strat_key):
        yield train_idx, val_idx


def get_cv_splits(
    X: pd.DataFrame,
    y: np.ndarray,
    n_splits: int = 5,
    shuffle: bool = True,
    random_state: int = 42,
    use_extended_strat: bool = False,
):
    """
    共通インターフェース。use_extended_strat=True なら extended strat、否则 StratifiedKFold(y)。
    """
    if use_extended_strat:
        return list(get_extended_stratified_splits(X, y, n_splits, shuffle, random_state))
    kf = get_stratified_kfold(y, n_splits, shuffle, random_state)
    return list(kf.split(X, y))
