"""
前処理関数。
うまくいった処理はここに切り出し、Notebook から from src.preprocessing import clean_data で利用。
"""
import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    共通の前処理（例）。
    欠損補完・エンコード・外れ値など、チームで決めた処理をまとめる。
    """
    out = df.copy()
    # 例: 欠損を中央値で補完（カラムに応じて要カスタム）
    # out = out.fillna(out.median(numeric_only=True))
    return out


def get_feature_columns(df: pd.DataFrame, target: str = "HeartDisease") -> list:
    """目的変数を除いた特徴量カラム名のリストを返す。"""
    return [c for c in df.columns if c != target]
