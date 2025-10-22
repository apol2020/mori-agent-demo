"""UserProfileToolのユニットテスト。"""

import pytest

from src.core.tools.user_profile_tool import UserProfileTool


@pytest.fixture
def user_profile_tool():
    """UserProfileToolのフィクスチャ。"""
    return UserProfileTool()


class TestUserProfileTool:
    """UserProfileToolのテストクラス。"""

    def test_tool_name(self, user_profile_tool):
        """ツール名が正しいことを確認。"""
        assert user_profile_tool.name == "get_user_profile"

    def test_tool_description(self, user_profile_tool):
        """ツールの説明が存在することを確認。"""
        assert len(user_profile_tool.description) > 0
        assert "get_user_profile" in user_profile_tool.description
        assert "profile_id" in user_profile_tool.description

    def test_execute_valid_profile_id(self, user_profile_tool):
        """正常なprofile_idで実行できることを確認。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        assert "profile_id" in result
        assert result["profile_id"] == "user_criollo_heavy"
        assert "age" in result
        assert "gender" in result
        assert "user_type" in result
        assert "primary_store_id" in result
        assert "primary_store_name" in result
        assert "visits" in result
        assert "narrative" in result

    def test_execute_without_profile_id(self, user_profile_tool):
        """profile_id未指定で実行した場合のエラー処理を確認。"""
        result = user_profile_tool.execute()
        assert "error" in result
        assert "profile_idを指定してください" in result["error"]

    def test_execute_nonexistent_profile_id(self, user_profile_tool):
        """存在しないprofile_idでエラーが返ることを確認。"""
        result = user_profile_tool.execute(profile_id="nonexistent_user")
        assert "error" in result
        assert "ユーザーが見つかりません" in result["error"]

    def test_execute_result_structure(self, user_profile_tool):
        """結果の構造が正しいことを確認（8つのキーが存在）。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        # エラーがないことを確認
        assert "error" not in result
        # 8つのカラムが全て存在することを確認
        expected_keys = [
            "profile_id",
            "age",
            "gender",
            "user_type",
            "primary_store_id",
            "primary_store_name",
            "visits",
            "narrative",
        ]
        for key in expected_keys:
            assert key in result, f"Expected key '{key}' not found in result"

    def test_execute_narrative_field(self, user_profile_tool):
        """narrativeフィールドが文字列で取得できることを確認。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        assert "narrative" in result
        assert isinstance(result["narrative"], str)
        assert len(result["narrative"]) > 0

    def test_execute_numeric_fields(self, user_profile_tool):
        """age, visitsが数値型で取得できることを確認。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        assert "age" in result
        assert "visits" in result
        # 整数型であることを確認
        assert isinstance(result["age"], int)
        assert isinstance(result["visits"], int)
        # 妥当な値であることを確認
        assert result["age"] > 0
        assert result["visits"] > 0

    def test_execute_user_criollo_heavy_details(self, user_profile_tool):
        """user_criollo_heavyの詳細情報が正しく取得できることを確認。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        # 基本情報の確認
        assert result["age"] == 28
        assert result["gender"] == "女性"
        assert result["user_type"] == "特定店舗ロイヤルカスタマー"
        assert result["primary_store_id"] == "STR-0014"
        assert result["primary_store_name"] == "洋菓子店クリオロ"
        assert result["visits"] == 26
        # narrativeにキーワードが含まれることを確認
        assert "クリオロ" in result["narrative"]

    def test_execute_empty_profile_id(self, user_profile_tool):
        """空文字列のprofile_idでエラーが返ることを確認。"""
        result = user_profile_tool.execute(profile_id="")
        assert "error" in result
        assert "profile_idを指定してください" in result["error"]

    def test_execute_returns_single_user_only(self, user_profile_tool):
        """1ユーザーのみが返されることを確認（セキュリティ制約）。"""
        result = user_profile_tool.execute(profile_id="user_criollo_heavy")
        # エラーでないことを確認
        assert "error" not in result
        # 結果が辞書であることを確認（リストではない）
        assert isinstance(result, dict)
        # profile_idが1つだけであることを確認
        assert result["profile_id"] == "user_criollo_heavy"
