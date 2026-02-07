"""
学習用スクリプト・ベースライン（LightGBM CV → 提出ファイル作成）。
コンテナ内の /data を参照（~/kaggle_data にマウント想定）。

使い方:
  python src/train.py
  または: qsub scripts/submit_job.sh src/train.py
"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import os

# --- 設定 ---
DATA_DIR = "/data/datasets/raw"
OUTPUT_DIR = "/data/outputs"
MODEL_DIR = "/data/models"
ID_COL = "id"
TARGET_COL = "Heart Disease"  # コンペの列名（スペースあり）
N_FOLDS = 5
SEED = 42

# LightGBM のデバイス: Kaggle公式イメージの LightGBM は GPU 対応済み
# デフォルトで "cuda" を使用（CPU で動かす場合は環境変数 LGBM_DEVICE=cpu を設定）
LGBM_DEVICE = os.environ.get("LGBM_DEVICE", "cuda")  # "cuda"（GPU・デフォルト） | "cpu"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


def train():
    print("=== データ読み込み ===")
    train_df = pd.read_csv(f"{DATA_DIR}/train.csv")
    test_df = pd.read_csv(f"{DATA_DIR}/test.csv")
    sub_df = pd.read_csv(f"{DATA_DIR}/sample_submission.csv")

    print(f"Train shape: {train_df.shape}")

    # 簡易的な前処理（数値列のみ使用、欠損埋め）
    num_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()
    features = [c for c in num_cols if c not in [ID_COL, TARGET_COL]]

    X = train_df[features]
    y = train_df[TARGET_COL]
    X_test = test_df[features]

    print(f"Features: {len(features)} cols")

    # --- Cross Validation ---
    kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof_preds = np.zeros(len(X))
    test_preds = np.zeros(len(X_test))

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y)):
        print(f"\n--- Fold {fold + 1} ---")
        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]

        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "n_estimators": 1000,
            "learning_rate": 0.05,
            "device": LGBM_DEVICE,  # "cuda" でGPU使用（Dockerfile でCUDA版ビルド済み）
            "verbose": -1,
            "random_state": SEED,
        }
        # CUDA版では gpu_platform_id / gpu_device_id は不要（OpenCL版のみで使用）

        model = lgb.LGBMClassifier(**params)

        callbacks = [
            lgb.early_stopping(stopping_rounds=50, verbose=True),
            lgb.log_evaluation(50),
        ]

        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            eval_metric="auc",
            callbacks=callbacks,
        )

        val_pred = model.predict_proba(X_val)[:, 1]
        oof_preds[val_idx] = val_pred
        test_preds += model.predict_proba(X_test)[:, 1] / N_FOLDS

        score = roc_auc_score(y_val, val_pred)
        print(f"Fold {fold + 1} AUC: {score:.4f}")

        model.booster_.save_model(f"{MODEL_DIR}/lgbm_fold{fold+1}.txt")

    # --- 結果集計 ---
    total_score = roc_auc_score(y, oof_preds)
    print(f"\n=== CV Score (AUC): {total_score:.4f} ===")

    sub_df[TARGET_COL] = test_preds
    sub_path = f"{OUTPUT_DIR}/submission_v1.csv"
    sub_df.to_csv(sub_path, index=False)
    print(f"✅ Submission saved to: {sub_path}")


if __name__ == "__main__":
    train()
