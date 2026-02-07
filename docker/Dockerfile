# Kaggle S6E2 Heart - 分析環境（GPU対応・日本語対応）
# Base: PyTorch公式イメージ（CUDA 12.1 + Python 3.10）
# devel版: nvcc等のCUDAコンパイラが必要（LightGBM CUDA版ビルドのため）
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel

# 作業ディレクトリ
WORKDIR /workspace

# 環境変数: Pythonのバッファリング無効化、日本語ロケール設定
ENV PYTHONUNBUFFERED=1 \
    LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:ja \
    LC_ALL=ja_JP.UTF-8

# システムパッケージのインストール
# - build-essential: C/C++コンパイラ（LightGBM等のビルドに必要）
# - cmake: LightGBM CUDA版ビルドに必要
# - git: バージョン管理
# - fonts-ipaexfont: 日本語フォント（matplotlib等での文字化け防止）
# - locales: ロケール設定
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
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

# LightGBM CUDA版をソースからビルド（pip版はCPUのみのため）
# CUDA 12.1 環境で USE_CUDA=1 でビルドし、Python パッケージをインストール
RUN git clone --recursive https://github.com/microsoft/LightGBM /tmp/LightGBM && \
    cd /tmp/LightGBM && \
    mkdir build && \
    cd build && \
    cmake -DUSE_CUDA=1 -DCMAKE_PREFIX_PATH=/usr/local/cuda .. && \
    make -j$(nproc) && \
    cd ../python-package && \
    python setup.py install && \
    cd / && \
    rm -rf /tmp/LightGBM

# Python依存関係のインストール（lightgbm は上でソースビルド済み）
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

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
