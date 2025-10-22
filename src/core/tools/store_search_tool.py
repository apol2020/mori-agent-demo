"""店舗データをSQLで検索するツール。"""

from pathlib import Path

from src.core.tools.base_sql_search_tool import BaseSQLSearchTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StoreSearchTool(BaseSQLSearchTool):
    """店舗データをSQLクエリで検索するツール。"""

    def __init__(self) -> None:
        """店舗検索ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_file = self.project_root / "input" / "filtered_store_data_カテゴリー情報あり.csv"
        self.table_name = "stores.csv"

    @property
    def name(self) -> str:
        """ツール名。"""
        return "search_stores"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """search_stores: 店舗データをSQLクエリで検索します。

【使用方法】
- SQLクエリを指定して店舗情報を検索できます
- FROM句には 'stores.csv' を指定してください
- SELECT文のみ使用可能です（INSERT/UPDATE/DELETE等は使用不可）

【重要な制約】
- 検索結果は最大10件までに制限されます
- クエリにLIMIT句がない場合、自動的に LIMIT 10 が追加されます
- LIMIT句を指定する場合も、10以下に制限されます

【データスキーマ】
テーブル名: stores.csv

カラム:
- store_id (TEXT): 店舗ID（例: "STR-0001"）
- store_name (TEXT): 店舗名
- description (TEXT): 店舗の説明
- category (TEXT): カテゴリ（"retail", "restaurant", "cafe"など）
- opening_hours (TEXT): 営業時間（JSON形式: {"monday": [{"open": "10:00", "close": "20:00"}], ...}）
- irregular_closures (TEXT): 臨時休業情報（JSON配列形式）
- phone (TEXT): 電話番号
- email (TEXT): メールアドレス
- address (TEXT): 住所
- Biz_Entertainment_Available (TEXT): ビジネス・エンターテインメント利用可否（"TRUE"または空文字）
- private_room (TEXT): 個室情報（JSON形式: {"available": true/false, "capacity": 数値, "charge": "説明"}）
- pets_allowed (TEXT): ペット同伴可否（"TRUE"または空文字）
- target_audience (TEXT): 対象客層（JSON配列形式: ["ファミリー", "ビジネス"]）
- store_exclusive_events (TEXT): 店舗独自イベント
- menu (TEXT): メニュー情報
- seasonal_items (TEXT): 季節商品情報
- allergy_info (TEXT): アレルギー情報
- gluten_free_info (TEXT): グルテンフリー情報
- vegan_info (TEXT): ヴィーガン情報
- kids_info (TEXT): 子供向け情報（JSON形式: {"kids_menu": bool, "highchair": bool, "diaper_changing": bool}）
- halal_info (TEXT): ハラール情報
- reservations (TEXT): 予約情報
- restroom_info (TEXT): トイレ情報
- accessibility (TEXT): バリアフリー情報
- parking (TEXT): 駐車場情報（JSON形式: {"available": bool, "capacity": 数値, "charge": "説明"}）
- nursing_room (TEXT): 授乳室情報
- access_route (TEXT): アクセス方法
- extraction_status (TEXT): データ抽出ステータス（"success"または"error"）
- error_message (TEXT): エラーメッセージ

【検索例】
1. 店舗名で検索:
   SELECT * FROM 'stores.csv' WHERE store_name LIKE '%ヒルズ%'

2. カテゴリで検索:
   SELECT * FROM 'stores.csv' WHERE category = 'retail'

3. 駐車場がある店舗を検索:
   SELECT store_name, address, parking FROM 'stores.csv'
   WHERE parking LIKE '%"available": true%'

4. ファミリー向けの店舗を検索:
   SELECT store_name, description, target_audience FROM 'stores.csv'
   WHERE target_audience LIKE '%ファミリー%'

5. 個室が利用可能な店舗を検索:
   SELECT store_name, phone, private_room FROM 'stores.csv'
   WHERE private_room LIKE '%"available": true%'

6. 特定のエリア（住所）で検索:
   SELECT * FROM 'stores.csv' WHERE address LIKE '%麻布台%'

7. ビジネス利用可能な店舗を検索:
   SELECT * FROM 'stores.csv' WHERE Biz_Entertainment_Available = 'TRUE'

8. ペット同伴可能な店舗を検索:
   SELECT * FROM 'stores.csv' WHERE pets_allowed = 'TRUE'
"""

    # execute, _validate_sql, _ensure_limit, _execute_duckdb_query は
    # BaseSQLSearchTool から継承
