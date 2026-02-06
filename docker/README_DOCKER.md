# Docker環境 - 詳細ドキュメント

このディレクトリには、チーム共通のDocker環境設定が含まれています。

## ファイル構成

```
docker/
├── Dockerfile           # イメージ定義（PyTorch + GPU + 日本語対応）
├── docker-compose.yml   # コンテナ起動設定
├── requirements.txt     # Python依存パッケージ
└── README_DOCKER.md     # このファイル
```

---

## Dockerfile の設計思想

### Base Image: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

**選定理由:**
- PyTorchとCUDAが事前インストール済み（初心者でもGPUをすぐ使える）
- 公式イメージなので安定性が高い
- runtime版（開発ツール不要）で軽量

**代替案:**
- CPU環境のみ: `python:3.10-slim` に変更（Dockerfileの1行目を書き換え）
- TensorFlow環境: `tensorflow/tensorflow:2.14.0-gpu`

### 日本語対応

```dockerfile
# 日本語フォントのインストール
RUN apt-get install -y fonts-ipaexfont fonts-ipafont

# matplotlibで日本語を使えるように設定
RUN echo "font.family : IPAexGothic" > /root/.config/matplotlib/matplotlibrc
```

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
  - /data1/share/kaggle-zemi:/data         # 共有ストレージ
  - ${HOME}/.kaggle:/home/kaggle/.kaggle:ro  # Kaggle API認証（読み取り専用）
```

**ポイント:**
- `..:/workspace`: プロジェクトルートをコンテナ内の `/workspace` にマウント
- `/data1/share/kaggle-zemi:/data`: サーバーの共有領域をコンテナ内の `/data` にマウント
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

### エクスポート（管理者）

```bash
docker save kaggle-s6e2-heart:latest | gzip > /data1/share/kaggle-zemi/kaggle-s6e2-heart.tar.gz
```

### インポート（メンバー）

```bash
docker load < /data1/share/kaggle-zemi/kaggle-s6e2-heart.tar.gz
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
