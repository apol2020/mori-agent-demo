"""ツール入力ストリーミングのAPI仕様差分を検証するテスト。

ClaudeとOpenAI APIのツール入力ストリーミング実装の違いを確認し、
共通化の可能性を評価する。
"""

import json
from typing import Any

import pytest

# --- モックデータの定義 ---


def create_claude_tool_call_chunk(
    tool_call_id: str,
    tool_name: str,
    partial_json: str,
) -> Any:
    """Claude形式のツール呼び出しチャンクを作成する。

    Claudeは`input_json_delta`として部分的なJSONを送信する。
    """

    class ClaudeChunk:
        def __init__(self) -> None:
            self.type = "AIMessageChunk"
            self.content = [
                {
                    "type": "input_json_delta",
                    "partial_json": partial_json,
                }
            ]
            self.tool_calls = [
                {
                    "id": tool_call_id,
                    "name": tool_name,
                    "args": {},  # 初期段階では空
                }
            ]

    return ClaudeChunk()


def create_openai_tool_call_chunk(
    tool_call_id: str,
    tool_name: str,
    args_fragment: str,
    index: int,
) -> Any:
    """OpenAI (GPT-5)形式のツール呼び出しチャンクを作成する。

    OpenAIは`tool_call_chunks`として部分的なargs文字列を送信する。
    """

    class OpenAIChunk:
        def __init__(self) -> None:
            self.type = "AIMessageChunk"
            self.content = ""
            self.tool_call_chunks = [
                {
                    "id": tool_call_id,
                    "name": tool_name,
                    "args": args_fragment,
                    "index": index,
                }
            ]

    return OpenAIChunk()


def create_tool_message_chunk(tool_call_id: str, tool_name: str, output: str) -> Any:
    """ツール実行結果のメッセージチャンクを作成する（両API共通）。"""

    class ToolChunk:
        def __init__(self) -> None:
            self.type = "tool"
            self.content = output
            self.tool_call_id = tool_call_id
            self.name = tool_name

    return ToolChunk()


# --- テストケース ---


@pytest.mark.integration
class TestToolInputStreamingSpec:
    """API仕様差分の検証テスト。"""

    def test_claude_input_json_delta_structure(self) -> None:
        """Claude APIのinput_json_delta形式を検証する。"""
        # Arrange: 3つのチャンクに分割されたJSON
        chunk1 = create_claude_tool_call_chunk("call_123", "get_weather", '{"location"')
        chunk2 = create_claude_tool_call_chunk("call_123", "get_weather", ': "Tokyo"')
        chunk3 = create_claude_tool_call_chunk("call_123", "get_weather", "}")

        # Act: partial_jsonを蓄積してパース
        accumulated_json = ""
        for chunk in [chunk1, chunk2, chunk3]:
            for content_item in chunk.content:
                if content_item.get("type") == "input_json_delta":
                    accumulated_json += content_item.get("partial_json", "")

        # Assert: 完全なJSONとしてパースできる
        parsed = json.loads(accumulated_json)
        assert parsed == {"location": "Tokyo"}
        assert isinstance(chunk1.content, list)
        assert chunk1.content[0]["type"] == "input_json_delta"

    def test_openai_tool_call_chunks_structure(self) -> None:
        """OpenAI APIのtool_call_chunks形式を検証する。"""
        # Arrange: 3つのチャンクに分割されたargs
        chunk1 = create_openai_tool_call_chunk("call_456", "get_weather", '{"location"', 0)
        chunk2 = create_openai_tool_call_chunk(None, None, ': "Tokyo"', 0)  # type: ignore
        chunk3 = create_openai_tool_call_chunk(None, None, "}", 0)  # type: ignore

        # Act: args断片を蓄積してパース
        accumulated_args = ""
        for chunk in [chunk1, chunk2, chunk3]:
            if hasattr(chunk, "tool_call_chunks"):
                for tcc in chunk.tool_call_chunks:
                    accumulated_args += tcc.get("args", "")

        # Assert: 完全なJSONとしてパースできる
        parsed = json.loads(accumulated_args)
        assert parsed == {"location": "Tokyo"}
        assert hasattr(chunk1, "tool_call_chunks")
        assert chunk1.tool_call_chunks[0]["index"] == 0

    def test_common_tool_message_structure(self) -> None:
        """両APIで共通のツールメッセージ構造を検証する。"""
        # Arrange
        tool_msg = create_tool_message_chunk("call_123", "get_weather", "Sunny, 25°C")

        # Assert: 両APIで同じ構造
        assert tool_msg.type == "tool"
        assert tool_msg.tool_call_id == "call_123"
        assert tool_msg.name == "get_weather"
        assert tool_msg.content == "Sunny, 25°C"

    def test_key_differences_between_apis(self) -> None:
        """API間の主要な差分を文書化する。"""
        # Claude形式の特徴
        claude_chunk = create_claude_tool_call_chunk("call_1", "test_tool", '{"key": "val"}')
        assert isinstance(claude_chunk.content, list)
        assert any(item.get("type") == "input_json_delta" for item in claude_chunk.content)

        # OpenAI形式の特徴
        openai_chunk = create_openai_tool_call_chunk("call_2", "test_tool", '{"key"', 0)
        assert hasattr(openai_chunk, "tool_call_chunks")
        assert isinstance(openai_chunk.tool_call_chunks, list)

        # 差分まとめ:
        # 1. Claude: content内のinput_json_delta (type="input_json_delta")
        # 2. OpenAI: tool_call_chunks属性 (argsフィールド + indexフィールド)
        # 3. 両方ともJSONを断片的に送信し、蓄積が必要


@pytest.mark.integration
class TestUnificationFeasibility:
    """共通化の可能性を評価するテスト。"""

    def test_can_detect_streaming_type_from_chunk_structure(self) -> None:
        """チャンク構造から自動的にストリーミングタイプを判別できるか検証する。"""
        claude_chunk = create_claude_tool_call_chunk("call_1", "test", '{"a":1}')
        openai_chunk = create_openai_tool_call_chunk("call_2", "test", '{"b"', 0)

        # Claudeの判別
        has_input_json_delta = isinstance(claude_chunk.content, list) and any(
            isinstance(item, dict) and item.get("type") == "input_json_delta" for item in claude_chunk.content
        )
        assert has_input_json_delta is True

        # OpenAIの判別
        has_tool_call_chunks = hasattr(openai_chunk, "tool_call_chunks") and bool(openai_chunk.tool_call_chunks)
        assert has_tool_call_chunks is True

        # 結論: 両方のパターンを単一の関数で処理可能
        # チャンク構造を検査して適切なロジックを選択できる

    def test_unified_accumulation_logic(self) -> None:
        """統一されたJSON蓄積ロジックの可能性を検証する。"""
        # 両APIとも最終的に完全なJSON文字列が必要
        # 差分は取得方法のみ

        # Claude形式からJSON断片を抽出
        claude_chunk = create_claude_tool_call_chunk("call_1", "test", '{"key":')
        claude_fragment = ""
        if isinstance(claude_chunk.content, list):
            for item in claude_chunk.content:
                if isinstance(item, dict) and item.get("type") == "input_json_delta":
                    claude_fragment = item.get("partial_json", "")

        # OpenAI形式からJSON断片を抽出
        openai_chunk = create_openai_tool_call_chunk("call_2", "test", '"value"}', 0)
        openai_fragment = ""
        if hasattr(openai_chunk, "tool_call_chunks"):
            for tcc in openai_chunk.tool_call_chunks:
                openai_fragment = tcc.get("args", "")

        # 抽出後のロジックは統一可能
        assert isinstance(claude_fragment, str)
        assert isinstance(openai_fragment, str)
        # どちらも文字列として蓄積し、最後にjson.loads()でパース

    def test_proposed_unified_interface(self) -> None:
        """提案する統一インターフェースの設計を検証する。"""

        def extract_tool_input_fragment(chunk: Any) -> str:
            """チャンクからツール入力の断片を抽出する統一メソッド。"""
            # Claudeのinput_json_deltaをチェック
            if isinstance(getattr(chunk, "content", None), list):
                for item in chunk.content:
                    if isinstance(item, dict) and item.get("type") == "input_json_delta":
                        return item.get("partial_json", "")

            # OpenAIのtool_call_chunksをチェック
            if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                # 通常は最初の要素のargsを返す
                for tcc in chunk.tool_call_chunks:
                    if isinstance(tcc, dict) and "args" in tcc:
                        return tcc.get("args", "")

            return ""

        # テスト
        claude_chunk = create_claude_tool_call_chunk("call_1", "test", '{"x":1}')
        openai_chunk = create_openai_tool_call_chunk("call_2", "test", '{"y":2}', 0)

        claude_result = extract_tool_input_fragment(claude_chunk)
        openai_result = extract_tool_input_fragment(openai_chunk)

        assert claude_result == '{"x":1}'
        assert openai_result == '{"y":2}'

        # 結論: 単一のヘルパー関数で両方のケースを処理可能


# --- 統合テスト用のフィクスチャ ---


@pytest.fixture
def sample_tool_streaming_scenario() -> dict[str, Any]:
    """ツールストリーミングのサンプルシナリオを提供する。"""
    return {
        "claude_chunks": [
            create_claude_tool_call_chunk("call_1", "calculate", '{"operation"'),
            create_claude_tool_call_chunk("call_1", "calculate", ': "multiply",'),
            create_claude_tool_call_chunk("call_1", "calculate", ' "values": [2, 3]}'),
            create_tool_message_chunk("call_1", "calculate", "6"),
        ],
        "openai_chunks": [
            create_openai_tool_call_chunk("call_2", "calculate", '{"operation"', 0),
            create_openai_tool_call_chunk(None, None, ': "multiply",', 0),  # type: ignore
            create_openai_tool_call_chunk(None, None, ' "values": [2, 3]}', 0),  # type: ignore
            create_tool_message_chunk("call_2", "calculate", "6"),
        ],
        "expected_input": {"operation": "multiply", "values": [2, 3]},
        "expected_output": "6",
    }


@pytest.mark.integration
def test_end_to_end_tool_streaming(sample_tool_streaming_scenario: dict[str, Any]) -> None:
    """エンドツーエンドのツールストリーミングシナリオを検証する。"""
    scenario = sample_tool_streaming_scenario

    # Claudeチャンクの処理
    claude_accumulated = ""
    for chunk in scenario["claude_chunks"][:-1]:  # 最後はツールメッセージ
        if isinstance(chunk.content, list):
            for item in chunk.content:
                if item.get("type") == "input_json_delta":
                    claude_accumulated += item.get("partial_json", "")

    claude_parsed = json.loads(claude_accumulated)
    assert claude_parsed == scenario["expected_input"]

    # OpenAIチャンクの処理
    openai_accumulated = ""
    for chunk in scenario["openai_chunks"][:-1]:  # 最後はツールメッセージ
        if hasattr(chunk, "tool_call_chunks"):
            for tcc in chunk.tool_call_chunks:
                openai_accumulated += tcc.get("args", "")

    openai_parsed = json.loads(openai_accumulated)
    assert openai_parsed == scenario["expected_input"]

    # 両方とも同じ結果を得る
    assert claude_parsed == openai_parsed
