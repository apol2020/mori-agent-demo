"""ChatMessageとMessageRoleモデルのユニットテスト。"""

from datetime import datetime

from src.core.models.agent_model import ChatMessage, MessageRole, TextPart, ToolExecution, ToolPart


class TestMessageRole:
    """MessageRole列挙型のテスト。"""

    def test_message_role_values(self) -> None:
        """MessageRoleが正しい値を持つことを確認。"""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_message_role_is_string_enum(self) -> None:
        """MessageRoleがstr型のEnumであることを確認。"""
        assert isinstance(MessageRole.USER.value, str)
        assert MessageRole.USER.value == "user"


class TestChatMessage:
    """ChatMessageモデルのテスト。"""

    def test_create_chat_message_with_required_fields(self) -> None:
        """必須フィールドのみでChatMessageを作成できることを確認。"""
        message = ChatMessage(role=MessageRole.USER, parts=[TextPart(content="Hello")])

        assert message.role == MessageRole.USER
        assert len(message.parts) == 1
        assert message.parts[0].type == "text"
        assert message.parts[0].content == "Hello"
        assert isinstance(message.timestamp, datetime)
        assert message.metadata is None

    def test_create_chat_message_with_all_fields(self) -> None:
        """すべてのフィールドを指定してChatMessageを作成できることを確認。"""
        timestamp = datetime.now()
        metadata = {"source": "test", "version": "1.0"}
        message = ChatMessage(
            role=MessageRole.ASSISTANT, parts=[TextPart(content="Hi there")], timestamp=timestamp, metadata=metadata
        )

        assert message.role == MessageRole.ASSISTANT
        assert message.parts[0].content == "Hi there"
        assert message.timestamp == timestamp
        assert message.metadata == metadata

    def test_chat_message_timestamp_auto_generated(self) -> None:
        """timestampが自動生成されることを確認。"""
        before = datetime.now()
        message = ChatMessage(role=MessageRole.SYSTEM, parts=[TextPart(content="System message")])
        after = datetime.now()

        assert before <= message.timestamp <= after

    def test_chat_message_with_custom_metadata(self) -> None:
        """カスタムmetadataを設定できることを確認。"""
        metadata = {
            "user_id": "123",
            "session_id": "abc",
            "platform": "web",
            "nested": {"key": "value"},
        }
        message = ChatMessage(role=MessageRole.USER, parts=[TextPart(content="Test")], metadata=metadata)

        assert message.metadata == metadata
        assert message.metadata["user_id"] == "123"
        assert message.metadata["nested"]["key"] == "value"

    def test_chat_message_different_roles(self) -> None:
        """異なるロールでChatMessageを作成できることを確認。"""
        user_msg = ChatMessage(role=MessageRole.USER, parts=[TextPart(content="User message")])
        assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, parts=[TextPart(content="Assistant message")])
        system_msg = ChatMessage(role=MessageRole.SYSTEM, parts=[TextPart(content="System message")])

        assert user_msg.role == MessageRole.USER
        assert assistant_msg.role == MessageRole.ASSISTANT
        assert system_msg.role == MessageRole.SYSTEM

    def test_chat_message_empty_content(self) -> None:
        """空のcontentでChatMessageを作成できることを確認。"""
        message = ChatMessage(role=MessageRole.USER, parts=[TextPart(content="")])

        assert message.parts[0].content == ""
        assert message.role == MessageRole.USER

    def test_chat_message_long_content(self) -> None:
        """長いcontentでChatMessageを作成できることを確認。"""
        long_content = "a" * 10000
        message = ChatMessage(role=MessageRole.ASSISTANT, parts=[TextPart(content=long_content)])

        assert message.parts[0].content == long_content
        assert len(message.parts[0].content) == 10000

    def test_chat_message_immutability_with_pydantic(self) -> None:
        """PydanticモデルとしてChatMessageが機能することを確認。"""
        message = ChatMessage(role=MessageRole.USER, parts=[TextPart(content="Test")])

        # Pydanticモデルのフィールドにアクセスできることを確認
        assert message.model_fields_set == {"role", "parts"}

    def test_chat_message_dict_conversion(self) -> None:
        """ChatMessageを辞書に変換できることを確認。"""
        timestamp = datetime.now()
        metadata = {"key": "value"}
        message = ChatMessage(
            role=MessageRole.USER, parts=[TextPart(content="Test")], timestamp=timestamp, metadata=metadata
        )

        message_dict = message.model_dump()

        assert message_dict["role"] == "user"
        assert len(message_dict["parts"]) == 1
        assert message_dict["parts"][0]["type"] == "text"
        assert message_dict["parts"][0]["content"] == "Test"
        assert message_dict["timestamp"] == timestamp
        assert message_dict["metadata"] == metadata

    def test_chat_message_json_serialization(self) -> None:
        """ChatMessageをJSON文字列にシリアライズできることを確認。"""
        message = ChatMessage(role=MessageRole.ASSISTANT, parts=[TextPart(content="JSON test")])

        json_str = message.model_dump_json()

        assert isinstance(json_str, str)
        assert "assistant" in json_str
        assert "JSON test" in json_str

    def test_chat_message_with_tool_execution(self) -> None:
        """ツール実行を含むメッセージを作成できることを確認。"""
        tool_exec = ToolExecution(tool_name="test_tool", input_data="input", output_data="output")
        message = ChatMessage(
            role=MessageRole.ASSISTANT,
            parts=[TextPart(content="Before tool"), ToolPart(tool_execution=tool_exec), TextPart(content="After tool")],
        )

        assert len(message.parts) == 3
        assert message.parts[0].type == "text"
        assert message.parts[1].type == "tool"
        assert message.parts[2].type == "text"
        assert message.parts[1].tool_execution.tool_name == "test_tool"

    def test_chat_message_empty_parts(self) -> None:
        """空のpartsでメッセージを作成できることを確認。"""
        message = ChatMessage(role=MessageRole.ASSISTANT, parts=[])

        assert len(message.parts) == 0
        assert message.role == MessageRole.ASSISTANT
