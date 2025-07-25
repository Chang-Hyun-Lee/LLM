# 실습 #1. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 작성하시오.
# 실습 #2. llama_index와 Streamlit을 사용하여 인덱스된 파일에 대해서 답변하는 어플리케이션을 멀티턴으로 바꾸시오.
# 실습 #3. llama_index와 Streamlit을 사용하여 파일을 업로드하고 업로드한 파일 전체에 대해서 설명하는 어플리케이션을 작성하시오.
# 실습 #4. 실습 #3의 어플리케이션에서 파일을 리스트업하고 삭제할 수 있는 인터페이스를 작성하시오.


# !pip install pydantic==2.7.1
# !pip install pydantic_core==2.18.2
# !pip install -U llama-index
# !pip install docx2txt


import os.path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

PERSIST_DIR = "./storage"
def get_response(prompt):
  if not os.path.exists(PERSIST_DIR):
      documents = SimpleDirectoryReader("data").load_data()
      index = VectorStoreIndex.from_documents(documents)
      index.storage_context.persist(persist_dir=PERSIST_DIR)
  else:
      storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
      index = load_index_from_storage(storage_context)

  query_engine = index.as_query_engine()
  response = query_engine.query(prompt)
  return response



import streamlit as st
import time

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("질문을 입력해 주세요..."): 
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        assistant_response = get_response(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_response.response})

        # Simulate stream of response with milliseconds delay
        message_placeholder = st.empty()
        full_response = ""
        
        for chunk in assistant_response.response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            # Add a blinking cursor to simulate typing
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)