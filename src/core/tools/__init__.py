"""Tools module for agent functionality."""

from src.core.tools.activity_planner_tool import ActivityPlannerTool
from src.core.tools.data_search_tool import DataSearchTool, EventInfoTool, StoreInfoTool
from src.core.tools.gift_recommendation_tool import GiftRecommendationTool
from src.core.tools.math_tool import MultiplyTool
from src.core.tools.registry import ToolRegistry
from src.core.tools.store_hours_tool import StoreHoursCheckTool
from src.core.tools.time_tool import GetCurrentTimeTool
from src.core.tools.user_analysis_tool import UserInterestAnalysisTool

# グローバルツールレジストリを作成
tool_registry = ToolRegistry()

# 既存のツールを明示的に登録
tool_registry.register_tool(GetCurrentTimeTool())
tool_registry.register_tool(MultiplyTool())

# データ検索ツールを登録
tool_registry.register_tool(DataSearchTool())
tool_registry.register_tool(StoreInfoTool())
tool_registry.register_tool(EventInfoTool())

# 営業時間チェックツールを登録
tool_registry.register_tool(StoreHoursCheckTool())

# ユーザー分析ツールを登録
tool_registry.register_tool(UserInterestAnalysisTool())

# ギフト提案ツールを登録
tool_registry.register_tool(GiftRecommendationTool())

# 活動計画ツールを登録
tool_registry.register_tool(ActivityPlannerTool())

__all__ = [
    "tool_registry",
    "ToolRegistry",
    "GetCurrentTimeTool",
    "MultiplyTool",
    "DataSearchTool",
    "StoreInfoTool",
    "EventInfoTool",
    "StoreHoursCheckTool",
    "UserInterestAnalysisTool",
    "GiftRecommendationTool",
    "ActivityPlannerTool"
]
