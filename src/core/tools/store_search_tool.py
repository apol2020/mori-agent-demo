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
        self.stores_url_file = self.project_root / "input" / "stores.csv"

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

【出力形式】
- 検索結果は、生データ（results）と表形式のMarkdown（table）の両方で返されます
- 複数店舗を提案する際は、tableフィールドの内容をそのままユーザーに表示してください
- 表形式では主要な情報（店舗名、カテゴリ、説明、営業時間、電話番号、住所、URL等）が見やすく整理されています

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

【重要】
- 店舗検索結果には自動的にweb_url（店舗のWebページURL）が追加されます
- store_idが含まれていればURLが自動的に付与されます

【検索例】
1. 店舗名で検索（URLが自動的に追加されます）:
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

            # URL情報を追加
            results_with_urls = self._add_store_urls(results)

            return {
                "results": results_with_urls,
                "count": len(results_with_urls),
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

    def _add_store_urls(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """検索結果に店舗URLを追加する。

        Args:
            results: 店舗検索結果のリスト

        Returns:
            URL情報が追加された検索結果のリスト
        """
        try:
            # stores.csvからURL情報を読み込む
            con = duckdb.connect()
            # パスはプロジェクト内の固定パスなので安全
            query = f"SELECT store_id, source FROM read_csv_auto('{str(self.stores_url_file)}')"  # noqa: S608
            url_data = con.execute(query).fetchall()
            con.close()

            # store_idをキーとした辞書を作成
            url_dict = {row[0]: row[1] for row in url_data if row[1]}  # URLが空でないもののみ

            # 各結果にURLを追加
            for result in results:
                store_id = result.get("store_id")
                if store_id and store_id in url_dict:
                    result["web_url"] = url_dict[store_id]

            return results

        except Exception as e:
            logger.warning(f"Failed to add store URLs: {str(e)}")
            # URL追加に失敗しても元の結果を返す
            return results

    def _generate_table_markdown(self, results: list[dict[str, Any]]) -> str:
        """検索結果から表形式のMarkdownテーブルを生成する。

        Args:
            results: 店舗検索結果のリスト

        Returns:
            表形式のMarkdownテーブル文字列
        """
        if not results:
            return ""

        # 表示する主要カラムを定義（優先度順）
        priority_columns = [
            "store_name",
            "category",
            "description",
            "opening_hours",
            "phone",
            "address",
            "web_url",
        ]

        # 実際に存在するカラムのみを使用
        all_columns = list(results[0].keys())
        display_columns = [col for col in priority_columns if col in all_columns]

        # 優先度リストにない残りのカラムも追加（store_idは除外）
        for col in all_columns:
            if col not in display_columns and col != "store_id":
                display_columns.append(col)

        # カラム数が多すぎる場合は主要なカラムのみに制限
        if len(display_columns) > 8:
            display_columns = display_columns[:8]

        # カラム名の日本語化マッピング
        column_labels = {
            "store_name": "店舗名",
            "category": "カテゴリ",
            "description": "説明",
            "opening_hours": "営業時間",
            "phone": "電話番号",
            "address": "住所",
            "web_url": "URL",
            "email": "メール",
            "parking": "駐車場",
            "pets_allowed": "ペット可",
            "private_room": "個室",
            "target_audience": "対象客層",
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
                elif col == "web_url" and value:
                    # URLは短縮して表示（リンクとして）
                    row_values.append(f"[リンク]({value})")
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
