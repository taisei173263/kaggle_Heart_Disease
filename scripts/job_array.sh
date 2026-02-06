#!/bin/bash
#$ -cwd
#$ -q tsmall
#$ -l mem_req=16g
#$ -l h_vmem=16g
#$ -l gpu=1
#$ -N kaggle-array
#$ -o logs/array_$TASK_ID.out
#$ -e logs/array_$TASK_ID.err
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

# ログディレクトリの作成
mkdir -p logs

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
