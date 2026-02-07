# Kaggle Playground S6E2 - Heart Disease Prediction

心疾患の有無を予測する2値分類タスク。評価指標は **ROC AUC** です。

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
│   └── JOB_GUIDE.md       # ジョブスクリプト使用ガイド
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

### 1. リポジトリのクローン

```bash
cd ~
git clone <リポジトリURL>
cd kaggle-s6e2-heart
```

### 2. Kaggle API認証の設定

Kaggle API の認証方法は **2種類** あります。どちらか一方を設定すれば OK です。

| 方法 | 用途 | 設定場所 |
|------|------|----------|
| **kaggle.json** | Docker コンテナ内で使用（推奨） | `~/.kaggle/kaggle.json` |
| **KAGGLE_API_TOKEN** | ホストで `scripts/submit.sh` を使う場合 | `.env` ファイル |

#### 2-1. Kaggle APIトークンの取得

1. [Kaggle](https://www.kaggle.com/) にログイン
2. 右上のアイコン → **Account** → **API** セクション
3. **Create New API Token** をクリック
4. `kaggle.json` がダウンロードされる

#### 2-2. kaggle.json の配置（Docker コンテナ用・推奨）

**重要:** `kaggle.json` は個人の認証情報なので、**絶対にGitにコミットしない**こと。

```bash
# ホームディレクトリに .kaggle フォルダを作成
mkdir -p ~/.kaggle

# ダウンロードした kaggle.json を移動
mv ~/Downloads/kaggle.json ~/.kaggle/

# パーミッション設定（重要: 自分だけが読み書きできるようにする）
chmod 600 ~/.kaggle/kaggle.json
```

確認:

```bash
ls -la ~/.kaggle/
# -rw------- 1 your_user your_group 68 Feb  6 12:00 kaggle.json
```

**補足:** `docker-compose.yml` が `~/.kaggle` をコンテナ内にマウントするため、コンテナ内で `kaggle` コマンドが使えます。

#### 2-3. KAGGLE_API_TOKEN の設定（ホストで submit.sh を使う場合）

ホスト上で `scripts/submit.sh` を使う場合は、`.env` ファイルにトークンを設定します。

```bash
# kaggle.json を開いてトークンを確認
cat ~/.kaggle/kaggle.json
# {"username":"your_username","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

# .env ファイルに設定（key の値を KGAT_ 形式に変換）
# 注: 新しい形式は KGAT_ プレフィックス付き
echo "KAGGLE_API_TOKEN=KGAT_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >> .env
```

**注意:** `kaggle.json` と `KAGGLE_API_TOKEN` は別物です。`kaggle.json` の `key` をそのまま使う場合は `KGAT_` プレフィックスを付けてください。

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
cat << 'EOF' > .env
USER_ID=1000
GROUP_ID=1000
KAGGLE_API_TOKEN=KGAT_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF
```

#### 3-3. Dockerイメージのビルド

**必ず `docker` フォルダに移動してから実行してください。**

```bash
cd docker
docker compose build
```

**初回は10〜15分程度かかります**（PyTorchイメージのダウンロード + ライブラリインストール）。

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
- `.env`
- `kaggle.json`

---

## 📤 Kaggleへの提出

### 方法1: スクリプトから提出

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

**学習ジョブの投入**

```bash
# 計算ノードの Docker 内で 1 回だけコマンド実行（推奨・PC を閉じても継続）
qsub scripts/submit_job.sh src/train.py --epochs 10

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

---

## 🔧 トラブルシューティング

### Q0. `could not select device driver "nvidia" with capabilities: [[gpu]]`

**原因:** ログインノード等、GPU や NVIDIA Container Toolkit がない環境で `docker compose up` している。

**解決策（2通り）:**

1. **GPU を使う（推奨）:** [計算ノード（GPU付き）で JupyterLab を使う](#計算ノードgpu付きで-jupyterlab-を使うsge-環境) に従い、`qrsh` で計算ノード（例: tn4）に入ってから `cd docker` → `docker compose up` し、手元のPCで `ssh -L 8888:tn4:8888 ユーザー@ln1` でトンネルを張り、ブラウザで http://localhost:8888 にアクセスする。

2. **CPU のみで使う:** `docker/docker-compose.yml` の `deploy:` 〜 `capabilities: [gpu]` のブロックをコメントアウト（各行の先頭に `#` を付ける）すると、GPU なしで起動します。

### Q1. `kaggle.json` が見つからないエラー

**エラー例:**

```
OSError: Could not find kaggle.json
```

**解決策:**

```bash
# ホスト側で kaggle.json が存在するか確認
ls -la ~/.kaggle/kaggle.json

# 存在しない場合は「2. Kaggle API認証の設定」を再実行
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
