import os
import streamlit as st
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def chat_with_bot(messages):
    gen = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=4096,
        stream=True
    )
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
