""" from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import streamlit as st

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine()
response = query_engine.query("소년과 소녀는 어디에서 처음 만났나? 한국어로 대답해줘.")
print(response)

st.markdown(response)
st.chat_message("user").markdown(response) """

import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
#st.markdown (query_engine.query("소년과 소녀는 어디에서 처음 만났나? 한국어로 대답해줘."))

# def chat_with_bot(messages):
#     response = query_engine.query(messages, streaming=True)
#     return response

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_bot(messages):
    gen = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
        stream=True
    )
    st.markdown(gen)
    return gen

# Streamlit 앱 정의
def main():
    st.title("Multi-turn Chatbot with Streamlit and OpenAI")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        gen = chat_with_bot(st.session_state.messages)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""        
            for chunk in gen:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content":full_response})

if __name__ == "__main__":
    main()
