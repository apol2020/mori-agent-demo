"""ユーザープロファイル取得ツール。"""

import os
from pathlib import Path
from typing import Any

import duckdb

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserProfileTool(BaseTool):
    """ユーザープロファイル情報を取得するツール。"""

    def __init__(self) -> None:
        """ユーザープロファイル取得ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        # 環境変数からファイル名を取得（デフォルト: narrative_data.csv）
        narrative_file_name = os.getenv("NARRATIVE_DATA_FILE", "narrative_data.csv")
        self.narrative_file = self.project_root / "input" / narrative_file_name

    @property
    def name(self) -> str:
        """ツール名。"""
        return "get_user_profile"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """get_user_profile: 対話中のユーザーのプロファイル情報を取得します。

【用途】
このツールは、対話中のユーザーの属性や行動パターンを理解し、パーソナライズされた提案を行うために使用します。

【重要な制約】
- 1つのユーザーデータのみを取得できます
- 複数ユーザーの横断検索や一覧取得はできません
- profile_idの指定が必須です

【入力パラメータ】
- profile_id (必須): ユーザープロファイルID（例: "user_criollo_heavy"）

【取得できる情報】
- profile_id: ユーザープロファイルID
- age: 年齢
- gender: 性別
- user_type: ユーザータイプ（例: "特定店舗ロイヤルカスタマー"）
- primary_store_id: 主要利用店舗ID
- primary_store_name: 主要利用店舗名
- visits: 主要店舗への訪問回数
- narrative: 行動パターン・嗜好性の詳細説明（長文テキスト）

【使用例】
1. いつもの店をレコメンドする場合:
   get_user_profile(profile_id="user_criollo_heavy")
   → primary_store_name（洋菓子店クリオロ）を確認してレコメンド

2. 新しい店を提案する場合:
   get_user_profile(profile_id="user_criollo_heavy")
   → narrativeから「和カフェやスペシャルティコーヒー専門店の利用あり」を確認
   → 類似カテゴリの別店舗を提案

3. 属性に基づく提案:
   get_user_profile(profile_id="user_criollo_heavy")
   → age（28歳）、gender（女性）を確認
   → 年齢・性別に適したギフトカテゴリを提案

【返り値】
- 成功時: ユーザー情報を含む辞書
- エラー時: {"error": "エラーメッセージ"}
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """ユーザープロファイル情報を取得する。

        Args:
            profile_id (str): ユーザープロファイルID

        Returns:
            ユーザー情報の辞書（8つのカラム）
            エラー時は {"error": "エラーメッセージ"}
        """
        profile_id = kwargs.get("profile_id", "")

        if not profile_id:
            return {"error": "profile_idを指定してください"}

        try:
            # DuckDBでCSVファイルを読み込み、指定されたprofile_idのデータを取得
            result = self._fetch_user_profile(profile_id)

            if not result:
                error_msg = f"ユーザーが見つかりません: {profile_id}"
                logger.warning(error_msg)
                return {"error": error_msg}

            logger.info(f"Successfully fetched profile for: {profile_id}")
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

            # CSVファイルからprofile_idで検索（1件のみ取得）
            # Note: ファイルパスはf-stringだが、profile_idはパラメータ化されているためSQLインジェクションのリスクはない
            query = f"""
                SELECT *
                FROM read_csv_auto('{self.narrative_file}')
                WHERE profile_id = ?
                LIMIT 1
            """  # noqa: S608

            result = con.execute(query, [profile_id]).fetchall()
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
