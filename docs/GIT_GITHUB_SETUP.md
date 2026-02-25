# Git / GitHub 初期設定ガイド

このドキュメントは、**GitHub に push する前**に一度だけ行う Git と GitHub の初期設定をまとめたものです。

---

## 📋 必要な設定の一覧

| 項目 | 内容 | 必要なタイミング |
|------|------|------------------|
| Git のユーザー名・メール | コミットの「作者」として記録される | 初回コミット前 |
| リモートの登録 | `origin` に GitHub の URL を設定 | clone した場合は済んでいることが多い |
| GitHub 認証 | push 時に本人確認 | 初回 push 前 |

---

## 1. Git の基本設定（初回のみ）

コミット時に「誰がコミットしたか」が記録されます。**一度設定すればそのマシンではずっと有効**です。

### 1-1. ユーザー名とメールの設定

```bash
# グローバルに設定（このマシンで行うすべての Git 操作に適用）
git config --global user.name "あなたの名前"
git config --global user.email "GitHubに登録しているメールアドレス"
```

**例:**

```bash
git config --global user.name "Taisei Yamada"
git config --global user.email "taisei@example.com"
```

**補足:**
- GitHub のメールは [Settings → Emails](https://github.com/settings/emails) で確認できます。
- プライバシー設定で「メールを非公開」にしている場合は、GitHub が発行する `username@users.noreply.github.com` 形式のアドレスを使うとよいです。

### 1-2. 設定の確認

```bash
git config --global user.name
git config --global user.email
```

---

## 2. リモートの確認・追加

GitHub のリポジトリを「どこに push するか」を指定するのがリモートです。

### 2-1. すでにリモートがあるか確認

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart   # プロジェクトのルートへ
git remote -v
```

**出力例:**

```
origin  https://github.com/taisei173263/kaggle_Heart_Disease.git (fetch)
origin  https://github.com/taisei173263/kaggle_Heart_Disease.git (push)
```

`origin` が表示されていれば、**clone 時にすでに設定済み**です。追加の作業は不要です。

### 2-2. リモートがない場合（手動で clone したなど）

```bash
git remote add origin https://github.com/taisei173263/kaggle_Heart_Disease.git
```

---

## 3. GitHub への push 認証

push するとき、GitHub が「本人か」を確認するため、**認証**が必要です。方法は主に **HTTPS** と **SSH** の2通りです。

### 方法A: HTTPS + Personal Access Token（PAT）（推奨・手軽）

#### Step 1: Personal Access Token の作成

1. [GitHub](https://github.com/) にログイン
2. 右上のアイコン → **Settings**
3. 左メニュー最下部の **Developer settings** → **Personal access tokens** → **Tokens (classic)** または **Fine-grained tokens**
4. **Generate new token** をクリック
5. **Note** に用途（例: `kaggle-heart push`）を入力
6. **Expiration** で有効期限を選択（例: 90 days または No expiration）
7. **Select scopes** で **repo** にチェック（リポジトリの読み書き）
8. **Generate token** をクリック
9. 表示されたトークン（`ghp_xxxx...` など）を **必ずコピーして安全な場所に保存**（再表示されません）

#### Step 2: push 時にトークンを使う

```bash
git push origin main
```

**Username:** GitHub のユーザー名  
**Password:** ここには **通常のパスワードではなく、先ほど作成した Personal Access Token を入力**します。

#### Step 3:  credential を保存する（毎回入力しないようにする）

初回 push でトークンを入力したあと、「認証情報を保存しますか？」と聞かれたら **保存**を選ぶと、次回以降は入力不要になります。

手動で credential を保存する場合（例: Linux）:

```bash
# キャッシュで一定時間記憶（例: 1時間 = 3600秒）
git config --global credential.helper 'cache --timeout=3600'

# または永続的に保存（平文で ~/.git-credentials に保存されるので注意）
git config --global credential.helper store
```

---

### 方法B: SSH キーを使う（サーバーで長く使う場合向け）

#### Step 1: SSH キーの生成

```bash
# メールは GitHub に登録しているアドレス
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519_github -N ""
```

`-N ""` でパスフレーズなしにしています。セキュリティを重視する場合はパスフレーズを設定してください。

#### Step 2: 公開鍵を GitHub に登録

```bash
# 公開鍵を表示（この内容をコピー）
cat ~/.ssh/id_ed25519_github.pub
```

1. GitHub → **Settings** → **SSH and GPG keys** → **New SSH key**
2. **Title** に識別用の名前（例: `Turbo server`）
3. **Key** にコピーした公開鍵を貼り付け → **Add SSH key**

#### Step 3: リモートを SSH に切り替える

```bash
cd ~/kaggle/competitions/kaggle-s6e2-heart
git remote set-url origin git@github.com:taisei173263/kaggle_Heart_Disease.git
git remote -v
# origin  git@github.com:taisei173263/kaggle_Heart_Disease.git (fetch)
# origin  git@github.com:taisei173263/kaggle_Heart_Disease.git (push)
```

#### Step 4: 接続テスト

```bash
ssh -T git@github.com
# Hi taisei173263! You've successfully authenticated...
```

表示されれば、以降は `git push origin main` でトークン入力なしに push できます。

---

## 4. 初回 push の流れ（まとめ）

1. **Git の基本設定**（未設定なら）
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your_email@example.com"
   ```

2. **リモートの確認**
   ```bash
   git remote -v
   ```
   `origin` がなければ `git remote add origin https://github.com/taisei173263/kaggle_Heart_Disease.git`

3. **変更をコミット**
   ```bash
   git add .
   git commit -m "メッセージ"
   ```

4. **push**（初回は認証が求められる）
   ```bash
   git push origin main
   ```
   - HTTPS の場合: ユーザー名 + **Personal Access Token** を入力
   - SSH の場合はそのまま完了

---

## 🔧 トラブルシューティング

### 「Permission denied」や「Authentication failed」

- **HTTPS:** パスワード欄に **GitHub のログイン用パスワードではなく、Personal Access Token** を入力しているか確認。
- **SSH:** `ssh -T git@github.com` で認証できるか確認。失敗する場合は公開鍵が GitHub に登録されているか、`git remote -v` で SSH URL になっているか確認。

### 「Support for password authentication was removed」

GitHub は通常のパスワードでの push を廃止しています。**Personal Access Token（HTTPS）** または **SSH キー** のどちらかで認証してください。

### コミット時の「your name and email were configured automatically」

`user.name` と `user.email` が未設定のため、ホスト名などから自動で補われています。  
正しい名前・メールで記録したい場合は、本文の「1. Git の基本設定」を実行してください。

---

## 📚 関連ドキュメント

- [GitHub - 認証について](https://docs.github.com/ja/authentication)
- [Personal Access Token の作成](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [SSH キーで GitHub に接続](https://docs.github.com/ja/authentication/connecting-to-github-with-ssh)
- このプロジェクト: `SETUP_SUMMARY.md`（リポジトリのクローン〜Kaggle まわり）
