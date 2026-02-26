# スクリプト一覧

このディレクトリには、Kaggle提出やジョブ投入に使うスクリプトが含まれています。

---

## 📁 ファイル一覧

### Kaggle提出

| ファイル | 用途 |
|---------|------|
| `submit.sh` | Kaggleへの提出スクリプト |

**使い方:**

```bash
./scripts/submit.sh data/output/submission.csv "メッセージ"
```

---

### ジョブスクリプト（SGE環境）

| ファイル | 用途 |
|---------|------|
| **`setup_build_job.sh`** | **環境構築（データ置き場 + Docker ビルド）を計算ノードで実行** |
| **`submit_job.sh`** | **計算ノードで Docker 内コマンドを1回実行**（推奨・汎用） |
| `job.sh` | シンプルなジョブスクリプト（main.py実行） |
| `job_template.sh` | カスタマイズ用テンプレート（詳細なコメント付き） |
| `job_array.sh` | アレイジョブ（複数パラメータの並列実行） |

**setup_build_job.sh の使い方（ログインノード負荷を避けたい場合）:**

```bash
mkdir -p logs
qsub scripts/setup_build_job.sh
# ログ: tail -f logs/setup-build.o<ジョブID>
```

**submit_job.sh の使い方（Login ノードから投入）:**

```bash
# プロジェクトルートで実行。計算ノードの Docker 内で train.py が動く
qsub scripts/submit_job.sh src/train.py --epochs 10
qsub scripts/submit_job.sh src/train.py
qsub -N my-exp scripts/submit_job.sh src/train.py --config configs/exp1.yaml
```

**その他のジョブスクリプト:**

```bash
# 基本的な投入
qsub scripts/job.sh

# カスタムジョブの作成
cp scripts/job_template.sh scripts/my_experiment.sh
vim scripts/my_experiment.sh
qsub scripts/my_experiment.sh

# アレイジョブ
qsub scripts/job_array.sh
```

**詳細:** `docs/JOB_GUIDE.md` を参照

---

## 🎯 クイックリファレンス

### Kaggle提出

```bash
# 提出
./scripts/submit.sh data/output/submission.csv "XGBoost v1"

# 提出履歴確認
kaggle competitions submissions -c playground-series-s6e2
```

### ジョブ投入（Docker 内で学習を回す）

```bash
# 計算ノードの Docker 内で 1 回だけコマンド実行（PC を閉じても継続）
qsub scripts/submit_job.sh src/train.py --epochs 10

# ジョブ確認
qstat

# ログ確認（ジョブ名はデフォルト kaggle-run）
tail -f logs/kaggle-run.o12345
tail -f logs/kaggle-run.e12345

# ジョブ削除
qdel 12345
```

---

## 📚 ドキュメント

- **Kaggle提出:** `README.md` の「Kaggleへの提出」セクション
- **ジョブスクリプト:** `docs/JOB_GUIDE.md`
- **チーム運用:** `TEAM_GUIDE.md`
