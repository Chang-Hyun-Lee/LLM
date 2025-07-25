## 실습 #1: LangGraph를 이용해 
# 코드의 스타일, 버그 가능성, 최적화에 대한 내용을 분석하고, 
# 최종적으로 이 분석들을 모두 반영하여 개선한 코드를 리턴하는 어플리케이션을 작성하시오. 
# 
# 스타일, 버그, 최적화에 대한 점검 기능은 LangGraph의 Node로 만들어 향후 변경이 용이하게 작업해야 합니다.

from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict
import os
from langchain.chains import LLMChain
import json
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")

class MyGraphState(TypedDict):
  code : str
  style : str
  bug : str
  optimal : str
  imporved_code : str

#path = os.path("../DAY03/exercise_1.py")

def call_llm(message):
    return llm.invoke(message)

def check_style(state : MyGraphState):
    style_agnet = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 코드 스타일 분석가 입니다. 가독성, 일관성을 중심으로 사용자 코드를 분석하고 결과를 한국어로 제공하세요.\n\nCONTEXT: {code}\n\nRESULT:")
        ]
    ) 
    style_agnet.format(code=state["code"])

    chain = LLMChain(llm=llm, prompt=style_agnet)
    result = chain.run(state["code"])

    state["style"] = result
    return state

def check_possibility_bug(state: MyGraphState):
    bug_agent = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 코드 버그 가능성 분석가 입니다.일반적인 버그패턴, 잠재적 에러를 중심으로 사용자 코드를 분석하고 결과를 한국어로 제공하세요.\n\nCONTEXT: {code}\n\nRESULT:")
        ]
    ) 
    bug_agent.format(code=state["code"])

    chain = LLMChain(llm=llm, prompt=bug_agent)
    result = chain.run(state["code"])

    state["bug"] = result
    return state

def check_optimal(state: MyGraphState):
    opti_agent = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 코드 최적화 분석가 입니다. 성능, 리소스 효율, 개선 가능성을 중심으로 사용자 코드를 분석하고 결과를 한국어로 제공하세요.\n\nCONTEXT: {code}\n\nRESULT:")
        ]
    ) 
    opti_agent.format(code=state["code"])

    chain = LLMChain(llm=llm, prompt=opti_agent)
    result = chain.run(state["code"])

    state["optimal"] = result
    return state

def agg_code(state: MyGraphState):
    agg_agent = ChatPromptTemplate.from_messages(
        [
            ("system", "당신은 입력된 코드들의 최종본을 만드는 코드 리팩토링 엔지니어 입니다. style 최적화 코드{style}, bug 최적화 코드{bug}, 성능 최적화 코드{opti} 을 종합한 코드를 제공하고 결과를 한국어로 제공하세요.\n\nFINAL_RESULT:")
        ]
    ) 
    agg_agent.format(style=state["style"], bug=state["bug"], opti=state["optimal"])

    chain = LLMChain(llm=llm, prompt=agg_agent)
    result = chain.run(style=state["style"], bug=state["bug"], opti=state["optimal"])

    state["imporved_code"] = result
    return state


workflow = StateGraph(MyGraphState)
workflow.add_node("Node1", check_style)
workflow.add_node("Node2", check_possibility_bug)
workflow.add_node("Node3", check_optimal)
workflow.add_node("Node4", agg_code)

workflow.add_edge(START, "Node1")
workflow.add_edge("Node1", "Node2")
workflow.add_edge("Node2", "Node3")
workflow.add_edge("Node3", "Node4")
workflow.add_edge("Node1", END)

app = workflow.compile()

code = """
import streamlit as st

import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def create_generator(history):
    chat_logs = []

    for item in history:
        if item[0] is not None: # 사용자
            message =  {
              "role": "user",
              "content": item[0]
            }
            chat_logs.append(message)            
        if item[1] is not None: # 챗봇
            message =  {
              "role": "assistant",
              "content": item[1]
            }
            chat_logs.append(message)            
    
    messages=[
        {
          "role": "system",
          "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."
        }
    ]
    messages.extend(chat_logs)
        
    gen = openai.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0.5,
      max_tokens=4096,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stream=True
    )
    return gen


st.title('Gradio 처럼 만든 멀티턴 채팅' + '스마일 :sunglasses:')

history = ''

if "history" not in st.session_state:
    st.session_state.history = [{"role": "assistant", "content": "질문하이소"}]

for history in st.session_state.history:
    with st.chat_message(history["role"]):
        st.markdown(history["content"])

ch_in = st.chat_input('뭐 궁금하니?')
if ch_in is not None:
    st.session_state.history.append({"role": "user", "content": ch_in})

    gen_Msg = create_generator(history)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        for char in gen_Msg:
            if char.choices[0].delta.content is not None:
                full_response[-1][1] += char.choices[0].delta.content

        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

"""
int_state = MyGraphState(
    code=code,
    style="",
    bug="",
    optimal="",
    imporved_code=""
)

result = app.invoke(int_state)
#print(result["style"])
#print("==============================================================================")
#print(result["bug"])
#print("==============================================================================")
#print(result["optimal"])
#print("==============================================================================")
print(result["imporved_code"])
