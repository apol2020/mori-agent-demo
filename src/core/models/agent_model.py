"""チャットと会話管理のためのエージェントモデル。"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """メッセージロールの列挙型。"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolExecution(BaseModel):
    """ツール実行情報モデル。"""

    tool_name: str
    input_data: str
    output_data: str
    timestamp: datetime = Field(default_factory=datetime.now)


class TextPart(BaseModel):
    """テキストパートモデル（時系列表示用）。"""

    type: Literal["text"] = "text"
    content: str


class ToolPart(BaseModel):
    """ツール実行パートモデル（時系列表示用）。"""

    type: Literal["tool"] = "tool"
    tool_execution: ToolExecution


MessagePart = Union[TextPart, ToolPart]


class ChatMessage(BaseModel):
    """チャットメッセージモデル。"""

    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict[str, Any]] = None
    parts: list[MessagePart] = Field(default_factory=list)
