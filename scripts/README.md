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
| `job.sh` | シンプルなジョブスクリプト（main.py実行） |
| `job_template.sh` | カスタマイズ用テンプレート（詳細なコメント付き） |
| `job_array.sh` | アレイジョブ（複数パラメータの並列実行） |

**使い方:**

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

### ジョブ投入

```bash
# ジョブ投入
qsub scripts/job.sh

# ジョブ確認
qstat

# ログ確認
tail -f logs/job_12345.out

# ジョブ削除
qdel 12345
```

---

## 📚 ドキュメント

- **Kaggle提出:** `README.md` の「Kaggleへの提出」セクション
- **ジョブスクリプト:** `docs/JOB_GUIDE.md`
- **チーム運用:** `TEAM_GUIDE.md`
