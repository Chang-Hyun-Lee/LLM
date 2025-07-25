# 실습 #1: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 특정 종목의 주가를 분석해주는 어플리케이션을 작성하시오.
# 실습 #2: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 레스토랑을 찾아서 검색해주는 어플리케이션을 작성하시오.
# 실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.


import streamlit as st
import os
import requests
import json
from openai import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI as LangChainOpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Kakao API를 이용한 식당 검색
def get_restaurant_data(query="식당"):
    @st.cache_data
    def data_load(search_query):
        API_KEY = "70200e2a88cc0ab7ee1632c35d8aac0b"
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {API_KEY}"}
        params = {"query": search_query}
        response_api = requests.get(url, headers=headers, params=params)
        return response_api.json()
    
    api_data = data_load(query)
    return json.dumps(api_data, ensure_ascii=False)

# Tool 정의
get_restaurant = Tool(
    name="get_restaurant_data",
    func=lambda q: get_restaurant_data(q),
    description="카카오 API에서 특정 키워드로 식당 데이터를 JSON으로 가져온다."
)

# LLM 및 Agent 초기화
llm = LangChainOpenAI(temperature=0)
tools = [get_restaurant]
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# Streamlit UI
if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("원하는 식당이나 지역을 입력하세요...")

if user_input:
    # 사용자 메시지 기록
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Agent 실행
    response = agent.run(user_input)
    
    # 응답 메시지 기록
    st.session_state["messages"].append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)



# 판교에 있는 괜찮은 이탈리안 식당을 몇개 추천해줄래?



