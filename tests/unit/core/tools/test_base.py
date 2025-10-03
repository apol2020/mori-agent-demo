"""BaseToolの抽象基底クラスのユニットテスト。"""

from typing import Any

import pytest

from src.core.tools.base import BaseTool


class ConcreteTestTool(BaseTool):
    """テスト用の具象ツールクラス。"""

    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A test tool for unit testing"

    def execute(self, **kwargs: Any) -> Any:
        return f"Executed with {kwargs}"


class TestBaseTool:
    """BaseToolの抽象基底クラスのテスト。"""

    def test_cannot_instantiate_base_tool_directly(self) -> None:
        """BaseToolを直接インスタンス化できないことを確認。"""
        with pytest.raises(TypeError):
            BaseTool()  # type: ignore[abstract]

    def test_concrete_tool_can_be_instantiated(self) -> None:
        """具象クラスはインスタンス化できることを確認。"""
        tool = ConcreteTestTool()
        assert isinstance(tool, BaseTool)

    def test_concrete_tool_has_name_property(self) -> None:
        """具象ツールがname プロパティを持つことを確認。"""
        tool = ConcreteTestTool()
        assert tool.name == "test_tool"
        assert isinstance(tool.name, str)

    def test_concrete_tool_has_description_property(self) -> None:
        """具象ツールがdescriptionプロパティを持つことを確認。"""
        tool = ConcreteTestTool()
        assert tool.description == "A test tool for unit testing"
        assert isinstance(tool.description, str)

    def test_concrete_tool_can_execute(self) -> None:
        """具象ツールがexecuteメソッドを実行できることを確認。"""
        tool = ConcreteTestTool()
        result = tool.execute(param1="value1", param2=42)
        assert "Executed with" in result
        assert "param1" in result

    def test_incomplete_concrete_tool_cannot_be_instantiated(self) -> None:
        """必要なメソッドを実装していない具象クラスはインスタンス化できないことを確認。"""

        class IncompleteTool(BaseTool):
            @property
            def name(self) -> str:
                return "incomplete"

            # descriptionとexecuteを実装していない

        with pytest.raises(TypeError):
            IncompleteTool()  # type: ignore[abstract]

    def test_base_tool_enforces_name_property(self) -> None:
        """BaseToolがnameプロパティの実装を強制することを確認。"""

        class NoNameTool(BaseTool):
            @property
            def description(self) -> str:
                return "No name"

            def execute(self, **kwargs: Any) -> Any:
                return "result"

        with pytest.raises(TypeError):
            NoNameTool()  # type: ignore[abstract]

    def test_base_tool_enforces_description_property(self) -> None:
        """BaseToolがdescriptionプロパティの実装を強制することを確認。"""

        class NoDescriptionTool(BaseTool):
            @property
            def name(self) -> str:
                return "no_description"

            def execute(self, **kwargs: Any) -> Any:
                return "result"

        with pytest.raises(TypeError):
            NoDescriptionTool()  # type: ignore[abstract]

    def test_base_tool_enforces_execute_method(self) -> None:
        """BaseToolがexecuteメソッドの実装を強制することを確認。"""

        class NoExecuteTool(BaseTool):
            @property
            def name(self) -> str:
                return "no_execute"

            @property
            def description(self) -> str:
                return "No execute"

        with pytest.raises(TypeError):
            NoExecuteTool()  # type: ignore[abstract]

    def test_execute_with_different_kwargs(self) -> None:
        """executeメソッドが異なるkwargsで動作することを確認。"""
        tool = ConcreteTestTool()

        result1 = tool.execute()
        result2 = tool.execute(a=1)
        result3 = tool.execute(a=1, b=2, c="three")

        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert isinstance(result3, str)
        assert "a" in result2 or "1" in result2
        assert "c" in result3 or "three" in result3
