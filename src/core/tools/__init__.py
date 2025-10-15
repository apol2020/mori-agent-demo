"""Tools module for agent functionality."""

from src.core.tools.activity_planner_tool import ActivityPlannerTool
from src.core.tools.data_search_tool import EventInfoTool, StoreHoursCheckTool, StoreInfoTool
from src.core.tools.event_search_tool import EventSearchTool
from src.core.tools.gift_recommendation_tool import GiftRecommendationTool
from src.core.tools.registry import ToolRegistry
from src.core.tools.user_analysis_tool import UserInterestAnalysisTool

# ツールレジストリのインスタンスを作成
tool_registry = ToolRegistry()

# ツールを登録（GetCurrentTimeToolは削除 - 現在時刻はシステムプロンプトに自動埋め込み）
tool_registry.register_tool(StoreInfoTool())
tool_registry.register_tool(EventInfoTool())
tool_registry.register_tool(EventSearchTool())
tool_registry.register_tool(StoreHoursCheckTool())
tool_registry.register_tool(UserInterestAnalysisTool())
tool_registry.register_tool(GiftRecommendationTool())
tool_registry.register_tool(ActivityPlannerTool())

__all__ = [
    "tool_registry",
    "StoreInfoTool",
    "EventInfoTool",
    "EventSearchTool",
    "StoreHoursCheckTool",
    "UserInterestAnalysisTool",
    "GiftRecommendationTool",
    "ActivityPlannerTool",
    "ToolRegistry",
]
