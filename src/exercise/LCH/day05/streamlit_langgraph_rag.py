import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from io import BytesIO

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

from langchain.tools.retriever import create_retriever_tool
from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langchain.vectorstores import FAISS

@st.cache_resource
def get_retriever():
    embeddings = OpenAIEmbeddings()
    retriever = FAISS.load_local("shower", embeddings=embeddings, allow_dangerous_deserialization=True)
    retriever = retriever.as_retriever()
    return retriever

# Agentic State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# agent에 추가하기 위한 tool
@st.cache_resource
def get_retriever_tool():
    retriever_tool = create_retriever_tool(
        get_retriever(),
        "retriever_for_RAG",
        "Search and return information from Vector Database",
    )
    return retriever_tool

# Graph상의 agent
def agent(state):
    """
    Invokes the agent model to generate a response based on the current state. Given
    the question, it will decide to retrieve using the retriever tool, or simply end.
    If you don't have sufficient information to answer, always you should use retriever tool.

    Args:
        state (messages): The current state

    Returns:
        dict: The updated state with the agent response appended to messages
    """
    print("---CALL AGENT---")
    messages = state["messages"]
    model = ChatOpenAI(temperature=0, streaming=True, model=os.getenv("gpt-4o-mini"))

    retriever_tool = get_retriever_tool()

    tools = [retriever_tool]
    model = model.bind_tools(tools)
    response = model.invoke(messages)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}

# Graph상의 generator
def generate(state):
    """
    Generate answer

    Args:
        state (messages): The current state

    Returns:
         dict: The updated state with re-phrased question
    """
    print("---GENERATE---")
    messages = state["messages"]
    question = messages[0].content
    last_message = messages[-1]

    docs = last_message.content

    # Prompt
    prompt = hub.pull("rlm/rag-prompt")

    # LLM
    llm = ChatOpenAI(temperature=0, model=os.getenv("gpt-4o-mini"), streaming=True)

    # Post-processing
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Chain
    rag_chain = prompt | llm | StrOutputParser()

    # Run
    response = rag_chain.invoke({"context": docs, "question": question})
    return {"messages": [response]}

def add_last_message(state):
    messages = state["messages"]
    last_message = messages[-1]
    return {"messages": [last_message.content]}

# 캐쉬되는 Graph
@st.cache_resource
def get_graph():
    workflow = StateGraph(AgentState)

    # Define the nodes we will cycle between
    workflow.add_node("agent", agent)  # agent
    retrieve = ToolNode([get_retriever_tool()])
    workflow.add_node("retrieve", retrieve)  # retrieval
    workflow.add_node(
        "generate", generate
    )  # Generating a response after we know the documents are relevant
    workflow.add_node("add_last_message", add_last_message)
    # Call agent node to decide to retrieve or not
    workflow.add_edge(START, "agent")

    # Decide whether to retrieve
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "retrieve",
            END: "add_last_message"
        },
    )

    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    graph = workflow.compile()    
    return graph

import pprint

def chat_with_bot(messages):
    graph = get_graph()
    inputs = {"messages": messages}
    
    latest_output = None
    for output in graph.stream(inputs):
        latest_output = output
        
    # 마지막 output에서 실제 생성된 콘텐츠 추출
    for key, value in latest_output.items():
        if isinstance(value, dict) and "messages" in value:
            # messages 배열의 마지막 메시지가 생성된 응답
            return value["messages"][-1]
    
    return None  # 응답을 찾지 못한 경우

# Streamlit 앱 정의
def main():
    st.title("Agentic RAG Chatbot with Streamlit and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("답변을 생성중입니다 ..."):
            response = chat_with_bot([{"role": "user", "content": user_input}])
            if response:
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        
if __name__ == "__main__":
    main()
