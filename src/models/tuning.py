"""
LightGBM ハイパーパラメータチューニング（Optuna）。

【学生実装課題】
  このファイルの objective 関数と run_tuning 関数を完成させてください。
  完成すると、手動で試すより効率よく最良のパラメータを探索できます。

【Optuna とは?】
  ハイパーパラメータの最適化フレームワーク。
  指定した探索空間の中から「最も評価指標が高いパラメータの組み合わせ」を
  自動的に効率よく探してくれる（ベイズ最適化ベース）。

  基本的な使い方:
    1. objective 関数を定義する（1つのパラメータセットを試して評価値を返す）
    2. study.optimize(objective, n_trials=50) で自動探索を実行する
    3. study.best_params で最良パラメータを確認する

実行方法（実装完了後）:
    python -m src.models.tuning
    python -m src.models.tuning --n_trials 100 --folds 3
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.config import DATA_DIR, TARGET_COL, FEATURE_NAMES, DEFAULT_SEED
from src.data import load_train_test
from src.utils import set_seed
from src.cv import get_cv_splits
from src.preprocessing import clean_data


def objective(trial, X: pd.DataFrame, y: np.ndarray, n_folds: int = 3, seed: int = DEFAULT_SEED) -> float:
    """
    【実装課題】Optuna の目的関数

    1 回のトライアルで以下を行います:
      1. trial.suggest_* でパラメータを 1 セット提案してもらう
      2. そのパラメータで n_folds CV を実行する
      3. OOF AUC を返す（Optuna はこれを最大化しようとする）

    Parameters
    ----------
    trial : optuna.trial.Trial
        Optuna が管理するトライアルオブジェクト。
        trial.suggest_* でパラメータを提案してもらう。
    X : pd.DataFrame
        特徴量（前処理済み）
    y : np.ndarray
        目的変数（0/1）
    n_folds : int
        チューニング時の CV 分割数。学習より少なくして高速化することが多い。
    seed : int
        再現性のための乱数シード

    Returns
    -------
    float
        OOF AUC スコア（大きいほど良い）

    実装のヒント:
    - trial.suggest_int("パラメータ名", 最小値, 最大値) → 整数パラメータ
    - trial.suggest_float("パラメータ名", 最小値, 最大値, log=True) → 実数パラメータ
      log=True にすると対数スケールで探索（learning_rate などに有効）
    - GBDTPipeline(**params) でモデルを生成して学習する

    実装例（骨格）:
    >>> params = {
    ...     "n_estimators": 1000,  # early stopping を使うので大きめに
    ...     "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
    ...     "max_depth": trial.suggest_int("max_depth", 4, 10),
    ...     "min_child_samples": trial.suggest_int("min_child_samples", 10, 200),
    ...     "subsample": trial.suggest_float("subsample", 0.6, 1.0),
    ...     "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
    ...     "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
    ...     "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
    ... }
    >>> # TODO: n_folds の CV を実行して OOF AUC を計算して return する
    """
    # ============================================================
    # TODO: ここにパラメータ探索空間を定義してください
    # ============================================================
    params = {
        "n_estimators": 1000,
        "early_stopping_rounds": 50,
        "random_state": seed,
        # TODO: 以下のパラメータを trial.suggest_* で定義してください
        #   - learning_rate: 対数スケール推奨 (log=True)
        #   - max_depth: 整数 4〜10
        #   - min_child_samples: 整数 10〜200
        #   - subsample: 実数 0.6〜1.0
        #   - colsample_bytree: 実数 0.6〜1.0
        #   - reg_alpha: 対数スケール推奨 1e-4〜10.0
        #   - reg_lambda: 対数スケール推奨 1e-4〜10.0
    }

    # ============================================================
    # TODO: CV を実行して OOF AUC を計算して return してください
    # ============================================================
    # ヒント: src/train.py の CV ループを参考にしてください
    raise NotImplementedError(
        "objective 関数を実装してください。"
        "src/models/tuning.py の docstring を参照してください。"
    )


def run_tuning(n_trials: int = 50, n_folds: int = 3, seed: int = DEFAULT_SEED):
    """
    【実装課題】チューニングの実行と結果表示

    objective 関数を実装したら、この関数も完成させてください。

    Parameters
    ----------
    n_trials : int
        試行回数。多いほど精度が上がるが時間がかかる。50〜200 が典型的。
    n_folds : int
        チューニング時の CV 分割数。3 にすると学習の 5-fold より高速。
    seed : int
        再現性のための乱数シード

    実装のヒント:
    >>> import optuna
    >>> optuna.logging.set_verbosity(optuna.logging.WARNING)
    >>> study = optuna.create_study(direction="maximize")
    >>> study.optimize(
    ...     lambda trial: objective(trial, X, y, n_folds=n_folds, seed=seed),
    ...     n_trials=n_trials,
    ...     show_progress_bar=True,
    ... )
    >>> print(f"Best AUC: {study.best_value:.4f}")
    >>> print(f"Best params: {study.best_params}")
    """
    set_seed(seed)

    # データ読み込みと前処理
    print("データを読み込んでいます...")
    train_df, _, _ = load_train_test(data_dir=DATA_DIR, optimize=True)
    train_df = clean_data(train_df)
    X = train_df[FEATURE_NAMES].copy()

    y_raw = train_df[TARGET_COL]
    if y_raw.dtype == object or str(y_raw.iloc[0]) in ("Presence", "Absence"):
        y = (y_raw == "Presence").astype(np.int32).values
    else:
        y = np.asarray(y_raw, dtype=np.int32)

    print(f"チューニング開始: n_trials={n_trials}, folds={n_folds}, seed={seed}")
    print("（実装完了後にここが動作します）")

    # ============================================================
    # TODO: optuna.create_study と study.optimize を実装してください
    # ============================================================
    raise NotImplementedError(
        "run_tuning を実装してください。"
        "objective 関数を先に実装してから取り組むことを推奨します。"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LightGBM Optuna チューニング")
    parser.add_argument("--n_trials", type=int, default=50, help="Optuna の試行回数")
    parser.add_argument("--folds", type=int, default=3, help="チューニング時の CV 分割数")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="乱数シード")
    args = parser.parse_args()

    run_tuning(n_trials=args.n_trials, n_folds=args.folds, seed=args.seed)
