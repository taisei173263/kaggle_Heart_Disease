"""
RealMLP パイプライン（任意）。pytabkit が入っていれば実行、なければスキップ。
カテゴリは str → category にキャスト。
"""
import numpy as np
from src.config import DEFAULT_SEED

RealMLPPipeline = None
try:
    import pytabkit
    _HAS_PYTABKIT = True
except ImportError:
    _HAS_PYTABKIT = False


if _HAS_PYTABKIT:
    class RealMLPPipeline:
        def __init__(
            self,
            n_ens: int = 3,
            random_state: int = DEFAULT_SEED,
            **kwargs,
        ):
            self.n_ens = n_ens
            self.random_state = random_state
            self.kwargs = kwargs
            self.model_ = None

        def fit(self, X, y, X_val=None, y_val=None):
            # カテゴリ列は str → category
            if hasattr(X, "columns"):
                X = X.copy()
                for c in X.select_dtypes(include=["object"]).columns:
                    X[c] = X[c].astype("category")
            self.model_ = pytabkit.RealMLP(n_ens=self.n_ens, random_state=self.random_state, **self.kwargs)
            self.model_.fit(X, y, X_val, y_val)
            return self

        def predict_proba(self, X) -> np.ndarray:
            if hasattr(X, "columns"):
                X = X.copy()
                for c in X.select_dtypes(include=["object"]).columns:
                    X[c] = X[c].astype("category")
            return self.model_.predict_proba(X)[:, 1].astype(np.float32)
else:
    class RealMLPPipeline:
        """pytabkit 未インストール時は fit/predict_proba で警告のみ。"""
        def __init__(self, *args, **kwargs):
            import warnings
            warnings.warn("pytabkit is not installed. RealMLP is skipped.", UserWarning)

        def fit(self, X, y, X_val=None, y_val=None):
            return self

        def predict_proba(self, X) -> np.ndarray:
            return np.full(len(X) if hasattr(X, "__len__") else X.shape[0], 0.5, dtype=np.float32)
