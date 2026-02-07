# 完全セットアップガイド（初回〜リーダーボード提出まで）

このドキュメントは、チームメンバーが **ゼロから環境構築し、最初の提出を行う** までの完全な手順書です。

---

## 📋 概要

このプロジェクトでは、**Kaggle公式Dockerイメージ** を使用して、Kaggle Notebook と完全に同じ環境で開発できます。

| 項目 | 内容 |
|------|------|
| コンペ | Playground Series S6E2（心疾患予測） |
| 評価指標 | ROC AUC |
| 環境 | Docker（Kaggle公式イメージ） |
| 実行場所 | SGE計算ノード（GPU付き） |

---

## 🚀 セットアップ手順（所要時間: 約1〜2時間）

### Step 1: リポジトリのクローン（5分）

```bash
cd ~
git clone https://github.com/taisei173263/kaggle_Heart_Disease.git kaggle/competitions/kaggle-s6e2-heart
cd kaggle/competitions/kaggle-s6e2-heart
```

### Step 2: Kaggle API認証の設定（5分）

#### 2-1. Kaggle APIトークンの取得

1. [Kaggle](https://www.kaggle.com/) にログイン
2. 右上のアイコン → **Account** → **API** セクション
3. **Create New API Token** をクリック
4. `kaggle.json` がダウンロードされる

#### 2-2. kaggle.json の配置

```bash
# ホームディレクトリに .kaggle フォルダを作成
mkdir -p ~/.kaggle

# ダウンロードした kaggle.json を移動（パスは環境に合わせて変更）
mv ~/Downloads/kaggle.json ~/.kaggle/

# パーミッション設定（重要: 自分だけが読み書きできるようにする）
chmod 600 ~/.kaggle/kaggle.json
```

#### 2-3. KAGGLE_API_TOKEN の設定（ホストで submit.sh を使う場合）

```bash
# .env ファイルを作成
cd ~/kaggle/competitions/kaggle-s6e2-heart
cp .env.example .env

# kaggle.json の key を確認
cat ~/.kaggle/kaggle.json
# {"username":"your_username","key":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}

# .env に追記（KGAT_ プレフィックスを付ける）
echo "KAGGLE_API_TOKEN=KGAT_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >> .env
```

### Step 3: データ置き場の作成（2分）

```bash
# ホームディレクトリにデータ置き場を作成
mkdir -p ~/kaggle_data/{datasets/raw,processed,models,outputs,working}

# 権限設定
chmod -R 777 ~/kaggle_data
chmod o+x ~
```

### Step 4: Dockerイメージのビルド（30分〜1時間）

**⚠️ 重要: 必ず `docker/` フォルダに移動してから実行すること**

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose build --no-cache
```

**ビルド中の注意:**
- Kaggle公式イメージ（約20〜40GB）のダウンロードに時間がかかります
- ビルド完了後、イメージサイズは **40GB超** になります（これが正常です）

**ビルド後の確認:**

```bash
docker images | grep kaggle-s6e2-heart
# kaggle-s6e2-heart   latest   xxxxx   47.4GB
```

### Step 5: データのダウンロード（5分）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# Kaggle からデータをダウンロード
kaggle competitions download -c playground-series-s6e2

# 解凍してデータ置き場にコピー
unzip playground-series-s6e2.zip -d data/raw/
cp data/raw/*.csv ~/kaggle_data/datasets/raw/

# 確認
ls -la ~/kaggle_data/datasets/raw/
# train.csv, test.csv, sample_submission.csv があればOK
```

### Step 6: 環境チェック（10分）

計算ノードで Docker 環境が正しく動作するか確認します。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# ログディレクトリを作成
mkdir -p logs

# 環境チェックジョブを投入
qsub scripts/submit_job.sh src/check_env.py

# ジョブの状態確認（r = 実行中、何も出なければ終了）
qstat

# 結果を確認（✅ が3つ出ればOK）
cat logs/kaggle-run.o*
```

**成功の目安:**
```
✅ データ読み込み成功: /data/datasets/raw/train.csv
   データ形状: (630000, 15)
✅ GPU認識成功: NVIDIA RTX 6000 Ada Generation
✅ 書き込みテスト成功: /data/working/test_output.txt
```

---

## 🎯 最初の提出（ベースライン学習）

環境チェックが成功したら、ベースライン学習を実行して Kaggle に提出します。

### Step 7: ベースライン学習の実行（10〜20分）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# 学習ジョブを投入
qsub scripts/submit_job.sh src/train.py

# ジョブの状態確認
qstat

# 終了後、ログを確認
cat logs/kaggle-run.o*
```

**成功の目安:**
```
=== CV Score (AUC): 0.9552 ===
✅ Submission saved to: /data/outputs/submission_v1.csv
```

### Step 8: Kaggle への提出（5分）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# 提出ファイルをプロジェクトにコピー
cp ~/kaggle_data/outputs/submission_v1.csv data/output/

# Kaggle に提出
./scripts/submit.sh data/output/submission_v1.csv "LightGBM baseline v1"
```

**提出成功の確認:**
```bash
# 提出履歴を確認
kaggle competitions submissions -c playground-series-s6e2
```

**おめでとうございます！** これでリーダーボードに乗りました 🎉

---

## 📁 プロジェクト構成

```
kaggle-s6e2-heart/
├── README.md                    # メンバー向けセットアップ手順
├── SETUP_SUMMARY.md             # このファイル（完全ガイド）
├── TEAM_GUIDE.md                # 管理者向け運用ガイド
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git除外設定
│
├── docker/                      # Docker環境
│   ├── Dockerfile               # Kaggle公式イメージ + 日本語対応
│   ├── docker-compose.yml       # コンテナ起動設定
│   ├── requirements.txt         # 追加パッケージ（最小限）
│   ├── README_DOCKER.md         # Docker詳細ドキュメント
│   ├── setup_check.sh           # 環境確認スクリプト
│   └── quick_start.sh           # クイックスタートスクリプト
│
├── data/                        # データ（Git管理外）
│   ├── raw/                     # 元データ
│   ├── processed/               # 前処理済みデータ
│   └── output/                  # 提出用CSV
│
├── src/                         # 共通コード
│   ├── check_env.py             # 環境チェックスクリプト
│   ├── train.py                 # ベースライン学習スクリプト
│   ├── config.py                # パス・定数管理
│   ├── preprocessing.py         # 前処理関数
│   └── utils.py                 # ユーティリティ関数
│
├── scripts/                     # ユーティリティスクリプト
│   ├── submit.sh                # Kaggle提出スクリプト
│   ├── submit_job.sh            # SGEジョブ投入（Docker内・推奨）
│   ├── job.sh                   # ジョブスクリプト（ホスト直接）
│   ├── job_template.sh          # カスタマイズ用テンプレート
│   └── job_array.sh             # アレイジョブ
│
├── notebooks/                   # Jupyter Notebook
├── models/                      # 学習済みモデル（Git管理外）
├── logs/                        # ジョブログ（Git管理外）
└── docs/                        # ドキュメント
    ├── JOB_GUIDE.md             # ジョブスクリプト使用ガイド
    └── LIGHTGBM_GPU.md          # LightGBM GPU 関連情報
```

---

## 💻 日常の使い方

### JupyterLab の起動（計算ノードで）

ログインノードには GPU がないため、計算ノードで Docker を起動します。

```bash
# 1. 計算ノードに接続
qrsh -q tsmall -l gpu=1 -l mem_req=16g -l h_vmem=16g

# 2. Docker を起動
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up

# 3. 別ターミナルで SSH トンネルを張る（手元のPCで）
ssh -L 8888:tn4:8888 ユーザー名@ログインノード

# 4. ブラウザで http://localhost:8888 にアクセス
```

### 学習ジョブの投入

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# 基本的な投入
qsub scripts/submit_job.sh src/train.py

# 引数を渡す場合
qsub scripts/submit_job.sh src/train.py --epochs 10

# ジョブ名を付ける場合
qsub -N xgb-v1 scripts/submit_job.sh src/train.py

# ジョブの状態確認
qstat

# ログの確認
tail -f logs/kaggle-run.o*

# ジョブの削除
qdel <ジョブID>
```

### Kaggle への提出

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart

# 提出ファイルをコピー
cp ~/kaggle_data/outputs/submission_v1.csv data/output/

# 提出
./scripts/submit.sh data/output/submission_v1.csv "メッセージ"

# 提出履歴の確認
kaggle competitions submissions -c playground-series-s6e2
```

---

## 🔧 トラブルシューティング

### Q1. `could not select device driver "nvidia"` エラー

**原因:** ログインノード（GPU なし）で Docker を起動している

**解決策:** 計算ノードで起動するか、GPU 設定をコメントアウト

```bash
# 計算ノードに入ってから起動
qrsh -q tsmall -l gpu=1 -l mem_req=16g -l h_vmem=16g
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up
```

### Q2. `kaggle.json` が見つからないエラー

**解決策:**

```bash
ls -la ~/.kaggle/kaggle.json
# 存在しない場合は Step 2 を再実行
```

### Q3. データが見つからないエラー

**解決策:**

```bash
ls -la ~/kaggle_data/datasets/raw/
# train.csv がない場合は Step 5 を再実行
```

### Q4. ジョブが `qw` 状態のまま

**原因:** 計算ノードのリソースが空いていない

**解決策:** しばらく待つか、リソース要求を減らす

```bash
# メモリを減らして再投入
qsub -l mem_req=8g -l h_vmem=8g scripts/submit_job.sh src/train.py
```

---

## 📚 次のステップ

### 1. EDA（探索的データ分析）

```bash
# JupyterLab で notebooks/00_eda_initial.ipynb を開く
```

### 2. 特徴量エンジニアリング

```python
# src/preprocessing.py に関数を追加
def create_features(df):
    df['age_x_cholesterol'] = df['age'] * df['cholesterol']
    return df
```

### 3. モデルの改善

- **LightGBM のパラメータチューニング**: Optuna を使用
- **他のモデルを試す**: XGBoost, CatBoost（GPU対応）
- **アンサンブル**: 複数モデルの予測を平均

### 4. 詳細ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `README.md` | 詳細なセットアップ手順 |
| `TEAM_GUIDE.md` | チーム運用ガイド |
| `docs/JOB_GUIDE.md` | ジョブスクリプトの詳細 |
| `docs/LIGHTGBM_GPU.md` | LightGBM GPU 関連情報 |
| `docker/README_DOCKER.md` | Docker 環境の詳細 |

---

## ✅ チェックリスト

### 初回セットアップ

- [ ] リポジトリをクローン
- [ ] `~/.kaggle/kaggle.json` を配置
- [ ] `chmod 600 ~/.kaggle/kaggle.json` を実行
- [ ] `~/kaggle_data/` を作成・権限設定
- [ ] Docker イメージをビルド（40GB超になればOK）
- [ ] データをダウンロード・配置
- [ ] 環境チェック（✅ が3つ）
- [ ] ベースライン学習を実行
- [ ] Kaggle に提出

### 日常の開発

- [ ] 計算ノードで Docker を起動
- [ ] JupyterLab または bash で作業
- [ ] 学習ジョブは `qsub scripts/submit_job.sh` で投入
- [ ] 提出は `./scripts/submit.sh` を使用
- [ ] Git で変更をコミット・プッシュ

---

## 🤝 サポート

- **Slack:** `#kaggle-support` チャンネル
- **GitHub Issues:** 技術的な問題・バグ報告
- **直接相談:** ゼミの先輩・メンター

---

**Happy Kaggling! 🎉**
