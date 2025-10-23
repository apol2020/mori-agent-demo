# 認証設定ファイル

このディレクトリには認証に必要な設定ファイルが含まれます。

## セットアップ手順

1. **ユーザー情報ファイルの作成**
   ```bash
   cp user_info.csv.example user_info.csv
   ```

   `user_info.csv` を編集して実際のユーザー情報を追加してください。
   形式：
   ```
   id,name,password,email
   USER001,username,plaintext_password,user@example.com
   ```

2. **設定ファイルの作成**
   ```bash
   cp config.yaml.example config.yaml
   ```

   `config.yaml` の `cookie.key` を変更してください（ランダムな文字列を推奨）。

3. **パスワードのハッシュ化**
   ```bash
   python src/utils/create_yaml.py
   ```

   このスクリプトは：
   - `user_info.csv` からユーザー情報を読み込み
   - パスワードをハッシュ化
   - `config.yaml` に認証情報を書き込み

## 重要な注意事項

⚠️ **セキュリティ**
- `config.yaml` と `user_info.csv` には機密情報が含まれます
- これらのファイルは `.gitignore` に追加済みで、Git にコミットされません
- 本番環境では必ず強力なパスワードと cookie キーを使用してください
- `cookie.key` は推測困難なランダムな文字列に変更してください

## ファイル一覧

- `config.yaml` - 認証設定ファイル（Git管理対象外）
- `user_info.csv` - ユーザー情報（Git管理対象外）
- `config.yaml.example` - 設定ファイルのサンプル
- `user_info.csv.example` - ユーザー情報ファイルのサンプル
