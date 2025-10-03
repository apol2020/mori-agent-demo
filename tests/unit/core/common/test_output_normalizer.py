"""OutputNormalizerのユニットテスト。"""

from src.core.common.output_normalizer import OutputNormalizer


class TestOutputNormalizer:
    """OutputNormalizerのテスト。"""

    def test_normalize_string_input(self) -> None:
        """文字列入力がそのまま返されることを確認。"""
        result = OutputNormalizer.normalize("Hello, World!")
        assert result == "Hello, World!"

    def test_normalize_empty_string(self) -> None:
        """空文字列がそのまま返されることを確認。"""
        result = OutputNormalizer.normalize("")
        assert result == ""

    def test_normalize_integer(self) -> None:
        """整数が文字列に変換されることを確認。"""
        result = OutputNormalizer.normalize(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_normalize_float(self) -> None:
        """浮動小数点数が文字列に変換されることを確認。"""
        result = OutputNormalizer.normalize(3.14)
        assert result == "3.14"
        assert isinstance(result, str)

    def test_normalize_boolean(self) -> None:
        """真偽値が文字列に変換されることを確認。"""
        result_true = OutputNormalizer.normalize(True)
        result_false = OutputNormalizer.normalize(False)
        assert result_true == "True"
        assert result_false == "False"

    def test_normalize_none(self) -> None:
        """Noneが文字列に変換されることを確認。"""
        result = OutputNormalizer.normalize(None)
        assert result == "None"
        assert isinstance(result, str)

    def test_normalize_dict_with_text_key(self) -> None:
        """textキーを持つ辞書が正しく正規化されることを確認。"""
        input_dict = {"text": "Response from agent"}
        result = OutputNormalizer.normalize(input_dict)
        assert result == "Response from agent"

    def test_normalize_dict_with_content_key(self) -> None:
        """contentキーを持つ辞書が正しく正規化されることを確認。"""
        input_dict = {"content": "Agent response content"}
        result = OutputNormalizer.normalize(input_dict)
        assert result == "Agent response content"

    def test_normalize_dict_without_special_keys(self) -> None:
        """特別なキーを持たない辞書が文字列に変換されることを確認。"""
        input_dict = {"key1": "value1", "key2": "value2"}
        result = OutputNormalizer.normalize(input_dict)
        assert isinstance(result, str)
        assert "key1" in result
        assert "value1" in result

    def test_normalize_list_of_dicts_with_text(self) -> None:
        """textキーを持つ辞書のリストが正しく連結されることを確認。"""
        input_list = [{"text": "Hello "}, {"text": "World"}]
        result = OutputNormalizer.normalize(input_list)
        assert result == "Hello World"

    def test_normalize_list_of_dicts_with_content(self) -> None:
        """contentキーを持つ辞書のリストが正しく連結されることを確認。"""
        input_list = [{"content": "First "}, {"content": "Second"}]
        result = OutputNormalizer.normalize(input_list)
        assert result == "First Second"

    def test_normalize_list_of_strings(self) -> None:
        """文字列のリストが連結されることを確認。"""
        input_list = ["Hello", " ", "World"]
        result = OutputNormalizer.normalize(input_list)
        assert result == "Hello World"

    def test_normalize_empty_list(self) -> None:
        """空のリストが空文字列を返すことを確認。"""
        result = OutputNormalizer.normalize([])
        assert result == ""

    def test_normalize_mixed_list(self) -> None:
        """混合型のリストが正しく処理されることを確認。"""
        input_list = [
            {"text": "Hello "},
            "middle ",
            {"content": "World"},
            {"other_key": "ignored"},
        ]
        result = OutputNormalizer.normalize(input_list)
        assert "Hello " in result
        assert "middle " in result
        assert "World" in result

    def test_normalize_nested_dict_with_text(self) -> None:
        """textキーを持つネストされた辞書が正しく処理されることを確認。"""
        input_dict = {"text": "Outer text", "nested": {"text": "Inner text"}}
        result = OutputNormalizer.normalize(input_dict)
        assert result == "Outer text"

    def test_normalize_list_with_empty_dicts(self) -> None:
        """空の辞書を含むリストが正しく処理されることを確認。"""
        input_list = [{"text": "Before"}, {}, {"content": "After"}]
        result = OutputNormalizer.normalize(input_list)
        assert "Before" in result
        assert "After" in result

    def test_normalize_preserves_whitespace(self) -> None:
        """ホワイトスペースが保持されることを確認。"""
        result = OutputNormalizer.normalize("  Hello  \n  World  ")
        assert result == "  Hello  \n  World  "

    def test_normalize_unicode_text(self) -> None:
        """Unicode文字が正しく処理されることを確認。"""
        unicode_text = "こんにちは世界 🌍"
        result = OutputNormalizer.normalize(unicode_text)
        assert result == unicode_text

    def test_normalize_list_with_unicode_dicts(self) -> None:
        """Unicode文字を含む辞書のリストが正しく処理されることを確認。"""
        input_list = [{"text": "日本語"}, {"content": "テキスト"}]
        result = OutputNormalizer.normalize(input_list)
        assert result == "日本語テキスト"

    def test_normalize_complex_nested_structure(self) -> None:
        """複雑にネストされた構造が正しく処理されることを確認。"""
        input_list = [
            {"text": "Start "},
            "middle ",
            {"content": "end"},
            {"ignored": "value"},
        ]
        result = OutputNormalizer.normalize(input_list)
        assert "Start " in result
        assert "middle " in result
        assert "end" in result

    def test_normalize_dict_with_integer_values(self) -> None:
        """整数値を含む辞書が正しく処理されることを確認。"""
        input_dict = {"text": 12345}
        result = OutputNormalizer.normalize(input_dict)
        assert result == "12345"
