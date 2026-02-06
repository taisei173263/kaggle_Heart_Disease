# セットアップサマリー

このドキュメントは、構築したDocker環境の概要と、各ファイルの役割を説明します。

---

## 📋 作成したファイル一覧

### 1. Docker環境

| ファイル | 役割 |
|---------|------|
| `docker/Dockerfile` | PyTorch + CUDA + 日本語対応のイメージ定義 |
| `docker/docker-compose.yml` | GPU設定・ボリュームマウント・JupyterLab起動設定 |
| `docker/requirements.txt` | Python依存パッケージ一覧 |

### 2. ドキュメント

| ファイル | 対象者 | 内容 |
|---------|--------|------|
| `README.md` | 全メンバー | セットアップ手順・日常の使い方 |
| `TEAM_GUIDE.md` | 管理者・リーダー | 運用フロー・トラブルシューティング |
| `docker/README_DOCKER.md` | 技術担当者 | Dockerの設計思想・カスタマイズ方法 |
| `SETUP_SUMMARY.md` | 全員 | このファイル（概要） |

### 3. ユーティリティスクリプト

| ファイル | 用途 |
|---------|------|
| `docker/setup_check.sh` | 環境の事前確認（Docker・GPU・kaggle.json等） |
| `docker/quick_start.sh` | ワンコマンドセットアップ |
| `scripts/submit.sh` | Kaggleへの提出 |
| `scripts/submit_job.sh` | SGEジョブ投入（Docker内で実行・推奨） |
| `scripts/job.sh` | シンプルなジョブスクリプト（Docker外・uv run） |
| `scripts/job_template.sh` | カスタマイズ用テンプレート |
| `scripts/job_array.sh` | アレイジョブ（複数パラメータ並列実行） |

### 4. 設定ファイル

| ファイル | 役割 |
|---------|------|
| `.env.example` | 環境変数のテンプレート |
| `.env` | 実際の環境変数（Git管理外） |
| `.gitignore` | Git除外設定 |

---

## 🚀 クイックスタート（3ステップ）

### 新規メンバーの場合

```bash
# 1. リポジトリをクローン
git clone <リポジトリURL>
cd kaggle-s6e2-heart

# 2. クイックスタートスクリプトを実行
./docker/quick_start.sh

# 3. ブラウザでアクセス
# http://<サーバーIP>:8888
```

**所要時間:** 5〜10分（共有イメージを使う場合）

**注意:** `docker compose` は **必ず `docker/` フォルダに移動してから** 実行すること。プロジェクトルートで実行すると動きません（README.md の「実行ディレクトリについて」を参照）。

---

## 🎯 主要な機能

### 1. GPU対応

- **Base Image:** `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime`
- **GPU設定:** `docker-compose.yml` の `deploy` セクション
- **確認方法:**
  ```bash
  docker compose exec app nvidia-smi
  docker compose exec app python -c "import torch; print(torch.cuda.is_available())"
  ```

### 2. 日本語対応

- **フォント:** IPAexゴシック・IPA明朝
- **matplotlib設定:** 自動で日本語フォントを使用
- **動作確認:**
  ```python
  import matplotlib.pyplot as plt
  plt.title("日本語タイトル")  # 文字化けしない
  ```

### 3. 権限管理

- **UID/GID:** ホストユーザーと一致（デフォルト: 1000:1000）
- **設定方法:** `.env` ファイルに `USER_ID` / `GROUP_ID` を記載
- **効果:** コンテナ内で作成したファイルが root 権限にならない

### 4. 共有ストレージ

- **ホスト:** `/data1/share/kaggle-zemi`
- **コンテナ内:** `/data`
- **用途:** チーム全体でデータ・モデル・イメージを共有

### 5. Kaggle API認証

- **ホスト:** `~/.kaggle/kaggle.json`
- **コンテナ内:** `/home/kaggle/.kaggle/kaggle.json`
- **マウント:** 読み取り専用（`:ro`）
- **セキュリティ:** イメージには含めない（Volumeマウントのみ）

### 6. JupyterLab自動起動

- **ポート:** 8888（変更可能）
- **認証:** 無効化（学内サーバー想定）
- **カスタマイズ:** `docker-compose.yml` の `command` セクション

---

## 📊 ディレクトリ構成

```
kaggle-s6e2-heart/
├── README.md                    # メンバー向けセットアップ手順
├── TEAM_GUIDE.md                # 管理者向け運用ガイド
├── SETUP_SUMMARY.md             # このファイル
├── .env.example                 # 環境変数テンプレート
├── .env                         # 実際の環境変数（Git管理外）
├── .gitignore                   # Git除外設定
│
├── docker/                      # Docker環境
│   ├── Dockerfile               # イメージ定義
│   ├── docker-compose.yml       # コンテナ起動設定
│   ├── requirements.txt         # Python依存パッケージ
│   ├── README_DOCKER.md         # Docker詳細ドキュメント
│   ├── setup_check.sh           # 環境確認スクリプト
│   └── quick_start.sh           # クイックスタートスクリプト
│
├── data/                        # データ（Git管理外）
│   ├── raw/                     # 元データ（編集禁止）
│   ├── processed/               # 前処理済みデータ
│   └── output/                  # 提出用CSV
│
├── notebooks/                   # Jupyter Notebook
│   ├── 00_eda_initial.ipynb
│   └── 01_preprocessing_v1.ipynb
│
├── src/                         # 共通コード
│   ├── __init__.py
│   ├── config.py
│   ├── preprocessing.py
│   ├── train.py
│   └── utils.py
│
├── scripts/                     # ユーティリティスクリプト
│   ├── submit.sh                # Kaggle提出スクリプト
│   ├── submit_job.sh            # SGEジョブ投入（Docker内で実行）
│   ├── job.sh                   # シンプルなジョブスクリプト
│   ├── job_template.sh          # カスタマイズ用テンプレート
│   └── job_array.sh             # アレイジョブ
│
└── models/                      # 学習済みモデル（Git管理外）
```

---

## 🔧 カスタマイズポイント

### 1. GPU を使わない場合

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

### 2. ポート番号を変更する場合

`docker-compose.yml` の `ports` を変更:

```yaml
ports:
  - "8889:8888"  # ホスト側を8889に変更
```

### 3. 追加のPythonパッケージをインストールする場合

`requirements.txt` に追加して再ビルド:

```bash
echo "transformers>=4.30" >> docker/requirements.txt
cd docker
docker compose build --no-cache
docker compose up -d
```

### 4. JupyterLabではなくbashで起動する場合

`docker-compose.yml` の `command` を変更:

```yaml
command: bash
```

---

## 📚 ドキュメントの読み方

### 初心者の場合

1. **README.md** を読む（セットアップ手順）
2. **docker/quick_start.sh** を実行
3. 困ったら **TEAM_GUIDE.md** の「よくある問題」を参照

### 管理者・リーダーの場合

1. **TEAM_GUIDE.md** を読む（運用フロー）
2. **docker/README_DOCKER.md** を読む（技術詳細）
3. メンバーに **README.md** を共有

### 技術担当者の場合

1. **docker/README_DOCKER.md** を読む（設計思想）
2. **Dockerfile** と **docker-compose.yml** を確認
3. カスタマイズが必要な場合は上記ファイルを編集

---

## 🎓 学習リソース

### Docker初心者向け

- [Docker公式ドキュメント（日本語）](https://docs.docker.jp/)
- [Docker Compose入門](https://docs.docker.com/compose/gettingstarted/)

### Kaggle初心者向け

- [Kaggle Learn](https://www.kaggle.com/learn)
- [Kaggle API Documentation](https://github.com/Kaggle/kaggle-api)

### GPU・CUDA関連

- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [PyTorch Docker Images](https://hub.docker.com/r/pytorch/pytorch)

---

## 🤝 サポート

### 質問・問題報告

- **Slack:** `#kaggle-support` チャンネル
- **GitHub Issues:** 技術的な問題・バグ報告
- **直接相談:** ゼミの先輩・メンター

### 定期ミーティング

- **週次ミーティング:** 毎週金曜 17:00〜
  - 進捗共有
  - スコア報告
  - 次週の方針決定

---

## ✅ チェックリスト

### 初回セットアップ時

- [ ] `./docker/setup_check.sh` を実行
- [ ] `~/.kaggle/kaggle.json` を配置
- [ ] `chmod 600 ~/.kaggle/kaggle.json` を実行
- [ ] `.env` ファイルを作成（UID/GIDが1000以外の場合）
- [ ] `./docker/quick_start.sh` を実行
- [ ] ブラウザで JupyterLab にアクセス
- [ ] GPU動作確認（`nvidia-smi`）
- [ ] Kaggle API動作確認（`kaggle competitions list`）

### 日常の開発時

- [ ] `cd docker && docker compose up -d` でコンテナ起動
- [ ] JupyterLab または bash で作業
- [ ] 共通コードは `src/` に配置
- [ ] Git で変更をコミット・プッシュ
- [ ] 学習ジョブは `qsub scripts/submit_job.sh src/train.py` で投入
- [ ] 提出は Docker 内で `kaggle competitions submit` または `./scripts/submit.sh` を使用
- [ ] 作業終了後は `cd docker && docker compose down`

---

## 🏆 成功のポイント

1. **ドキュメントを読む:** README.md と TEAM_GUIDE.md を熟読
2. **環境を統一:** 全員が同じDockerイメージを使う
3. **コードを共有:** うまくいった処理は `src/` に切り出す
4. **スコアを記録:** Google Spreadsheet等で管理
5. **コミュニケーション:** Slackで積極的に質問・共有

---

## 📞 連絡先

- **プロジェクトリーダー:** [名前] (@slack_id)
- **技術担当:** [名前] (@slack_id)
- **Slackチャンネル:** `#kaggle-s6e2-heart`

---

**Happy Kaggling! 🎉**
