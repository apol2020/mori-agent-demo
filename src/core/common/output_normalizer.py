"""エージェント応答の出力正規化ユーティリティ。"""

import re
from typing import Any, Union

from src.utils.logger import get_logger

logger = get_logger(__name__)


class OutputNormalizer:
    """エージェント出力を一貫した文字列形式に正規化する。

    このユーティリティは、異なるエージェント実装からの様々な出力形式を処理し、
    標準的な文字列表現に正規化する。また、店舗IDなどの内部情報をユーザーから隠す機能も提供する。
    """

    @staticmethod
    def normalize(output: Any) -> str:
        """エージェント出力を文字列形式に正規化する。

        Args:
            output: エージェントからの出力（str、dict、list、その他の型）

        Returns:
            正規化された文字列出力（店舗IDなどの内部情報を除去済み）
        """
        if isinstance(output, str):
            return OutputNormalizer._remove_internal_info(output)

        if isinstance(output, list):
            # メッセージチャンクのリストからテキストを抽出
            text_content = ""
            for item in output:
                if isinstance(item, dict):
                    # 辞書アイテムを処理
                    if "text" in item:
                        text_content += item["text"]
                    elif "content" in item:
                        text_content += item["content"]
                elif isinstance(item, str):
                    text_content += item
            return OutputNormalizer._remove_internal_info(text_content)

        if isinstance(output, dict):
            # 単一の辞書出力を処理
            if "text" in output:
                return OutputNormalizer._remove_internal_info(str(output["text"]))
            if "content" in output:
                return OutputNormalizer._remove_internal_info(str(output["content"]))
            return OutputNormalizer._remove_internal_info(str(output))

        # その他の型の場合は文字列に変換
        return OutputNormalizer._remove_internal_info(str(output))

    @staticmethod
    def _remove_internal_info(text: str) -> str:
        """テキストから店舗IDなどの内部情報を除去する。

        Args:
            text: 処理対象のテキスト

        Returns:
            内部情報を除去したテキスト
        """
        # 店舗ID関連の説明文を先に除去（より具体的なパターンを先に処理）
        text = re.sub(r"店舗ID[：:]\s*STR-\d+", "", text)
        text = re.sub(r"\(STR-\d+\)", "", text)
        text = re.sub(r"[\(\[]STR-\d+[\)\]]", "", text)

        # store_id フィールドが含まれる場合の処理
        text = re.sub(r'"store_id":\s*"STR-\d+"[,\s]*', "", text)
        text = re.sub(r"store_id:\s*STR-\d+[,\s]*", "", text)

        # 店舗ID（STR-XXXX形式）を単体で除去（最後に処理）
        text = re.sub(r"STR-\d+", "", text)

        # 連続した空白やカンマを整理
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r",\s*,", ",", text)
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r"{\s*,", "{", text)

        return text.strip()

    @staticmethod
    def filter_store_data(
        data: Union[dict[str, Any], list[dict[str, Any]]],
    ) -> Union[dict[str, Any], list[dict[str, Any]]]:
        """店舗データから店舗IDを除去する。

        Args:
            data: 店舗データ（辞書または辞書のリスト）

        Returns:
            店舗IDを除去したデータ
        """
        if isinstance(data, list):
            return [OutputNormalizer._filter_single_store_data(item) for item in data]
        # dataはdict型のみ（Union型の残りの可能性）
        return OutputNormalizer._filter_single_store_data(data)

    @staticmethod
    def _filter_single_store_data(store_data: dict[str, Any]) -> dict[str, Any]:
        """単一の店舗データから店舗IDを除去する。

        Args:
            store_data: 店舗データ辞書

        Returns:
            店舗IDを除去した店舗データ
        """
        filtered_data = store_data.copy()
        # store_idフィールドを除去
        filtered_data.pop("store_id", None)

        return filtered_data
