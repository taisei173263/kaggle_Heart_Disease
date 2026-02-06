"""
パス・定数の管理。
Notebook やスクリプトから from src.config import DATA_RAW_DIR で利用。
"""
from pathlib import Path

# プロジェクトルート（このファイルから2階層上）
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# データパス
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_OUTPUT_DIR = DATA_DIR / "output"

# モデル保存先
MODELS_DIR = PROJECT_ROOT / "models"

# デフォルトの乱数シード
DEFAULT_SEED = 42

# 評価指標
EVAL_METRIC = "roc_auc"

# Kaggle コンペ ID（提出コマンド用）
KAGGLE_COMPETITION = "playground-series-s6e2"
