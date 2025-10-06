# パーソナライゼーション機能実装確認コマンド集

## 1. 基本ツール登録確認
.venv\Scripts\python.exe -c "
from src.core.tools import tool_registry
tools = tool_registry.get_tool_descriptions()
print(f'登録ツール数: {len(tools)}')
for tool in tools: print(f'- {tool[\"name\"]}')"

## 2. ユーザー分析ツール単体テスト
.venv\Scripts\python.exe -c "
from src.core.tools.user_analysis_tool import UserInterestAnalysisTool
tool = UserInterestAnalysisTool()
result = tool.execute(chat_history=[
    {'role': 'user', 'content': 'レストランでディナーしたい'},
    {'role': 'user', 'content': '友人と夜に食事'}
])
print(f'成功: {result[\"success\"]}')
if result['success']: print(f'分析: {result[\"analysis\"][\"analysis_summary\"]}')"

## 3. プロンプトパーソナライゼーション確認
.venv\Scripts\python.exe -c "
from src.config.prompts import get_agent_system_prompt
normal = get_agent_system_prompt()
test_analysis = {'analysis_summary': 'テスト分析結果'}
personalized = get_agent_system_prompt(test_analysis)
print(f'通常プロンプト: {len(normal.content)}文字')
print(f'パーソナライズ: {len(personalized.content)}文字')
print(f'差分: +{len(personalized.content) - len(normal.content)}文字')"

## 4. 実データ取得テスト
.venv\Scripts\python.exe -c "
from src.core.tools.data_search_tool import DataSearchTool
from src.core.tools.time_tool import GetCurrentTimeTool
time_tool = GetCurrentTimeTool()
print(f'現在時刻: {time_tool.execute(timezone=\"Asia/Tokyo\")}')
search_tool = DataSearchTool()
events = search_tool.execute(query='イベント', category='イベント')
print(f'イベント数: {len(events.get(\"events\", []))}')"

## 5. Streamlitアプリ起動
.venv\Scripts\python.exe -m streamlit run src/app.py

## 6. Git状態確認
git status
git log --oneline -3

## 7. 環境情報確認
.venv\Scripts\python.exe -c "
import sys
print(f'Python: {sys.version}')
try:
    import streamlit as st
    print(f'Streamlit: {st.__version__}')
except:
    print('Streamlit: 未インストール')
try:
    import langchain
    print(f'LangChain: 利用可能')
except:
    print('LangChain: 未インストール')"

## 8. パフォーマンステスト（複数シナリオ）
.venv\Scripts\python.exe -c "
from src.core.tools.user_analysis_tool import UserInterestAnalysisTool
import time

scenarios = {
    'エンタメ': [{'role': 'user', 'content': '映画や展示を見たい'}],
    'ファミリー': [{'role': 'user', 'content': '子供と楽しめる場所'}],
    'ビジネス': [{'role': 'user', 'content': '商談できるレストラン'}]
}

for name, history in scenarios.items():
    start = time.time()
    tool = UserInterestAnalysisTool()
    result = tool.execute(chat_history=history)
    elapsed = time.time() - start
    print(f'{name}: {elapsed:.3f}秒 - {result[\"analysis\"][\"analysis_summary\"] if result[\"success\"] else \"失敗\"}')"
