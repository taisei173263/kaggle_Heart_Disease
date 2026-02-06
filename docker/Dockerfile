# Kaggle S6E2 Heart - 分析環境
FROM python:3.11-slim

WORKDIR /workspace

# システム依存（必要に応じて追加）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# プロジェクトルートをマウントする想定で requirements をコピー
COPY docker/requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

# Jupyter 用（Notebook で作業する場合）
RUN pip install --no-cache-dir jupyter ipykernel

CMD ["bash"]
