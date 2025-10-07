"""Tools module for agent functionality."""

from src.core.tools.activity_planner_tool import ActivityPlannerTool
from src.core.tools.data_search_tool import DataSearchTool, EventInfoTool, StoreByIdTool, StoreInfoTool, StoreHoursCheckTool
from src.core.tools.gift_recommendation_tool import GiftRecommendationTool
from src.core.tools.registry import ToolRegistry
from src.core.tools.time_tool import GetCurrentTimeTool
from src.core.tools.user_analysis_tool import UserInterestAnalysisTool

# ツールレジストリのインスタンスを作成
tool_registry = ToolRegistry()

# ツールを登録
tool_registry.register_tool(GetCurrentTimeTool())
tool_registry.register_tool(DataSearchTool())
tool_registry.register_tool(StoreInfoTool())
tool_registry.register_tool(StoreByIdTool())
tool_registry.register_tool(EventInfoTool())
tool_registry.register_tool(StoreHoursCheckTool())
tool_registry.register_tool(UserInterestAnalysisTool())
tool_registry.register_tool(GiftRecommendationTool())
tool_registry.register_tool(ActivityPlannerTool())

__all__ = [
    "tool_registry",
    "GetCurrentTimeTool",
    "DataSearchTool",
    "StoreInfoTool",
    "StoreByIdTool",
    "EventInfoTool",
    "StoreHoursCheckTool",
    "UserInterestAnalysisTool",
    "GiftRecommendationTool",
    "ActivityPlannerTool",
    "ToolRegistry",
]
