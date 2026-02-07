# Docker環境 - 詳細ドキュメント

このディレクトリには、チーム共通のDocker環境設定が含まれています。

> **⚠️ 実行ディレクトリ**
>
> `docker-compose.yml` はこの `docker/` 内にあり、`context: ..` でプロジェクトルートを参照しています。
> **必ず `cd docker` してから** `docker compose` を実行してください。プロジェクトルートで `docker compose up` するとファイルが見つかりません。

## ファイル構成

```
docker/
├── Dockerfile           # イメージ定義（PyTorch + GPU + 日本語対応）
├── docker-compose.yml   # コンテナ起動設定
├── requirements.txt     # Python依存パッケージ
├── README_DOCKER.md     # このファイル
├── setup_check.sh       # 環境の事前確認スクリプト
└── quick_start.sh       # ワンコマンドセットアップスクリプト
```

---

## Dockerfile の設計思想

### Base Image: gcr.io/kaggle-images/python:latest

**選定理由:**
- **Kaggle公式イメージ**: Kaggle Notebook と完全に同じ環境
- **全てのライブラリがプリインストール済み**:
  - データ処理: pandas, numpy, polars
  - 可視化: matplotlib, seaborn, plotly
  - 機械学習: scikit-learn, xgboost, lightgbm (GPU版), catboost
  - ディープラーニング: PyTorch, TensorFlow (両方 GPU 対応)
  - その他: optuna, JupyterLab, RAPIDS など
- **GPU 対応**: LightGBM, XGBoost, CatBoost 全て GPU 版が含まれる
- **バージョン管理不要**: Kaggle が管理しているため、常に最新の安定版

**トレードオフ:**
- イメージサイズが大きい（20GB〜40GB）
- ダウンロードに時間がかかる（初回のみ）
- ディスク容量に余裕が必要

**代替案:**
- 軽量環境が必要な場合: `python:3.10-slim` や `pytorch/pytorch:latest` に変更

### 環境の一貫性

Kaggle公式イメージを使うことで、以下のメリットがあります:
- ローカルでの実験結果が Kaggle Notebook でそのまま再現できる
- バージョン違いによる挙動の差異がない
- GPU 関連のビルドやインストールが不要（全て済んでいる）

**参考:** [Kaggle Docker Images on GitHub](https://github.com/Kaggle/docker-python)

### 日本語対応

```dockerfile
# 日本語フォントのインストール
RUN apt-get install -y fonts-ipaexfont fonts-ipafont

# matplotlibで日本語を使えるように設定（システム全体）
RUN mkdir -p /etc/matplotlib && \
    echo "font.family : IPAexGothic" > /etc/matplotlib/matplotlibrc
```

**ポイント:** `/etc/matplotlib/matplotlibrc` に設定することで、root 以外のユーザー（kaggle）でも日本語フォントが有効になります。

これにより、以下が可能になります:

```python
import matplotlib.pyplot as plt
plt.title("日本語タイトル")  # 文字化けしない
```

### 権限管理（UID/GID）

```dockerfile
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN useradd -m -u ${USER_ID} -g ${GROUP_ID} kaggle
USER ${USER_ID}:${GROUP_ID}
```

**目的:**
- コンテナ内で作成したファイルが、ホスト側で `root` 所有にならないようにする
- チームメンバー全員が同じUID/GID（通常は1000）を使うことで、ファイル権限の問題を回避

**確認方法:**

```bash
# ホスト側
id -u  # 1000
id -g  # 1000

# コンテナ内
docker compose exec app id
# uid=1000(kaggle) gid=1000(kaggle)
```

---

## docker-compose.yml の設計思想

### Volume Mount

```yaml
volumes:
  - ..:/workspace                          # プロジェクト全体
  - ${HOME}/kaggle_data:/data              # データ置き場（ホームの kaggle_data）
  - ${HOME}/.kaggle:/home/kaggle/.kaggle:ro  # Kaggle API認証（読み取り専用）
```

**ポイント:**
- `..:/workspace`: プロジェクトルートをコンテナ内の `/workspace` にマウント
- `${HOME}/kaggle_data:/data`: 各ユーザーのホーム配下の `kaggle_data` をコンテナ内の `/data` にマウント（事前に `mkdir -p ~/kaggle_data/{datasets/raw,processed,models,outputs,working}` で作成）
- `${HOME}/.kaggle`: 各ユーザーのホームディレクトリから認証情報を読み込む（`:ro` で読み取り専用）

### GPU設定

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

**動作確認:**

```bash
docker compose exec app nvidia-smi
docker compose exec app python -c "import torch; print(torch.cuda.is_available())"
```

**SGE 環境（計算ノードで使う場合）:** ログインノードには GPU がないため、`qrsh -q tsmall -l gpu=1 -l mem_req=16g -l h_vmem=16g` で計算ノード（例: tn4）に入り、そこで `cd docker` → `docker compose up` する。手元のPCからは `ssh -L 8888:tn4:8888 ユーザー@ln1` でトンネルを張り、ブラウザで http://localhost:8888 にアクセス。詳細は README の「計算ノード（GPU付き）で JupyterLab を使う」を参照。

### JupyterLab自動起動

```yaml
command: >
  bash -c "
  jupyter lab
  --ip=0.0.0.0
  --port=8888
  --no-browser
  --allow-root
  --NotebookApp.token=''
  --NotebookApp.password=''
  "
```

**セキュリティ注意:**
- `--NotebookApp.token=''`: トークン認証を無効化（学内サーバー想定）
- **外部公開する場合は必ずトークン/パスワードを設定すること**

---

## カスタマイズ方法

### 1. CPUのみで動かしたい

`docker-compose.yml` の `deploy` ブロックをコメントアウト:

```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: all
#           capabilities: [gpu]
```

### 2. ポート番号を変更したい

`docker-compose.yml` の `ports` を変更:

```yaml
ports:
  - "8889:8888"  # ホスト側を8889に変更
```

ブラウザで `http://<サーバーIP>:8889` にアクセス。

### 3. 追加のPythonパッケージをインストールしたい

`requirements.txt` に追加して再ビルド:

```bash
echo "transformers>=4.30" >> requirements.txt
docker compose build --no-cache
docker compose up -d
```

### 4. JupyterLabではなくbashで起動したい

`docker-compose.yml` の `command` を変更:

```yaml
command: bash
```

起動後、手動でJupyterLabを起動:

```bash
docker compose exec app bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

---

## ビルド時間の短縮

### マルチステージビルド（上級者向け）

現在のDockerfileは1ステージですが、開発環境と本番環境を分けたい場合はマルチステージビルドを検討してください。

### ビルドキャッシュの活用

```bash
# キャッシュを使ってビルド（デフォルト）
docker compose build

# キャッシュを使わずビルド（requirements.txt変更時など）
docker compose build --no-cache
```

---

## トラブルシューティング

### Q1. ビルドが遅い

**原因:** PyTorchイメージが大きい（約5GB）

**解決策:**
- 初回のみ時間がかかります（10〜15分）
- 2回目以降はキャッシュが効くので高速です
- イメージを `docker save` で共有すれば、メンバーはビルド不要

### Q2. GPUが認識されない

**確認項目:**
1. ホスト側で `nvidia-smi` が動くか
2. NVIDIA Container Toolkit がインストールされているか
3. `docker-compose.yml` の `deploy` ブロックが有効か

**インストール手順（Ubuntu）:**

```bash
# NVIDIA Container Toolkit のインストール
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### Q3. コンテナ内でファイルを作成すると root 権限になる

**原因:** UID/GIDが一致していない

**解決策:**

```bash
# 自分のUID/GIDを確認
id -u && id -g

# .env ファイルに記載
cat << EOF > .env
USER_ID=$(id -u)
GROUP_ID=$(id -g)
EOF

# 再ビルド
docker compose down
docker compose build --no-cache
docker compose up -d
```

---

## イメージの共有方法

### エクスポート（管理者・任意）

共有ストレージがある場合の例です。なければ各人が `docker compose build` で構築します。

```bash
# 例: 共有ストレージに保存する場合（パスは環境に合わせて変更）
docker save kaggle-s6e2-heart:latest | gzip > /path/to/shared/kaggle-s6e2-heart.tar.gz
```

### インポート（メンバー・共有イメージがある場合）

```bash
# 例: 共有ストレージからロード（パスは環境に合わせて変更）
docker load < /path/to/shared/kaggle-s6e2-heart.tar.gz
docker images | grep kaggle-s6e2-heart
```

### 更新時の運用フロー

1. 管理者が `requirements.txt` や `Dockerfile` を更新
2. 管理者が再ビルドして `docker save` で共有
3. メンバーが `docker load` で最新イメージを取得
4. `docker compose up -d` で起動（ビルド不要）

---

## 参考リンク

- [Docker Compose GPU support](https://docs.docker.com/compose/gpu-support/)
- [PyTorch Docker Images](https://hub.docker.com/r/pytorch/pytorch)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
