"""イベントデータをSQLで検索するツール。"""

from pathlib import Path

from src.core.tools.base_sql_search_tool import BaseSQLSearchTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class EventSearchTool(BaseSQLSearchTool):
    """イベントデータをSQLクエリで検索するツール。"""

    def __init__(self) -> None:
        """イベント検索ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_file = self.project_root / "input" / "events.csv"
        self.table_name = "events.csv"

    @property
    def name(self) -> str:
        """ツール名。"""
        return "search_events"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """search_events: イベントデータと期間限定商品をSQLクエリで検索します。

【対象データ】
このツールで検索できるのは以下のデータです:
- イベント情報（展示会、キャンペーン、ワークショップなど）
- 期間限定商品（イベント期間中のみ販売される商品や限定キャンペーン商品）

【使用方法】
- SQLクエリを指定してイベント・期間限定商品情報を検索できます
- FROM句には 'events.csv' を指定してください
- SELECT文のみ使用可能です（INSERT/UPDATE/DELETE等は使用不可）

【重要な制約】
- 検索結果は最大10件までに制限されます
- クエリにLIMIT句がない場合、自動的に LIMIT 10 が追加されます
- LIMIT句を指定する場合も、10以下に制限されます

【データスキーマ】
テーブル名: events.csv

カラム:
- event_name (TEXT): イベント名/期間限定商品名
- description (TEXT): イベント・商品の説明
- date_time (TEXT): 開催日時・販売期間（YYYY-MM-DD形式または"開始日/終了日"形式）
- location (TEXT): 開催場所・販売場所（JSON形式: {"venue": "会場名", "address": "住所"}）
- capacity (TEXT): 定員
- source_url (TEXT): 情報元URL
- extracted_at (TEXT): データ抽出日時
- additional_info (TEXT): 追加情報
- contact_info (TEXT): 連絡先（JSON形式: {"phone": "電話番号", "email": "メールアドレス"}）
- cost (TEXT): 費用情報（JSON形式: {"is_free": true/false, "amount": "金額", "notes": "備考"}）
- registration_required (TEXT): 事前登録の要否（"True"または空文字）
- target_audience (TEXT): 対象者（JSON配列形式: ["家族", "子供"]）

【検索例】
1. イベント名・商品名で検索:
   SELECT * FROM 'events.csv' WHERE event_name LIKE '%BMW%'

2. 無料イベント・無料商品を検索:
   SELECT * FROM 'events.csv' WHERE cost LIKE '%"is_free": true%'

3. 特定期間のイベント・期間限定商品を検索:
   SELECT * FROM 'events.csv' WHERE date_time LIKE '2025-10%'

4. 特定会場のイベント・商品を検索:
   SELECT event_name, description, date_time FROM 'events.csv'
   WHERE location LIKE '%麻布台%'

5. 複数条件での検索:
   SELECT event_name, date_time, location FROM 'events.csv'
   WHERE description LIKE '%記念%' AND registration_required = 'True'
   ORDER BY date_time

【使用場面】
- 「期間限定の商品を教えて」→ このツールを使用
- 「今月のイベントは？」→ このツールを使用
- 「キャンペーン商品を検索」→ このツールを使用
- 通常商品の検索 → search_products ツールを使用
"""

    # execute, _validate_sql, _ensure_limit, _execute_duckdb_query は
    # BaseSQLSearchTool から継承
