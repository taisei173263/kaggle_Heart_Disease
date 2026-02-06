# ジョブスクリプト使用ガイド

このドキュメントでは、Sun Grid Engine（SGE）を使ったジョブ投入方法を説明します。

---

## 📁 ジョブスクリプト一覧

| ファイル | 用途 |
|---------|------|
| `scripts/job.sh` | シンプルなジョブスクリプト（main.py実行） |
| `scripts/job_template.sh` | カスタマイズ用テンプレート（詳細なコメント付き） |
| `scripts/job_array.sh` | アレイジョブ（複数パラメータの並列実行） |

---

## 🚀 基本的な使い方

### 1. シンプルなジョブ投入

```bash
cd ~/kaggle-s6e2-heart
qsub scripts/job.sh
```

**出力例:**

```
Your job 12345 ("job.sh") has been submitted
```

### 2. ジョブの状態確認

```bash
# 自分のジョブを確認
qstat

# 詳細情報
qstat -j 12345

# 全ユーザーのジョブ
qstat -u "*"
```

**出力例:**

```
job-ID  prior   name       user         state submit/start at     queue
----------------------------------------------------------------------------------
12345   0.50000 job.sh     taisei       r     02/06/2026 16:50:00 tsmall@node01
```

### 3. ジョブの削除

```bash
# ジョブIDを指定
qdel 12345

# 自分の全ジョブを削除
qdel -u $USER
```

### 4. ログの確認

```bash
# 標準出力（リアルタイム）
tail -f logs/job_12345.out

# 標準エラー出力
tail -f logs/job_12345.err
```

---

## 🎯 カスタムジョブの作成

### Step 1: テンプレートをコピー

```bash
cp scripts/job_template.sh scripts/my_experiment.sh
```

### Step 2: スクリプトを編集

```bash
vim scripts/my_experiment.sh
# または
nano scripts/my_experiment.sh
```

**編集例:**

```bash
#!/bin/bash
#$ -cwd
#$ -q tsmall
#$ -l mem_req=32g        # メモリを32GBに変更
#$ -l h_vmem=32g
#$ -l gpu=2              # GPU数を2に変更
#$ -N my-xgboost         # ジョブ名を変更
#$ -o logs/xgboost_$JOB_ID.out
#$ -e logs/xgboost_$JOB_ID.err

mkdir -p logs

echo "Starting XGBoost training..."
uv run python -u src/train.py --model xgboost --n_estimators 1000

exit $?
```

### Step 3: ジョブを投入

```bash
qsub scripts/my_experiment.sh
```

---

## 🔧 SGEオプション詳細

### キュー（-q）

```bash
#$ -q tsmall   # 小規模ジョブ用（デフォルト）
#$ -q tlarge   # 大規模ジョブ用
#$ -q gpu      # GPU専用キュー（環境による）
```

**確認方法:**

```bash
qconf -sql  # 利用可能なキュー一覧
```

### メモリ（-l mem_req, -l h_vmem）

```bash
#$ -l mem_req=4g     # 4GB
#$ -l mem_req=8g     # 8GB
#$ -l mem_req=16g    # 16GB
#$ -l mem_req=32g    # 32GB
#$ -l mem_req=64g    # 64GB
```

**推奨:** `mem_req` と `h_vmem` は同じ値に設定

### GPU数（-l gpu）

```bash
#$ -l gpu=0    # CPU のみ
#$ -l gpu=1    # GPU 1枚
#$ -l gpu=2    # GPU 2枚
#$ -l gpu=4    # GPU 4枚
```

### ジョブ名（-N）

```bash
#$ -N my-job-name
```

ジョブ名は `qstat` で表示されます。

### 出力ファイル（-o, -e）

```bash
#$ -o logs/job_$JOB_ID.out   # 標準出力
#$ -e logs/job_$JOB_ID.err   # 標準エラー出力
```

**変数:**
- `$JOB_ID`: ジョブID
- `$JOB_NAME`: ジョブ名
- `$TASK_ID`: アレイジョブのタスクID

### メール通知（-M, -m）

```bash
#$ -M your_email@example.com   # 通知先メールアドレス
#$ -m be                        # b=開始, e=終了, a=中断
```

### 並列実行（-pe）

```bash
#$ -pe smp 8    # 8コア並列実行
```

---

## 🎨 アレイジョブの使い方

複数のパラメータ設定を並列実行する場合に便利です。

### 基本的な使い方

```bash
qsub scripts/job_array.sh
```

これで、タスクID 1〜5 の5つのジョブが並列実行されます。

### アレイジョブの確認

```bash
qstat
```

**出力例:**

```
job-ID  prior   name       user         state submit/start at     queue
----------------------------------------------------------------------------------
12345   0.50000 kaggle-ar  taisei       r     02/06/2026 16:50:00 tsmall@node01
12346   0.50000 kaggle-ar  taisei       r     02/06/2026 16:50:01 tsmall@node02
12347   0.50000 kaggle-ar  taisei       r     02/06/2026 16:50:02 tsmall@node03
```

### カスタマイズ例

```bash
#!/bin/bash
#$ -t 1-10    # タスクID 1〜10（10個のジョブ）

# パラメータファイルから読み込む
PARAMS_FILE="configs/params.txt"
PARAMS=$(sed -n "${SGE_TASK_ID}p" $PARAMS_FILE)

echo "Task $SGE_TASK_ID: $PARAMS"
uv run python -u src/train.py $PARAMS
```

**params.txt の例:**

```
--model xgboost --n_estimators 500 --learning_rate 0.1
--model xgboost --n_estimators 1000 --learning_rate 0.05
--model lightgbm --n_estimators 500 --learning_rate 0.1
--model lightgbm --n_estimators 1000 --learning_rate 0.05
--model catboost --n_estimators 500 --learning_rate 0.1
```

---

## 📊 ジョブの監視

### リアルタイムログ監視

```bash
# 標準出力をリアルタイム表示
tail -f logs/job_12345.out

# 標準エラー出力をリアルタイム表示
tail -f logs/job_12345.err

# 両方を表示
tail -f logs/job_12345.out logs/job_12345.err
```

### GPU使用状況の確認

```bash
# ノードにログインしてGPU確認
qlogin -q tsmall -l gpu=1
nvidia-smi

# または、ジョブスクリプト内で定期的に記録
watch -n 10 nvidia-smi >> logs/gpu_usage.log
```

### メモリ使用状況の確認

```bash
qstat -j 12345 | grep usage
```

---

## 🐛 トラブルシューティング

### Q1. ジョブが Eqw 状態（エラー）になる

**原因:** スクリプトにエラーがある、または権限がない

**解決策:**

```bash
# エラー詳細を確認
qstat -j 12345

# ジョブを削除して修正
qdel 12345

# 実行権限を確認
chmod +x scripts/job.sh
```

### Q2. ジョブが qw 状態（待機）のまま

**原因:** リソースが空いていない

**解決策:**

```bash
# キューの状態を確認
qstat -f

# 他のキューを試す
#$ -q tlarge

# メモリ要求を減らす
#$ -l mem_req=8g
```

### Q3. GPU が認識されない

**原因:** GPU が割り当てられていない

**解決策:**

```bash
# GPU を明示的に要求
#$ -l gpu=1

# ジョブスクリプト内で確認
nvidia-smi
echo $CUDA_VISIBLE_DEVICES
```

### Q4. ログファイルが作成されない

**原因:** ログディレクトリが存在しない

**解決策:**

```bash
# ログディレクトリを作成
mkdir -p logs

# または、ジョブスクリプト内で作成
#!/bin/bash
mkdir -p logs
```

---

## 💡 ベストプラクティス

### 1. ログディレクトリの整理

```bash
# 日付ごとにディレクトリを分ける
#$ -o logs/$(date +%Y%m%d)/job_$JOB_ID.out
#$ -e logs/$(date +%Y%m%d)/job_$JOB_ID.err
```

### 2. 実験名を付ける

```bash
#$ -N xgb-lr0.1-n1000
```

### 3. 結果を自動保存

```bash
# ジョブスクリプトの最後に
if [ $EXIT_CODE -eq 0 ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    cp data/output/submission.csv /data1/share/kaggle-zemi/submissions/${TIMESTAMP}_${JOB_NAME}.csv
    cp models/model.pkl /data1/share/kaggle-zemi/models/${TIMESTAMP}_${JOB_NAME}.pkl
fi
```

### 4. GPU使用率を記録

```bash
# ジョブスクリプト内で
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 60 > logs/gpu_${JOB_ID}.csv &
GPU_MONITOR_PID=$!

# メインスクリプト実行
uv run python -u src/train.py

# GPU監視を停止
kill $GPU_MONITOR_PID
```

### 5. エラー時の通知

```bash
# ジョブスクリプトの最後に
if [ $EXIT_CODE -ne 0 ]; then
    echo "Job $JOB_ID failed with exit code $EXIT_CODE" | mail -s "Job Failed" your_email@example.com
fi
```

---

## 📚 よく使うコマンド一覧

```bash
# ジョブ投入
qsub scripts/job.sh

# ジョブ確認
qstat
qstat -u $USER
qstat -j 12345

# ジョブ削除
qdel 12345
qdel -u $USER

# キュー確認
qconf -sql
qstat -f

# ノードにログイン
qlogin -q tsmall -l gpu=1

# ログ確認
tail -f logs/job_12345.out
less logs/job_12345.out

# GPU確認
nvidia-smi
watch -n 1 nvidia-smi
```

---

## 🎓 学習リソース

- [Sun Grid Engine Documentation](http://gridscheduler.sourceforge.net/htmlman/manuals.html)
- [SGE Cheat Sheet](https://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)

---

## 📞 サポート

- **質問:** Slack `#kaggle-support` チャンネル
- **SGE管理者:** サーバー管理者に連絡
