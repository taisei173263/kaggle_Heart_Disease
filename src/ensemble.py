"""
アンサンブル: シンプル平均、Rank average、重み付き平均（CV で重み最適化）。
"""
import numpy as np
from scipy.optimize import minimize
from sklearn.metrics import roc_auc_score


def rank_average(preds: list[np.ndarray]) -> np.ndarray:
    """各予測を rank 化 → 平均 → 0-1 に再スケール。"""
    n = len(preds[0])
    ranks = np.zeros(n, dtype=np.float64)
    for p in preds:
        ranks += np.argsort(np.argsort(p)) / (n - 1) if n > 1 else np.zeros(n)
    return (ranks / len(preds)).astype(np.float32)


def simple_average(preds: list[np.ndarray]) -> np.ndarray:
    """シンプル平均。"""
    return np.mean(preds, axis=0).astype(np.float32)


def optimize_weights_by_auc(
    preds: list[np.ndarray],
    y_true: np.ndarray,
    method: str = "mean",
) -> tuple[np.ndarray, np.ndarray]:
    """
    OOF 予測の重みを AUC 最大化で学習。重みは非負・和1。
    Returns:
        weights, blended_pred
    """
    preds = np.stack(preds, axis=1)  # (n, n_models)
    n_models = preds.shape[1]

    def neg_auc(w):
        w = np.maximum(w, 0)
        w = w / w.sum()
        p = preds @ w
        return -roc_auc_score(y_true, p)

    w0 = np.ones(n_models) / n_models
    res = minimize(neg_auc, w0, method="L-BFGS-B", bounds=[(0, 1)] * n_models)
    weights = np.maximum(res.x, 0)
    weights = weights / weights.sum()
    blended = (preds @ weights).astype(np.float32)
    return weights, blended


def blend_predictions(
    preds: list[np.ndarray],
    weights: np.ndarray | None = None,
) -> np.ndarray:
    """重み付き平均。weights が None なら均等。"""
    if weights is None:
        return simple_average(preds)
    preds = np.stack(preds, axis=1)
    return (preds @ np.asarray(weights)).astype(np.float32)


def run_ensemble_cli():
    """python -m src.ensemble: OOF と test を読み、mean/rank/optimized でアンサンブルし保存。"""
    import argparse
    from pathlib import Path
    import pandas as pd
    from src.config import MODELS_DIR, DATA_OUTPUT_DIR, DATA_DIR, TARGET_COL

    parser = argparse.ArgumentParser()
    parser.add_argument("--oof_dir", type=str, default=None, help="OOF/test .npy があるディレクトリ (default: models)")
    parser.add_argument("--out_dir", type=str, default=None, help="提出 CSV の出力先 (default: data/output)")
    args = parser.parse_args()
    oof_dir = Path(args.oof_dir or str(MODELS_DIR))
    out_dir = Path(args.out_dir or str(DATA_OUTPUT_DIR))
    out_dir.mkdir(parents=True, exist_ok=True)

    oof_files = sorted(oof_dir.glob("oof_*.npy"))
    test_files = sorted(oof_dir.glob("test_*.npy"))
    if not oof_files or not test_files:
        print("No oof_*.npy / test_*.npy found in", oof_dir)
        return
    model_names = [f.stem.replace("oof_", "") for f in oof_files]
    oof_list = [np.load(oof_dir / f"oof_{m}.npy") for m in model_names]
    test_list = [np.load(oof_dir / f"test_{m}.npy") for m in model_names]
    train_df = pd.read_csv(DATA_DIR / "train.csv")
    y = train_df[TARGET_COL].values

    sub_template = pd.read_csv(DATA_DIR / "sample_submission.csv")
    for name, pred in [("mean", simple_average(test_list)), ("rank", rank_average(test_list))]:
        sub = sub_template.copy()
        sub[TARGET_COL] = pred
        sub.to_csv(out_dir / f"submission_ensemble_{name}.csv", index=False)
        oof_blend = simple_average(oof_list) if name == "mean" else rank_average(oof_list)
        print(f"Ensemble {name} OOF AUC: {roc_auc_score(y, oof_blend):.4f}")

    weights, oof_opt = optimize_weights_by_auc(oof_list, y)
    test_opt = blend_predictions(test_list, weights)
    sub_template.copy().assign(**{TARGET_COL: test_opt}).to_csv(out_dir / "submission_ensemble_optimized.csv", index=False)
    print(f"Ensemble optimized OOF AUC: {roc_auc_score(y, oof_opt):.4f}, weights: {weights}")


if __name__ == "__main__":
    run_ensemble_cli()
