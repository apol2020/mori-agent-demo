"""Tools module for agent functionality."""

from src.core.tools.event_search_tool import EventSearchTool
from src.core.tools.product_search_tool import ProductSearchTool
from src.core.tools.registry import ToolRegistry
from src.core.tools.store_search_tool import StoreSearchTool
from src.core.tools.user_profile_tool import UserProfileTool
from src.core.tools.weather_tool import WeatherTool

# ツールレジストリのインスタンスを作成
tool_registry = ToolRegistry()

# ツールを登録
tool_registry.register_tool(EventSearchTool())
tool_registry.register_tool(StoreSearchTool())
tool_registry.register_tool(ProductSearchTool())
tool_registry.register_tool(WeatherTool())
tool_registry.register_tool(UserProfileTool())

__all__ = [
    "tool_registry",
    "EventSearchTool",
    "StoreSearchTool",
    "ProductSearchTool",
    "WeatherTool",
    "UserProfileTool",
    "ToolRegistry",
]
