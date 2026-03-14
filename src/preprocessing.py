"""
前処理関数。

【学生実装課題】
  このファイルの clean_data 関数と numeric_type_cast 関数を実装してください。
  train.py から `from src.preprocessing import clean_data` で呼び出されます。

実装する内容:
  1. 欠損補完: 数値列 → 中央値、カテゴリ列 → 最頻値
  2. 型変換: object 型の数値列を int / float に変換

ヒント:
  - df[col].median() で中央値が取得できます
  - df[col].mode()[0] で最頻値（最初の値）が取得できます
  - pd.to_numeric(df[col], errors="coerce") で数値変換できます
"""
import numpy as np
import pandas as pd

from src.config import TARGET_COL, CATEGORICAL_LIKE, FEATURE_NAMES


def numeric_type_cast(df: pd.DataFrame) -> pd.DataFrame:
    """
    【実装課題 1/2】型変換

    object 型になっている数値列を適切な int / float 型に変換してください。
    ただし、TARGET_COL（ターゲット列）は変換しないよう注意してください。

    Parameters
    ----------
    df : pd.DataFrame
        変換前の DataFrame

    Returns
    -------
    pd.DataFrame
        型変換後の DataFrame（元の df は変更しない）

    実装のポイント:
    - FEATURE_NAMES に含まれる列を対象にする（src.config を参照）
    - CATEGORICAL_LIKE に含まれる列は整数型（int）に変換する
    - それ以外の数値っぽい列は float に変換する
    - pd.to_numeric(series, errors="coerce") を使うと便利
      （変換できない値は NaN になる）

    実装例:
    >>> out = df.copy()
    >>> for col in FEATURE_NAMES:
    ...     if col not in out.columns:
    ...         continue
    ...     if col in CATEGORICAL_LIKE:
    ...         out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    ...     else:
    ...         out[col] = pd.to_numeric(out[col], errors="coerce")
    >>> return out
    """
    out = df.copy()
    for col in FEATURE_NAMES:
        if col not in out.columns:
            continue
        if col in CATEGORICAL_LIKE:
            out[col] = pd.to_numeric(out[col], errors="coerce")
            # Int64 は nullable。環境によっては int64 に fillna(0) して astype(int) でも可
            if out[col].isnull().any():
                out[col] = out[col].astype("Int64")
            else:
                out[col] = out[col].astype(np.int64)
        else:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype(np.float64)
    return out


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    【実装課題 2/2】欠損補完

    各列の欠損値（NaN）を適切な値で埋めてください。

    Parameters
    ----------
    df : pd.DataFrame
        欠損補完前の DataFrame（numeric_type_cast 後のもの）

    Returns
    -------
    pd.DataFrame
        欠損補完後の DataFrame（元の df は変更しない）

    実装のポイント:
    - CATEGORICAL_LIKE に含まれる列 → 最頻値（mode）で補完
    - それ以外の数値列 → 中央値（median）で補完
    - TARGET_COL は補完しない（学習データにしか存在しないため）
    - train でフィットした補完値を test にも適用したい場合は
      別途辞書で保持する設計にすることもできる（今回は簡略化）

    実装例:
    >>> out = df.copy()
    >>> for col in FEATURE_NAMES:
    ...     if col not in out.columns or out[col].isnull().sum() == 0:
    ...         continue
    ...     if col in CATEGORICAL_LIKE:
    ...         fill_val = out[col].mode()[0]
    ...     else:
    ...         fill_val = out[col].median()
    ...     out[col] = out[col].fillna(fill_val)
    >>> return out
    """
    out = df.copy()
    for col in FEATURE_NAMES:
        if col not in out.columns or out[col].isnull().sum() == 0:
            continue
        if col in CATEGORICAL_LIKE:
            mode_vals = out[col].mode()
            fill_val = mode_vals[0] if len(mode_vals) > 0 else 0
        else:
            fill_val = out[col].median()
            if pd.isna(fill_val):
                fill_val = 0
        out[col] = out[col].fillna(fill_val)
    return out


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    前処理のメインエントリーポイント。train.py から呼び出されます。

    numeric_type_cast → fill_missing の順に適用します。
    上の2つの関数を実装すれば、この関数は変更不要です。

    Parameters
    ----------
    df : pd.DataFrame
        元データ（train_df または test_df）

    Returns
    -------
    pd.DataFrame
        前処理済みの DataFrame
    """
    out = numeric_type_cast(df)
    out = fill_missing(out)
    return out


def get_feature_columns(df: pd.DataFrame, target: str = TARGET_COL) -> list:
    """目的変数を除いた特徴量カラム名のリストを返す。"""
    return [c for c in df.columns if c != target]
