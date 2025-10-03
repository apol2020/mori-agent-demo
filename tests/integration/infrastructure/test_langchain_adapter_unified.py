"""LangChainAdapterの統一ツール入力処理のテスト。"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.infrastructure.llm.langchain_adapter import LangChainAdapter


def create_mock_claude_chunk(tool_call_id: str, tool_name: str, partial_json: str) -> Any:
    """Claude形式のモックチャンクを作成する。"""
    chunk = MagicMock()
    chunk.type = "AIMessageChunk"
    chunk.content = [{"type": "input_json_delta", "partial_json": partial_json}]
    chunk.tool_calls = [{"id": tool_call_id, "name": tool_name, "args": {}}]
    return chunk


def create_mock_openai_chunk(
    tool_call_id: str | None,
    tool_name: str | None,
    args_fragment: str,
    index: int,
) -> Any:
    """OpenAI形式のモックチャンクを作成する。"""
    chunk = MagicMock()
    chunk.type = "AIMessageChunk"
    chunk.content = ""
    chunk.tool_call_chunks = [{"id": tool_call_id, "name": tool_name, "args": args_fragment, "index": index}]
    return chunk


@pytest.mark.integration
class TestLangChainAdapterUnified:
    """統一されたツール入力処理のテスト。"""

    @pytest.fixture
    def adapter(self) -> LangChainAdapter:
        """テスト用のLangChainAdapterインスタンスを作成する。"""
        mock_llm = MagicMock()
        return LangChainAdapter(llm=mock_llm, tools=[])

    def test_extract_json_fragment_from_claude(self, adapter: LangChainAdapter) -> None:
        """Claude形式からJSON断片を抽出できることを確認する。"""
        chunk = create_mock_claude_chunk("call_123", "test_tool", '{"key": "value"}')
        index_to_id_map: dict[int, str] = {}

        json_fragment, tool_call_id = adapter._extract_json_fragment(chunk, index_to_id_map)

        assert json_fragment == '{"key": "value"}'
        assert tool_call_id == ""  # Claudeの場合は空（後で解決される）

    def test_extract_json_fragment_from_openai(self, adapter: LangChainAdapter) -> None:
        """OpenAI形式からJSON断片を抽出できることを確認する。"""
        chunk = create_mock_openai_chunk("call_456", "test_tool", '{"key": "value"}', 0)
        index_to_id_map: dict[int, str] = {}

        json_fragment, tool_call_id = adapter._extract_json_fragment(chunk, index_to_id_map)

        assert json_fragment == '{"key": "value"}'
        assert tool_call_id == "call_456"
        assert index_to_id_map[0] == "call_456"

    def test_process_tool_input_streaming_claude(self, adapter: LangChainAdapter) -> None:
        """Claude形式のストリーミングを統一メソッドで処理できることを確認する。"""
        tool_calls_map: dict[str, dict[str, Any]] = {
            "call_123": {"tool_name": "test_tool", "tool_input": {}, "accumulated_json": ""}
        }
        index_to_id_map: dict[int, str] = {}

        # 3つのチャンクに分割されたJSONを処理
        chunks = [
            create_mock_claude_chunk("call_123", "test_tool", '{"location"'),
            create_mock_claude_chunk("call_123", "test_tool", ': "Tokyo"'),
            create_mock_claude_chunk("call_123", "test_tool", "}"),
        ]

        for chunk in chunks:
            adapter._process_tool_input_streaming(tool_calls_map, index_to_id_map, chunk)

        # 最終的に完全なJSONがパースされている
        assert tool_calls_map["call_123"]["tool_input"] == {"location": "Tokyo"}
        assert tool_calls_map["call_123"]["accumulated_json"] == '{"location": "Tokyo"}'

    def test_process_tool_input_streaming_openai(self, adapter: LangChainAdapter) -> None:
        """OpenAI形式のストリーミングを統一メソッドで処理できることを確認する。"""
        tool_calls_map: dict[str, dict[str, Any]] = {
            "call_456": {"tool_name": "test_tool", "tool_input": {}, "accumulated_json": ""}
        }
        index_to_id_map: dict[int, str] = {}

        # 3つのチャンクに分割されたJSONを処理
        chunks = [
            create_mock_openai_chunk("call_456", "test_tool", '{"location"', 0),
            create_mock_openai_chunk(None, None, ': "Tokyo"', 0),
            create_mock_openai_chunk(None, None, "}", 0),
        ]

        for chunk in chunks:
            adapter._process_tool_input_streaming(tool_calls_map, index_to_id_map, chunk)

        # 最終的に完全なJSONがパースされている
        assert tool_calls_map["call_456"]["tool_input"] == {"location": "Tokyo"}
        assert tool_calls_map["call_456"]["accumulated_json"] == '{"location": "Tokyo"}'

    def test_unified_processing_produces_same_result(self, adapter: LangChainAdapter) -> None:
        """Claude/OpenAI両方で同じ結果が得られることを確認する。"""
        # Claude形式の処理
        claude_map: dict[str, dict[str, Any]] = {
            "call_1": {"tool_name": "calculate", "tool_input": {}, "accumulated_json": ""}
        }
        claude_index_map: dict[int, str] = {}
        claude_chunks = [
            create_mock_claude_chunk("call_1", "calculate", '{"a": 5,'),
            create_mock_claude_chunk("call_1", "calculate", ' "b": 3}'),
        ]
        for chunk in claude_chunks:
            adapter._process_tool_input_streaming(claude_map, claude_index_map, chunk)

        # OpenAI形式の処理
        openai_map: dict[str, dict[str, Any]] = {
            "call_2": {"tool_name": "calculate", "tool_input": {}, "accumulated_json": ""}
        }
        openai_index_map: dict[int, str] = {}
        openai_chunks = [
            create_mock_openai_chunk("call_2", "calculate", '{"a": 5,', 0),
            create_mock_openai_chunk(None, None, ' "b": 3}', 0),
        ]
        for chunk in openai_chunks:
            adapter._process_tool_input_streaming(openai_map, openai_index_map, chunk)

        # 両方とも同じtool_inputを得る
        assert claude_map["call_1"]["tool_input"] == openai_map["call_2"]["tool_input"]
        assert claude_map["call_1"]["tool_input"] == {"a": 5, "b": 3}
