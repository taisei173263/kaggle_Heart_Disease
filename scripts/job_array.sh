#!/bin/bash
#$ -cwd
#$ -o /dev/null
#$ -e /dev/null
#$ -q tsmall
#$ -l mem_req=16g
#$ -l h_vmem=16g
#$ -l gpu=1
#$ -N kaggle-array
#$ -t 1-5

# ========================================
# Kaggle S6E2 Heart - アレイジョブスクリプト（ホスト直接実行版）
# ========================================
#
# ⚠️ 注意: このスクリプトは Docker を使わず、ホスト上で直接 uv run を実行します。
#          uv がホストにインストールされている必要があります。
#
# 複数のパラメータ設定を並列実行する場合に使用
#
# 使い方:
#   qsub scripts/job_array.sh
#
# SGEオプション:
#   -t 1-5  : タスクID 1〜5 を並列実行（5つのジョブ）
#
# ========================================

# プロジェクトルート（投入元ディレクトリ）
if [ -n "${SGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$SGE_O_WORKDIR"
elif [ -n "${UGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$UGE_O_WORKDIR"
else
    PROJECT_ROOT="$(pwd)"
fi

# ログをプロジェクトの logs/ に出力
LOGDIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGDIR"
if [ -n "${JOB_ID:-}" ] && [ -n "${SGE_TASK_ID:-}" ]; then
    exec >> "$LOGDIR/kaggle-array.o${JOB_ID}.${SGE_TASK_ID}" 2>> "$LOGDIR/kaggle-array.e${JOB_ID}.${SGE_TASK_ID}"
fi

echo "=========================================="
echo "Array Job ID: $JOB_ID"
echo "Task ID: $SGE_TASK_ID"
echo "Hostname: $(hostname)"
echo "Start Time: $(date)"
echo "=========================================="
echo ""

# タスクIDに応じてパラメータを変更
case $SGE_TASK_ID in
    1)
        MODEL="xgboost"
        N_ESTIMATORS=500
        LEARNING_RATE=0.1
        ;;
    2)
        MODEL="xgboost"
        N_ESTIMATORS=1000
        LEARNING_RATE=0.05
        ;;
    3)
        MODEL="lightgbm"
        N_ESTIMATORS=500
        LEARNING_RATE=0.1
        ;;
    4)
        MODEL="lightgbm"
        N_ESTIMATORS=1000
        LEARNING_RATE=0.05
        ;;
    5)
        MODEL="catboost"
        N_ESTIMATORS=500
        LEARNING_RATE=0.1
        ;;
    *)
        echo "Error: Invalid task ID: $SGE_TASK_ID"
        exit 1
        ;;
esac

echo "Parameters for Task $SGE_TASK_ID:"
echo "  MODEL: $MODEL"
echo "  N_ESTIMATORS: $N_ESTIMATORS"
echo "  LEARNING_RATE: $LEARNING_RATE"
echo ""

# GPU情報
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=index,name,utilization.gpu --format=csv
    echo ""
fi

# メインスクリプトの実行
echo "Starting training..."
uv run python -u src/train.py \
    --model $MODEL \
    --n_estimators $N_ESTIMATORS \
    --learning_rate $LEARNING_RATE \
    --output_dir models/task_${SGE_TASK_ID}

EXIT_CODE=$?
echo ""
echo "=========================================="
echo "Task $SGE_TASK_ID completed"
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
