"""
パス・定数の管理。
Notebook やスクリプトから from src.config import ... で利用。
環境変数 DATA_DIR でデータパスを上書き可能（Docker では /data/datasets/raw）。
"""
import os
from pathlib import Path

# プロジェクトルート（このファイルから2階層上）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# データパス（Docker では DATA_DIR=/data/datasets/raw を指定推奨）
_DATA_DIR_STR = os.environ.get("DATA_DIR", str(PROJECT_ROOT / "data" / "raw"))
DATA_DIR = Path(_DATA_DIR_STR)
DATA_RAW_DIR = DATA_DIR  # 後方互換
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# 保存先: Docker 内（/data マウント）で実行時は /data に保存（書き込み権限を確実に）
# ローカルではプロジェクトの data/output と models を使用
_use_data_mount = _DATA_DIR_STR.strip().startswith("/data")
DATA_OUTPUT_DIR = Path("/data/outputs") if _use_data_mount else (PROJECT_ROOT / "data" / "output")
MODELS_DIR = Path("/data/models") if _use_data_mount else (PROJECT_ROOT / "models")

# デフォルトの乱数シード
DEFAULT_SEED = 42

# 評価指標
EVAL_METRIC = "roc_auc"

# Kaggle コンペ ID
KAGGLE_COMPETITION = "playground-series-s6e2"

# --- コンペ固有 ---
ID_COL = "id"
TARGET_COL = "Heart Disease"

# 13 特徴（id, target 除外）。スペース含むカラム名のまま扱う
FEATURE_NAMES = [
    "Age",
    "Sex",
    "Chest pain type",
    "BP",
    "Cholesterol",
    "FBS over 120",
    "EKG results",
    "Max HR",
    "Exercise angina",
    "ST depression",
    "Slope of ST",
    "Number of vessels fluro",
    "Thallium",
]

# 低カーディナリティ（カテゴリ扱い可能）
CATEGORICAL_LIKE = {"Sex", "Chest pain type", "FBS over 120", "EKG results", "Exercise angina", "Slope of ST", "Number of vessels fluro", "Thallium"}

# extended strat 用キー列
EXTENDED_STRAT_COLS = ["Thallium", "Chest pain type", "Number of vessels fluro", TARGET_COL]
