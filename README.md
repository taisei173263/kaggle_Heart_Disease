# Kaggle Playground S6E2 - Heart Disease Prediction

心疾患の有無を予測する2値分類タスク。評価指標は **ROC AUC** です。

## フォルダ構成

```
kaggle-s6e2-heart/
├── .gitignore
├── README.md
├── docker/                # Docker関連（分析環境の共有用）
├── data/
│   ├── raw/               # KaggleからDLした元データ (train.csv, test.csv)
│   ├── processed/         # 前処理済みデータ (feather/parquet)
│   └── output/            # 提出用 submission.csv
├── notebooks/             # 試行錯誤用Notebook
├── src/                   # 共通コード（Notebookから import）
└── models/                # 学習済みモデル保存先
```

## セットアップ（チームメンバー向け）

### 1. リポジトリのクローン

```bash
git clone <リポジトリURL>
cd kaggle-s6e2-heart
```

### 2. データの配置

- Kaggle から `train.csv`, `test.csv` 等をダウンロード
- `data/raw/` に配置する（**raw は編集・上書きしない**）

### 3. 環境構築（Docker 推奨）

```bash
cd docker
docker compose build
docker compose up -d
docker compose exec app bash   # コンテナ内で作業
```

コンテナ内で `pip install -r docker/requirements.txt` は Dockerfile で実行済みです。

### 4. 共通コードの利用

Notebook やスクリプトからは次のように import します。

```python
from src.config import DATA_RAW_DIR
from src.preprocessing import clean_data
from src.utils import set_seed
```

## 開発のルール

- **data/raw/** は元データのみ。加工したデータは **data/processed/** に別名で保存する。
- うまくいった前処理・学習ループは `src/` に切り出し、Notebook では `import` して使う。
- モデルは `models/20260206_xgboost/` のように日付・モデル名でフォルダ分けして保存する。

## 参考

- [Kaggle - Heart Disease Prediction](https://www.kaggle.com/competitions/playground-series-s6e2)
