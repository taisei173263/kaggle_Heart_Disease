#!/bin/bash
#
# SGE ジョブ: 環境構築（データ置き場作成 + Docker イメージビルド）
#
# ログインノードに負荷をかけず、計算ノードでビルドするためのスクリプトです。
#
# 事前にログインノードで行うこと:
#   - リポジトリのクローン
#   - .env の作成と KAGGLE_USERNAME / KAGGLE_KEY の設定
#
# 使い方（プロジェクトルートで）:
#   mkdir -p logs
#   qsub scripts/setup_build_job.sh
#
# オプション（キャッシュなしで完全ビルド）:
#   qsub -v BUILD_OPTS="--no-cache" scripts/setup_build_job.sh
#
# 注意: 計算ノードごとに Docker イメージが別の場合は、ビルド後に
#       イメージを共有ストレージに保存（docker save）し、他ノードで
#       docker load する運用を検討してください。
#
# =============================================================================

#$ -S /bin/bash
#$ -cwd
#$ -V
#$ -o /dev/null
#$ -e /dev/null
#$ -q tsmall
#$ -l gpu=0
#$ -l mem_req=24g
#$ -l h_vmem=24g
#$ -N setup-build

set -e

# プロジェクトルート
if [ -n "${SGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$SGE_O_WORKDIR"
elif [ -n "${UGE_O_WORKDIR:-}" ]; then
    PROJECT_ROOT="$UGE_O_WORKDIR"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
DOCKER_DIR="$PROJECT_ROOT/docker"

# ログ出力
LOGDIR="$PROJECT_ROOT/logs"
mkdir -p "$LOGDIR"
if [ -n "${JOB_ID:-}" ]; then
    exec >> "$LOGDIR/setup-build.o$JOB_ID" 2>> "$LOGDIR/setup-build.e$JOB_ID"
fi

echo "=========================================="
echo "Environment setup job (up to Docker build)"
echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Job Name: $JOB_NAME"
echo "Hostname: $(hostname)"
echo "Start Time: $(date)"
echo "Project Root: $PROJECT_ROOT"
echo "=========================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: データ置き場の作成
# -----------------------------------------------------------------------------
echo "[Step 1/2] Creating data directories under \$HOME..."
mkdir -p "$HOME/kaggle_data"/{datasets/raw,processed,models,outputs,working}
chmod -R 777 "$HOME/kaggle_data" 2>/dev/null || true
chmod o+x "$HOME" 2>/dev/null || true
echo "  Done: $HOME/kaggle_data"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Docker イメージのビルド
# -----------------------------------------------------------------------------
echo "[Step 2/2] Building Docker image (this may take 30–60 minutes)..."

if [ ! -f "$DOCKER_DIR/docker-compose.yml" ]; then
    echo "ERROR: docker-compose.yml not found at $DOCKER_DIR"
    exit 1
fi

# BUILD_OPTS が未指定の場合は --no-cache（初回推奨）。既存キャッシュ活用なら "" で投入可
OPTS="${BUILD_OPTS:---no-cache}"
cd "$DOCKER_DIR"
docker compose build $OPTS
EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "Build finished successfully. Verify with:"
    echo "  docker images | grep kaggle-s6e2-heart"
    echo ""
    echo "Next: run environment check on a compute node:"
    echo "  qsub scripts/submit_job.sh src/check_env.py"
fi

exit $EXIT_CODE
