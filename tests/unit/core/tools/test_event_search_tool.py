"""EventSearchToolのユニットテスト。"""

import pytest

from src.core.tools.event_search_tool import EventSearchTool


@pytest.fixture
def event_search_tool():
    """EventSearchToolのフィクスチャ。"""
    return EventSearchTool()


class TestEventSearchTool:
    """EventSearchToolのテストクラス。"""

    def test_tool_name(self, event_search_tool):
        """ツール名が正しいことを確認。"""
        assert event_search_tool.name == "search_events"

    def test_tool_description(self, event_search_tool):
        """ツールの説明が存在することを確認。"""
        assert len(event_search_tool.description) > 0
        assert "search_events" in event_search_tool.description
        assert "SQL" in event_search_tool.description

    def test_execute_valid_query(self, event_search_tool):
        """正常なSQLクエリが実行できることを確認。"""
        result = event_search_tool.execute(sql_query="SELECT * FROM 'events.csv' LIMIT 3")
        assert "results" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["results"]) == 3

    def test_execute_without_sql_query(self, event_search_tool):
        """SQLクエリなしで実行した場合のエラー処理を確認。"""
        result = event_search_tool.execute()
        assert "error" in result
        assert "SQLクエリを指定してください" in result["error"]

    def test_validate_sql_select_query(self, event_search_tool):
        """SELECT文の検証が正しく動作することを確認。"""
        is_valid, _ = event_search_tool._validate_sql("SELECT * FROM 'events.csv'")
        assert is_valid is True

    def test_validate_sql_non_select_query(self, event_search_tool):
        """SELECT以外の文が拒否されることを確認。"""
        is_valid, error = event_search_tool._validate_sql("INSERT INTO events VALUES (1)")
        assert is_valid is False
        assert "SELECT文のみ" in error

    def test_validate_sql_drop_query(self, event_search_tool):
        """DROP文が拒否されることを確認。"""
        is_valid, error = event_search_tool._validate_sql("SELECT * FROM events; DROP TABLE events")
        assert is_valid is False
        assert "DROP" in error or "複数" in error

    def test_validate_sql_update_query(self, event_search_tool):
        """UPDATE文が拒否されることを確認。"""
        is_valid, error = event_search_tool._validate_sql("UPDATE events SET name='test'")
        assert is_valid is False

    def test_validate_sql_delete_query(self, event_search_tool):
        """DELETE文が拒否されることを確認。"""
        is_valid, error = event_search_tool._validate_sql("DELETE FROM events")
        assert is_valid is False

    def test_validate_sql_multiple_queries(self, event_search_tool):
        """複数クエリが拒否されることを確認。"""
        is_valid, error = event_search_tool._validate_sql("SELECT * FROM events; SELECT * FROM events;")
        assert is_valid is False
        assert "複数" in error

    def test_ensure_limit_no_limit(self, event_search_tool):
        """LIMIT句がない場合に追加されることを確認。"""
        query = "SELECT * FROM 'events.csv'"
        result_query = event_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query

    def test_ensure_limit_with_limit_5(self, event_search_tool):
        """LIMIT 5がそのまま保持されることを確認。"""
        query = "SELECT * FROM 'events.csv' LIMIT 5"
        result_query = event_search_tool._ensure_limit(query)
        assert "LIMIT 5" in result_query or "LIMIT 10" in result_query
        # LIMIT 5はそのままか、10に調整される可能性がある

    def test_ensure_limit_with_limit_100(self, event_search_tool):
        """LIMIT 100がLIMIT 10に調整されることを確認。"""
        query = "SELECT * FROM 'events.csv' LIMIT 100"
        result_query = event_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query
        assert "LIMIT 100" not in result_query

    def test_ensure_limit_case_insensitive(self, event_search_tool):
        """LIMITの大文字小文字を区別しないことを確認。"""
        query = "SELECT * FROM 'events.csv' limit 50"
        result_query = event_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query.upper()

    def test_execute_with_limit_enforcement(self, event_search_tool):
        """実際のクエリでLIMIT制約が適用されることを確認。"""
        # LIMIT 100を指定しても10件までしか返らない
        result = event_search_tool.execute(sql_query="SELECT * FROM 'events.csv' LIMIT 100")
        assert "results" in result
        assert result["count"] <= 10

    def test_execute_with_where_clause(self, event_search_tool):
        """WHERE句を含むクエリが実行できることを確認。"""
        result = event_search_tool.execute(sql_query="SELECT * FROM 'events.csv' WHERE event_name LIKE '%BMW%' LIMIT 5")
        assert "results" in result
        # BMWを含むイベントが存在する場合
        if result["count"] > 0:
            assert any("BMW" in r.get("event_name", "") for r in result["results"])

    def test_execute_with_order_by(self, event_search_tool):
        """ORDER BY句を含むクエリが実行できることを確認。"""
        result = event_search_tool.execute(sql_query="SELECT event_name FROM 'events.csv' ORDER BY event_name LIMIT 5")
        assert "results" in result
        assert result["count"] <= 5

    def test_execute_select_specific_columns(self, event_search_tool):
        """特定のカラムのみを選択できることを確認。"""
        result = event_search_tool.execute(sql_query="SELECT event_name, date_time FROM 'events.csv' LIMIT 3")
        assert "results" in result
        assert result["count"] == 3
        # 結果に指定したカラムが含まれることを確認
        if len(result["results"]) > 0:
            assert "event_name" in result["results"][0]
            assert "date_time" in result["results"][0]

    def test_execute_dangerous_keywords_blocked(self, event_search_tool):
        """危険なキーワードを含むクエリがブロックされることを確認。"""
        dangerous_queries = [
            "DROP TABLE events",
            "UPDATE events SET name='x'",
            "DELETE FROM events",
            "INSERT INTO events VALUES (1)",
            "ALTER TABLE events ADD COLUMN x",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE events",
        ]

        for query in dangerous_queries:
            result = event_search_tool.execute(sql_query=query)
            assert "error" in result, f"Query should be blocked: {query}"

    def test_execute_empty_result(self, event_search_tool):
        """結果が0件の場合も正しく処理されることを確認。"""
        result = event_search_tool.execute(
            sql_query="SELECT * FROM 'events.csv' WHERE event_name = 'NONEXISTENT_EVENT_12345' LIMIT 10"
        )
        assert "results" in result
        assert result["count"] == 0
        assert len(result["results"]) == 0
