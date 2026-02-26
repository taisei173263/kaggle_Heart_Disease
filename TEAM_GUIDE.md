# チーム運用ガイド

このドキュメントは、チームリーダー・管理者向けの運用ガイドです。

---

## 🎯 運用フロー

### 1. 初回セットアップ（管理者）

#### 1-1. Docker環境の構築

**必ず `docker` フォルダに移動してから実行すること。**

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose build
```

**所要時間:** 10〜15分（PyTorchイメージのダウンロード + ライブラリインストール）

#### 1-2. イメージの共有ストレージへの保存（オプション）

共有ストレージがある場合の例です。なければ各人が `docker compose build` で構築します。

```bash
# イメージをtar.gzに保存（パスは環境に合わせて変更）
docker save kaggle-s6e2-heart:latest | gzip > /path/to/shared/kaggle-s6e2-heart.tar.gz

# サイズ確認（Kaggle公式イメージは約15〜20GB圧縮後）
ls -lh /path/to/shared/kaggle-s6e2-heart.tar.gz
```

#### 1-3. READMEの共有

チームメンバーに以下を共有:
- `README.md`（セットアップ手順）
- Slackやメールで「Docker環境が準備できました」と通知

### 2. メンバーのセットアップ（各自）

#### 2-1. リポジトリのクローン

```bash
cd ~
git clone <リポジトリURL>
cd kaggle-s6e2-heart
```

#### 2-2. セットアップ確認スクリプトの実行

```bash
./docker/setup_check.sh
```

**出力例:**

```
✓ Docker がインストールされています
✓ Docker Compose がインストールされています
✓ .env ファイルが見つかりました
⚠ kaggle-s6e2-heart イメージが見つかりません
```

#### 2-3. イメージのロード（共有イメージがある場合）

```bash
# 共有イメージがある場合（パスは環境に合わせて変更）
docker load < /path/to/shared/kaggle-s6e2-heart.tar.gz

# または、ローカルでビルド（30分〜1時間）
cd docker
docker compose build --no-cache
```

**所要時間:** ロードは5〜10分、ビルドは30分〜1時間

#### 2-4. コンテナの起動

**必ず `docker` フォルダに移動してから起動すること。**

```bash
cd docker
docker compose up -d
```

ブラウザで `http://<サーバーIP>:8888` にアクセス。

---

## 📦 環境の更新（ライブラリ追加時）

### シナリオ: transformers を追加したい

#### Step 1: requirements.txt の更新

```bash
cd ~/kaggle-s6e2-heart/docker
echo "transformers>=4.30" >> requirements.txt
git add requirements.txt
git commit -m "Add transformers to requirements"
git push origin main
```

#### Step 2: イメージの再ビルド（管理者）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose build --no-cache
docker save kaggle-s6e2-heart:latest | gzip > /data1/share/kaggle-zemi/kaggle-s6e2-heart.tar.gz
```

#### Step 3: メンバーへの通知

Slackやメールで:

```
【更新通知】Docker環境を更新しました
- transformers を追加
- 更新手順:
  1. git pull origin main
  2. cd docker && docker compose build --no-cache
  3. docker compose down && docker compose up -d
```

#### Step 4: メンバーの更新作業

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
git pull origin main
cd docker
docker compose build --no-cache
docker compose down
docker compose up -d
```

---

## 🔐 セキュリティ管理

### 認証情報の管理方針

**このプロジェクトでは `.env` ファイルで認証を統一管理します:**

- ✅ **採用**: プロジェクト直下の `.env` に `KAGGLE_USERNAME` と `KAGGLE_KEY` を設定
- ❌ **不採用**: `~/.kaggle/kaggle.json` の配置（従来の方法は使用しない）

**理由:**
- プロジェクト内で完結（チーム全員が同じ手順）
- ホストと Docker コンテナで同じ設定を共有
- 設定ファイルが1か所に集約

### .env ファイルの取り扱い

`.env` には `KAGGLE_USERNAME` と `KAGGLE_KEY` が含まれるため、**絶対にGitにコミットしないこと**（`.gitignore` に追加済み）。

**絶対にやってはいけないこと:**
- ❌ Gitにコミット
- ❌ Slackやメールで共有
- ❌ Dockerイメージに含める
- ❌ 共有ストレージに置く

**正しい方法:**
- ✅ 各自が自分のKaggleアカウントで発行
- ✅ プロジェクト直下の `.env` に配置
- ✅ `.gitignore` で除外されていることを確認

**確認:**

```bash
cat .gitignore | grep .env
# .env  ← 含まれていることを確認
```

---

## 🐛 よくある問題と解決策

### 問題1: メンバーのファイルが root 権限になる

**原因:** UID/GIDが1000以外

**解決策:**

各メンバーに `.env` ファイルを作成してもらう:

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
cat << EOF > .env
USER_ID=$(id -u)
GROUP_ID=$(id -g)
EOF

cd docker
docker compose down
docker compose up -d
```

### 問題2: ポート 8888 が競合する

**原因:** 複数人が同じサーバーで JupyterLab を起動

**解決策:**

各メンバーに異なるポートを割り当てる:

```yaml
# メンバーAの docker-compose.yml
ports:
  - "8888:8888"

# メンバーBの docker-compose.yml
ports:
  - "8889:8888"

# メンバーCの docker-compose.yml
ports:
  - "8890:8888"
```

または、コンテナ名を変更:

```yaml
container_name: kaggle-s6e2-heart-taisei
```

### 問題3: GPU が認識されない

**原因:** NVIDIA Container Toolkit 未インストール

**解決策（管理者権限必要）:**

```bash
# Ubuntu 20.04/22.04
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 問題4: 共有ストレージの容量不足

**確認:**

```bash
df -h /data1/share/kaggle-zemi
```

**対策:**
- 古いモデルファイルを削除
- 不要な中間データを削除
- Dockerイメージの古いバージョンを削除

---

## 📊 データ管理のベストプラクティス

### ディレクトリ構成

現在は各ユーザーのホームディレクトリ `~/kaggle_data` を使用しています（Plan B）。

```
~/kaggle_data/                     # 各ユーザーのホーム配下
├── datasets/
│   └── raw/
│       ├── train.csv              # 元データ
│       ├── test.csv
│       └── sample_submission.csv
├── processed/                     # 前処理済みデータ
├── models/                        # 学習済みモデル
│   ├── lgbm_fold1.txt
│   └── lgbm_fold2.txt
├── outputs/                       # 提出ファイル
│   └── submission_v1.csv
└── working/                       # 一時ファイル
```

### 命名規則

**モデル:**
```
YYYYMMDD_名前_モデル名/
例: 20260206_taisei_xgboost/
```

**提出ファイル:**
```
名前_vN.csv
例: taisei_v1.csv, taisei_v2.csv
```

---

## 🚀 効率的な開発フロー

### 1. 個人開発（Notebook）

```python
# notebooks/taisei_01_eda.ipynb
import sys
sys.path.append('/workspace')

from src.utils import set_seed
set_seed(42)

# 試行錯誤...
```

### 2. 共通化（src/）

うまくいった処理を関数化:

```python
# src/feature_engineering.py
def create_interaction_features(df):
    """交互作用特徴量を作成"""
    df['age_x_cholesterol'] = df['age'] * df['cholesterol']
    return df
```

### 3. 共有（Git）

```bash
git add src/feature_engineering.py
git commit -m "Add interaction features"
git push origin main
```

### 4. チームで利用

```python
# 他のメンバーのNotebook
from src.feature_engineering import create_interaction_features

df = create_interaction_features(df)
```

---

## 📈 スコア管理

### Google Spreadsheet でのスコア管理（推奨）

| 日付 | 名前 | モデル | Public LB | Private LB | メモ |
|------|------|--------|-----------|------------|------|
| 2026-02-06 | taisei | XGBoost | 0.8234 | - | Baseline |
| 2026-02-07 | hanako | LightGBM | 0.8312 | - | Feature engineering v1 |
| 2026-02-08 | taisei | Ensemble | 0.8401 | - | XGB + LGBM |

### Kaggle API での自動取得

```bash
# 最新のスコアを取得
kaggle competitions submissions -c playground-series-s6e2 | head -5
```

---

## 🎓 初心者向けサポート

### オンボーディングチェックリスト

- [ ] Kaggleアカウント作成
- [ ] `.env` ファイルに `KAGGLE_USERNAME` と `KAGGLE_KEY` を設定
- [ ] Git の基本操作（clone, pull, commit, push）
- [ ] Docker環境の起動
- [ ] JupyterLabへのアクセス
- [ ] 最初のNotebook作成
- [ ] 最初の提出

### 推奨学習リソース

- [Kaggle Learn](https://www.kaggle.com/learn): 無料のチュートリアル
- [Kaggle Courses - Intro to Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning)
- [Docker入門（日本語）](https://docs.docker.jp/get-started/index.html)

---

## 📞 サポート体制

### 質問の優先順位

1. **緊急（環境が動かない）**: Slack の `#kaggle-support` で即座に質問
2. **技術的な質問**: GitHub Issues に投稿
3. **アイデア共有**: Slack の `#kaggle-ideas` で議論

### 定期ミーティング

- **週次ミーティング**: 毎週金曜 17:00〜
  - 進捗共有
  - スコア報告
  - 次週の方針決定

---

## 🏆 コンペ終了後

### 1. 環境のクリーンアップ

```bash
# コンテナの停止・削除
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose down

# イメージの削除（任意）
docker rmi kaggle-s6e2-heart:latest
```

### 2. 振り返り

- 何がうまくいったか
- 何がうまくいかなかったか
- 次回への改善点

### 3. ドキュメント化

- 最終的なアプローチをREADMEに追記
- 学んだことをWikiやブログに記録

---

## 参考リンク

- [Kaggle - Playground Series S6E2](https://www.kaggle.com/competitions/playground-series-s6e2)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Git Book（日本語）](https://git-scm.com/book/ja/v2)
