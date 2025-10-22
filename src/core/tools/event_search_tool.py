"""イベントデータをSQLで検索するツール。"""

import re
from pathlib import Path
from typing import Any

import duckdb

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventSearchTool(BaseTool):
    """イベントデータをSQLクエリで検索するツール。"""

    def __init__(self) -> None:
        """イベント検索ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.events_file = self.project_root / "input" / "events.csv"

    @property
    def name(self) -> str:
        """ツール名。"""
        return "search_events"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """search_events: イベントデータと期間限定商品をSQLクエリで検索します。

【対象データ】
このツールで検索できるのは以下のデータです:
- イベント情報（展示会、キャンペーン、ワークショップなど）
- 期間限定商品（イベント期間中のみ販売される商品や限定キャンペーン商品）

【使用方法】
- SQLクエリを指定してイベント・期間限定商品情報を検索できます
- FROM句には 'events.csv' を指定してください
- SELECT文のみ使用可能です（INSERT/UPDATE/DELETE等は使用不可）

【重要な制約】
- 検索結果は最大10件までに制限されます
- クエリにLIMIT句がない場合、自動的に LIMIT 10 が追加されます
- LIMIT句を指定する場合も、10以下に制限されます

【データスキーマ】
テーブル名: events.csv

カラム:
- event_name (TEXT): イベント名/期間限定商品名
- description (TEXT): イベント・商品の説明
- date_time (TEXT): 開催日時・販売期間（YYYY-MM-DD形式または"開始日/終了日"形式）
- location (TEXT): 開催場所・販売場所（JSON形式: {"venue": "会場名", "address": "住所"}）
- capacity (TEXT): 定員
- source_url (TEXT): 情報元URL
- extracted_at (TEXT): データ抽出日時
- additional_info (TEXT): 追加情報
- contact_info (TEXT): 連絡先（JSON形式: {"phone": "電話番号", "email": "メールアドレス"}）
- cost (TEXT): 費用情報（JSON形式: {"is_free": true/false, "amount": "金額", "notes": "備考"}）
- registration_required (TEXT): 事前登録の要否（"True"または空文字）
- target_audience (TEXT): 対象者（JSON配列形式: ["家族", "子供"]）

【検索例】
1. イベント名・商品名で検索:
   SELECT * FROM 'events.csv' WHERE event_name LIKE '%BMW%'

2. 無料イベント・無料商品を検索:
   SELECT * FROM 'events.csv' WHERE cost LIKE '%"is_free": true%'

3. 特定期間のイベント・期間限定商品を検索:
   SELECT * FROM 'events.csv' WHERE date_time LIKE '2025-10%'

4. 特定会場のイベント・商品を検索:
   SELECT event_name, description, date_time FROM 'events.csv'
   WHERE location LIKE '%麻布台%'

5. 複数条件での検索:
   SELECT event_name, date_time, location FROM 'events.csv'
   WHERE description LIKE '%記念%' AND registration_required = 'True'
   ORDER BY date_time

【使用場面】
- 「期間限定の商品を教えて」→ このツールを使用
- 「今月のイベントは？」→ このツールを使用
- 「キャンペーン商品を検索」→ このツールを使用
- 通常商品の検索 → search_products ツールを使用
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """SQLクエリを実行してイベントを検索する。

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

            # events.csvへのパスを実際のファイルパスに置換
            sql_query = sql_query.replace("'events.csv'", f"'{self.events_file}'")
            sql_query = sql_query.replace('"events.csv"', f"'{self.events_file}'")
            sql_query = sql_query.replace("read_csv('events.csv')", f"read_csv('{self.events_file}')")

            # DuckDBでクエリ実行
            results = self._execute_duckdb_query(sql_query)

            logger.info(f"Query executed successfully: {len(results)} results found")
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
