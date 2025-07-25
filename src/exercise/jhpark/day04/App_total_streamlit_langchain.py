import os
import streamlit as st
import openai
import json
import requests
from urllib.parse import quote
from pykrx import stock
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.callbacks import Callbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain.agents import load_tools

## restaurant tool

@tool
def get_restaurant_info(place, kind):
    """Return restaurant informaton for given place and kind."""
    searching = f"{place} {kind}"
    kakao_api_key = os.getenv("KAKAO_API_KEY")
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query={}'.format(searching)
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }
    places = requests.get(url, headers = headers).json()
    return places


## camping tool
ServiceKey=os.getenv("GOCAMPING_SERVICE_KEY")

def get_url_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")
        return None
    
@tool
def get_camping_info_context(keyword):
    """Return camping information context for given keyword. keyword should be an word."""
    keyword = quote(keyword)
    url = f"http://apis.data.go.kr/B551011/GoCamping/searchList?serviceKey={ServiceKey}&keyword={keyword}&numOfRows=10&pageNo=1&MobileOS=ETC&MobileApp=TestApp&_type=json"

    result = get_url_content(url)
    data = json.loads(result)
    
    context = ''
    if data['response']['body']['numOfRows'] > 0 :
        sites = data['response']['body']['items']['item']

        i = 1
        for site in sites:
            context = context + str(i) + ") " + site['facltNm'] + ":" + site['intro'] + "\n"
            i = i + 1
    else:
        context = '데이터 없음'
    return context    

## stock tool
from langchain_community.tools.tavily_search import TavilySearchResults

@tool
def get_market_ohlcv(start_date, end_date, ticker):
    """Return prices within given dates for ticker stock. start_date and end_date shoule be 'YYYYMMDD' format."""
    start_date = start_date.strip()
    end_date = end_date.strip()
    ticker = ticker.strip()
    stock_name = stock.get_market_ticker_name(ticker)
    df = stock.get_market_ohlcv(start_date, end_date, ticker)
    df['종목명'] = [stock_name] * len(df)

    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)
@tool
def get_ticker_info_by_search(stock_name):
    """Return ticker search results for given stock name"""
    search = GoogleSerperAPIWrapper()
    return search.run(f"{stock_name} 종목코드")

@st.cache_resource
def init_agent():
    openai.api_key = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("""주어진 도구들을 사용하여 사용자의 요청에 친절하게 답변하세요. 주식정보의 종목코드(티커)는 6자리 숫자입니다. 종목코드를 모르면 검색해서 찾은 후 답변하세요. 답변할 수 없으면 답변할 수 없다고 대답하세요.""")
    search = TavilySearchResults(k=5)

    tools = [get_camping_info_context, get_restaurant_info, get_market_ohlcv, get_ticker_info_by_search]
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True).with_config(
        {"run_name": "Agent"}
    )
    return model, prompt, tools, agent, agent_executor

## main function
def chat_with_bot(agent_executor, history):
    chat_history = []
    for item in history:
        if item["role"] == "user":
            chat_history.append(HumanMessage(content=item["content"]))
        else:
            chat_history.append(AIMessage(content=item["content"]))

    response = agent_executor.invoke(
        {
            "input": {history[-1]["content"]},
            "chat_history": chat_history
        }
    )
    return response["output"]

def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI(+ Stock)")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    model, prompt, tools, agent, agent_executor = init_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        with st.spinner('답변을 준비중입니다 ... '):
            response = chat_with_bot(agent_executor, st.session_state.messages)
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content":response})

if __name__ == "__main__":
    main()
