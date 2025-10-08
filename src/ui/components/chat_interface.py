"""エージェント会話用のチャットインターフェースコンポーネント。"""

from typing import Optional

import streamlit as st

from src.core.models.agent_model import ChatMessage, MessageRole, ToolExecution
from src.ui.config.tool_display_config import ToolDisplayConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _format_message_content(content: str) -> str:
    """メッセージコンテンツの改行と段落分けを適切にフォーマットする。

    Args:
        content: 元のメッセージコンテンツ

    Returns:
        フォーマット済みのメッセージコンテンツ
    """
    if not content:
        return content

    # まず基本的な改行処理を行う
    content = content.replace('\r\n', '\n').replace('\r', '\n')

    # 特定のパターンで改行を強制的に追加
    import re

    # 1. 感嘆符や句読点の後で文章が続く場合に改行を追加
    content = re.sub(r'([！!？?。])([^\n\s])', r'\1\n\n\2', content)

    # 2. 「だね！」「するよ。」などの文章終了パターンの後に改行
    content = re.sub(r'(だね[！!])([^\n])', r'\1\n\n\2', content)
    content = re.sub(r'(するよ[。])([^\n])', r'\1\n\n\2', content)
    content = re.sub(r'(だから[、,])([^\n])', r'\1\n\n\2', content)

    # 3. 絵文字の後に改行を追加（絵文字 + テキストの組み合わせ、ただしリスト項目は除く）
    content = re.sub(r'(🥗|☕|🍰|📍|⏰|💡|🌟|🍽️|🥐|📸)(\s*)([^\n\s-])', r'\1\n\n\3', content)
    # 絵文字の後のリスト項目は適切に処理
    content = re.sub(r'(🥗|☕|🍰|📍|⏰|💡|🌟|🍽️|🥐|📸)(\s+)(-\s+)', r'\1\n\2\3', content)

    # 4. リストアイテム（-で始まる、数字で始まる）の前に改行を追加（ただし絵文字の直後は除く）
    content = re.sub(r'([^\n🥐📸🍰🥗])(\s*-\s+)', r'\1\n\n\2', content)
    # 番号付きリスト（1. 2. 3.など）の前に改行を追加
    content = re.sub(r'([^\n])(\s*\d+\.\s+)', r'\1\n\n\2', content)

    # 5. 見出し（##や###）の前後に改行を追加
    content = re.sub(r'([^\n])(#+\s+)', r'\1\n\n\2', content)
    content = re.sub(r'(#+\s+[^\n]+)([^\n])', r'\1\n\n\2', content)

    # 6. 「例えば：」「現在」「麻布台ヒルズ」などの重要なキーワードの前に改行
    important_keywords = [
        r'(例えば：)',
        r'(現在[^\n]{1,10}だから)',
        r'(麻布台ヒルズ)',
        r'(分析結果から)',
        r'(予算の希望)',
        r'(具体的に)',
    ]

    for pattern in important_keywords:
        content = re.sub(r'([^\n])' + pattern, r'\1\n\n\2', content)

    # 7. 特定の文字列パターンの後に改行を追加（ただしリスト項目の一部を除く）
    patterns_for_newline = [
        r'(あなたにぴったりのランチスタイル：)',
        r'(カフェスタイルランチ)',
        r'(スイーツも楽しめるお店)',
        r'(提案するよ)',
        r'(タイミングだね)',
        r'(おすすめ：)',
        r'(対応してるよ！)',
        r'(できるよ！)',
        r'(チェックできるよ！)',
        r'(探してみる！)',
        r'(調べてみるね！)',
        r'(見つかったよ！)',
        r'(開催中)',
        r'(スポット（現在\d+:\d+）)',
    ]

    for pattern in patterns_for_newline:
        content = re.sub(pattern + r'([^\n])', r'\1\n\2', content)

    # 8. 長い文章を適切に分割（50文字以上の行）
    lines = content.split('\n')
    processed_lines = []

    for line in lines:
        line = line.strip()
        if len(line) > 80 and '。' in line:
            # 句点で文章を分割
            sentences = line.split('。')
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    if i < len(sentences) - 1:
                        processed_lines.append(sentence.strip() + '。')
                    else:
                        processed_lines.append(sentence.strip())
        else:
            processed_lines.append(line)

    # 9. 視覚的な改善: カテゴリ見出しと絵文字の追加
    enhanced_lines = []
    for line in processed_lines:
        line = line.strip()
        if line:
            # カテゴリ見出しに絵文字と太字を追加
            if re.match(r'^(トレンディ[&＆]おしゃれ系|ヘルシー志向|気軽に楽しめる|ベーカリー[・･]カフェ系|スイーツ[・･]デザート系|デリ[・･]軽食系)', line):
                # 適切な絵文字を選択
                if 'トレンディ' in line or 'おしゃれ' in line:
                    line = f"✨ **{line}**"
                elif 'ヘルシー' in line:
                    line = f"🥗 **{line}**"
                elif '気軽' in line:
                    line = f"😊 **{line}**"
                elif 'ベーカリー' in line or 'カフェ系' in line:
                    line = f"🥐 **{line}**"
                elif 'スイーツ' in line or 'デザート' in line:
                    line = f"🍰 **{line}**"
                elif 'デリ' in line or '軽食' in line:
                    line = f"🥗 **{line}**"

            # 質問部分を強調
            elif re.match(r'^(具体的にどんな|例えば：|好みを教えて|どんな気分|それとも|どのお店が)', line):
                line = f"💭 **{line}**"

            # 見出し・カテゴリ部分を強調
            elif re.match(r'^(今すぐ行けそうなスポット|仕事の合間)', line):
                line = f"🎯 **{line}**"

            # 現在時刻などの情報を強調
            elif re.match(r'^現在', line):
                line = f"⏰ {line}"

            # 麻布台ヒルズの情報を強調
            elif '麻布台ヒルズ' in line:
                line = f"🏢 {line}"

            # 番号付きリストの処理
            elif re.match(r'^\d+\.\s+', line):
                # 番号付きリストアイテムの処理
                number_match = re.match(r'^(\d+\.\s+)(.+)', line)
                if number_match:
                    number_part = number_match.group(1)
                    item_text = number_match.group(2)

                    # 絵文字がない場合は内容に応じて追加
                    if not re.match(r'^[🏢🧁☕🥤📸🥙🍰🥗]', item_text):
                        if 'マーケット' in item_text or 'ヒルズ' in item_text:
                            line = f"{number_part}🏢 {item_text}"
                        elif 'チーズケーキ' in item_text or 'スイーツ' in item_text or 'モンブラン' in item_text:
                            line = f"{number_part}🧁 {item_text}"
                        elif 'カフェ' in item_text or 'CAFÉ' in item_text:
                            line = f"{number_part}☕ {item_text}"
                        elif 'ドリンク' in item_text:
                            line = f"{number_part}🥤 {item_text}"
                        else:
                            line = f"{number_part}🔹 {item_text}"

            # リストアイテムに適切な絵文字を追加
            elif line.startswith('- '):
                item_text = line[2:].strip()
                # 既に絵文字がある場合は追加しない
                if not re.match(r'^[📸🍴👥🥬✨🚶💰🍣🍝🇫🇷🍜☕💴🥖🧁🥙]', item_text):
                    if 'インスタ映え' in item_text or 'スタイリッシュ' in item_text or 'ペストリー' in item_text:
                        line = f"📸 {line}"
                    elif '話題' in item_text or 'グルメ' in item_text:
                        line = f"🍴 {line}"
                    elif '友達' in item_text or '雰囲気' in item_text:
                        line = f"👥 {line}"
                    elif 'サラダ' in item_text or 'オーガニック' in item_text or 'ヘルシー' in item_text:
                        line = f"🥬 {line}"
                    elif '美容' in item_text or '美しい' in item_text:
                        line = f"✨ {line}"
                    elif 'カジュアル' in item_text or '一人' in item_text:
                        line = f"🚶 {line}"
                    elif 'リーズナブル' in item_text or 'ランチセット' in item_text:
                        line = f"💰 {line}"
                    elif '和食' in item_text:
                        line = f"🍣 {line}"
                    elif 'イタリアン' in item_text:
                        line = f"🍝 {line}"
                    elif 'フレンチ' in item_text:
                        line = f"🇫🇷 {line}"
                    elif 'アジア料理' in item_text:
                        line = f"🍜 {line}"
                    elif 'カフェ' in item_text:
                        line = f"☕ {line}"
                    elif '予算' in item_text:
                        line = f"💴 {line}"
                    elif 'パン' in item_text or 'サンドイッチ' in item_text or '焼きたて' in item_text:
                        line = f"🥖 {line}"
                    elif 'ケーキ' in item_text or 'タルト' in item_text or 'スイーツ' in item_text or '季節限定' in item_text:
                        line = f"🧁 {line}"
                    elif 'ドリンク' in item_text or 'テイクアウト' in item_text:
                        line = f"🥤 {line}"
                    elif '軽食' in item_text or 'サンドイッチ' in item_text or '栄養' in item_text:
                        line = f"🥙 {line}"

            enhanced_lines.append(line)
        else:
            # 空行は段落分けとして保持（連続空行を避ける）
            if enhanced_lines and enhanced_lines[-1] != '':
                enhanced_lines.append('')

    # 最後に連続する空行を整理
    result_lines = []
    for line in enhanced_lines:
        if line == '' and result_lines and result_lines[-1] == '':
            continue  # 連続する空行をスキップ
        result_lines.append(line)

    return '\n'.join(result_lines)


def render_tool_execution(tool_execution: ToolExecution) -> None:
    """ツール実行情報をエクスパンダーで表示する。

    表示設定はToolDisplayConfigから取得される。

    Args:
        tool_execution: ツール実行情報
    """
    tool_name = tool_execution.tool_name

    # 設定を取得
    icon = ToolDisplayConfig.get_icon(tool_name)
    expanded = ToolDisplayConfig.get_expanded(tool_name)
    input_label = ToolDisplayConfig.get_input_label(tool_name)
    output_label = ToolDisplayConfig.get_output_label(tool_name)
    input_language = ToolDisplayConfig.get_input_language(tool_name)
    output_language = ToolDisplayConfig.get_output_language(tool_name)
    show_timestamp = ToolDisplayConfig.get_show_timestamp(tool_name)
    timestamp_format = ToolDisplayConfig.get_timestamp_format(tool_name)

    # エクスパンダーで表示
    with st.expander(f"{icon} ツール実行: {tool_name}", expanded=expanded):
        st.markdown(input_label)
        st.code(tool_execution.input_data, language=input_language)
        st.markdown(output_label)
        st.code(tool_execution.output_data, language=output_language)
        if show_timestamp:
            st.caption(f"実行時刻: {tool_execution.timestamp.strftime(timestamp_format)}")


def render_chat_message(message: ChatMessage) -> None:
    """単一のチャットメッセージをレンダリングする。"""
    role_name_map = {
        MessageRole.USER: "user",
        MessageRole.ASSISTANT: "assistant",
        MessageRole.SYSTEM: "system",
    }

    with st.chat_message(role_name_map[message.role]):
        for part in message.parts:
            if part.type == "text":
                # 改行と段落分けを適切に処理するため、内容を前処理
                formatted_content = _format_message_content(part.content)
                # HTMLを使用してより確実な改行処理を行う
                html_content = formatted_content.replace('\n', '<br>')
                st.markdown(html_content, unsafe_allow_html=True)
            elif part.type == "tool":
                render_tool_execution(part.tool_execution)


def render_chat_history(messages: list[ChatMessage]) -> None:
    """チャット履歴をレンダリングする。"""
    for message in messages:
        render_chat_message(message)


def render_chat_input(
    key: str = "chat_input",
    placeholder: str = "メッセージを入力してください...",
) -> Optional[str]:
    """チャット入力をレンダリングしてユーザーのメッセージを返す。"""
    result = st.chat_input(placeholder, key=key)
    return result if result else None


def render_chat_controls(use_container_width: bool = True) -> dict:
    """チャットコントロールボタンをレンダリングして状態を返す。

    Args:
        use_container_width: コンテナ幅全体を使用するかどうか

    Returns:
        ボタン状態の辞書
    """
    new_session = st.button(
        "🆕 新しい会話を始める",
        help="新しい会話を開始します",
        use_container_width=use_container_width,
    )

    export_chat = st.button(
        "💾 エクスポート",
        help="会話履歴をエクスポートします",
        use_container_width=use_container_width,
    )

    return {
        "new_session": new_session,
        "export_chat": export_chat,
    }


def render_error_message(error: str) -> None:
    """エラーメッセージをレンダリングする。"""
    st.error(f"⚠️ エラー: {error}")
