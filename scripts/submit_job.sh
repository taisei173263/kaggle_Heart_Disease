#!/bin/bash
#
# SGE ジョブ投入スクリプト（計算ノード上で Docker 内コマンドを実行）
#
# 使い方（プロジェクトルートで。事前に mkdir -p logs を推奨）:
#   qsub scripts/submit_job.sh src/train.py --epochs 10
#   qsub scripts/submit_job.sh python src/train.py --epochs 10
#   qsub -N my-exp scripts/submit_job.sh src/train.py --config configs/exp1.yaml
#   qsub scripts/submit_job.sh python -c "print(1+1)"
#
# =============================================================================
# なぜ docker compose run で up ではないのか？（初心者向け）
# =============================================================================
# - up: コンテナを「常駐」させ、バックグラウンドで動かす。JupyterLab のように
#       ずっと起動しておくサービス向け。ジョブで「1回だけ処理して終了」には向かない。
# - run: 指定したコマンドを「1回だけ」実行し、終了したらコンテナを自動削除する。
#        学習ジョブのように「投げたら終わる」タスクに最適。--rm でゴミを残さない。
# =============================================================================

#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -q tsmall
#$ -l gpu=1
#$ -l mem_req=16g
#$ -l h_vmem=16g
#$ -N kaggle-run

set -e

# プロジェクトルート: 投入元ディレクトリ（SGE/UGE が設定）があればそれを使い、なければスクリプトの位置から取得
if [ -n "${SGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$SGE_O_WORKDIR"
elif [ -n "${UGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$UGE_O_WORKDIR"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
DOCKER_DIR="$PROJECT_ROOT/docker"

# ログをプロジェクトの logs/ に出力（計算ノードで -o/-e の相対パスがスプール配下になり権限エラーになるため）
LOGDIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGDIR"
if [ -n "${JOB_ID:-}" ]; then
    exec >> "$LOGDIR/kaggle-run.o$JOB_ID" 2>> "$LOGDIR/kaggle-run.e$JOB_ID"
fi

# 引数がなければ usage を表示して終了
if [ $# -eq 0 ]; then
    echo "Usage: qsub scripts/submit_job.sh [python] <script.py> [args...]"
    echo "  Example: qsub scripts/submit_job.sh src/train.py --epochs 10"
    echo "  Example: qsub scripts/submit_job.sh python src/train.py --epochs 10"
    echo "  Example: qsub scripts/submit_job.sh python -c \"print(1+1)\""
    exit 1
fi

# 第1引数が .py で終わる場合は先頭に python を付ける（省略形）
if [[ "$1" == *.py ]]; then
    set -- python "$@"
fi

echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Job Name: $JOB_NAME"
echo "Hostname: $(hostname)"
echo "Start Time: $(date)"
echo "Project Root: $PROJECT_ROOT"
echo "Command: $*"
echo "=========================================="
echo ""

# GPU 確認（計算ノードで nvidia-smi が使える場合）
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information:"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader
    echo ""
fi

# docker-compose.yml があるディレクトリで、指定コマンドを 1 回だけ実行（終了後コンテナ削除）
# 引数はそのままコンテナ内のコマンドになる（.py の場合は先頭に python を付与済み）
cd "$DOCKER_DIR"
docker compose run --rm app "$@"
EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "=========================================="
exit $EXIT_CODE
