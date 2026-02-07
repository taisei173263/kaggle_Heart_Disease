# Kaggle コンペの進め方ガイド

このドキュメントでは、環境構築後の **Kaggle コンペの進め方** と **ジョブ投入のベストプラクティス** を解説します。

---

## 📊 Kaggle コンペの基本フロー

```
1. EDA（探索的データ分析）
   ↓
2. ベースライン作成
   ↓
3. 特徴量エンジニアリング
   ↓
4. モデル改善・チューニング
   ↓
5. アンサンブル
   ↓
6. 最終提出
```

---

## 🔍 Phase 1: EDA（探索的データ分析）

### 目的

- データの全体像を把握する
- 欠損値・外れ値を確認する
- 特徴量とターゲットの関係を理解する

### やり方

```bash
# JupyterLab を起動（計算ノードで）
qrsh -q tsmall -l gpu=1 -l mem_req=16g -l h_vmem=16g
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up
```

```python
# notebooks/00_eda_initial.ipynb で
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# データ読み込み
train = pd.read_csv('/data/datasets/raw/train.csv')

# 基本情報
print(train.shape)
print(train.info())
print(train.describe())

# ターゲット分布
train['Heart Disease'].value_counts().plot(kind='bar')

# 相関行列
sns.heatmap(train.corr(), annot=True, cmap='coolwarm')
```

### チェックポイント

- [ ] データサイズ（行数・列数）を確認
- [ ] 各列のデータ型を確認
- [ ] 欠損値の有無を確認
- [ ] ターゲット変数の分布を確認（不均衡かどうか）
- [ ] 数値変数の分布を確認
- [ ] カテゴリ変数のユニーク数を確認

---

## 🎯 Phase 2: ベースライン作成

### 目的

- 最小限の前処理で動くモデルを作る
- 提出までの一連の流れを確認する
- 改善の基準点を作る

### やり方

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# ベースライン学習を実行
qsub scripts/submit_job.sh src/train.py

# ログを確認
cat logs/kaggle-run.o*

# 提出
cp ~/kaggle_data/outputs/submission_v1.csv data/output/
./scripts/submit.sh data/output/submission_v1.csv "LightGBM baseline v1"
```

### チェックポイント

- [ ] CV スコアを記録（例: AUC 0.9552）
- [ ] Public LB スコアを記録
- [ ] CV と LB の乖離を確認（大きな乖離は過学習の兆候）

---

## 🛠️ Phase 3: 特徴量エンジニアリング

### 目的

- モデルの予測精度を向上させる特徴量を作成
- ドメイン知識を活用

### よく使う手法

#### 1. 数値変数の変換

```python
# 対数変換（歪んだ分布を正規化）
df['log_age'] = np.log1p(df['age'])

# 二乗・平方根
df['age_squared'] = df['age'] ** 2
df['age_sqrt'] = np.sqrt(df['age'])

# ビニング（連続値をカテゴリ化）
df['age_bin'] = pd.cut(df['age'], bins=[0, 30, 50, 70, 100], labels=['young', 'middle', 'senior', 'elderly'])
```

#### 2. 交互作用特徴量

```python
# 2つの特徴量の積
df['age_x_cholesterol'] = df['age'] * df['cholesterol']

# 比率
df['bp_ratio'] = df['systolic_bp'] / (df['diastolic_bp'] + 1)
```

#### 3. 集約特徴量

```python
# グループごとの統計量
df['mean_age_by_sex'] = df.groupby('sex')['age'].transform('mean')
df['age_diff_from_mean'] = df['age'] - df['mean_age_by_sex']
```

#### 4. カテゴリ変数のエンコーディング

```python
# Label Encoding
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['sex_encoded'] = le.fit_transform(df['sex'])

# Target Encoding（CV内で行うこと！リーク注意）
from sklearn.model_selection import KFold
# ... 実装は省略
```

### 特徴量を追加したら

```bash
# src/preprocessing.py に関数を追加
# src/train.py で呼び出し
# ジョブを投入して検証
qsub -N feat-v2 scripts/submit_job.sh src/train.py
```

---

## 📈 Phase 4: モデル改善・チューニング

### 1. ハイパーパラメータチューニング（Optuna）

```python
import optuna

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'num_leaves': trial.suggest_int('num_leaves', 20, 150),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
    }
    
    # CV で評価
    cv_score = cross_validate(params)
    return cv_score

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)

print(f"Best params: {study.best_params}")
print(f"Best score: {study.best_value}")
```

### 2. 他のモデルを試す

| モデル | 特徴 | GPU対応 |
|--------|------|---------|
| LightGBM | 高速、メモリ効率が良い | ❌（CPU版） |
| XGBoost | 精度が高い、GPU対応 | ✅ |
| CatBoost | カテゴリ変数に強い、GPU対応 | ✅ |
| Neural Network | 大規模データに強い | ✅ |

```python
# XGBoost（GPU版）
import xgboost as xgb

params = {
    'tree_method': 'gpu_hist',  # GPU を使用
    'gpu_id': 0,
    'objective': 'binary:logistic',
    'eval_metric': 'auc',
}

# CatBoost（GPU版）
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    task_type='GPU',
    devices='0',
    iterations=1000,
    learning_rate=0.05,
)
```

### 3. Cross Validation の工夫

```python
# Stratified K-Fold（デフォルト）
from sklearn.model_selection import StratifiedKFold
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Group K-Fold（グループ単位で分割）
from sklearn.model_selection import GroupKFold
gkf = GroupKFold(n_splits=5)

# Time Series Split（時系列データ）
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
```

---

## 🎭 Phase 5: アンサンブル

### 1. 単純平均

```python
# 複数モデルの予測を平均
pred_lgb = model_lgb.predict_proba(X_test)[:, 1]
pred_xgb = model_xgb.predict_proba(X_test)[:, 1]
pred_cat = model_cat.predict_proba(X_test)[:, 1]

final_pred = (pred_lgb + pred_xgb + pred_cat) / 3
```

### 2. 重み付き平均

```python
# CV スコアに基づいて重み付け
weights = [0.4, 0.35, 0.25]  # LGB, XGB, CAT
final_pred = weights[0] * pred_lgb + weights[1] * pred_xgb + weights[2] * pred_cat
```

### 3. Stacking

```python
from sklearn.ensemble import StackingClassifier

estimators = [
    ('lgb', lgb_model),
    ('xgb', xgb_model),
    ('cat', cat_model),
]

stacking = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(),
    cv=5,
)
```

---

## 🖥️ ジョブ投入のベストプラクティス

### 基本的なジョブ投入

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# 学習ジョブを投入
qsub scripts/submit_job.sh src/train.py

# ジョブ名を付けて投入（ログの識別に便利）
qsub -N lgb-v2 scripts/submit_job.sh src/train.py

# 引数を渡す
qsub scripts/submit_job.sh src/train.py --model xgboost --n_estimators 1000
```

### ジョブの監視

```bash
# ジョブの状態確認
qstat

# 詳細情報
qstat -j <ジョブID>

# リアルタイムログ監視
tail -f logs/kaggle-run.o<ジョブID>

# ジョブの削除
qdel <ジョブID>
```

### 複数実験を並列実行

```bash
# 方法1: 複数の qsub を投入
qsub -N lgb-lr01 scripts/submit_job.sh src/train.py --learning_rate 0.1
qsub -N lgb-lr005 scripts/submit_job.sh src/train.py --learning_rate 0.05
qsub -N lgb-lr001 scripts/submit_job.sh src/train.py --learning_rate 0.01

# 方法2: アレイジョブを使用
qsub scripts/job_array.sh
```

### リソースの調整

```bash
# メモリを増やす
qsub -l mem_req=32g -l h_vmem=32g scripts/submit_job.sh src/train.py

# GPU を 2 枚使う
qsub -l gpu=2 scripts/submit_job.sh src/train.py

# 別のキューを使う
qsub -q tlarge scripts/submit_job.sh src/train.py
```

### ログの整理

```bash
# ログディレクトリの確認
ls -la logs/

# 古いログを削除
rm logs/kaggle-run.o*
rm logs/kaggle-run.e*

# 特定のジョブのログを確認
cat logs/kaggle-run.o199138
```

---

## 📝 実験管理のコツ

### 1. 実験ログを記録する

| 日付 | 実験名 | 変更内容 | CV Score | LB Score | メモ |
|------|--------|----------|----------|----------|------|
| 2/6 | baseline | LightGBM 数値のみ | 0.9552 | 0.9548 | 初回提出 |
| 2/7 | feat-v1 | 交互作用特徴量追加 | 0.9580 | - | +0.0028 |
| 2/8 | xgb-v1 | XGBoost に変更 | 0.9575 | - | LGBより少し低い |

### 2. コードをバージョン管理する

```bash
# 実験ごとにコミット
git add src/train.py
git commit -m "Add interaction features, CV=0.9580"
git push origin main
```

### 3. モデルを保存する

```python
# モデル保存
model.booster_.save_model(f'/data/models/lgbm_v2_fold{fold}.txt')

# 予測結果も保存
np.save('/data/outputs/oof_preds_v2.npy', oof_preds)
np.save('/data/outputs/test_preds_v2.npy', test_preds)
```

---

## 🚀 スコアを上げるためのヒント

### 1. データをよく見る

- EDA に時間をかける
- 外れ値・異常値を確認
- 特徴量とターゲットの関係を可視化

### 2. 検証を信じる

- CV スコアと LB スコアの相関を確認
- 過学習に注意（CV >> LB は危険信号）
- 安定した CV 設計を心がける

### 3. シンプルから始める

- 最初は単純なモデルで
- 徐々に複雑にしていく
- 改善が見られなくなったら次のアプローチへ

### 4. Discussion・Notebook を読む

- Kaggle の Discussion で情報収集
- 公開 Notebook からアイデアを得る
- ただし、そのまま使うのではなく理解して応用

### 5. チームで協力

- 週次ミーティングで進捗共有
- うまくいった手法を共有
- 異なるアプローチを試す

---

## 📚 参考リンク

- [Kaggle Learn](https://www.kaggle.com/learn) - 無料のチュートリアル
- [Kaggle Courses](https://www.kaggle.com/learn) - 機械学習コース
- [Feature Engineering Book](https://www.oreilly.com/library/view/feature-engineering-for/9781491953235/) - 特徴量エンジニアリングの書籍
- [Optuna Documentation](https://optuna.readthedocs.io/) - ハイパーパラメータチューニング

---

**Good luck with your Kaggle journey! 🏆**
