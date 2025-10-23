"""UserProfileToolのユニットテスト。"""

import pytest

from src.core.tools.user_profile_tool import UserProfileTool


@pytest.fixture
def user_profile_tool():
    """UserProfileToolのフィクスチャ（user001としてログイン）。"""
    return UserProfileTool(username="user001")


class TestUserProfileTool:
    """UserProfileToolのテストクラス。"""

    def test_tool_name(self, user_profile_tool):
        """ツール名が正しいことを確認。"""
        assert user_profile_tool.name == "get_user_profile"

    def test_tool_description(self, user_profile_tool):
        """ツールの説明が存在することを確認。"""
        assert len(user_profile_tool.description) > 0
        assert "get_user_profile" in user_profile_tool.description

    def test_execute_without_params(self, user_profile_tool):
        """パラメータなしで実行した場合、ログイン中のユーザー情報を取得できることを確認。"""
        result = user_profile_tool.execute()
        # エラーがないことを確認
        assert "error" not in result
        # user001のデータが取得できていることを確認
        assert result["username"] == "user001"
        assert result["profile_id"] == "user_criollo_heavy"
        assert result["age"] == 28
        assert result["gender"] == "女性"

    def test_execute_result_structure(self, user_profile_tool):
        """結果の構造が正しいことを確認（5つのキーが存在）。"""
        result = user_profile_tool.execute()
        # エラーがないことを確認
        assert "error" not in result
        # 5つのカラムが全て存在することを確認
        expected_keys = [
            "username",
            "profile_id",
            "age",
            "gender",
            "preferences",
        ]
        for key in expected_keys:
            assert key in result, f"Expected key '{key}' not found in result"

    def test_execute_preferences_field(self, user_profile_tool):
        """preferencesフィールドが文字列で取得できることを確認。"""
        result = user_profile_tool.execute()
        assert "preferences" in result
        assert isinstance(result["preferences"], str)
        assert len(result["preferences"]) > 0

    def test_execute_numeric_fields(self, user_profile_tool):
        """ageが数値型で取得できることを確認。"""
        result = user_profile_tool.execute()
        assert "age" in result
        # 整数型であることを確認
        assert isinstance(result["age"], int)
        # 妥当な値であることを確認
        assert result["age"] > 0

    def test_execute_user001_details(self, user_profile_tool):
        """user001の詳細情報が正しく取得できることを確認。"""
        result = user_profile_tool.execute()
        # 基本情報の確認
        assert result["username"] == "user001"
        assert result["profile_id"] == "user_criollo_heavy"
        assert result["age"] == 28
        assert result["gender"] == "女性"
        # preferencesにキーワードが含まれることを確認
        assert "チョコレート" in result["preferences"] or "洋菓子" in result["preferences"]

    def test_execute_user002(self):
        """user002でログインした場合の動作を確認。"""
        tool = UserProfileTool(username="user002")
        result = tool.execute()
        # エラーがないことを確認
        assert "error" not in result
        # user002のデータが取得できていることを確認
        assert result["username"] == "user002"
        assert result["profile_id"] == "user_diverse_frequent"
        assert result["age"] == 35
        assert result["gender"] == "男性"

    def test_execute_without_login(self):
        """ログインしていない場合のエラー処理を確認。"""
        tool = UserProfileTool()  # usernameなし
        result = tool.execute()
        assert "error" in result
        assert "ログイン情報が見つかりません" in result["error"]

    def test_execute_returns_single_user_only(self, user_profile_tool):
        """1ユーザーのみが返されることを確認（セキュリティ制約）。"""
        result = user_profile_tool.execute()
        # エラーでないことを確認
        assert "error" not in result
        # 結果が辞書であることを確認（リストではない）
        assert isinstance(result, dict)
        # profile_idが1つだけであることを確認
        assert result["profile_id"] == "user_criollo_heavy"
