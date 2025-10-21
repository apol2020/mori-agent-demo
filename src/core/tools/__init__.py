"""Tools module for agent functionality."""

from src.core.tools.data_search_tool import EventInfoTool, StoreHoursCheckTool, StoreInfoTool
from src.core.tools.event_search_tool import EventSearchTool
from src.core.tools.registry import ToolRegistry
from src.core.tools.store_search_tool import StoreSearchTool
from src.core.tools.weather_tool import WeatherTool

# ツールレジストリのインスタンスを作成
tool_registry = ToolRegistry()

# ツールを登録
tool_registry.register_tool(StoreInfoTool())
tool_registry.register_tool(EventInfoTool())
tool_registry.register_tool(EventSearchTool())
tool_registry.register_tool(StoreSearchTool())
tool_registry.register_tool(StoreHoursCheckTool())
tool_registry.register_tool(WeatherTool())

__all__ = [
    "tool_registry",
    "StoreInfoTool",
    "EventInfoTool",
    "EventSearchTool",
    "StoreSearchTool",
    "StoreHoursCheckTool",
    "WeatherTool",
    "ToolRegistry",
]
