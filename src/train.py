"""
ベースライン学習スクリプト。

Kaggle コンペの「メインループ」を理解するためのシンプルな実装。
やっていること:
  1. データを読み込む
  2. 前処理を適用する（src/preprocessing.py）
  3. 5-fold Cross Validation（交差検証）でモデルを学習する
  4. OOF（Out-of-Fold）スコアを表示して提出ファイルを保存する

実行方法:
    python -m src.train
    python -m src.train --seed 42 --folds 5
"""
from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.config import (
    DATA_DIR,
    DATA_OUTPUT_DIR,
    MODELS_DIR,
    ID_COL,
    TARGET_COL,
    FEATURE_NAMES,
    DEFAULT_SEED,
)
from src.data import load_train_test
from src.utils import set_seed
from src.cv import get_cv_splits
from src.preprocessing import clean_data
from src.models.gbdt import GBDTPipeline


def _ensure_dirs():
    """出力ディレクトリが存在しない場合に作成する。"""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # --- 引数 ---
    # 最小限のオプションのみ。複雑な引数は後から必要になったら追加する。
    parser = argparse.ArgumentParser(description="LightGBM ベースライン学習")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="乱数シード（再現性のため）")
    parser.add_argument("--folds", type=int, default=5, help="CV の分割数")
    args = parser.parse_args()

    set_seed(args.seed)
    _ensure_dirs()

    # =========================================================
    # Step 1: データ読み込み
    # =========================================================
    print("=== Step 1: データ読み込み ===")
    train_df, test_df, sub_df = load_train_test(data_dir=DATA_DIR, optimize=True)
    print(f"  Train: {train_df.shape}, Test: {test_df.shape}")

    # ターゲットを 0/1 整数に統一
    # （"Presence"/"Absence" 形式と 0/1 形式が混在する場合に対応）
    y_raw = train_df[TARGET_COL]
    if y_raw.dtype == object or str(y_raw.iloc[0]) in ("Presence", "Absence"):
        y = (y_raw == "Presence").astype(np.int32).values
    else:
        y = np.asarray(y_raw, dtype=np.int32)

    # =========================================================
    # Step 2: 前処理
    # =========================================================
    # clean_data は src/preprocessing.py で実装してください。
    # 欠損補完・型変換などの基本的な前処理を行います。
    print("=== Step 2: 前処理 ===")
    train_df = clean_data(train_df)
    test_df = clean_data(test_df)

    # 特徴量だけを抽出
    X = train_df[FEATURE_NAMES].copy()
    X_test = test_df[FEATURE_NAMES].copy()

    # =========================================================
    # Step 3: 5-fold Cross Validation
    # =========================================================
    # Kaggle の「メインループ」。ここが理解できれば後は応用です。
    #
    # OOF (Out-of-Fold) とは?
    #   各 fold の検証データへの予測を集めたもの。
    #   全 train データに対してリーク（情報漏洩）なしで評価できる。
    #   → OOF スコア ≈ Public LB スコア になるのが理想。
    #
    # なぜ 5-fold CV をするのか?
    #   データを5分割し、4分割で学習・1分割で評価を5回繰り返す。
    #   1回だけ train/val に分けるより、評価の安定性が大幅に向上する。
    print(f"=== Step 3: {args.folds}-fold CV (seed={args.seed}) ===")

    oof = np.zeros(len(X), dtype=np.float32)
    test_preds = np.zeros(len(X_test), dtype=np.float32)

    splits = get_cv_splits(X, y, n_splits=args.folds, random_state=args.seed)

    for fold, (tr_idx, val_idx) in enumerate(splits):
        X_tr, X_val = X.iloc[tr_idx], X.iloc[val_idx]
        y_tr, y_val = y[tr_idx], y[val_idx]

        # モデル学習
        # GBDTPipeline のパラメータは src/models/gbdt.py を参照
        model = GBDTPipeline(random_state=args.seed)
        model.fit(X_tr, y_tr, X_val, y_val)

        # OOF 予測
        oof[val_idx] = model.predict_proba(X_val)

        # テスト予測（各 fold の平均をとる）
        test_preds += model.predict_proba(X_test) / args.folds

        fold_auc = roc_auc_score(y_val, oof[val_idx])
        print(f"  Fold {fold + 1}/{args.folds}  AUC: {fold_auc:.4f}")

    # =========================================================
    # Step 4: CV スコアの確認と提出ファイルの保存
    # =========================================================
    # OOF AUC = 全 fold のリーク無し評価スコア
    # これが Public LB と近い値になっていれば CV が機能している証拠
    oof_auc = roc_auc_score(y, oof)
    print(f"\n=== OOF AUC: {oof_auc:.4f} ===")

    # OOF と test 予測を保存（アンサンブルで後で使う）
    np.save(MODELS_DIR / "oof_gbdt.npy", oof)
    np.save(MODELS_DIR / "test_gbdt.npy", test_preds)

    # 提出ファイルを生成
    sub_out = sub_df.copy()
    sub_out[TARGET_COL] = test_preds
    out_path = DATA_OUTPUT_DIR / "submission.csv"
    sub_out.to_csv(out_path, index=False)
    print(f"提出ファイルを保存しました: {out_path}")
    print(f"提出: ./scripts/submit.sh {out_path} 'LightGBM baseline'")


if __name__ == "__main__":
    main()
