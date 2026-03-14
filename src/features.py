"""
特徴量エンジニアリング（読む素材・完成版）。

【このファイルの使い方】
  このファイルは「読んで理解する」素材です。実装を変更する必要はありません。
  特に以下の3点を理解してください:

  1. なぜ Target Encoding（TE）が有効なのか
  2. なぜ fold 内で fit しなければならないのか（リーク防止）
  3. 交互作用特徴量の考え方

【Kaggle 初心者向け解説】
  特徴量エンジニアリングとは、元の特徴量から新しい特徴量を作ること。
  モデルが「学習しやすい形」にデータを変換する作業です。

  例えば、年齢(Age)と最大心拍数(Max HR)が別々にあるより、
  「年齢 ÷ 最大心拍数」という比率にしたほうが心臓への負荷を
  直接的に表現できる、といった考え方です。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional

from src.config import FEATURE_NAMES, TARGET_COL


def optional_preprocess(
    df: pd.DataFrame,
    use_log1p_st: bool = False,
    use_ekg_merge: bool = False,
    use_winsorize: bool = False,
    winsorize_quantile: float = 0.01,
) -> pd.DataFrame:
    """
    オプションの前処理を適用する。

    【解説】
    ベースラインが動いた後に「スコアが上がるか試す」処理群。
    EDA で観察した特性に基づいて有効なものを ON にする。

    Parameters
    ----------
    use_log1p_st : bool
        ST depression を log1p 変換するか。
        ST depression は 0 が多く右に裾が長い分布（歪んでいる）。
        log1p = log(1 + x) を適用すると分布が正規分布に近づき、
        線形モデルや距離ベースのモデルで効きやすくなる。
    use_ekg_merge : bool
        EKG results の値 1 を 2 にまとめるか。
        EDA で「1 と 2 が同じような陽性率を示す」なら統合が有効。
    use_winsorize : bool
        BP, Cholesterol の両端 1% をクリップするか。
        外れ値をカットすることで、ツリー系モデルでは効果薄いが
        線形モデル（LR）では有意に効くことがある。
    """
    out = df.copy()

    if use_log1p_st and "ST depression" in out.columns:
        # clip(lower=0): 念のため負の値を 0 にしてから log1p 適用
        out["ST depression"] = np.log1p(out["ST depression"].clip(lower=0))

    if use_ekg_merge and "EKG results" in out.columns:
        # EKG results は 0, 1, 2 の 3 値。1 と 2 は同様の陽性率の場合は統合
        out["EKG results"] = out["EKG results"].replace(1, 2)

    if use_winsorize:
        for col in ("BP", "Cholesterol"):
            if col not in out.columns:
                continue
            lo = out[col].quantile(winsorize_quantile)
            hi = out[col].quantile(1 - winsorize_quantile)
            out[col] = out[col].clip(lo, hi)

    return out


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    交互作用特徴量・派生特徴量を追加する。

    【解説】
    「交互作用特徴量」とは、2つ以上の特徴量を組み合わせた新しい特徴量のこと。
    ドメイン知識（医学的知識）を活かして設計するのが理想的。

    例:
    - Age_per_MaxHR: 「年齢 / 最大心拍数」
        → 最大心拍数の理論値は「220 - 年齢」なので、
          年齢に対して心拍数がどれだけ下がっているかを表す
    - BP_x_Chol: 「血圧 × コレステロール / 10000」
        → 両方が高いと心疾患リスクが高まるという医学的背景
    - Expected_MaxHR: 「220 - 年齢」（理論上の最大心拍数）
    - MaxHR_deficit: 「理論値 - 実測値」
        → 実測値が理論値より大幅に低い場合は心臓機能の低下を示す

    交互作用特徴量の考え方:
    - 数値 × 数値 → 積・比・差など
    - カテゴリ × 数値 → カテゴリ別に平均・分散（TE がこれに近い）
    - ドメイン知識がなければ EDA の「相関」をヒントに設計する
    """
    out = df.copy()

    if "Age" in out.columns and "Max HR" in out.columns:
        out["Age_per_MaxHR"] = out["Age"] / (out["Max HR"] + 1)

    if "BP" in out.columns and "Cholesterol" in out.columns:
        out["BP_x_Chol"] = (out["BP"] * out["Cholesterol"]) / 10000.0

    if "ST depression" in out.columns and "Exercise angina" in out.columns:
        # Stress_Score: 運動時の心臓ストレスを表す複合指標
        out["Stress_Score"] = out["ST depression"] + out["Exercise angina"]

    if "Age" in out.columns:
        # Expected_MaxHR: 年齢から推定される理論最大心拍数
        out["Expected_MaxHR"] = 220 - out["Age"]

    if "Expected_MaxHR" in out.columns and "Max HR" in out.columns:
        # MaxHR_deficit: 理論値と実測値の差（大きいほど心機能が低い可能性）
        out["MaxHR_deficit"] = out["Expected_MaxHR"] - out["Max HR"]

    return out


def build_target_encoding_fold(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
    columns: list[str],
    global_mean: float = 0.5,
    global_median: float = 0.5,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Target Encoding（TE）を fold 内でフィットして val/test に適用する。

    【Target Encoding とは?】
    カテゴリ変数を「そのカテゴリにおけるターゲットの統計値」で置き換える手法。

    例えば「Thallium」列に値 3 がある場合:
      → Thallium=3 の訓練データ内での Heart Disease=1 の割合（平均）を計算
      → その値で 3 を置き換える
      → 3 という数字より「心疾患との関連強度」として表現できる

    LightGBM などのツリーモデルは元のカテゴリ値でも学習できるが、
    TE を使うことで「陽性率の序列」が数値として明示されるため、
    少ない木でより良い分岐が学習できる。

    【なぜ fold 内でフィットしなければならないのか?（リーク防止）】

    NG な例（リーク発生）:
      全訓練データで mean_target を計算 → val にも同じ値を使う
      → val データのターゲットの情報が mean_target に含まれている
      → 擬似的にターゲットが「見えている」状態になる
      → CV スコアが過楽観的になり LB スコアと乖離する

    正しい実装（このコードのやり方）:
      fold の tr_idx だけで mean_target を計算 → val_idx の行にのみ適用
      → val データはこの計算に含まれていないのでリークなし
      → test データにも同じ tr_idx の統計値を適用する

    計算している統計値:
    - {col}_te_mean:   カテゴリ別のターゲット平均（最も基本的な TE）
    - {col}_te_median: カテゴリ別のターゲット中央値（外れ値に頑健）
    - {col}_te_var:    カテゴリ別のターゲット分散（不確実性の指標）
    - {col}_te_count:  カテゴリ別のサンプル数（出現頻度の指標）
    - {col}_te_freq:   カテゴリの出現頻度（全体に占める割合）

    Parameters
    ----------
    X_train, y_train : fold の学習データと目的変数
    X_val            : fold の検証データ（TE の fit には含めない！）
    X_test           : テストデータ
    columns          : TE を適用するカラムのリスト
    global_mean      : 未知カテゴリ（val/test にしかないカテゴリ）の代替値

    Returns
    -------
    X_train_te, X_val_te, X_test_te
        元の X_* は変更せず、TE の新列 DataFrame のみを返す。
        呼び出し側で pd.concat([X_tr, X_tr_te], axis=1) のように結合する。
    """
    y_train = np.asarray(y_train).ravel()
    tr_te_list, val_te_list, te_te_list = [], [], []

    for col in columns:
        if col not in X_train.columns:
            continue

        # 訓練データ（このfoldの tr_idx だけ）でターゲット統計を計算
        agg = pd.DataFrame({"y": y_train, "v": X_train[col].astype(str)}).groupby("v")["y"].agg(
            ["mean", "median", "var", "count"]
        )
        agg = agg.fillna(0)
        agg["var"] = agg["var"].fillna(0).astype(np.float32)

        # 頻度（そのカテゴリが訓練データ全体に占める割合）
        freq = X_train[col].astype(str).value_counts(normalize=True).to_dict()

        def map_te(x, suffix=""):
            v = x[col].astype(str)
            # 未知カテゴリ（訓練データに存在しない値）は global_* で埋める
            return pd.DataFrame({
                f"{col}_te_mean{suffix}":   v.map(agg["mean"]).fillna(global_mean).astype(np.float32).values,
                f"{col}_te_median{suffix}": v.map(agg["median"]).fillna(global_median).astype(np.float32).values,
                f"{col}_te_var{suffix}":    v.map(agg["var"]).fillna(0).astype(np.float32).values,
                f"{col}_te_count{suffix}":  v.map(agg["count"]).fillna(0).astype(np.float32).values,
                f"{col}_te_freq{suffix}":   v.map(freq).fillna(0).astype(np.float32).values,
            })

        tr_te_list.append(map_te(X_train))
        val_te_list.append(map_te(X_val))
        te_te_list.append(map_te(X_test))

    X_tr_te  = pd.concat(tr_te_list,  axis=1) if tr_te_list  else pd.DataFrame(index=X_train.index)
    X_val_te = pd.concat(val_te_list, axis=1) if val_te_list else pd.DataFrame(index=X_val.index)
    X_te_te  = pd.concat(te_te_list,  axis=1) if te_te_list  else pd.DataFrame(index=X_test.index)

    return X_tr_te, X_val_te, X_te_te


def build_onehot_fold(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
    columns: list[str],
    sparse: bool = True,
) -> tuple:
    """
    One-Hot Encoding を fold 内でフィットして val/test に適用する。

    【One-Hot Encoding とは?】
    カテゴリ変数の各値を 0/1 のフラグ列に展開する手法。
    例: Sex={0, 1} → Sex_0=[1,0,...], Sex_1=[0,1,...] の 2 列に分解

    handle_unknown="ignore" にしているため、val/test に未知カテゴリが
    あっても全ての列が 0 になるだけでエラーにならない。

    TE との使い分け:
    - TE: カテゴリ数が多い場合（高カーディナリティ）に有効
    - OHE: カテゴリ数が少ない場合（低カーディナリティ）に有効
    - 線形モデル（LR）では OHE の方が効きやすい場合がある

    Returns
    -------
    X_tr_oh, X_val_oh, X_te_oh (sparse なら scipy sparse matrix)
    enc : 学習済み OneHotEncoder（必要なら特徴量名取得等に使える）
    """
    from sklearn.preprocessing import OneHotEncoder
    enc = OneHotEncoder(sparse_output=sparse, handle_unknown="ignore")
    enc.fit(X_train[columns].astype(str))
    X_tr_oh  = enc.transform(X_train[columns].astype(str))
    X_val_oh = enc.transform(X_val[columns].astype(str))
    X_te_oh  = enc.transform(X_test[columns].astype(str))
    return X_tr_oh, X_val_oh, X_te_oh, enc


def get_numeric_columns_for_lr(df: pd.DataFrame) -> list[str]:
    """
    LR（ロジスティック回帰）用の数値列リストを返す。

    LR は数値のみを入力とするため、カテゴリ列は別途 OHE や TE で
    数値化してから結合して使う。
    """
    return [c for c in FEATURE_NAMES if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]


def get_categorical_columns_for_onehot(df: pd.DataFrame) -> list[str]:
    """
    One-Hot Encoding に使う低カーディナリティ列のリストを返す。

    CATEGORICAL_LIKE（config.py で定義）に含まれ、かつ df に存在する列。
    """
    from src.config import CATEGORICAL_LIKE
    return [c for c in CATEGORICAL_LIKE if c in df.columns]
