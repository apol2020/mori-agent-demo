"""MultiplyToolのユニットテスト。"""

from src.core.tools.math_tool import MultiplyTool


class TestMultiplyTool:
    """MultiplyToolのテスト。"""

    def test_multiply_tool_name(self) -> None:
        """ツール名が正しいことを確認。"""
        tool = MultiplyTool()
        assert tool.name == "multiply"

    def test_multiply_tool_description(self) -> None:
        """ツールの説明が正しいことを確認。"""
        tool = MultiplyTool()
        assert "掛け算" in tool.description
        assert tool.description != ""

    def test_multiply_positive_numbers(self) -> None:
        """正の数の掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=3, b=4)
        assert result == 12

    def test_multiply_negative_numbers(self) -> None:
        """負の数の掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=-3, b=4)
        assert result == -12

    def test_multiply_by_zero(self) -> None:
        """ゼロとの掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=5, b=0)
        assert result == 0

    def test_multiply_both_negative(self) -> None:
        """両方負の数の掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=-3, b=-4)
        assert result == 12

    def test_multiply_large_numbers(self) -> None:
        """大きな数の掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=1000, b=2000)
        assert result == 2000000

    def test_multiply_one(self) -> None:
        """1との掛け算が正しく動作することを確認。"""
        tool = MultiplyTool()
        result = tool.execute(a=42, b=1)
        assert result == 42

    def test_multiply_tool_is_reusable(self) -> None:
        """同じツールインスタンスを複数回使用できることを確認。"""
        tool = MultiplyTool()
        assert tool.execute(a=2, b=3) == 6
        assert tool.execute(a=5, b=6) == 30
        assert tool.execute(a=10, b=10) == 100
