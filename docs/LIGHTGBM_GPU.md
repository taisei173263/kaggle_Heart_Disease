# LightGBM を GPU で動かすために（現状まとめ）

## 現象

`device='gpu'` で実行すると次のエラーで落ちる:

```
lightgbm.basic.LightGBMError: No OpenCL device found
```

## 原因

- LightGBM の **標準 GPU 版** は **OpenCL** を使う（CUDA ではない）。
- `pip install lightgbm` で入るバイナリは **CPU 用** か、GPU 対応していても実行時に **OpenCL ランタイム** を要求する。
- Docker 内（PyTorch 公式イメージ）には **NVIDIA ドライバと CUDA** はあるが、**OpenCL 用の ICD（NVIDIA OpenCL）** が入っていない、またはコンテナから見えていない可能性が高い。

## 解決の方向性（2通り）

### 方法1: OpenCL をコンテナに入れて `device='gpu'` を使う

- ホスト／コンテナに **NVIDIA 用 OpenCL** を入れる。
- 例（Ubuntu）: `nvidia-opencl-icd`, `nvidia-opencl-dev`, `opencl-headers` などをインストール。
- 参考: [LightGBM GPU Tutorial](https://lightgbm.readthedocs.io/en/latest/GPU-Tutorial.html) では `nvidia-opencl-icd-375`, `nvidia-opencl-dev`, `opencl-headers` を入れている。
- CUDA を入れているだけでは不十分で、**OpenCL 用のライブラリとランタイム** が別途必要。

**Dockerfile で試す例（要検証）:**

```dockerfile
# PyTorch ベースのあとで
RUN apt-get update && apt-get install -y --no-install-recommends \
    ocl-icd-libopencl1 \
    ocl-icd-opencl-dev \
    opencl-headers \
    && rm -rf /var/lib/apt/lists/*
# NVIDIA の OpenCL は CUDA に含まれる場合あり。ベースイメージに CUDA があれば
# OpenCL の .so が /usr/local/cuda/lib64/libOpenCL.so などにあることがある。
# その場合は icd の設定が必要な場合あり。
```

- その後、LightGBM を **ソースから** `-DUSE_GPU=ON` でビルドし直す必要がある（pip のバイナリは OpenCL 対応していないことが多い）。
- 参考: [LightGBM Installation Guide - Build GPU Version (Linux)](https://lightgbm.readthedocs.io/en/latest/Installation-Guide.html#build-gpu-version)

---

### 方法2: LightGBM を CUDA 版でビルドして `device='cuda'` を使う（推奨）

- LightGBM には **OpenCL 版**（`device_type=gpu`）とは別に **CUDA 版**（`device_type=cuda`）がある。
- Linux ＋ NVIDIA GPU（Compute Capability 6.0 以上）向け。
- 参考: [LightGBM Installation Guide - Build CUDA Version](https://lightgbm.readthedocs.io/en/latest/Installation-Guide.html#build-cuda-version)

**手順の流れ:**

1. **Dockerfile で LightGBM をソースからビルド**
   - ベースイメージ: 現在の `pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime` のまま（CUDA は既に入っている）。
   - 依存: CMake, gcc, CUDA（ベースに含まれる想定）。

   ```dockerfile
   # LightGBM を CUDA でビルドしてインストール
   RUN pip uninstall -y lightgbm 2>/dev/null || true
   RUN git clone --recursive https://github.com/microsoft/LightGBM /tmp/LightGBM \
       && cd /tmp/LightGBM \
       && cmake -B build -S . -DUSE_CUDA=ON \
       && cmake --build build -j$(nproc) \
       && cd python-package && pip install . -e --no-build-isolation \
       && cd / && rm -rf /tmp/LightGBM
   ```
   （実際には `python-package` のインストール方法は [LightGBM python-package](https://github.com/microsoft/LightGBM/tree/master/python-package) を確認し、CUDA ビルド済みの lib を指すようにする必要があります。）

2. **Python 側**
   - パラメータで **`device='cuda'`** を指定する（`device='gpu'` は OpenCL 用）。

   ```python
   params = {
       ...
       "device": "cuda",  # CUDA ビルド時のみ。OpenCL 版は "gpu"
       ...
   }
   ```

- 注意: pip の `lightgbm` は **CUDA 版を配布していない** ため、**必ずソースから `-DUSE_CUDA=ON` でビルド**する必要がある。

---

## 現在の実装状態

### ✅ 対応済み: CUDA 版をビルド

- **Dockerfile** で LightGBM を **`-DUSE_CUDA=1`** でソースビルドし、Python パッケージをインストール済み。
- **ベースイメージ** を `runtime` から **`devel`** に変更（nvcc コンパイラが必要なため）。
- **`src/train.py`** はデフォルトで **`device='cuda'`** を使用（環境変数 `LGBM_DEVICE=cpu` で CPU に切替可能）。

### 使い方

**GPU で学習（デフォルト）:**

```bash
qsub scripts/submit_job.sh src/train.py
```

**CPU で学習（環境変数で切替）:**

```bash
# docker-compose.yml の environment に追加するか、ジョブスクリプト内で export
export LGBM_DEVICE=cpu
qsub scripts/submit_job.sh src/train.py
```

### ビルド後の確認

ジョブのログに次のような表示が出れば、CUDA 版が動作しています:

```
[LightGBM] [Info] This is the GPU trainer!!
[LightGBM] [Info] Total Bins 3393
[LightGBM] [Info] Number of data points in the train set: 504000, number of used features: 13
```

## 参考リンク

- [LightGBM GPU Tutorial](https://lightgbm.readthedocs.io/en/latest/GPU-Tutorial.html)
- [LightGBM Installation Guide - Build GPU Version (OpenCL)](https://lightgbm.readthedocs.io/en/latest/Installation-Guide.html#build-gpu-version)
- [LightGBM Installation Guide - Build CUDA Version](https://lightgbm.readthedocs.io/en/latest/Installation-Guide.html#build-cuda-version)
- [LightGBM GPU Docker (公式)](https://github.com/microsoft/LightGBM/tree/master/docker/gpu)
- [Issue #4497: LightGBMError: No OpenCL device found](https://github.com/microsoft/LightGBM/issues/4497)
