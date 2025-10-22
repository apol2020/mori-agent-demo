"""店舗データをSQLで検索するツール。"""

import re
from pathlib import Path
from typing import Any

import duckdb

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StoreSearchTool(BaseTool):
    """店舗データをSQLクエリで検索するツール。"""

    def __init__(self) -> None:
        """店舗検索ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.stores_file = self.project_root / "input" / "filtered_store_data_カテゴリー情報あり.csv"

    @property
    def name(self) -> str:
        """ツール名。"""
        return "search_stores"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """search_stores: 店舗データをSQLクエリで検索します。

【使用方法】
- SQLクエリを指定して店舗情報を検索できます
- FROM句には 'stores.csv' を指定してください
- SELECT文のみ使用可能です（INSERT/UPDATE/DELETE等は使用不可）

【重要な制約】
- 検索結果は最大10件までに制限されます
- クエリにLIMIT句がない場合、自動的に LIMIT 10 が追加されます
- LIMIT句を指定する場合も、10以下に制限されます

【データスキーマ】
テーブル名: stores.csv

カラム:
- store_id (TEXT): 店舗ID（例: "STR-0001"）
- store_name (TEXT): 店舗名
- description (TEXT): 店舗の説明
- category (TEXT): カテゴリ（"retail", "restaurant", "cafe"など）
- opening_hours (TEXT): 営業時間（JSON形式: {"monday": [{"open": "10:00", "close": "20:00"}], ...}）
- irregular_closures (TEXT): 臨時休業情報（JSON配列形式）
- phone (TEXT): 電話番号
- email (TEXT): メールアドレス
- address (TEXT): 住所
- Biz_Entertainment_Available (TEXT): ビジネス・エンターテインメント利用可否（"TRUE"または空文字）
- private_room (TEXT): 個室情報（JSON形式: {"available": true/false, "capacity": 数値, "charge": "説明"}）
- pets_allowed (TEXT): ペット同伴可否（"TRUE"または空文字）
- target_audience (TEXT): 対象客層（JSON配列形式: ["ファミリー", "ビジネス"]）
- store_exclusive_events (TEXT): 店舗独自イベント
- menu (TEXT): メニュー情報
- seasonal_items (TEXT): 季節商品情報
- allergy_info (TEXT): アレルギー情報
- gluten_free_info (TEXT): グルテンフリー情報
- vegan_info (TEXT): ヴィーガン情報
- kids_info (TEXT): 子供向け情報（JSON形式: {"kids_menu": bool, "highchair": bool, "diaper_changing": bool}）
- halal_info (TEXT): ハラール情報
- reservations (TEXT): 予約情報
- restroom_info (TEXT): トイレ情報
- accessibility (TEXT): バリアフリー情報
- parking (TEXT): 駐車場情報（JSON形式: {"available": bool, "capacity": 数値, "charge": "説明"}）
- nursing_room (TEXT): 授乳室情報
- access_route (TEXT): アクセス方法
- extraction_status (TEXT): データ抽出ステータス（"success"または"error"）
- error_message (TEXT): エラーメッセージ

【検索例】
1. 店舗名で検索:
   SELECT * FROM 'stores.csv' WHERE store_name LIKE '%ヒルズ%'

2. カテゴリで検索:
   SELECT * FROM 'stores.csv' WHERE category = 'retail'

3. 駐車場がある店舗を検索:
   SELECT store_name, address, parking FROM 'stores.csv'
   WHERE parking LIKE '%"available": true%'

4. ファミリー向けの店舗を検索:
   SELECT store_name, description, target_audience FROM 'stores.csv'
   WHERE target_audience LIKE '%ファミリー%'

5. 個室が利用可能な店舗を検索:
   SELECT store_name, phone, private_room FROM 'stores.csv'
   WHERE private_room LIKE '%"available": true%'

6. 特定のエリア（住所）で検索:
   SELECT * FROM 'stores.csv' WHERE address LIKE '%麻布台%'

7. ビジネス利用可能な店舗を検索:
   SELECT * FROM 'stores.csv' WHERE Biz_Entertainment_Available = 'TRUE'

8. ペット同伴可能な店舗を検索:
   SELECT * FROM 'stores.csv' WHERE pets_allowed = 'TRUE'
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """SQLクエリを実行して店舗を検索する。

        Args:
            sql_query (str): 実行するSQLクエリ（SELECT文のみ）

        Returns:
            検索結果の辞書（results: 結果リスト, count: 件数）
            エラー時は {"error": "エラーメッセージ"}
        """
        sql_query = kwargs.get("sql_query", "")

        if not sql_query:
            return {"error": "SQLクエリを指定してください"}

        try:
            # SQLクエリのバリデーション
            is_valid, error_message = self._validate_sql(sql_query)
            if not is_valid:
                logger.warning(f"Invalid SQL query: {error_message}")
                return {"error": error_message}

            # LIMIT句の調整
            sql_query = self._ensure_limit(sql_query)

            # stores.csvへのパスを実際のファイルパスに置換
            sql_query = sql_query.replace("'stores.csv'", f"'{self.stores_file}'")
            sql_query = sql_query.replace('"stores.csv"', f"'{self.stores_file}'")
            sql_query = sql_query.replace("read_csv('stores.csv')", f"read_csv('{self.stores_file}')")

            # DuckDBでクエリ実行
            results = self._execute_duckdb_query(sql_query)

            logger.info(f"Query executed successfully: {len(results)} results found")

            # 検索結果が0件の場合、メッセージを追加
            if len(results) == 0:
                return {"results": [], "count": 0, "message": "検索条件に一致する店舗が見つかりませんでした"}

            return {"results": results, "count": len(results)}

        except Exception as e:
            error_msg = f"クエリ実行中にエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def _validate_sql(self, sql_query: str) -> tuple[bool, str]:
        """SQLクエリが安全かどうかを検証する。

        Args:
            sql_query: 検証するSQLクエリ

        Returns:
            (検証成功/失敗, エラーメッセージ)のタプル
        """
        # 空白を正規化
        normalized_query = " ".join(sql_query.split()).upper()

        # SELECT文で始まっているかチェック
        if not normalized_query.startswith("SELECT"):
            return False, "SELECT文のみ実行可能です"

        # 危険なキーワードのチェック
        dangerous_keywords = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "PRAGMA",
            "ATTACH",
            "DETACH",
        ]

        for keyword in dangerous_keywords:
            # キーワードの前後に単語境界があることを確認（部分一致を避ける）
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, normalized_query):
                return False, f"危険な操作が検出されました: {keyword}"

        # 複数クエリのチェック（セミコロン区切り）
        # ただし、文字列リテラル内のセミコロンは除外
        # 簡易的なチェック: セミコロンの後に何かしらの文字がある場合
        semicolon_pattern = r";[\s\S]+\S"
        if re.search(semicolon_pattern, sql_query.strip()):
            return False, "複数のクエリを同時に実行することはできません"

        return True, ""

    def _ensure_limit(self, sql_query: str) -> str:
        """SQLクエリにLIMIT句を追加または調整する。

        Args:
            sql_query: 元のSQLクエリ

        Returns:
            LIMIT句が調整されたSQLクエリ
        """
        # LIMIT句の検出（大文字小文字を区別しない）
        limit_pattern = r"\bLIMIT\s+(\d+)\b"
        match = re.search(limit_pattern, sql_query, re.IGNORECASE)

        if match:
            # 既存のLIMIT値を取得
            current_limit = int(match.group(1))
            if current_limit > 10:
                # 10以下に制限
                sql_query = re.sub(limit_pattern, "LIMIT 10", sql_query, flags=re.IGNORECASE)
                logger.info(f"LIMIT adjusted from {current_limit} to 10")
        else:
            # LIMIT句がない場合は追加
            # セミコロンがある場合は、その前に追加
            if sql_query.strip().endswith(";"):
                sql_query = sql_query.strip()[:-1] + " LIMIT 10;"
            else:
                sql_query = sql_query.strip() + " LIMIT 10"
            logger.info("LIMIT 10 added to query")

        return sql_query

    def _execute_duckdb_query(self, sql_query: str) -> list[dict[str, Any]]:
        """DuckDBを使用してSQLクエリを実行する。

        Args:
            sql_query: 実行するSQLクエリ

        Returns:
            クエリ結果（辞書のリスト）

        Raises:
            Exception: クエリ実行時のエラー
        """
        con = None
        try:
            # インメモリDuckDBコネクション作成
            con = duckdb.connect()

            # クエリ実行
            result = con.execute(sql_query).fetchall()
            columns = [desc[0] for desc in con.description] if con.description else []

            # 結果を辞書のリストに変換
            results = []
            for row in result:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # datetimeオブジェクトを文字列に変換
                    if hasattr(value, "isoformat"):
                        value = value.isoformat()
                    row_dict[column] = value
                results.append(row_dict)

            return results

        finally:
            # コネクションをクローズ
            if con:
                con.close()
