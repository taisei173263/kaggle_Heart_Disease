# Kaggle Playground S6E2 - Heart Disease Prediction

心疾患の有無を予測する2値分類タスク。評価指標は **ROC AUC** です。

---

## 🚀 初めての方へ

**Kaggle 初心者の方は、まず [`SETUP_SUMMARY.md`](SETUP_SUMMARY.md) をお読みください。**

このドキュメントでは、環境構築から最初の Kaggle 提出まで、ステップバイステップで解説しています。

| 対象 | 読むべきドキュメント |
|------|---------------------|
| **初めて環境構築する方** | [`SETUP_SUMMARY.md`](SETUP_SUMMARY.md) |
| **チームで運用する方** | [`TEAM_GUIDE.md`](TEAM_GUIDE.md) |
| **データを共有したい方** | [`docs/DATA_SHARING_GUIDE.md`](docs/DATA_SHARING_GUIDE.md) |
| **Git/GitHub の設定が必要な方** | [`docs/GIT_GITHUB_SETUP.md`](docs/GIT_GITHUB_SETUP.md) |
| **コンペの進め方を知りたい方** | [`docs/WORKFLOW_GUIDE.md`](docs/WORKFLOW_GUIDE.md) |

---

## 📁 フォルダ構成

```
kaggle-s6e2-heart/
├── .gitignore
├── .env.example           # 環境変数のテンプレート
├── README.md
├── TEAM_GUIDE.md          # チーム運用ガイド
├── SETUP_SUMMARY.md       # セットアップサマリー
├── docker/                # Docker関連（分析環境の共有用）
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── README_DOCKER.md
│   ├── setup_check.sh
│   └── quick_start.sh
├── docs/                  # ドキュメント
│   ├── JOB_GUIDE.md       # ジョブスクリプト使用ガイド
│   ├── LIGHTGBM_GPU.md    # LightGBM GPU 関連情報
│   └── WORKFLOW_GUIDE.md  # Kaggle コンペの進め方ガイド
├── data/
│   ├── raw/               # KaggleからDLした元データ (train.csv, test.csv)
│   ├── processed/         # 前処理済みデータ (feather/parquet)
│   └── output/            # 提出用 submission.csv
├── notebooks/             # 試行錯誤用Notebook
├── src/                   # 共通コード（Notebookから import）
├── scripts/               # スクリプト
│   ├── submit.sh          # Kaggle提出スクリプト
│   ├── submit_job.sh      # SGEジョブ投入（Docker内で実行・推奨）
│   ├── job.sh             # ジョブスクリプト（Docker外・uv run）
│   ├── job_template.sh    # ジョブスクリプト（テンプレート）
│   └── job_array.sh       # アレイジョブスクリプト
├── logs/                  # ジョブログ保存先
└── models/                # 学習済みモデル保存先
```

---

## 🚀 セットアップ（初回のみ）

> **⚠️ 実行ディレクトリについて（必読）**
>
> `docker-compose.yml` は **`docker/` ディレクトリ内** にあり、ビルドコンテキストが `context: ..`（プロジェクトルート）になっています。
>
> **正しい起動手順:** 必ず **プロジェクトルートから `cd docker` してから** `docker compose` を実行してください。
>
> ```bash
> # ✅ 正しい
> cd ~/kaggle/competitions/kaggle-s6e2-heart
> cd docker
> docker compose up -d --build
> ```
>
> ```bash
> # ❌ 間違い: プロジェクトルートでいきなり docker compose してもファイルが見つかりません
> cd ~/kaggle/competitions/kaggle-s6e2-heart
> docker compose up -d   # 動かない
> ```

### 前提条件

- **サーバー環境:** Ubuntu 20.04以降
- **Docker:** 20.10以降
- **NVIDIA Container Toolkit:** GPU利用時に必要（後述）
- **データ置き場:** ホームに `~/kaggle_data` を作成（初回に `mkdir` と `chmod` で準備）
- **Kaggle CLI（ホスト用）:** ホストで `./scripts/submit.sh` や `kaggle competitions download` を使う場合は、ホストに Kaggle CLI のインストールが必要（後述）

### 1. リポジトリのクローン

```bash
cd ~
git clone <リポジトリURL>
cd kaggle-s6e2-heart
```

### 2. Kaggle API認証の設定

**重要な変更点:** このプロジェクトでは、Kaggle API の認証を **`.env` ファイルのみ** で管理します。

- ✅ **推奨**: プロジェクト直下の `.env` に `KAGGLE_USERNAME` と `KAGGLE_KEY` を設定
- ❌ **不要**: `~/.kaggle/kaggle.json` の配置は不要（従来の方法）

**メリット:**
- プロジェクト内で認証情報が完結（`/home/taisei/kaggle/competitions` 以下のみ）
- ホストと Docker コンテナの両方で同じ設定を使用
- チーム全員が同じ手順で設定可能

#### 2-1. Kaggle APIトークンの取得

1. [Kaggle](https://www.kaggle.com/) にログイン
2. 右上のアイコン → **Account** → **API** セクション
3. **Create New API Token** をクリック
4. `kaggle.json` がダウンロードされる

#### 2-2. .env ファイルへの設定フロー

**重要:** `.env` は個人の認証情報を含むため、**絶対にGitにコミットしない**こと（`.gitignore` に追加済み）。

```bash
# ステップ1: .env.example をコピーして .env を作成
cp .env.example .env

# ステップ2: ダウンロードした kaggle.json を開いて username と key を確認
cat ~/Downloads/kaggle.json
# 出力例: {"username":"your_username","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

# ステップ3: .env ファイルを編集して KAGGLE_USERNAME と KAGGLE_KEY を設定
vim .env
# または: nano .env
```

`.env` の設定例:

```bash
# UID/GID設定（コンテナ内のファイル権限用）
USER_ID=1000
GROUP_ID=1000

# Kaggle API認証（必須）
KAGGLE_USERNAME=your_username
KAGGLE_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**設定のポイント:**
- `kaggle.json` の `username` と `key` の値を**そのまま**コピーしてください
- `key` は 32 文字の英数字です（`KGAT_` などのプレフィックスは不要）
- この設定で、ホストと Docker コンテナの両方で Kaggle API が使えます

#### 2-3. Kaggle CLI のインストール（ホストで submit.sh を使う場合）

`./scripts/submit.sh` や `kaggle competitions download` は**ホスト上**で実行されるため、ホストに Kaggle CLI が入っている必要があります。

```bash
# pip でインストール（推奨）
pip install --user kaggle

# または uv を使う場合
uv pip install kaggle

# 動作確認
kaggle --version
```

- **Docker コンテナ内**では Kaggle 公式イメージに既に Kaggle CLI が含まれているため、追加インストールは不要です。
- ホストに Python がない場合は、データのダウンロード・提出はコンテナ内で行ってください（`docker compose exec app kaggle competitions download -c playground-series-s6e2` など）。

### 3. Docker環境のビルド

#### 3-1. UID/GIDの確認

コンテナ内で作成したファイルの権限問題を避けるため、自分のUID/GIDを確認します。

```bash
id -u  # UID（例: 1000）
id -g  # GID（例: 1000）
```

#### 3-2. 環境変数の設定（オプション）

デフォルトは `1000:1000` です。異なる場合は `.env` ファイルを作成:

```bash
# プロジェクトルートで実行
# すでに .env を作成済みの場合は、USER_ID と GROUP_ID を追記
echo "USER_ID=1000" >> .env
echo "GROUP_ID=1000" >> .env
```

#### 3-3. Dockerイメージのビルド

**必ず `docker` フォルダに移動してから実行してください。**

```bash
cd docker
docker compose build --no-cache
```

**⚠️ 重要: 初回は30分〜1時間程度かかります**
- Kaggle公式イメージ（`gcr.io/kaggle-images/python`）は **20GB〜40GB** の大容量イメージです
- ダウンロードに時間がかかりますが、その分 **全てのライブラリがプリインストール済み** です
- LightGBM, XGBoost, CatBoost, PyTorch, TensorFlow など、全て GPU 対応版が含まれています

**補足:** Kaggle Notebook と完全に同じ環境が手に入るため、ローカルでの実験結果がそのまま Kaggle に反映されます。

**ビルド後の確認:**
- **イメージが 40GB 超:** Kaggle 公式環境（PyTorch / TensorFlow / GPU 版 LightGBM 等）がすべて入っている証拠です。
- **ログインノードで `could not select device driver "nvidia"`:** ログインノードに GPU がないための正常な反応です。学習は `qsub scripts/submit_job.sh src/train.py` で計算ノードに投げれば GPU が使われます（[Q0](#q0-could-not-select-device-driver-nvidia-with-capabilities-gpu) も参照）。

---

## 💻 日常の使い方

### JupyterLabの起動

**必ず `docker` フォルダに移動してから起動すること。**

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up -d
```

ブラウザで以下にアクセス:

```
http://<サーバーのIPアドレス>:8888
```

**例:** `http://192.168.1.100:8888`

**注意:**
- ポート `8888` が他の人と競合する場合は、`docker-compose.yml` の `ports` を変更してください（例: `"8889:8888"`）。
- トークン認証は無効化されています（学内サーバー想定）。外部公開する場合は `--NotebookApp.token=''` を削除してください。
- **SGE 環境でログインノードに GPU がない場合:** `could not select device driver nvidia` が出たら、下の「計算ノード（GPU付き）で JupyterLab を使う」に従って計算ノードで起動するか、[Q0](#q0-could-not-select-device-driver-nvidia-with-capabilities-gpu) のとおり `docker-compose.yml` の GPU 設定をコメントアウトして CPU のみで起動してください。

### コンテナ内でbashを使う

（`docker` フォルダで `docker compose up -d` した状態で）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose exec app bash
```

コンテナ内で:

```bash
# Pythonスクリプトの実行
python src/train.py

# Kaggle APIの動作確認
kaggle competitions list

# GPUの確認
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

### コンテナの停止

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker   # 必ず docker フォルダに移動
docker compose down
```

---

### 計算ノード（GPU付き）で JupyterLab を使う（SGE 環境）

ログインノード（`ln1` 等）では GPU が使えず `could not select device driver nvidia` が出る場合、**計算ノードに入ってから** Docker を起動します。手元のPCからは SSH トンネルで JupyterLab にアクセスします。

#### ステップ1: 計算ノードに接続（GPU を確保）

```bash
# 例: tsmall キューで GPU 1 枚・メモリ 16GB を確保
qrsh -q tsmall -l gpu=1 -l mem_req=16g -l h_vmem=16g
```

プロンプトが `tn4` 等の**計算ノード名**に変わったら成功です。`nvidia-smi` で GPU を確認できます。

#### ステップ2: 作業ディレクトリに移動して Docker を起動

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up
```

**このターミナルは閉じずにそのままにしてください。** ログの最後に `http://127.0.0.1:8888/lab?token=...` のような URL が出れば起動成功です。

**補足:** ログインノード用に GPU 設定をコメントアウトしている場合は、先に以下で GPU を有効にしてください。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
sed -i 's/^ *# *deploy:/    deploy:/' docker-compose.yml
sed -i 's/^ *# *resources:/      resources:/' docker-compose.yml
sed -i 's/^ *# *reservations:/        reservations:/' docker-compose.yml
sed -i 's/^ *# *devices:/          devices:/' docker-compose.yml
sed -i 's/^ *# *- driver: nvidia/            - driver: nvidia/' docker-compose.yml
sed -i 's/^ *# *count: all/              count: all/' docker-compose.yml
sed -i 's/^ *# *capabilities: \[gpu\]/              capabilities: [gpu]/' docker-compose.yml
```

#### ステップ3: 手元のPCから SSH トンネルを張る

**手元のPC（Mac/Windows）** で新しいターミナルを開き、以下を実行します。`tn4` はステップ1で入った計算ノード名、`ln1` 等は普段 SSH するログインノードのホスト名またはIPに合わせてください。

```bash
ssh -L 8888:tn4:8888 taisei@ln1のホスト名またはIP
```

#### ステップ4: ブラウザでアクセス

手元のブラウザで **http://localhost:8888** を開きます。JupyterLab の画面が表示されれば完了です。

**まとめ:** 計算ノードで `docker compose up` → 手元で `ssh -L 8888:計算ノード名:8888 ユーザー@ログインノード` → ブラウザで http://localhost:8888

---

## 📊 データの配置

### ローカルデータ（個人用）

プロジェクト内の `data/raw/` に配置:

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
kaggle competitions download -c playground-series-s6e2
unzip playground-series-s6e2.zip -d data/raw/
```

### データ置き場（プランB: ホームディレクトリ）

コンテナ内の `/data` は、ホストの **`~/kaggle_data`** にマウントされています。初回のみ以下を実行してください。

```bash
mkdir -p ~/kaggle_data/{datasets/raw,processed,models,outputs,working}
chmod -R 777 ~/kaggle_data
chmod o+x ~
```

データを置く例（例: 生データを raw に）:

```bash
cp ~/kaggle/competitions/kaggle-s6e2-heart/data/raw/*.csv ~/kaggle_data/datasets/raw/
```

コンテナ内では `/data` としてマウントされています:

```python
import pandas as pd

# /data（~/kaggle_data）から読み込み
df = pd.read_csv('/data/datasets/raw/train.csv')
```

---

## 🎯 開発のルール

### ディレクトリの使い分け

- **`data/raw/`**: Kaggleからダウンロードした元データ。**絶対に編集・上書きしない**。
- **`data/processed/`**: 前処理済みデータ（feather/parquet形式推奨）。
- **`data/output/`**: 提出用 `submission.csv`。
- **`notebooks/`**: 試行錯誤用Notebook。ファイル名は `01_eda_v1.ipynb` のように番号+内容で命名。
- **`src/`**: 共通コード。うまくいった前処理・学習ループは関数化してここに配置。
- **`models/`**: 学習済みモデル。`models/20260206_xgboost/` のように日付・モデル名でフォルダ分け。

### Notebookからの共通コード利用

```python
# Notebookの先頭で
import sys
sys.path.append('/workspace')  # コンテナ内のパス

from src.config import DATA_RAW_DIR, DATA_PROCESSED_DIR
from src.preprocessing import clean_data
from src.utils import set_seed

set_seed(42)
```

### Gitへのコミット

```bash
# 変更をステージング
git add src/preprocessing.py notebooks/02_feature_engineering.ipynb

# コミット
git commit -m "Add feature engineering notebook"

# プッシュ
git push origin main
```

**注意:** `.gitignore` により、以下は自動的に除外されます:
- `data/` 内のCSV・モデルファイル
- `.env`（認証情報を含むため）

---

## 📤 Kaggleへの提出

### 方法1: スクリプトから提出

ホストで `./scripts/submit.sh` を実行します。**ホストに Kaggle CLI が入っている必要があります**（未インストールの場合は「2-3. Kaggle CLI のインストール」を参照）。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
./scripts/submit.sh data/output/submission.csv "XGBoost v1 with feature engineering"
```

### 方法2: Kaggle CLIから直接提出

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose exec app bash

# コンテナ内で
kaggle competitions submit -c playground-series-s6e2 \
  -f data/output/submission.csv \
  -m "LightGBM v2"
```

---

## 🖥️ ジョブスクリプトの使い方（SGE環境）

サーバーでSun Grid Engine（SGE）を使っている場合、ジョブスクリプトで学習を投入できます。

### スクリプトの種類

| スクリプト | 実行環境 | 用途 |
|-----------|----------|------|
| **`submit_job.sh`** | Docker コンテナ内 | **推奨。** チーム共通の Docker 環境で実行 |
| `job.sh` 等 | ホスト直接（uv run） | uv がホストにある場合のみ |

**初心者には `submit_job.sh` を推奨します。** Docker 環境を使うことで、依存関係の問題を防げます。

### 基本的な使い方

**初回のみ: 環境チェック（疎通確認）**

```bash
# データ・GPU・書き込みの疎通を確認
mkdir -p logs
qsub scripts/submit_job.sh src/check_env.py

# ジョブ終了後、結果を確認（✅ が3つ出ればOK）
tail -20 logs/kaggle-run.o<ジョブID>
```

**ベースライン学習（初回提出用）**

Docker イメージのビルドが終わったら、GPU のある計算ノードにジョブを投げるだけです。

```bash
# プロジェクトルートで実行（計算ノードに注文を出す）
mkdir -p logs
qsub scripts/submit_job.sh src/train.py
```

**動作確認の流れ:**

1. **状況確認:** `qstat` で `r` (Running) になっていれば、計算ノードで Docker が立ち上がり学習が走っています。
2. **ログ確認:** 終了後、`logs/kaggle-run.o<ジョブID>` を確認。`[LightGBM] [Info] This is the GPU trainer!!` が出ていれば GPU 学習の成功です。

```bash
qstat
cat logs/kaggle-run.o*   # または tail -100 logs/kaggle-run.o<ジョブID>
```

**提出まで:**

```bash
# 提出ファイルをプロジェクトの data/output にコピーして提出
cp ~/kaggle_data/outputs/submission_v1.csv data/output/
./scripts/submit.sh data/output/submission_v1.csv "LightGBM baseline v1"
```

**その他の学習ジョブ**

```bash
# 計算ノードの Docker 内で任意のスクリプトを実行
qsub scripts/submit_job.sh src/train.py

# または従来のジョブ投入（ホストで uv run）
qsub scripts/job.sh

# ジョブの状態確認
qstat

# ログをリアルタイム表示
tail -f logs/kaggle-run.o12345
```

### カスタムジョブの作成

```bash
# テンプレートをコピー
cp scripts/job_template.sh scripts/my_experiment.sh

# 編集
vim scripts/my_experiment.sh

# 投入
qsub scripts/my_experiment.sh
```

### アレイジョブ（複数パラメータの並列実行）

```bash
# 5つのパラメータ設定を並列実行
qsub scripts/job_array.sh
```

**詳細:** `docs/JOB_GUIDE.md` を参照

**LightGBM について:** Kaggle公式イメージの LightGBM は CPU 版のため、GPU で GBDT を使いたい場合は XGBoost や CatBoost を検討してください。詳細は `docs/LIGHTGBM_GPU.md` を参照。

**Kaggle コンペの進め方:** 環境構築後の開発フロー（EDA → 特徴量エンジニアリング → モデル改善 → アンサンブル）については `docs/WORKFLOW_GUIDE.md` を参照してください。

---

## 🔧 トラブルシューティング

### Q0. `could not select device driver "nvidia" with capabilities: [[gpu]]`

**原因:** ログインノード等、GPU や NVIDIA Container Toolkit がない環境で `docker compose up` している。

**解決策（2通り）:**

1. **GPU を使う（推奨）:** [計算ノード（GPU付き）で JupyterLab を使う](#計算ノードgpu付きで-jupyterlab-を使うsge-環境) に従い、`qrsh` で計算ノード（例: tn4）に入ってから `cd docker` → `docker compose up` し、手元のPCで `ssh -L 8888:tn4:8888 ユーザー@ln1` でトンネルを張り、ブラウザで http://localhost:8888 にアクセスする。

2. **CPU のみで使う:** `docker/docker-compose.yml` の `deploy:` 〜 `capabilities: [gpu]` のブロックをコメントアウト（各行の先頭に `#` を付ける）すると、GPU なしで起動します。

### Q1. Kaggle API 認証エラー

**エラー例:**

```
Error: Missing username/key in configuration.
```

**解決策:**

```bash
# .env ファイルが存在するか確認
ls -la .env

# 存在しない場合は .env.example からコピー
cp .env.example .env

# KAGGLE_USERNAME と KAGGLE_KEY を設定（「2. Kaggle API認証の設定」を参照）
vim .env
```

### Q2. コンテナ内で作成したファイルが root 権限になる

**解決策:**

```bash
# 自分のUID/GIDを確認
id -u && id -g

# docker-compose.yml の USER_ID/GROUP_ID を修正
# または .env ファイルに記載
echo "USER_ID=$(id -u)" > .env
echo "GROUP_ID=$(id -g)" >> .env

# 再ビルド
cd docker
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Q3. GPU が認識されない

**解決策:**

```bash
# ホスト側でGPUが見えるか確認
nvidia-smi

# NVIDIA Container Toolkit がインストールされているか確認
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# インストールされていない場合
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

### Q4. ポート 8888 が使用中

**解決策:**

`docker-compose.yml` の `ports` を変更:

```yaml
ports:
  - "8889:8888"  # ホスト側のポートを8889に変更
```

ブラウザで `http://<サーバーIP>:8889` にアクセス。

---

## 🐳 Docker イメージの共有（チーム内配布）

Docker Hubを使わず、サーバー内でイメージを共有する方法。

### イメージのエクスポート（管理者が実行・任意）

共有ストレージがある場合の例です。なければ各人がローカルで `docker compose build` 即可。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose build

# 例: 共有ストレージに保存する場合（パスは環境に合わせて変更）
# docker save kaggle-s6e2-heart:latest | gzip > /path/to/shared/kaggle-s6e2-heart.tar.gz
```

### イメージのインポート（メンバーが実行・共有イメージがある場合）

```bash
# 例: 共有ストレージからイメージをロード（パスは環境に合わせて変更）
# docker load < /path/to/shared/kaggle-s6e2-heart.tar.gz

# 確認
docker images | grep kaggle-s6e2-heart
```

通常は `cd docker` のうえ `docker compose up -d --build` でローカルビルドして起動即可。

---

## 📚 参考リンク

- [Kaggle - Playground Series S6E2](https://www.kaggle.com/competitions/playground-series-s6e2)
- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 🤝 困ったときは

- **Slack/Discord:** チーム内のチャンネルで質問
- **Issue:** GitHubのIssueに問題を報告
- **直接相談:** ゼミの先輩・メンター
