#!/bin/bash
#$ -cwd
#$ -q tsmall
#$ -l mem_req=16g
#$ -l h_vmem=16g
#$ -l gpu=1
#$ -N kaggle-s6e2-heart
#$ -o logs/job_$JOB_ID.out
#$ -e logs/job_$JOB_ID.err
#$ -M your_email@example.com
#$ -m be

# ========================================
# Kaggle S6E2 Heart - ジョブスクリプトテンプレート
# ========================================
#
# 使い方:
#   1. このファイルをコピーして編集
#      cp scripts/job_template.sh scripts/my_experiment.sh
#   2. 必要に応じてパラメータを変更
#   3. ジョブを投入
#      qsub scripts/my_experiment.sh
#
# SGEオプション説明:
#   -cwd              : カレントディレクトリで実行
#   -q tsmall         : キュー名（tsmall, tlarge等）
#   -l mem_req=16g    : 要求メモリ（4g, 8g, 16g, 32g等）
#   -l h_vmem=16g     : 最大メモリ（mem_reqと同じ値を推奨）
#   -l gpu=1          : GPU数（0, 1, 2等）
#   -N <name>         : ジョブ名
#   -o <path>         : 標準出力ファイル
#   -e <path>         : 標準エラー出力ファイル
#   -M <email>        : 通知先メールアドレス
#   -m be             : メール通知タイミング（b=開始, e=終了, a=中断）
#
# ========================================

# ログディレクトリの作成
mkdir -p logs

# ジョブ情報の出力
echo "=========================================="
echo "Job ID: $JOB_ID"
echo "Job Name: $JOB_NAME"
echo "Queue: $QUEUE"
echo "Hostname: $(hostname)"
echo "Start Time: $(date)"
echo "Working Directory: $(pwd)"
echo "=========================================="
echo ""

# 環境変数の設定
export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=0

# GPU情報の確認
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information:"
    nvidia-smi
    echo ""
fi

# Python環境の確認
echo "Python Environment:"
python --version
echo ""

# 依存パッケージの確認（オプション）
# pip list | grep -E "torch|pandas|xgboost|lightgbm"
# echo ""

# ========================================
# メインスクリプトの実行
# ========================================

echo "Starting experiment..."
echo ""

# 例1: 単一スクリプトの実行
uv run python -u src/train.py

# 例2: パラメータを渡す場合
# uv run python -u src/train.py --model xgboost --n_estimators 1000

# 例3: 複数のスクリプトを順次実行
# uv run python -u src/preprocessing.py
# uv run python -u src/train.py
# uv run python -u src/predict.py

# 例4: Notebookを実行する場合
# jupyter nbconvert --to notebook --execute notebooks/01_train.ipynb

# ========================================
# 終了処理
# ========================================

EXIT_CODE=$?
echo ""
echo "=========================================="
echo "End Time: $(date)"
echo "Exit Code: $EXIT_CODE"
echo "=========================================="

# 結果ファイルのコピー（オプション）
# if [ $EXIT_CODE -eq 0 ]; then
#     cp data/output/submission.csv /data1/share/kaggle-zemi/submissions/$(date +%Y%m%d_%H%M%S)_submission.csv
# fi

exit $EXIT_CODE
