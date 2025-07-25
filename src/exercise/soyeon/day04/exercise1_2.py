#실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 어플리케이션을 작성하시오.
#실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.

# tavily search는 export TAVILY_API_KEY= 로 설정하고 사용

import os
import streamlit as st
import json
import urllib.request
import urllib.parse
import openai

from langchain import hub
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import SystemMessagePromptTemplate

# 이전에 받았던 네이버 api키로 받기 
NAVER_CLIENT_ID = "bN1aUL6XWa3mtO8SF9x3"
NAVER_CLIENT_SECRET = "DiiJIjYDZW"
openai.api_key = os.getenv("OPENAI_API_KEY")

# 맛집검색 
@tool
def get_restaurants(location_query: str) -> str:
    """맛집을 검색 (부산에 중식집 추천해줘)'"""
    try:
        encoded_query = urllib.parse.quote(location_query)
        url = f"https://openapi.naver.com/v1/search/local.json?query={encoded_query}&display=5"

        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
        request.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)

        response = urllib.request.urlopen(request)
        result = response.read().decode('utf-8')

        return result
    except Exception as e:
        return f"[ERROR] {str(e)}"

# 에이전트    
@st.cache_resource
def init_agent():
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("""
        너는 맛집 추천을 해주는 에이전트야. 사용자가 요구하는 지역에 해당하는 맛집을 3~5개 추천해줘
        거기에서 많이 시켜 먹는 메뉴랑 주소, 전화번호, 휴일 등 음식점에 대한 정보를 
        2~3줄 분량으로 작성해줘
    """)
    tools = [get_restaurants]

    agent = create_openai_tools_agent(
        model.with_config({"tags": ["agent_llm"]}),
        tools,
        prompt
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools).with_config(
        {"run_name": "맛집추천Agent"}
    )

    return agent_executor

#챗봇
def chat_with_bot(agent_executor, history):
    return agent_executor.invoke({"input": history[-1]["content"]})["output"]

# streamlit
st.title("맛집 추천 챗봇")
user_input = st.chat_input("예: 부산에 중식집 알려줘")

agent_executor = init_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("검색 중..."):
         response = chat_with_bot(agent_executor, st.session_state.messages)
    with st.chat_message("assistant"):
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})