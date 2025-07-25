##실습 #3: Streamlit과 LangChain agent를 사용하여 예전에 만들었던 캠핑장을 추천해주는 어플리케이션을 작성하시오.


import os
import streamlit as st
import openai
import json
import requests
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

@tool
def get_recommandation_camping(location):
    """Return Camping Location"""
    ServiceKey = kakao_api_key = os.getenv("GOCAMPING_SERVICE_KEY")
    #KeyWord = get_keyword(question=location)
    #print(KeyWord)
    url = f"http://apis.data.go.kr/B551011/GoCamping/searchList?serviceKey={ServiceKey}&keyword={location}&numOfRows=10&pageNo=1&MobileOS=ETC&MobileApp=TestApp&_type=json"
    
    response = get_url_content(url)
    return response
    #return json.load(response)


def get_keyword(question):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "다음 질문에서 가장 중요한 키워드 단어 하나만 뽑아줘."
            },
            {
                "role": "user",
                "content": question
            }
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message.content


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
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("전국 캠핑 전문가입니다. 입력한 지역의 식당을 추천해주세요.")

    tools = [get_recommandation_camping]
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
    st.title("Multi-turn Chatbot with Streamlit and OpenAI(+ Camping)")
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
