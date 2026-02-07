import sys
import os
import pandas as pd
import torch

print("=== 環境チェック開始 ===")

# 1. データ読み込みテスト
data_path = '/data/datasets/raw/train.csv'
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    print(f"✅ データ読み込み成功: {data_path}")
    print(f"   データ形状: {df.shape}")
else:
    print(f"❌ データが見つかりません: {data_path}")

# 2. GPU認識テスト
if torch.cuda.is_available():
    print(f"✅ GPU認識成功: {torch.cuda.get_device_name(0)}")
else:
    print("❌ GPUが見つかりません (CPUモード)")

# 3. 書き込みテスト
output_path = '/data/working/test_output.txt'
try:
    with open(output_path, 'w') as f:
        f.write("書き込みテストOK")
    print(f"✅ 書き込みテスト成功: {output_path}")
except Exception as e:
    print(f"❌ 書き込み失敗: {e}")

print("=== 環境チェック終了 ===")