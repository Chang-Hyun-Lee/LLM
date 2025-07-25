import streamlit as st
import os
import pandas as pd
from pykrx import stock
import requests
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain import hub
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from llama_index.core import VectorStoreIndex, Document

# 환경 변수 설정
os.environ["TAVILY_API_KEY"] = "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"

# 🔁 주가 데이터 불러오기 + 캐싱
@st.cache_data(show_spinner="📊 주가 데이터를 불러오는 중입니다...")
def load_all_ohlcv(start_date: str, end_date: str) -> pd.DataFrame:
    ticker_list = stock.get_market_ticker_list()
    all_data = []

    for ticker in ticker_list:
        try:
            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
            df = df.copy()
            df["티커"] = ticker
            all_data.append(df)
        except Exception as e:
            print(f"{ticker} 에러 발생: {e}")

    result_df = pd.concat(all_data)
    result_df.reset_index(inplace=True)
    return result_df

def search_naver_local(query, count):
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/local.json?query={encText}&display={count}"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request)
    rescode = response.getcode()

    if rescode == 200:
        response_body = response.read()
        data = json.loads(response_body.decode('utf-8'))
        return data.get("items", [])
    else:
        return []


# 🔁 LlamaIndex 인덱스 생성 + 캐싱
@st.cache_resource(show_spinner="🔍 인덱스를 만드는 중입니다...")
def create_index_from_df(df: pd.DataFrame) -> VectorStoreIndex:
    documents = []
    for ticker in df["티커"].unique():
        sub_df = df[df["티커"] == ticker]
        text = f"종목코드: {ticker}\n"
        for _, row in sub_df.iterrows():
            text += f"{row['날짜'].date()} - 시가: {row['시가']}, 고가: {row['고가']}, 저가: {row['저가']}, 종가: {row['종가']}, 거래량: {row['거래량']}\n"
        documents.append(Document(text=text))
    return VectorStoreIndex.from_documents(documents)

# 🔁 스트리밍 핸들러 정의
class StreamHandler(BaseCallbackHandler):
    def __init__(self):
        self.tokens = ""
        self.container = st.empty()

    def on_llm_new_token(self, token, **kwargs):
        self.tokens += token
        self.container.markdown(self.tokens + "▌")

# 📈 LangChain 구성
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
search_tool = TavilySearchResults(k=5)

# 데이터 준비
start_date = "2024-01-01"
end_date = "2025-07-20"
df = load_all_ohlcv(start_date, end_date)
index = create_index_from_df(df)
query_engine = index.as_query_engine()

# LlamaIndex 툴 정의
llama_tool = Tool(
    name = "StockIndexQA",
    func = lambda q: query_engine.query(q).response,
    description="주식 인덱스에서 정보를 찾아주는 도구입니다. 예: '삼성전자 주가 알려줘'"
)

tools = [search_tool, llama_tool]
prompt = hub.pull("hwchase17/openai-functions-agent")

if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# Streamlit 설정
st.set_page_config(page_title="📈 종목 주가 분석 에이전트", page_icon="📊")
st.title("📈 주가 분석 AI 챗봇")
st.caption("종목 이름이나 티커를 입력하면 AI가 검색하고 요약해드립니다.")

# 채팅 이력
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 채팅 출력
for role, content in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(content)
        

# 입력 필드
user_input = st.chat_input("예: 삼성전자 주가 알려줘")

# 메시지 처리
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        handler = StreamHandler()
        callback_manager = CallbackManager([handler])
        streaming_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True, callback_manager=callback_manager)

        agent = create_openai_functions_agent(streaming_llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, memory = st.session_state.memory, tools=tools, verbose=True)

        for _ in agent_executor.stream({"input": user_input}):
            pass

        st.session_state.chat_history.append(("assistant", handler.tokens))
