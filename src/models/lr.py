"""
LogisticRegression パイプライン。
solver: lbfgs / saga, class_weight: None / balanced, スケーリング: MinMax / Standard。
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from src.config import DEFAULT_SEED


class LRPipeline:
    def __init__(
        self,
        solver: str = "lbfgs",
        max_iter: int = 2000,
        class_weight: str | None = None,
        scale: str = "minmax",
        C: float = 1.0,
        random_state: int = DEFAULT_SEED,
    ):
        self.solver = solver
        self.max_iter = max_iter
        self.class_weight = class_weight  # None or "balanced"
        self.scale = scale  # "minmax" or "standard"
        self.C = C
        self.random_state = random_state
        self.scaler = MinMaxScaler() if scale == "minmax" else StandardScaler()
        self.model = LogisticRegression(
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            C=C,
            random_state=random_state,
        )

    def fit(self, X: np.ndarray, y: np.ndarray, X_val=None, y_val=None):
        X_sc = self.scaler.fit_transform(X)
        self.model.fit(X_sc, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_sc = self.scaler.transform(X)
        return self.model.predict_proba(X_sc)[:, 1].astype(np.float32)

    def get_params(self):
        return {
            "solver": self.solver,
            "max_iter": self.max_iter,
            "class_weight": self.class_weight,
            "scale": self.scale,
            "C": self.C,
        }
