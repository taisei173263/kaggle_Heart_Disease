#!/usr/bin/env bash
# Kaggle に提出する（要: pip install kaggle と Kaggle API 認証）
# 認証: .env の KAGGLE_API_TOKEN または KAGGLE_USERNAME/KAGGLE_KEY または ~/.kaggle/kaggle.json
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

# 認証: KAGGLE_API_TOKEN（新形式）→ KAGGLE_USERNAME/KAGGLE_KEY → ~/.kaggle/kaggle.json
if [[ -z "${KAGGLE_API_TOKEN:-}" ]]; then
  if [[ -z "${KAGGLE_USERNAME:-}" ]] || [[ -z "${KAGGLE_KEY:-}" ]]; then
    if [[ ! -f "$HOME/.kaggle/kaggle.json" ]]; then
      echo "Error: Kaggle 認証がありません。次のいずれかを設定してください:"
      echo "  1) .env に KAGGLE_API_TOKEN=KGAT_... を書く（Kaggle → Account → API で表示されるトークンをコピー）"
      echo "  2) .env に KAGGLE_USERNAME と KAGGLE_KEY を書く（従来の kaggle.json の username/key）"
      echo "  3) ~/.kaggle/kaggle.json を配置する"
      echo "  401 Unauthorized が出る場合: トークンを再発行し、.env を更新してください。"
      exit 1
    fi
  fi
fi

kaggle competitions submit -c playground-series-s6e2 -f "$SUB_FILE" -m "$MSG"
echo "Submitted: $SUB_FILE"
