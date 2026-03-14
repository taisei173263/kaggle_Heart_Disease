# 勝ちパイプライン（S6E2 Heart Disease）

Public/Private で安定して高い ROC-AUC を狙う再現性の高い学習パイプラインです。  
**既存のフォルダ構造とジョブスクリプトに合わせてあります。**

## フォルダ構造（既存のまま）

- **`data/raw/`** … 入力（train.csv, test.csv, sample_submission.csv）
- **`data/processed/`** … 前処理済みデータ
- **`data/output/`** … 提出用 CSV（submission.csv 等）
- **`models/`** … 学習済みモデル・OOF/test 予測（oof_*.npy, test_*.npy）
- **`logs/`** … ジョブログ（SGE 用）

Docker 内ではデータは `/data/datasets/raw`（ホストの `~/kaggle_data/datasets/raw`）にマウントされ、プロジェクトは `/workspace` にマウントされます。

## 実行手順（ジョブスクリプトを使う）

学習・推論は **既存の `scripts/submit_job.sh`** で投入します。プロジェクトルートで実行してください。

### 1. 学習（LR）

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
mkdir -p logs
qsub scripts/submit_job.sh python -m src.train --seed 42 --folds 5 --model lr --lr_recipe te --lr_scale minmax
```

### 2. 学習（GBDT）

```bash
qsub scripts/submit_job.sh python -m src.train --seed 42 --folds 5 --model gbdt
```

### 3. ジョブ確認・ログ

```bash
qstat
tail -f logs/kaggle-run.o<ジョブID>
```

### 4. 推論・提出ファイル生成

学習が終わったら、**同じ Docker 環境で**（計算ノードで `docker compose run` するか、ローカルで）推論を実行します。

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
python -m src.predict --checkpoint models --model lr
# → data/output/submission.csv が生成される
```

### 5. アンサンブル（LR と GBDT の OOF が揃っている場合）

```bash
python -m src.ensemble
# → data/output/submission_ensemble_mean.csv, submission_ensemble_rank.csv, submission_ensemble_optimized.csv
```

### 6. Kaggle に提出

既存の提出スクリプトを使います。

```bash
./scripts/submit.sh data/output/submission.csv "LR TE v1"
```

## ローカルで試す場合（Docker 外）

データが `data/raw/` にあるとき:

```bash
python -m src.train --seed 42 --folds 5 --model lr
python -m src.predict --checkpoint models --model lr
```

Docker 内でデータが `/data/datasets/raw` のときは、`submit_job.sh` がコンテナ内で `DATA_DIR=/data/datasets/raw` になるよう環境に依存します（docker-compose の `environment` で `DATA_DIR` を渡すか、スクリプト内で export する運用で対応）。

## 出力の場所（既存構造に合わせた）

| 内容 | 保存先 |
|------|--------|
| OOF 予測 | `models/oof_{model}.npy` |
| テスト予測 | `models/test_{model}.npy` |
| 提出 CSV | `data/output/submission_{model}.csv`, `data/output/submission.csv` |
| アンサンブル提出 | `data/output/submission_ensemble_*.csv` |

## CLI オプション（train）

| オプション | 説明 | デフォルト |
|-----------|------|------------|
| `--seed` | 乱数シード | 42 |
| `--folds` | CV 分割数 | 5 |
| `--model` | lr / gbdt / realmlp | lr |
| `--extended_strat` | extended strat で層化 | False |
| `--use_log1p_st` | ST depression を log1p | False |
| `--use_ekg_merge` | EKG 1→2 マージ | False |
| `--use_winsorize` | BP/Cholesterol 両端 1% カット | False |
| `--use_interactions` | 交互作用特徴追加 | False |
| `--lr_recipe` | te / onehot / onehot_freq | te |
| `--lr_solver` | lbfgs / saga | lbfgs |
| `--lr_scale` | minmax / standard | minmax |
| `--lr_C` | 正則化強度 | 1.0 |

## 想定スコアレンジ

- **LR 単体（TE + MinMax）**: OOF AUC >= 0.9550 を目標
- **GBDT 単体**: OOF AUC >= 0.9555 を目標
- **アンサンブル**: 単体 max を上回る（+0.0001 でも可）

## よくある落とし穴

1. **リーク**: ターゲット統計は必ず fold 内で fit し、val/test にのみ transform。全 train で fit すると LB が崩れる。
2. **型**: カラム名にスペースあり（`Chest pain type`, `Heart Disease` 等）。数値っぽい低カーディナリティ列はモデルごとにカテゴリ扱いを検討。
3. **欠損埋め**: TE の unseen は global_mean / global_median / 0 で明示的に埋める。
4. **フリップラベル**: 「ノイズ行を削除して CV を 0.999 にする」は LB 崩壊の元。データ掃除は禁止。正則化（LR の C、GBDT の min_child_samples / reg_*）で過信を抑える。
