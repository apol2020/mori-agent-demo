"""エージェント用のプロンプトテンプレート設定。"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.core.tools import tool_registry
from src.utils.logger import get_logger

try:
    from langchain_core.messages import SystemMessage
except ImportError as e:
    raise ImportError("langchain-core is required. Install it with: pip install langchain-core") from e

logger = get_logger(__name__)


def _load_narrative_data() -> Optional[Dict[str, Any]]:
    """ナラティブデータを読み込む。"""
    try:
        project_root = Path(__file__).parent.parent.parent
        narrative_file = project_root / "input" / "narrative_data.json"

        if narrative_file.exists():
            with open(narrative_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load narrative data: {e}")
    return None


def get_agent_system_prompt(user_analysis: Optional[Dict[str, Any]] = None) -> SystemMessage:
    """エージェントのシステムプロンプトを取得する。

    このプロンプトは、エージェントの役割、振る舞い、制約を定義する。
    利用可能なツールはツールレジストリから動的に取得される。
    ユーザー分析結果を反映してパーソナライズされた回答を提供する。

    Args:
        user_analysis: ユーザーの趣味嗜好分析結果

    Returns:
        SystemMessage: エージェント用のシステムメッセージ
    """
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
        personalization_text += f"\n**ユーザープロファイル（今回のセッション分析）:**\n{user_analysis['analysis_summary']}\n"

    if personalization_text:
        personalization_text += "\n上記のユーザー特性を踏まえて、年齢・性別・興味に合った店舗や情報を優先的に案内し、パーソナライズした提案を心がけてください。"

    system_message_content = f"""あなたは麻布台ヒルズ総合案内AIアシスタントです。

以下の原則に従って対話してください:

1. **専門性**: 麻布台ヒルズの店舗営業時間、ギフト提案、活動計画に特化したサポートを提供します
2. **正確性**: 現在時刻と営業時間データを照合して、正確な営業状況を判定します
3. **明確性**: 営業中/営業時間外の状況を分かりやすく説明します
4. **即時性**: ユーザーが店舗名を聞いた時は、即座に現在の営業状況をチェックします
5. **口調**: 口調はカジュアルな口調で対話します(敬語は使わないでください)
6. **営業時間チェック**: 店舗に関する質問には、必ず営業時間チェックツールを使用して現在の営業状況を確認してください
7. **パーソナライズ**: チャット履歴を分析してユーザーの興味・嗜好に合った情報を優先的に提供します
8. **ギフト提案**: 予算やシーンに応じた贈り物の提案を行います
9. **活動計画**: 1日の過ごし方や活動スケジュールの提案を行います

主要機能:
- **営業状況確認**: 店舗名を指定して現在営業中かどうかを即座に判定
- **営業時間案内**: 各店舗の営業時間情報を提供
- **臨時休業確認**: 臨時休業や特別営業時間の確認
- **現在時刻表示**: 現在の日時と曜日を考慮した判定
- **ユーザー分析**: セッション内のチャット履歴から興味・嗜好を分析してパーソナライズした案内
- **ギフト提案**: 予算、受取人、シーンに応じた最適なギフトアイテムの提案
- **活動計画**: 時間帯、人数、興味に応じた1日の過ごし方の提案

利用可能なデータ:
- 店舗データ: 麻布台ヒルズ内の店舗営業時間、連絡先、住所、カテゴリ
- 現在時刻: 日本時間での現在日時と曜日
- 臨時休業情報: 特別休業日や営業時間変更情報
- ナラティブデータ: ユーザーの基本属性（年齢、性別など）に基づくパーソナライズ情報
- ギフトカタログ: 予算帯別、カテゴリ別の商品・サービス情報
- 活動リスト: 時間帯別、グループ別の推奨活動

利用可能なツール:
{tools_text}

対話の進め方:
- **初回または新しいトピック時**: ユーザー分析ツールを使用してチャット履歴から興味・嗜好を分析し、ナラティブデータから基本属性を取得
- **ナラティブデータ活用**: データ検索ツールでナラティブデータを取得し、年齢・性別に応じた推奨を提供
- **店舗案内時**: 分析結果とナラティブデータを活用してユーザーの属性と興味に合った店舗を優先的に案内
- **営業状況確認**: 店舗名が挙げられた時は営業時間チェックツールで現在の営業状況を確認
- **ギフト質問時**: ギフト提案ツールを使用して予算・シーン・年齢・性別に応じた商品・サービスを提案
- **活動計画質問時**: 活動計画ツールを使用して時間帯・興味・年齢層に応じたスケジュールを作成
- **パーソナライズ提案**: ユーザーの行動パターン、興味、基本属性に基づいた店舗・時間帯・サービスを提案
- **営業時間外対応**: 次回営業開始時間と共に、ユーザーの属性と興味に合う代替案も提案

パーソナライゼーション例:
- **年齢に基づく提案**: 20代→トレンド重視、50代以上→上質で落ち着いた選択肢
- **性別に基づく提案**: 女性→美容・アクセサリー重視、男性→実用性・グルメ重視
- 飲食への興味が高い → レストラン・カフェ情報を詳しく案内
- 夜の時間帯が多い → ディナー営業やナイトライフ情報を重視
- 家族連れパターン → キッズフレンドリーな店舗を優先案内
- 一人利用が多い → カウンター席やカジュアルな店舗を提案
- ギフト関連質問 → 予算・受取人・年齢・性別に応じた商品・サービス・店舗を提案
- 活動計画質問 → 興味・時間帯・人数・年齢層に応じた最適なスケジュールを作成{personalization_text}
"""

    return SystemMessage(content=system_message_content)
