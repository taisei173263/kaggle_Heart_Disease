# データ共有ガイド

環境構築（GitHub からクローン済み）のあと、**プロジェクトの `data` フォルダ**からコンペ用データを参照する方法です。

---

## 📍 参照元の場所

```
/home/taisei/kaggle/competitions/kaggle-s6e2-heart/data
```

このディレクトリに置いたデータを、他のメンバーが各自の環境から参照します。

**中身の想定:**
- `data/raw/` … 元データ（train.csv, test.csv, sample_submission.csv）
- `data/processed/` … 前処理済みデータ（任意）
- `data/output/` … 提出用ファイルなど（任意）

---

## 👤 役割ごとの手順

### データを置く人（1人でOK・例: taisei）

データを **1回だけ** ダウンロードして、上記 `data` に置き、他ユーザーが読めるようにします。

#### Step 1: データをダウンロードして `data` に置く

```bash
cd /home/taisei/kaggle/competitions/kaggle-s6e2-heart

# Kaggle からダウンロード
kaggle competitions download -c playground-series-s6e2

# 解凍して data/raw に入れる
unzip -o playground-series-s6e2.zip -d data/raw/

# 中身の確認
ls data/raw/
# train.csv  test.csv  sample_submission.csv が並んでいればOK
```

#### Step 2: 他のユーザーが読めるように権限を開ける

```bash
# 自分のホームを「通過」できるように（中身の一覧は見せない）
chmod o+x /home/taisei

# このプロジェクトの data 以下を、他ユーザーが読めるようにする
chmod -R o+rX /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data

# 確認（others に r-x が付いていればOK）
ls -ld /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data
ls -ld /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw
```

これで、**フルパスを知っている人**が `data/raw` や `data/processed` を参照できる状態になります。

---

### データを参照する人（他のメンバー）

自分用のデータ置き場（`~/kaggle_data`）から、**上記の data フォルダ**を参照するだけです。

#### Step 1: 参照用のシンボリックリンクを張る

```bash
# データ置き場を作成
mkdir -p ~/kaggle_data/datasets
cd ~/kaggle_data/datasets

# 参照元: /home/taisei/.../data の raw / processed をリンク
ln -sf /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw   raw
ln -sf /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/processed processed

# 張れたか確認
ls -la
# raw -> /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw
# processed -> /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/processed

# 中身が見えるか確認
ls raw/
# train.csv  test.csv  sample_submission.csv
```

#### Step 2: Docker でそのまま使う

このプロジェクトでは `~/kaggle_data` がコンテナ内の `/data` にマウントされるので、**追加設定は不要**です。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose up -d
```

コンテナ内では次のパスで参照できます。

- `/data/datasets/raw/train.csv`
- `/data/datasets/raw/test.csv`
- `/data/datasets/processed/`（中身を置いている場合）

**確認例:**

```bash
docker compose exec kaggle ls /data/datasets/raw/
# train.csv  test.csv  sample_submission.csv
```

---

## 📊 全体の流れ（図）

```
[データを置く人]
  Kaggle から DL → /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw/
                    + chmod で他ユーザーに読めるようにする

[参照する人]
  ~/kaggle_data/datasets/raw   → シンボリックリンク → 上記 data/raw
  ~/kaggle_data/datasets/processed → シンボリックリンク → 上記 data/processed

  Docker 起動 → コンテナ内の /data/datasets/raw, /data/datasets/processed から同じデータを参照
```

---

## 🔧 よくあるトラブル

### 参照する人: 「Permission denied」や中身が見えない

**原因:** データを置いた側で `chmod` がまだか、パスが違う。

**データを置いた人が実行:**

```bash
chmod o+x /home/taisei
chmod -R o+rX /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data
```

**参照する人が確認:**

```bash
# このパスで一覧が出ればOK
ls /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw/
```

---

### 参照する人: シンボリックリンクが「壊れている」と出る

**確認:**

```bash
ls -la ~/kaggle_data/datasets/raw
```

`raw -> ...` の先のパスが正しいか確認し、間違っていれば作り直します。

```bash
rm ~/kaggle_data/datasets/raw ~/kaggle_data/datasets/processed
ln -sf /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/raw   ~/kaggle_data/datasets/raw
ln -sf /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/processed ~/kaggle_data/datasets/processed
```

---

### Docker の中でファイルが見えない

1. **ホストで** `~/kaggle_data/datasets/raw/` に `train.csv` などが見えているか確認。
2. 見えていれば、コンテナをやり直す。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart/docker
docker compose down
docker compose up -d
```

---

## 📁 前処理済みデータを共有する場合

データを置く人が前処理結果も `data` に入れておけば、同じリンクで参照できます。

**データを置く人:**

```bash
# 例: 前処理の出力を data/processed にコピー
cp どこか/train_processed.csv /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data/processed/

# 権限はすでに data 全体に o+rX しているので追加の chmod は不要
```

**参照する人:**  
すでに `processed` へのシンボリックリンクを張っていれば、そのまま `~/kaggle_data/datasets/processed/` から参照できます。

---

## 🔐 注意（データを置く人）

- `chmod o+x /home/taisei` は「ホームを通過すること」だけ許可しており、`ls /home/taisei` では中身は見えません。
- 見せているのは **kaggle-s6e2-heart/data 以下だけ**です。それ以外のファイルは、この設定だけでは他ユーザーからは読めません。
- 共有をやめたいときは、次のように戻せます。

```bash
chmod o-x /home/taisei
chmod -R o-rX /home/taisei/kaggle/competitions/kaggle-s6e2-heart/data
```

---

## 📚 関連ドキュメント

- `SETUP_SUMMARY.md` … 初回環境構築
- `TEAM_GUIDE.md` … チーム運用
- `README.md` … プロジェクト概要
