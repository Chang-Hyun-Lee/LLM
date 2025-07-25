
#실습 #5: 실습 #2, #3, #4을 하나로 합치시오(레스토랑, 캠핑, 주식).

import os
import streamlit as st
import openai
import json
from pykrx import stock
import requests
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
from datetime import datetime # 오늘 날짜를 가져오기 위해
import difflib

today_str = datetime.now().strftime('%Y%m%d')
stock_name_list = []
stock_onlyName_list = []
stock_code_list = stock.get_market_ticker_list(today_str)
for i, ticker in enumerate(stock_code_list):
    company_name = stock.get_market_ticker_name(ticker)
    if company_name is not None:
        stock_name_list.append({"ticker" :ticker, "name": company_name})
        stock_onlyName_list.append(company_name)
    #print(f"{ticker}: {company_name}")

print(stock_name_list)

def find_ticker_code(name):
    result = ""
    for nm in stock_name_list:
        if nm["name"] == name:
            result = nm["ticker"]
            print(f"Same {name} _ {result}")
    
    return result

from fuzzywuzzy import process 
def find_best_match(user_query: str, choices: list, threshold: int = 70) -> str or None:
    best_match = process.extractOne(user_query, choices)
    print(f"best_match {best_match}")
    if best_match and best_match[1] >= threshold: # 유사도 점수가 임계값(threshold) 이상일 경우만
        return best_match[0] # 매치된 종목명 반환
    return None # 매치되는 종목이 없으면 None

def find_diff_check(user_name, compared_list):
    close_matches = difflib.get_close_matches(user_name, compared_list, n=1, cutoff=0.4)
    print(close_matches)
    return close_matches[0]

@tool
def get_market_ohlcv(start_date, end_date, name):
    """Return prices within given dates for ticker stock. start_date and end_date shoule be 'YYYYMMDD' format."""
    start_date = start_date.strip()
    end_date = end_date.strip()
    print(f"bf Name : {start_date}")
    print(f"bf Name : {end_date}")
    print(f"bf Name : {name}")
    #matchedName = find_best_match(name, stock_onlyName_list)
    matchedName = find_diff_check(name, stock_onlyName_list)
    print(f"Matched : {matchedName}")
    #stock_name = stock.get_market_ticker_name(matchedName)
    #print(f"stock_name : {stock_name}")
    code =find_ticker_code(matchedName)
    print(f"code : {code}")
    df = stock.get_market_ohlcv(start_date, end_date, code)
    df['종목명'] = [matchedName] * len(df)

    return json.dumps(df.to_dict(orient='records'), ensure_ascii=False)


@tool
def get_recommandation_food(location):
    """식당 추천, oo위치의 식당 추천, 맛집, 먹는 장소와 관련된 질문을 받았을 때 실행되는 기능이야."""
    kakao_api_key = os.getenv("KAKAO_API_KEY")
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query={}'.format(location)
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }
    places = requests.get(url, headers = headers).json()
    return places


@tool
def get_recommandation_camping(location):
    """캠핑장 추천 질문을 받았을 때 실행되는 Tool. 캠핑장 또는 oo가 있는 캠핑장, 어떤 위치에 있는 캠핑장등 캠핑과 관련된 질문일 경우 본 기능이 실행됨."""
    ServiceKey = kakao_api_key = os.getenv("GOCAMPING_SERVICE_KEY")
    #KeyWord = get_keyword(question=location)
    #print(KeyWord)
    url = f"http://apis.data.go.kr/B551011/GoCamping/searchList?serviceKey={ServiceKey}&keyword={location}&numOfRows=10&pageNo=1&MobileOS=ETC&MobileApp=TestApp&_type=json"
    
    response = get_url_content(url)
    return response
    #return json.load(response)


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
    

@st.cache_resource
def init_agent():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("사용자의 질문에 답하기 위해 항상 가장 정확하고 적절한 도구를 하나만 선택하여 사용하세요. 주식 관련 질문에는 `get_stock_market_ohlcv` 도구를, 캠핑장 관련 질문에는 `get_camping_site_recommendation` 도구를, 음식점 관련 질문에는 `get_restaurant_recommendation` 도구를 사용해야 합니다. 각 도구의 설명을 정확히 이해하고 사용하세요.")
    tools = [get_market_ohlcv, get_recommandation_camping, get_recommandation_food]
    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}), tools, prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
        {"run_name": "Agent"}
    )

    return model, prompt, tools, agent, agent_executor

def chat_with_bot(agent_executor, history):
    response = agent_executor.invoke({"input": {history[-1]["content"]}})
    return response["output"]

def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI(+ Stock, Rest', Camping)")
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
