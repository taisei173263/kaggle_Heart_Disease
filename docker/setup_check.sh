#!/usr/bin/env bash
# Docker環境のセットアップ確認スクリプト
# 使い方: ./docker/setup_check.sh

set -e

echo "=========================================="
echo "Kaggle S6E2 - Docker環境セットアップ確認"
echo "=========================================="
echo ""

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_error() {
    echo -e "${RED}✗${NC} $1"
}

# 1. Docker のインストール確認
echo "[1] Docker のインストール確認"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_ok "Docker がインストールされています: $DOCKER_VERSION"
else
    check_error "Docker がインストールされていません"
    echo "    インストール: https://docs.docker.com/engine/install/"
    exit 1
fi
echo ""

# 2. Docker Compose のインストール確認
echo "[2] Docker Compose のインストール確認"
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    check_ok "Docker Compose がインストールされています: $COMPOSE_VERSION"
else
    check_error "Docker Compose がインストールされていません"
    echo "    Docker 20.10以降に含まれています"
    exit 1
fi
echo ""

# 3. NVIDIA Container Toolkit の確認（GPU利用時）
echo "[3] NVIDIA Container Toolkit の確認（GPU利用時）"
if command -v nvidia-smi &> /dev/null; then
    check_ok "nvidia-smi が利用可能です"
    
    if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        check_ok "NVIDIA Container Toolkit が正しく設定されています"
    else
        check_warn "NVIDIA Container Toolkit が設定されていない可能性があります"
        echo "    インストール: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/"
    fi
else
    check_warn "nvidia-smi が見つかりません（CPU環境の場合は問題ありません）"
fi
echo ""

# 4. kaggle.json の確認
echo "[4] Kaggle API認証情報の確認"
if [ -f "$HOME/.kaggle/kaggle.json" ]; then
    check_ok "kaggle.json が見つかりました: $HOME/.kaggle/kaggle.json"
    
    # パーミッション確認
    PERMS=$(stat -c "%a" "$HOME/.kaggle/kaggle.json" 2>/dev/null || stat -f "%A" "$HOME/.kaggle/kaggle.json" 2>/dev/null)
    if [ "$PERMS" = "600" ]; then
        check_ok "パーミッションが正しく設定されています (600)"
    else
        check_warn "パーミッションが推奨設定ではありません (現在: $PERMS, 推奨: 600)"
        echo "    修正: chmod 600 $HOME/.kaggle/kaggle.json"
    fi
else
    check_error "kaggle.json が見つかりません"
    echo "    作成方法: README.md の「2. Kaggle API認証の設定」を参照"
fi
echo ""

# 5. データ置き場の確認（プランB: ホームの kaggle_data）
echo "[5] データ置き場の確認"
SHARED_DIR="${HOME}/kaggle_data"
if [ -d "$SHARED_DIR" ]; then
    check_ok "データ置き場が見つかりました: $SHARED_DIR"
    
    # 書き込み権限確認
    if [ -w "$SHARED_DIR" ]; then
        check_ok "書き込み権限があります"
    else
        check_warn "書き込み権限がありません"
        echo "    実行: chmod -R 777 $SHARED_DIR"
        echo "    実行: chmod o+x $(dirname $SHARED_DIR)"
    fi
else
    check_warn "データ置き場が見つかりません: $SHARED_DIR"
    echo "    作成: mkdir -p $SHARED_DIR/{datasets/raw,processed,models,outputs,working}"
    echo "    権限: chmod -R 777 $SHARED_DIR"
    echo "    通過: chmod o+x $HOME"
fi
echo ""

# 6. UID/GID の確認
echo "[6] UID/GID の確認"
USER_ID=$(id -u)
GROUP_ID=$(id -g)
echo "    あなたのUID: $USER_ID"
echo "    あなたのGID: $GROUP_ID"

if [ "$USER_ID" = "1000" ] && [ "$GROUP_ID" = "1000" ]; then
    check_ok "デフォルト値（1000:1000）と一致しています"
else
    check_warn "デフォルト値と異なります"
    echo "    .env ファイルに以下を追加してください:"
    echo "    USER_ID=$USER_ID"
    echo "    GROUP_ID=$GROUP_ID"
fi
echo ""

# 7. ポート 8888 の使用状況確認
echo "[7] ポート 8888 の使用状況確認"
if command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":8888 "; then
        check_warn "ポート 8888 は既に使用されています"
        echo "    docker-compose.yml の ports を変更してください（例: 8889:8888）"
    else
        check_ok "ポート 8888 は利用可能です"
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tuln | grep -q ":8888 "; then
        check_warn "ポート 8888 は既に使用されています"
        echo "    docker-compose.yml の ports を変更してください（例: 8889:8888）"
    else
        check_ok "ポート 8888 は利用可能です"
    fi
else
    check_warn "ポート確認ツール（ss/netstat）が見つかりません"
fi
echo ""

# 8. Dockerイメージの確認
echo "[8] Dockerイメージの確認"
if docker images | grep -q "kaggle-s6e2-heart"; then
    check_ok "kaggle-s6e2-heart イメージが存在します"
    echo "    docker compose up -d で起動できます"
else
    check_warn "kaggle-s6e2-heart イメージが見つかりません"
    echo "    以下のいずれかを実行してください:"
    echo "    - docker compose build（ビルド: 10〜15分）"
    echo "    - docker load < /data1/share/kaggle-zemi/kaggle-s6e2-heart.tar.gz（共有イメージから）"
fi
echo ""

# まとめ
echo "=========================================="
echo "確認完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "  1. 問題がある項目を修正してください"
echo "  2. docker compose build（または docker load）"
echo "  3. docker compose up -d"
echo "  4. ブラウザで http://$(hostname -I | awk '{print $1}'):8888 にアクセス"
echo ""
