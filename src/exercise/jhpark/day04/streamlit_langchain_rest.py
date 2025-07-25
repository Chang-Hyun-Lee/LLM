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

@tool
def find_location_food(location, key_word):
    """ Find food locations based on a given location and keyword"""
    searching = f"{location} {key_word}"
    kakao_api_key = os.getenv("KAKAO_API_KEY")
    url = 'https://dapi.kakao.com/v2/local/search/keyword.json?query={}'.format(searching)
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }
    location = requests.get(url, headers=headers).json()
    return location        

@st.cache_resource
def init_agent():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = hub.pull("hwchase17/openai-tools-agent")
    prompt.messages[0] = SystemMessagePromptTemplate.from_template("당신은 지역 전문가입니다. 주어진 정보를 보고 음식점 추천해 주세요.")
    
    tools = [find_location_food]
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
