#!/usr/bin/env python3
"""パーソナライゼーション機能の実装確認スクリプト"""

print("=== パーソナライゼーション機能実装確認 ===\n")

# 1. ツール登録確認
print("【1】ツール登録確認:")
try:
    from src.core.tools import tool_registry
    tools = tool_registry.get_tool_descriptions()
    print(f"✅ 登録ツール数: {len(tools)}")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description'][:50]}...")

    # ユーザー分析ツールが含まれているかチェック
    user_tool_exists = any(tool['name'] == 'user_interest_analysis' for tool in tools)
    if user_tool_exists:
        print("✅ ユーザー分析ツールが正常に登録されています")
    else:
        print("❌ ユーザー分析ツールが見つかりません")

except Exception as e:
    print(f"❌ ツール登録確認エラー: {e}")

print()

# 2. ユーザー分析ツール動作確認
print("【2】ユーザー分析ツール動作確認:")
try:
    from src.core.tools.user_analysis_tool import UserInterestAnalysisTool

    # テスト用チャット履歴
    test_history = [
        {"role": "user", "content": "レストランでディナーを楽しみたい"},
        {"role": "user", "content": "友人と夜に食事する場所を探している"},
        {"role": "user", "content": "イタリアン料理が好きです"},
    ]

    tool = UserInterestAnalysisTool()
    result = tool.execute(chat_history=test_history)

    if result['success']:
        analysis = result['analysis']
        print("✅ ユーザー分析成功:")
        print(f"   主な興味: {analysis['primary_interests']}")
        print(f"   行動パターン: {analysis['behavior_patterns']}")
        print(f"   分析サマリー: {analysis['analysis_summary']}")
    else:
        print(f"❌ ユーザー分析失敗: {result.get('message')}")

except Exception as e:
    print(f"❌ ユーザー分析ツールエラー: {e}")

print()

# 3. パーソナライズプロンプト確認
print("【3】パーソナライズプロンプト確認:")
try:
    from src.config.prompts import get_agent_system_prompt

    # 通常プロンプト
    normal_prompt = get_agent_system_prompt()
    print(f"✅ 通常プロンプト長: {len(normal_prompt.content)}文字")

    # パーソナライズプロンプト
    if 'result' in locals() and result['success']:
        personalized_prompt = get_agent_system_prompt(analysis)
        print(f"✅ パーソナライズプロンプト長: {len(personalized_prompt.content)}文字")

        # ユーザープロファイル情報が含まれているかチェック
        if "ユーザープロファイル" in personalized_prompt.content:
            print("✅ ユーザープロファイル情報が正常に組み込まれています")
        else:
            print("❌ ユーザープロファイル情報が見つかりません")

except Exception as e:
    print(f"❌ プロンプト確認エラー: {e}")

print()

# 4. 実データ取得確認
print("【4】実データ取得確認:")
try:
    from src.core.tools.data_search_tool import DataSearchTool
    from src.core.tools.time_tool import GetCurrentTimeTool

    # 現在時刻取得
    time_tool = GetCurrentTimeTool()
    current_time = time_tool.execute(timezone='Asia/Tokyo')
    print(f"✅ 現在時刻: {current_time}")

    # イベントデータ取得
    search_tool = DataSearchTool()
    events = search_tool.execute(query='イベント', category='イベント')
    event_count = len(events.get('events', []))
    print(f"✅ 取得イベント数: {event_count}")

    if event_count > 0:
        first_event = events['events'][0]
        event_name = first_event.get('event_name', 'N/A')
        event_date = first_event.get('date_time', 'N/A')
        print(f"   例: {event_name} ({event_date})")

except Exception as e:
    print(f"❌ 実データ取得エラー: {e}")

print()

# 5. 統合動作確認
print("【5】統合動作確認:")
try:
    # 複数シナリオでの分析結果比較
    scenarios = {
        "エンタメ好き": [
            {"role": "user", "content": "アートイベントに興味があります"},
            {"role": "user", "content": "映画や展示を見に行きたい"},
        ],
        "ファミリー層": [
            {"role": "user", "content": "子供と一緒に楽しめる場所を探している"},
            {"role": "user", "content": "家族で行けるレストランはありますか"},
        ],
        "ビジネス利用": [
            {"role": "user", "content": "商談で使えるお店を教えて"},
            {"role": "user", "content": "会議室のような静かな場所はありますか"},
        ]
    }

    for scenario_name, chat_history in scenarios.items():
        scenario_tool = UserInterestAnalysisTool()
        scenario_result = scenario_tool.execute(chat_history=chat_history)

        if scenario_result['success']:
            scenario_analysis = scenario_result['analysis']
            print(f"✅ {scenario_name}: {scenario_analysis['analysis_summary']}")
        else:
            print(f"❌ {scenario_name}: 分析失敗")

except Exception as e:
    print(f"❌ 統合動作確認エラー: {e}")

print("\n" + "="*60)
print("🎉 実装確認完了！")
print("すべての機能が正常に動作している場合、Streamlitアプリで完全なテストが可能です。")
print("Streamlit起動: streamlit run src/app.py")
