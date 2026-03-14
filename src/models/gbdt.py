"""
GBDT パイプライン（LightGBM / XGBoost 両対応）。

【このファイルの使い方】
  train.py から GBDTPipeline をインポートして使います。
  まずはデフォルトパラメータで動かし、スコアを確認した後に
  パラメータを手動で調整するか、src/models/tuning.py で
  Optuna による自動チューニングを実装してください。

【LightGBM vs XGBoost】
  - LightGBM が利用可能な場合は LightGBM を使います（高速・省メモリ）
  - LightGBM がない環境では自動的に XGBoost にフォールバックします

【GPU について】
  環境変数 LGBM_DEVICE=gpu を設定すると GPU で学習します（計算ノード推奨）。
  ログインノードなど GPU のない環境では cpu のままにしてください。
"""
import os
import numpy as np
from src.config import DEFAULT_SEED

# 環境変数で GPU/CPU を切り替える。計算ノードでは gpu が有効。
LGBM_DEVICE = os.environ.get("LGBM_DEVICE", "cpu")


def _try_lgb():
    """LightGBM のインポートを試みる。失敗したら None を返す。"""
    try:
        import lightgbm as lgb
        return lgb
    except ImportError:
        return None


def _try_xgb():
    """XGBoost のインポートを試みる。失敗したら None を返す。"""
    try:
        import xgboost as xgb
        return xgb
    except ImportError:
        return None


class GBDTPipeline:
    """
    LightGBM を優先、なければ XGBoost で学習する GBDT パイプライン。

    【各パラメータの解説】

    n_estimators : int (default=1000)
        木の最大本数。大きいほど表現力が上がるが過学習しやすい。
        early_stopping_rounds と組み合わせて使うことで、
        実際には最適な本数で自動的に打ち切られる。

    learning_rate : float (default=0.05)
        各木の寄与度（学習率）。小さいほど慎重に学習するが時間がかかる。
        n_estimators を増やしながら learning_rate を下げると良くなることが多い。
        典型的な値: 0.01 〜 0.1

    max_depth : int (default=6)
        1本の木の最大の深さ。深いほど複雑なパターンを学べるが過学習しやすい。
        典型的な値: 4 〜 8

    min_child_samples : int (default=20)
        葉ノードに必要な最小サンプル数。大きいほど過学習が抑えられる。
        データが多い場合は 50〜200 にすると汎化性能が上がることがある。

    reg_alpha : float (default=0.1)
        L1 正則化（Lasso）の強度。疎な特徴量選択に相当。

    reg_lambda : float (default=0.1)
        L2 正則化（Ridge）の強度。過学習を抑える基本的な正則化。

    subsample : float (default=0.8)
        各木を学習する際に使う訓練データのサンプリング率。
        0.8 = 各木で 80% のデータをランダムに使う。過学習抑制に有効。

    colsample_bytree : float (default=0.8)
        各木を学習する際に使う特徴量のサンプリング率。
        0.8 = 各木で 80% の特徴量をランダムに使う。過学習抑制に有効。

    early_stopping_rounds : int (default=50)
        検証スコアが改善しなくなってから何ラウンド待つか。
        この回数続けて改善しなければ学習を打ち切る（過学習防止）。

    【チューニングの優先順位】
    1. n_estimators + early_stopping_rounds （まずここを調整）
    2. max_depth, num_leaves
    3. min_child_samples
    4. subsample, colsample_bytree
    5. reg_alpha, reg_lambda
    6. learning_rate を下げて n_estimators を増やす（最後の仕上げ）

    自動チューニングは src/models/tuning.py を参照してください。
    """

    def __init__(
        self,
        n_estimators: int = 1000,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        min_child_samples: int = 20,
        reg_alpha: float = 0.1,
        reg_lambda: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        early_stopping_rounds: int = 50,
        random_state: int = DEFAULT_SEED,
        use_lgb: bool | None = None,
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.min_child_samples = min_child_samples
        self.reg_alpha = reg_alpha
        self.reg_lambda = reg_lambda
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.early_stopping_rounds = early_stopping_rounds
        self.random_state = random_state
        self.use_lgb = use_lgb
        self.model_ = None
        self._backend = None  # "lgb" or "xgb"

    def _resolve_backend(self):
        """使用するバックエンド（lgb/xgb）を決定する。"""
        if self._backend is not None:
            return
        if self.use_lgb is True or (self.use_lgb is None and _try_lgb() is not None):
            self._backend = "lgb"
        elif _try_xgb() is not None:
            self._backend = "xgb"
        else:
            raise RuntimeError("LightGBM も XGBoost も利用できません。どちらかをインストールしてください。")

    def fit(self, X, y, X_val=None, y_val=None):
        """
        モデルを学習する。

        X_val, y_val を渡すと early stopping が有効になる（推奨）。
        early stopping なしだと n_estimators 本全てを使うため過学習しやすい。
        """
        self._resolve_backend()
        if self._backend == "lgb":
            return self._fit_lgb(X, y, X_val, y_val)
        return self._fit_xgb(X, y, X_val, y_val)

    def _fit_lgb(self, X, y, X_val, y_val):
        """LightGBM で学習する。"""
        import lightgbm as lgb
        callbacks = []
        if X_val is not None and y_val is not None:
            callbacks = [
                lgb.early_stopping(self.early_stopping_rounds, verbose=False),
                lgb.log_evaluation(0),  # ログを抑制（0 = 出力なし）
            ]
        self.model_ = lgb.LGBMClassifier(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            min_child_samples=self.min_child_samples,
            reg_alpha=self.reg_alpha,
            reg_lambda=self.reg_lambda,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            objective="binary",   # 2値分類
            metric="auc",         # 早期終了の判定に使う指標
            device=LGBM_DEVICE,   # "cpu" or "gpu"
            verbose=-1,
            random_state=self.random_state,
        )
        if X_val is not None and y_val is not None:
            self.model_.fit(X, y, eval_set=[(X_val, y_val)], callbacks=callbacks)
        else:
            self.model_.fit(X, y)
        return self

    def _fit_xgb(self, X, y, X_val, y_val):
        """XGBoost で学習する（LightGBM がない場合のフォールバック）。"""
        import xgboost as xgb
        dtrain = xgb.DMatrix(X, label=y)
        dval = xgb.DMatrix(X_val, label=y_val) if (X_val is not None and y_val is not None) else None
        params = {
            "objective": "binary:logistic",
            "eval_metric": "auc",
            "max_depth": self.max_depth,
            "eta": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "reg_alpha": self.reg_alpha,
            "reg_lambda": self.reg_lambda,
            "min_child_weight": self.min_child_samples,
            "seed": self.random_state,
        }
        evals = [(dtrain, "train")]
        if dval is not None:
            evals.append((dval, "val"))
        self.model_ = xgb.train(
            params,
            dtrain,
            num_boost_round=self.n_estimators,
            evals=evals,
            early_stopping_rounds=self.early_stopping_rounds if dval is not None else None,
            verbose_eval=False,
        )
        return self

    def predict_proba(self, X) -> np.ndarray:
        """
        各サンプルの陽性クラス（Heart Disease=1）の確率を返す。

        Returns
        -------
        np.ndarray of shape (n_samples,)
            各サンプルが陽性（心疾患あり）である確率（0〜1）
        """
        self._resolve_backend()
        if self._backend == "lgb":
            return self.model_.predict_proba(X)[:, 1].astype(np.float32)
        import xgboost as xgb
        d = xgb.DMatrix(X)
        return self.model_.predict(d).astype(np.float32)
