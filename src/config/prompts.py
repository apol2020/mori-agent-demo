"""エージェント用のプロンプトテンプレート設定。"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pytz

from src.core.tools import tool_registry
from src.utils.logger import get_logger

try:
    from langchain_core.messages import SystemMessage
except ImportError as e:
    raise ImportError("langchain-core is required. Install it with: pip install langchain-core") from e

logger = get_logger(__name__)


def _load_narrative_data() -> Optional[dict[str, Any]]:
    """ナラティブデータを読み込む。"""
    try:
        project_root = Path(__file__).parent.parent.parent
        narrative_file = project_root / "input" / "narrative_data.json"

        if narrative_file.exists():
            with open(narrative_file, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load narrative data: {e}")
    return None


def _get_current_time_jst() -> str:
    """日本時間の現在時刻を取得する。

    Returns:
        現在時刻の文字列（曜日情報を含む）
    """
    try:
        tz = pytz.timezone("Asia/Tokyo")
        current_datetime = datetime.now(tz)
        current_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

        # 曜日情報を追加
        weekdays = {0: "月曜日", 1: "火曜日", 2: "水曜日", 3: "木曜日", 4: "金曜日", 5: "土曜日", 6: "日曜日"}
        weekday_name = weekdays[current_datetime.weekday()]
        return f"{current_time} ({weekday_name})"
    except Exception as e:
        logger.error(f"Failed to get current time: {e}")
        return "時刻取得エラー"


def get_agent_system_prompt(user_analysis: Optional[dict[str, Any]] = None) -> SystemMessage:
    """エージェントのシステムプロンプトを取得する。

    このプロンプトは、エージェントの役割、振る舞い、制約を定義する。
    利用可能なツールはツールレジストリから動的に取得される。
    ユーザー分析結果を反映してパーソナライズされた回答を提供する。
    現在時刻は自動で取得してシステムプロンプトに埋め込まれる。

    Args:
        user_analysis: ユーザーの趣味嗜好分析結果

    Returns:
        SystemMessage: エージェント用のシステムメッセージ
    """
    # 現在時刻を取得（自動埋め込み）
    current_time_jst = _get_current_time_jst()

    # ツールレジストリからツール情報を取得
    tool_descriptions = tool_registry.get_tool_descriptions()

    # ツールリストを整形
    if tool_descriptions:
        tools_text = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in tool_descriptions])
    else:
        tools_text = "（現在利用可能なツールはありません）"

    # ナラティブデータを読み込み
    narrative_data = _load_narrative_data()

    # ユーザー分析に基づくパーソナライゼーション情報
    personalization_text = ""

    # ナラティブデータがある場合の情報
    if narrative_data:
        narrative_info = []
        if narrative_data.get("age"):
            narrative_info.append(f"年齢: {narrative_data['age']}歳")
        if narrative_data.get("gender"):
            narrative_info.append(f"性別: {narrative_data['gender']}")

        if narrative_info:
            personalization_text += f"\n\n**ユーザー基本情報:**\n{', '.join(narrative_info)}\n"

    if user_analysis and user_analysis.get("analysis_summary"):
        personalization_text += (
            f"\n**ユーザープロファイル（今回のセッション分析）:**\n{user_analysis['analysis_summary']}\n"
        )

    if personalization_text:
        personalization_text += (
            "\n上記のユーザー特性を踏まえて、年齢・性別・興味に合った店舗や情報を"
            "優先的に案内し、パーソナライズした提案を心がけてください。"
        )

    system_message_content = f"""あなたは麻布台ヒルズ総合案内AIアシスタントです。

[現在時刻: {current_time_jst}]

以下の原則に従って対話してください:

1. **専門性**: 麻布台ヒルズの店舗・イベント情報に特化したサポートを提供します
2. **正確性**: 現在時刻と営業時間データを照合して、正確な営業状況を判定します
3. **明確性**: 営業中/営業時間外の状況を分かりやすく説明します
4. **即時性**: ユーザーが店舗名を聞いた時は、即座に現在の営業状況をチェックします
5. **口調**: 口調はカジュアルな口調で対話します(敬語は使わないでください)
6. **対話的なニーズ把握**: ユーザーから「何かイベントはありますか？」「おすすめの店舗はありますか？」のような
    漠然とした質問があった場合は、すぐにツールを使って検索するのではなく、まずユーザーのニーズを深掘りする質問をしてください。
    例:
    - 「何かイベントはありますか？」→「どんな雰囲気のイベントを探してる？音楽系、アート系、それとも体験型？」
    - 「おすすめの店舗はありますか？」→「どんなお店に興味ある？食事、ショッピング、それとも他の何か？」
    - 「何か食べたい」→「和食、洋食、それともアジア料理とか？今日の気分はどんな感じ？」
    ユーザーの好みや状況を2〜3回の質問で引き出してから、適切なツールを使って検索を行ってください

**マークダウン記法のルール:**
- **見出し**: `##`または`###`で始め、記号の後には必ずスペースを入れる
- **太字**: `**テキスト**`の形式（例: `**開催日**: 10/17`）
- **店舗紹介フォーマット**:
  - 店舗名は `### 店舗名` のみ（説明文は含めない）
  - 説明文は見出しの次の行に普通の文として書く
  - 詳細情報は箇条書き（`-`）で各項目を改行して記載
  - 最後にコメントや補足を通常文で追加
- **通常の文章**: 絵文字で始まる文章でも見出し記号（`##`/`###`）は付けない
- **リスト**: 各項目を `-` で箇条書きにし、必ず改行する
- **リスト後**: 箇条書き終了後は空行を入れてから次の文を書く

利用可能なツール:
{tools_text}{personalization_text}
"""

    return SystemMessage(content=system_message_content)
