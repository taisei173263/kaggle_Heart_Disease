#!/usr/bin/env bash
# Kaggle に提出する（要: pip install kaggle と Kaggle API 認証の設定）
# 認証情報は .env に KAGGLE_USERNAME と KAGGLE_KEY で記載するか、環境変数で設定
# 使い方: ./scripts/submit.sh [submission.csv のパス] [メッセージ]
# 例:     ./scripts/submit.sh data/output/submission.csv "XGBoost v1"

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# プロジェクト直下の .env があれば読み込む（Kaggle 認証用）
if [[ -f "$PROJECT_ROOT/.env" ]]; then
  set -a
  source "$PROJECT_ROOT/.env"
  set +a
fi

SUB_FILE="${1:-data/output/submission.csv}"
MSG="${2:-submit from script}"

if [[ ! -f "$SUB_FILE" ]]; then
  echo "Error: $SUB_FILE not found."
  exit 1
fi

if [[ -z "${KAGGLE_USERNAME:-}" ]] || [[ -z "${KAGGLE_KEY:-}" ]]; then
  echo "Error: KAGGLE_USERNAME or KAGGLE_KEY is not set. Add them to .env or export them."
  exit 1
fi

kaggle competitions submit -c playground-series-s6e2 -f "$SUB_FILE" -m "$MSG"
echo "Submitted: $SUB_FILE"
