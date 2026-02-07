#!/bin/bash
#$ -cwd
#$ -o /dev/null
#$ -e /dev/null
#$ -q tsmall
#$ -l mem_req=16g
#$ -l h_vmem=16g
#$ -l gpu=1
#$ -N job-uv

# Kaggle S6E2 Heart - ジョブスクリプト（ホスト直接実行版）
# 使い方: qsub scripts/job.sh
#
# ⚠️ 注意: このスクリプトは Docker を使わず、ホスト上で直接 uv run を実行します。
#          uv がホストにインストールされている必要があります。
#
# 💡 推奨: Docker 環境を使う場合は scripts/submit_job.sh を使ってください。
#          qsub scripts/submit_job.sh src/train.py --epochs 10

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
if [ -n "${JOB_ID:-}" ]; then
    exec >> "$LOGDIR/job-uv.o$JOB_ID" 2>> "$LOGDIR/job-uv.e$JOB_ID"
fi

# ジョブ情報の出力
echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Job Name: $JOB_NAME"
echo "Hostname: $(hostname)"
echo "Start Time: $(date)"
echo "Working Directory: $(pwd)"
echo "=========================================="
echo ""

# GPU情報の確認
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information:"
    nvidia-smi
    echo ""
fi

# Python環境の確認
echo "Python Version:"
python --version
echo ""

# メインスクリプトの実行
echo "Starting main.py..."
echo ""

uv run python -u main.py

# 終了情報
EXIT_CODE=$?
echo ""
echo "=========================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
