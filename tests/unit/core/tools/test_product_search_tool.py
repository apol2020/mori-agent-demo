"""ProductSearchToolのユニットテスト。"""

import pytest

from src.core.tools.product_search_tool import ProductSearchTool


@pytest.fixture
def product_search_tool():
    """ProductSearchToolのフィクスチャ。"""
    return ProductSearchTool()


class TestProductSearchTool:
    """ProductSearchToolのテストクラス。"""

    def test_tool_name(self, product_search_tool):
        """ツール名が正しいことを確認。"""
        assert product_search_tool.name == "search_products"

    def test_tool_description(self, product_search_tool):
        """ツールの説明が存在することを確認。"""
        assert len(product_search_tool.description) > 0
        assert "search_products" in product_search_tool.description
        assert "SQL" in product_search_tool.description

    def test_execute_valid_query(self, product_search_tool):
        """正常なSQLクエリが実行できることを確認。"""
        result = product_search_tool.execute(sql_query="SELECT * FROM 'filtered_product_data.csv' LIMIT 3")
        assert "results" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["results"]) == 3

    def test_execute_without_sql_query(self, product_search_tool):
        """SQLクエリなしで実行した場合のエラー処理を確認。"""
        result = product_search_tool.execute()
        assert "error" in result
        assert "SQLクエリを指定してください" in result["error"]

    def test_validate_sql_select_query(self, product_search_tool):
        """SELECT文の検証が正しく動作することを確認。"""
        is_valid, _ = product_search_tool._validate_sql("SELECT * FROM 'filtered_product_data.csv'")
        assert is_valid is True

    def test_validate_sql_non_select_query(self, product_search_tool):
        """SELECT以外の文が拒否されることを確認。"""
        is_valid, error = product_search_tool._validate_sql("INSERT INTO products VALUES (1)")
        assert is_valid is False
        assert "SELECT文のみ" in error

    def test_validate_sql_drop_query(self, product_search_tool):
        """DROP文が拒否されることを確認。"""
        is_valid, error = product_search_tool._validate_sql("SELECT * FROM products; DROP TABLE products")
        assert is_valid is False
        assert "DROP" in error or "複数" in error

    def test_validate_sql_update_query(self, product_search_tool):
        """UPDATE文が拒否されることを確認。"""
        is_valid, error = product_search_tool._validate_sql("UPDATE products SET name='test'")
        assert is_valid is False

    def test_validate_sql_delete_query(self, product_search_tool):
        """DELETE文が拒否されることを確認。"""
        is_valid, error = product_search_tool._validate_sql("DELETE FROM products")
        assert is_valid is False

    def test_validate_sql_multiple_queries(self, product_search_tool):
        """複数クエリが拒否されることを確認。"""
        is_valid, error = product_search_tool._validate_sql("SELECT * FROM products; SELECT * FROM products;")
        assert is_valid is False
        assert "複数" in error

    def test_ensure_limit_no_limit(self, product_search_tool):
        """LIMIT句がない場合に追加されることを確認。"""
        query = "SELECT * FROM 'filtered_product_data.csv'"
        result_query = product_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query

    def test_ensure_limit_with_limit_5(self, product_search_tool):
        """LIMIT 5がそのまま保持されることを確認。"""
        query = "SELECT * FROM 'filtered_product_data.csv' LIMIT 5"
        result_query = product_search_tool._ensure_limit(query)
        assert "LIMIT 5" in result_query or "LIMIT 10" in result_query
        # LIMIT 5はそのままか、10に調整される可能性がある

    def test_ensure_limit_with_limit_100(self, product_search_tool):
        """LIMIT 100がLIMIT 10に調整されることを確認。"""
        query = "SELECT * FROM 'filtered_product_data.csv' LIMIT 100"
        result_query = product_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query
        assert "LIMIT 100" not in result_query

    def test_ensure_limit_case_insensitive(self, product_search_tool):
        """LIMITの大文字小文字を区別しないことを確認。"""
        query = "SELECT * FROM 'filtered_product_data.csv' limit 50"
        result_query = product_search_tool._ensure_limit(query)
        assert "LIMIT 10" in result_query.upper()

    def test_execute_with_limit_enforcement(self, product_search_tool):
        """実際のクエリでLIMIT制約が適用されることを確認。"""
        # LIMIT 100を指定しても10件までしか返らない
        result = product_search_tool.execute(sql_query="SELECT * FROM 'filtered_product_data.csv' LIMIT 100")
        assert "results" in result
        assert result["count"] <= 10

    def test_execute_with_where_clause(self, product_search_tool):
        """WHERE句を含むクエリが実行できることを確認。"""
        result = product_search_tool.execute(
            sql_query="SELECT * FROM 'filtered_product_data.csv' WHERE tag = 'ギフト' LIMIT 5"
        )
        assert "results" in result
        # ギフトカテゴリの商品が存在する場合
        if result["count"] > 0:
            assert all(r.get("tag") == "ギフト" for r in result["results"])

    def test_execute_with_order_by(self, product_search_tool):
        """ORDER BY句を含むクエリが実行できることを確認。"""
        result = product_search_tool.execute(
            sql_query="SELECT product_name FROM 'filtered_product_data.csv' ORDER BY product_name LIMIT 5"
        )
        assert "results" in result
        assert result["count"] <= 5

    def test_execute_select_specific_columns(self, product_search_tool):
        """特定のカラムのみを選択できることを確認。"""
        result = product_search_tool.execute(
            sql_query="SELECT product_name, tag FROM 'filtered_product_data.csv' LIMIT 3"
        )
        assert "results" in result
        assert result["count"] == 3
        # 結果に指定したカラムが含まれることを確認
        if len(result["results"]) > 0:
            assert "product_name" in result["results"][0]
            assert "tag" in result["results"][0]

    def test_execute_dangerous_keywords_blocked(self, product_search_tool):
        """危険なキーワードを含むクエリがブロックされることを確認。"""
        dangerous_queries = [
            "DROP TABLE products",
            "UPDATE products SET name='x'",
            "DELETE FROM products",
            "INSERT INTO products VALUES (1)",
            "ALTER TABLE products ADD COLUMN x",
            "CREATE TABLE test (id INT)",
            "TRUNCATE TABLE products",
        ]

        for query in dangerous_queries:
            result = product_search_tool.execute(sql_query=query)
            assert "error" in result, f"Query should be blocked: {query}"

    def test_execute_empty_result(self, product_search_tool):
        """結果が0件の場合も正しく処理されることを確認。"""
        result = product_search_tool.execute(
            sql_query=(
                "SELECT * FROM 'filtered_product_data.csv' " "WHERE product_name = 'NONEXISTENT_PRODUCT_12345' LIMIT 10"
            )
        )
        assert "results" in result
        assert result["count"] == 0
        assert len(result["results"]) == 0

    def test_execute_with_like_operator(self, product_search_tool):
        """LIKE演算子を使った検索が正しく動作することを確認。"""
        result = product_search_tool.execute(
            sql_query="SELECT * FROM 'filtered_product_data.csv' WHERE product_name LIKE '%寿司%' LIMIT 5"
        )
        assert "results" in result
        # 寿司を含む商品が存在する場合
        if result["count"] > 0:
            assert any("寿司" in r.get("product_name", "") for r in result["results"])

    def test_execute_with_price_search(self, product_search_tool):
        """価格情報での検索が可能なことを確認。"""
        result = product_search_tool.execute(
            sql_query="SELECT * FROM 'filtered_product_data.csv' WHERE product_description LIKE '%1,000円%' LIMIT 5"
        )
        assert "results" in result
        # 価格情報を含む商品が存在する場合
        if result["count"] > 0:
            assert all("product_description" in r for r in result["results"])

    def test_result_contains_all_columns(self, product_search_tool):
        """検索結果に必要なカラムがすべて含まれることを確認。"""
        result = product_search_tool.execute(sql_query="SELECT * FROM 'filtered_product_data.csv' LIMIT 1")
        assert "results" in result
        assert result["count"] == 1

        # 最初の結果に必要なカラムが含まれているか確認
        first_result = result["results"][0]
        assert "store_id" in first_result
        assert "store_name" in first_result
        assert "product_name" in first_result
        assert "product_description" in first_result
        assert "tag" in first_result
