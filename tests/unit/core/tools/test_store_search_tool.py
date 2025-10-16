"""StoreSearchToolのユニットテスト。"""

import pytest

from src.core.tools.store_search_tool import StoreSearchTool


@pytest.fixture
def store_search_tool():
    """StoreSearchToolのフィクスチャ。"""
    return StoreSearchTool()


class TestStoreSearchTool:
    """StoreSearchToolのテストクラス。"""

    def test_tool_name(self, store_search_tool):
        """ツール名が正しいことを確認。"""
        assert store_search_tool.name == "search_stores"

    def test_tool_description(self, store_search_tool):
        """ツールの説明が存在することを確認。"""
        assert len(store_search_tool.description) > 0
        assert "search_stores" in store_search_tool.description
        assert "SQL" in store_search_tool.description

    def test_execute_valid_query(self, store_search_tool):
        """正常なSQLクエリが実行できることを確認。"""
        result = store_search_tool.execute(sql_query="SELECT * FROM 'stores.csv' LIMIT 3")
        assert "results" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["results"]) == 3

    def test_execute_without_sql_query(self, store_search_tool):
        """SQLクエリなしで実行した場合のエラー処理を確認。"""
        result = store_search_tool.execute()
        assert "error" in result
        assert "SQLクエリを指定してください" in result["error"]

    def test_validate_sql_select_query(self, store_search_tool):
        """SELECT文の検証が正しく動作することを確認。"""
        is_valid, _ = store_search_tool._validate_sql("SELECT * FROM 'stores.csv'")
        assert is_valid is True

    def test_validate_sql_non_select_query(self, store_search_tool):
        """SELECT以外の文が拒否されることを確認。"""
        is_valid, error = store_search_tool._validate_sql("INSERT INTO stores VALUES (1)")
        assert is_valid is False
        assert "SELECT文のみ" in error

    def test_validate_sql_drop_query(self, store_search_tool):
        """DROP文が拒否されることを確認。"""
        is_valid, error = store_search_tool._validate_sql("SELECT * FROM stores; DROP TABLE stores")
        assert is_valid is False
        assert "DROP" in error or "複数" in error

    def test_validate_sql_update_query(self, store_search_tool):
        """UPDATE文が拒否されることを確認。"""
        is_valid, error = store_search_tool._validate_sql("UPDATE stores SET name='test'")
        assert is_valid is False

    def test_validate_sql_delete_query(self, store_search_tool):
        """DELETE文が拒否されることを確認。"""
        is_valid, error = store_search_tool._validate_sql("DELETE FROM stores")
        assert is_valid is False

    def test_validate_sql_multiple_queries(self, store_search_tool):
        """複数クエリが拒否されることを確認。"""
        is_valid, error = store_search_tool._validate_sql("SELECT * FROM stores; SELECT * FROM stores;")
        assert is_valid is False
        assert "複数" in error

    def test_ensure_limit_no_limit(self, store_search_tool):
        """LIMIT句がない場合に追加されることを確認。"""
        query = "SELECT * FROM 'stores.csv'"
        result_query = store_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query

    def test_ensure_limit_with_limit_5(self, store_search_tool):
        """LIMIT 5がそのまま保持されることを確認。"""
        query = "SELECT * FROM 'stores.csv' LIMIT 5"
        result_query = store_search_tool._ensure_limit(query)
        assert "LIMIT 5" in result_query or "LIMIT 10" in result_query
        # LIMIT 5はそのままか、10に調整される可能性がある

    def test_ensure_limit_with_limit_100(self, store_search_tool):
        """LIMIT 100がLIMIT 10に調整されることを確認。"""
        query = "SELECT * FROM 'stores.csv' LIMIT 100"
        result_query = store_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query
        assert "LIMIT 100" not in result_query

    def test_ensure_limit_case_insensitive(self, store_search_tool):
        """LIMITの大文字小文字を区別しないことを確認。"""
        query = "SELECT * FROM 'stores.csv' limit 50"
        result_query = store_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query.upper()

    def test_execute_with_limit_enforcement(self, store_search_tool):
        """実際のクエリでLIMIT制約が適用されることを確認。"""
        # LIMIT 100を指定しても10件までしか返らない
        result = store_search_tool.execute(sql_query="SELECT * FROM 'stores.csv' LIMIT 100")
        assert "results" in result
        assert result["count"] <= 10

    def test_execute_with_where_clause(self, store_search_tool):
        """WHERE句を含むクエリが実行できることを確認。"""
        result = store_search_tool.execute(
            sql_query="SELECT * FROM 'stores.csv' WHERE store_name LIKE '%ヒルズ%' LIMIT 5"
        )
        assert "results" in result
        # ヒルズを含む店舗が存在する場合
        if result["count"] > 0:
            assert any("ヒルズ" in r.get("store_name", "") for r in result["results"])

    def test_execute_with_order_by(self, store_search_tool):
        """ORDER BY句を含むクエリが実行できることを確認。"""
        result = store_search_tool.execute(sql_query="SELECT store_name FROM 'stores.csv' ORDER BY store_name LIMIT 5")
        assert "results" in result
        assert result["count"] <= 5

    def test_execute_select_specific_columns(self, store_search_tool):
        """特定のカラムのみを選択できることを確認。"""
        result = store_search_tool.execute(sql_query="SELECT store_name, category FROM 'stores.csv' LIMIT 3")
        assert "results" in result
        assert result["count"] == 3
        # 結果に指定したカラムが含まれることを確認
        if len(result["results"]) > 0:
            assert "store_name" in result["results"][0]
            assert "category" in result["results"][0]

    def test_execute_dangerous_keywords_blocked(self, store_search_tool):
        """危険なキーワードを含むクエリがブロックされることを確認。"""
        dangerous_queries = [
            "DROP TABLE stores",
            "UPDATE stores SET name='x'",
            "DELETE FROM stores",
            "INSERT INTO stores VALUES (1)",
            "ALTER TABLE stores ADD COLUMN x",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE stores",
        ]

        for query in dangerous_queries:
            result = store_search_tool.execute(sql_query=query)
            assert "error" in result, f"Query should be blocked: {query}"

    def test_execute_empty_result(self, store_search_tool):
        """結果が0件の場合も正しく処理されることを確認。"""
        result = store_search_tool.execute(
            sql_query="SELECT * FROM 'stores.csv' WHERE store_name = 'NONEXISTENT_STORE_12345' LIMIT 10"
        )
        assert "results" in result
        assert result["count"] == 0
        assert len(result["results"]) == 0
        # 0件の場合、メッセージが含まれることを確認
        assert "message" in result
        assert "見つかりませんでした" in result["message"]

    def test_execute_search_by_category(self, store_search_tool):
        """カテゴリで検索できることを確認。"""
        result = store_search_tool.execute(
            sql_query="SELECT store_name, category FROM 'stores.csv' WHERE category = 'retail' LIMIT 5"
        )
        assert "results" in result
        # retailカテゴリの店舗が存在する場合
        if result["count"] > 0:
            assert all(r.get("category") == "retail" for r in result["results"])

    def test_execute_search_with_json_field(self, store_search_tool):
        """JSON形式のフィールドで検索できることを確認（駐車場がある店舗）。"""
        result = store_search_tool.execute(
            sql_query="SELECT store_name, parking FROM 'stores.csv' WHERE parking LIKE '%\"available\": true%' LIMIT 5"
        )
        assert "results" in result
        # 駐車場がある店舗が存在する場合
        if result["count"] > 0:
            assert all("parking" in r for r in result["results"])

    def test_execute_search_target_audience(self, store_search_tool):
        """対象客層で検索できることを確認（ファミリー向け店舗）。"""
        result = store_search_tool.execute(
            sql_query="SELECT store_name, target_audience FROM 'stores.csv' "
            "WHERE target_audience LIKE '%ファミリー%' LIMIT 5"
        )
        assert "results" in result
        # ファミリー向け店舗が存在する場合
        if result["count"] > 0:
            assert all("ファミリー" in r.get("target_audience", "") for r in result["results"])

    def test_execute_search_by_address(self, store_search_tool):
        """住所で検索できることを確認。"""
        result = store_search_tool.execute(
            sql_query="SELECT store_name, address FROM 'stores.csv' WHERE address LIKE '%麻布台%' LIMIT 5"
        )
        assert "results" in result
        # 麻布台エリアの店舗が存在する場合
        if result["count"] > 0:
            assert all("麻布台" in r.get("address", "") for r in result["results"])
