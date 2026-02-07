# Kaggle S6E2 Heart - 分析環境（GPU対応・日本語対応）
# Base: Kaggle公式Dockerイメージ（全てのライブラリがプリインストール済み）
# ⚠️ 注意: このイメージは展開後 20GB〜40GB になります
FROM gcr.io/kaggle-images/python:latest

# 作業ディレクトリ
WORKDIR /workspace

# 環境変数: Pythonのバッファリング無効化、日本語ロケール設定
ENV PYTHONUNBUFFERED=1 \
    LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:ja \
    LC_ALL=ja_JP.UTF-8

# 日本語フォントのインストール（matplotlib等での文字化け防止）
# Kaggle公式イメージにはフォントが含まれていないため追加
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-ipaexfont \
    fonts-ipafont \
    locales \
    && locale-gen ja_JP.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# matplotlib日本語フォント設定（IPAexゴシックを使用）
# システム全体の設定として /etc/matplotlib に配置（全ユーザーで有効）
RUN mkdir -p /etc/matplotlib && \
    echo "font.family : IPAexGothic" > /etc/matplotlib/matplotlibrc && \
    # フォントキャッシュをクリア（初回起動時の再構築を促す）
    rm -rf /root/.cache/matplotlib

# 追加のPython依存関係（Kaggle公式イメージに含まれないもののみ）
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# UID/GID設定用のスクリプト（docker-composeで上書き可能）
# デフォルトはroot（1000:1000で起動する場合はdocker-compose.ymlで指定）
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN if [ ${USER_ID} -ne 0 ]; then \
        groupadd -g ${GROUP_ID} kaggle || true && \
        useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash kaggle && \
        chown -R kaggle:kaggle /workspace; \
    fi

# デフォルトユーザー（docker-compose.ymlで上書き可能）
USER ${USER_ID}:${GROUP_ID}

# JupyterLab起動用のデフォルトコマンド（docker-compose.ymlで上書き可能）
CMD ["bash"]
