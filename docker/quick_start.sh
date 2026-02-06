#!/usr/bin/env bash
# クイックスタートスクリプト（初回セットアップ用）
# 使い方: ./docker/quick_start.sh

set -e

echo "=========================================="
echo "Kaggle S6E2 - クイックスタート"
echo "=========================================="
echo ""

# プロジェクトルートに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 色付き出力
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}[1/4]${NC} セットアップ確認中..."
./docker/setup_check.sh

echo ""
echo -e "${GREEN}[2/4]${NC} Dockerイメージの準備"
echo ""

# イメージが既に存在するか確認
if docker images | grep -q "kaggle-s6e2-heart"; then
    echo "✓ kaggle-s6e2-heart イメージが見つかりました"
else
    echo "イメージが見つかりません。以下のいずれかを選択してください:"
    echo ""
    echo "  1) 共有ストレージからロード（推奨・高速: 1〜2分）"
    echo "  2) ローカルでビルド（初回のみ: 10〜15分）"
    echo ""
    read -p "選択 [1/2]: " choice
    
    case $choice in
        1)
            SHARED_IMAGE="/data1/share/kaggle-zemi/kaggle-s6e2-heart.tar.gz"
            if [ -f "$SHARED_IMAGE" ]; then
                echo "共有イメージをロード中..."
                docker load < "$SHARED_IMAGE"
                echo "✓ ロード完了"
            else
                echo "エラー: 共有イメージが見つかりません: $SHARED_IMAGE"
                echo "管理者に確認してください"
                exit 1
            fi
            ;;
        2)
            echo "イメージをビルド中（10〜15分かかります）..."
            cd docker
            docker compose build
            cd ..
            echo "✓ ビルド完了"
            ;;
        *)
            echo "無効な選択です"
            exit 1
            ;;
    esac
fi

echo ""
echo -e "${GREEN}[3/4]${NC} UID/GID の設定"
echo ""

USER_ID=$(id -u)
GROUP_ID=$(id -g)

if [ "$USER_ID" != "1000" ] || [ "$GROUP_ID" != "1000" ]; then
    echo "あなたのUID/GID: $USER_ID:$GROUP_ID"
    echo ".env ファイルを作成します..."
    
    cat << EOF > .env
USER_ID=$USER_ID
GROUP_ID=$GROUP_ID
EOF
    
    echo "✓ .env ファイルを作成しました"
else
    echo "✓ デフォルト値（1000:1000）を使用します"
fi

echo ""
echo -e "${GREEN}[4/4]${NC} コンテナの起動"
echo ""

cd docker
docker compose up -d

echo ""
echo "=========================================="
echo "セットアップ完了！"
echo "=========================================="
echo ""
echo "JupyterLabにアクセス:"
echo "  http://$(hostname -I | awk '{print $1}'):8888"
echo ""
echo "コンテナ内でbashを使う:"
echo "  cd ~/kaggle-s6e2-heart/docker"
echo "  docker compose exec app bash"
echo ""
echo "コンテナを停止:"
echo "  cd ~/kaggle-s6e2-heart/docker"
echo "  docker compose down"
echo ""
