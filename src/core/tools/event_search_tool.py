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
        return """search_events: イベントデータをSQLクエリで検索します。

【使用方法】
- SQLクエリを指定してイベント情報を検索できます
- FROM句には 'events.csv' を指定してください
- SELECT文のみ使用可能です（INSERT/UPDATE/DELETE等は使用不可）

【重要な制約】
- 検索結果は最大10件までに制限されます
- クエリにLIMIT句がない場合、自動的に LIMIT 10 が追加されます
- LIMIT句を指定する場合も、10以下に制限されます

【出力形式】
- 検索結果は、生データ（results）と表形式のMarkdown（table）の両方で返されます
- 複数イベントを提案する際は、tableフィールドの内容をそのままユーザーに表示してください
- 表形式では主要な情報（イベント名、日時、開催場所、説明、費用、事前登録、URL等）が見やすく整理されています

【データスキーマ】
テーブル名: events.csv

カラム:
- event_name (TEXT): イベント名
- description (TEXT): イベントの説明
- date_time (TEXT): 開催日時（YYYY-MM-DD形式または"開始日/終了日"形式）
- location (TEXT): 開催場所（JSON形式: {"venue": "会場名", "address": "住所"}）
- capacity (TEXT): 定員
- source_url (TEXT): 情報元URL
- extracted_at (TEXT): データ抽出日時
- additional_info (TEXT): 追加情報
- contact_info (TEXT): 連絡先（JSON形式: {"phone": "電話番号", "email": "メールアドレス"}）
- cost (TEXT): 費用情報（JSON形式: {"is_free": true/false, "amount": "金額", "notes": "備考"}）
- registration_required (TEXT): 事前登録の要否（"True"または空文字）
- target_audience (TEXT): 対象者（JSON配列形式: ["家族", "子供"]）

【重要】
- イベント検索結果には必ずsource_urlカラムを含めてください
- SELECT *を使用するか、明示的にsource_urlを指定してください

【検索例】
1. イベント名で検索（URLを含む）:
   SELECT * FROM 'events.csv' WHERE event_name LIKE '%BMW%'

2. 無料イベントを検索（URLを含む）:
   SELECT * FROM 'events.csv' WHERE cost LIKE '%"is_free": true%'

3. 特定期間のイベントを検索（URLを含む）:
   SELECT * FROM 'events.csv' WHERE date_time LIKE '2025-10%'

4. 複数条件での検索（URLを明示的に指定）:
   SELECT event_name, date_time, location, source_url FROM 'events.csv'
   WHERE description LIKE '%記念%' AND registration_required = 'True'
   ORDER BY date_time
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """SQLクエリを実行してイベントを検索する。

        Args:
            sql_query (str): 実行するSQLクエリ（SELECT文のみ）

        Returns:
            検索結果の辞書（results: 結果リスト, count: 件数, table: 表形式のMarkdown）
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

            # 検索結果が0件の場合、メッセージを追加
            if len(results) == 0:
                return {"results": [], "count": 0, "message": "検索条件に一致するイベントが見つかりませんでした"}

            return {
                "results": results,
                "count": len(results),
            }

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

    def _generate_table_markdown(self, results: list[dict[str, Any]]) -> str:
        """検索結果から表形式のMarkdownテーブルを生成する。

        Args:
            results: イベント検索結果のリスト

        Returns:
            表形式のMarkdownテーブル文字列
        """
        if not results:
            return ""

        # 表示する主要カラムを定義（優先度順）
        priority_columns = [
            "event_name",
            "date_time",
            "location",
            "description",
            "cost",
            "registration_required",
            "source_url",
        ]

        # 実際に存在するカラムのみを使用
        all_columns = list(results[0].keys())
        display_columns = [col for col in priority_columns if col in all_columns]

        # 優先度リストにない残りのカラムも追加
        for col in all_columns:
            if col not in display_columns:
                display_columns.append(col)

        # カラム数が多すぎる場合は主要なカラムのみに制限
        if len(display_columns) > 8:
            display_columns = display_columns[:8]

        # カラム名の日本語化マッピング
        column_labels = {
            "event_name": "イベント名",
            "date_time": "日時",
            "location": "開催場所",
            "description": "説明",
            "cost": "費用",
            "registration_required": "事前登録",
            "source_url": "URL",
            "capacity": "定員",
            "contact_info": "連絡先",
            "target_audience": "対象者",
            "additional_info": "追加情報",
        }

        # ヘッダー行
        headers = [column_labels.get(col, col) for col in display_columns]
        header_line = "| " + " | ".join(headers) + " |"
        separator_line = "|" + "|".join([" --- " for _ in headers]) + "|"

        # データ行
        data_lines = []
        for result in results:
            row_values = []
            for col in display_columns:
                value = result.get(col, "")

                # 値の整形
                if value is None or value == "":
                    row_values.append("-")
                elif col == "source_url" and value:
                    # URLは短縮して表示（リンクとして）
                    row_values.append(f"[リンク]({value})")
                elif col == "registration_required":
                    # 事前登録の表示を簡潔に
                    row_values.append("要" if value == "True" else "不要")
                elif isinstance(value, str) and len(value) > 50:
                    # 長いテキストは省略
                    row_values.append(value[:47] + "...")
                elif isinstance(value, str) and ("\n" in value or "|" in value):
                    # 改行やパイプ文字を含む場合は置換
                    value = value.replace("\n", " ").replace("|", "\\|")
                    if len(value) > 50:
                        value = value[:47] + "..."
                    row_values.append(value)
                else:
                    row_values.append(str(value))

            data_line = "| " + " | ".join(row_values) + " |"
            data_lines.append(data_line)

        # テーブル全体を結合
        table_lines = [header_line, separator_line] + data_lines
        return "\n".join(table_lines)
