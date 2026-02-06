"""
学習用スクリプト・実験管理用。
CLI や Notebook から呼び出して学習・評価・保存を行う。
"""
import pandas as pd
from pathlib import Path

from .config import DEFAULT_SEED, MODELS_DIR, EVAL_METRIC
from .utils import set_seed


def run_train(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame | None = None,
    y_val: pd.Series | None = None,
    model_name: str = "xgboost",
    save_dir: str | Path | None = None,
    seed: int = DEFAULT_SEED,
) -> object:
    """
    学習を実行し、モデルを返す（および保存）。
    save_dir 例: models/20260206_xgboost
    """
    set_seed(seed)

    if model_name == "xgboost":
        import xgboost as xgb
        model = xgb.XGBClassifier(
            random_state=seed,
            eval_metric="auc",
            use_label_encoder=False,
        )
    else:
        raise ValueError(f"Unknown model_name: {model_name}")

    fit_kw = {}
    if X_val is not None and y_val is not None:
        fit_kw["eval_set"] = [(X_val, y_val)]

    model.fit(X_train, y_train, **fit_kw)

    if save_dir is not None:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        model.save_model(str(save_path / "model.json"))

    return model
