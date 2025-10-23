"""ユーザープロファイル取得ツール。"""

import os
from pathlib import Path
from typing import Any, Optional

import duckdb

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserProfileTool(BaseTool):
    """ユーザープロファイル情報を取得するツール。"""

    def __init__(self, username: Optional[str] = None) -> None:
        """ユーザープロファイル取得ツールを初期化する。

        Args:
            username: ログイン中のユーザー名（セッション情報から取得）
        """
        self.project_root = Path(__file__).parent.parent.parent.parent
        # 環境変数からファイル名を取得（デフォルト: narrative_data.csv）
        narrative_file_name = os.getenv("NARRATIVE_DATA_FILE", "narrative_data.csv")
        self.narrative_file = self.project_root / "input" / narrative_file_name
        self.username = username

    @property
    def name(self) -> str:
        """ツール名。"""
        return "get_user_profile"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """get_user_profile: 対話中のユーザーの嗜好情報を取得します。

【用途】
このツールは、ユーザーの好みや興味、属性を理解し、パーソナライズされた提案を行うために使用します。

【重要な制約とガイドライン】
- **パラメータなしで呼び出してください**（ログイン中のユーザーのプロファイルを自動取得します）
- 1つのユーザーデータのみを取得できます
- 複数ユーザーの横断検索や一覧取得はできません
- **取得したプロファイル情報（嗜好、行動履歴など）をユーザーに直接言及しないでください**
  例: NG「クリオロをよく使っているね」「26回も訪問しているね」
  例: OK「高品質なチョコレートが楽しめる○○店はいかがですか？」
- 嗜好情報は内部的にレコメンドの参考にするのみで、ユーザーには自然な提案として伝えてください

【入力パラメータ】
- なし（ログイン中のユーザー情報を自動取得）

【取得できる情報】
- username: ユーザー名
- profile_id: プロファイルID
- age: 年齢
- gender: 性別
- preferences: ユーザーの嗜好・興味（テキスト）

【使用例】
1. 好みに合った店を提案する場合:
   get_user_profile()
   → preferencesから「高品質なチョコレートや洋菓子が好き」を確認
   → 高級洋菓子店や専門店を提案
   → ユーザーへは「高品質なチョコレートが楽しめる○○店はいかがですか？」と自然に提案

2. 新しい店を提案する場合:
   get_user_profile()
   → preferencesから「和カフェやスペシャルティコーヒーにも興味がある」を確認
   → 和カフェやコーヒー専門店を提案
   → ユーザーへは「和カフェの○○店もおすすめです」と自然に提案

3. 属性（年齢・性別）を加味した提案:
   get_user_profile()
   → age（28歳）、gender（女性）を確認
   → 年齢・性別に適したギフトカテゴリを提案

【返り値】
- 成功時: ユーザー情報を含む辞書
- エラー時: {"error": "エラーメッセージ"}
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """ユーザープロファイル情報を取得する。

        Args:
            なし（ログイン中のユーザー情報を自動取得）

        Returns:
            ユーザー情報の辞書（username, profile_id, age, gender, preferences）
            エラー時は {"error": "エラーメッセージ"}
        """
        # usernameが設定されていない場合はエラー
        if not self.username:
            return {"error": "ログイン情報が見つかりません。ログインしてください。"}

        try:
            # usernameを使ってナラティブデータを取得
            result = self._fetch_user_profile_by_username()

            if not result:
                error_msg = f"ユーザー情報が見つかりません: {self.username}"
                logger.warning(error_msg)
                return {"error": error_msg}

            logger.info(f"Successfully fetched profile for user: {self.username}")
            return result

        except Exception as e:
            error_msg = f"プロファイル情報の取得に失敗しました: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def _fetch_user_profile(self, profile_id: str) -> dict[str, Any]:
        """DuckDBを使用してCSVからユーザープロファイルを取得する。

        Args:
            profile_id: ユーザープロファイルID

        Returns:
            ユーザー情報の辞書（1件のみ）、見つからない場合は空辞書

        Raises:
            Exception: ファイル読み込みやクエリ実行時のエラー
        """
        con = None
        try:
            # インメモリDuckDBコネクション作成
            con = duckdb.connect()

            # CSVファイルからprofile_idとusernameで検索（1件のみ取得）
            # Note: ファイルパスはf-stringだが、パラメータはプレースホルダ化されている
            # ためSQLインジェクションのリスクはない
            if self.username:
                # usernameが指定されている場合、ログインユーザーのデータのみ取得
                query = f"""
                    SELECT *
                    FROM read_csv_auto('{self.narrative_file}')
                    WHERE profile_id = ? AND username = ?
                    LIMIT 1
                """  # noqa: S608
                params = [profile_id, self.username]
            else:
                # usernameが指定されていない場合、profile_idのみで検索（後方互換性）
                query = f"""
                    SELECT *
                    FROM read_csv_auto('{self.narrative_file}')
                    WHERE profile_id = ?
                    LIMIT 1
                """  # noqa: S608
                params = [profile_id]

            result = con.execute(query, params).fetchall()
            columns = [desc[0] for desc in con.description] if con.description else []

            # 結果が0件の場合は空辞書を返す
            if len(result) == 0:
                return {}

            # 結果を辞書に変換
            row = result[0]
            row_dict: dict[str, Any] = {}
            for i, column in enumerate(columns):
                value = row[i]
                # datetimeオブジェクトを文字列に変換
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                row_dict[column] = value

            return row_dict

        finally:
            # コネクションをクローズ
            if con:
                con.close()

    def _fetch_user_profile_by_username(self) -> dict[str, Any]:
        """usernameを使ってCSVからユーザープロファイルを取得する。

        Returns:
            ユーザー情報の辞書（1件のみ）、見つからない場合は空辞書

        Raises:
            Exception: ファイル読み込みやクエリ実行時のエラー
        """
        con = None
        try:
            # インメモリDuckDBコネクション作成
            con = duckdb.connect()

            # CSVファイルからusernameで検索（1件のみ取得）
            query = f"""
                SELECT *
                FROM read_csv_auto('{self.narrative_file}')
                WHERE username = ?
                LIMIT 1
            """  # noqa: S608

            result = con.execute(query, [self.username]).fetchall()
            columns = [desc[0] for desc in con.description] if con.description else []

            # 結果が0件の場合は空辞書を返す
            if len(result) == 0:
                return {}

            # 結果を辞書に変換
            row = result[0]
            row_dict: dict[str, Any] = {}
            for i, column in enumerate(columns):
                value = row[i]
                # datetimeオブジェクトを文字列に変換
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                row_dict[column] = value

            return row_dict

        finally:
            # コネクションをクローズ
            if con:
                con.close()
