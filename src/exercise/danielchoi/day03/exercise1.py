#1: gradio로 만든 멀티턴 채팅 어플리케이션을 streamlit으로 유사하게 구현하시오.

import streamlit as st
from openai import OpenAI
from typing import List, Dict, Any

class MultiTurnChatApp:
    def __init__(self):
        self.client = OpenAI(
            api_key="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"
        )
        # Initialize session state for messages if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def chat_stream(self, message: str) -> None:
        """Handle chat message and stream response"""
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": message})

        # Prepare messages for API
        messages = [
            {"role": m["role"], "content": m["content"]} 
            for m in st.session_state.messages
        ]

        # Create response placeholder
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            # Stream the response
            for chunk in self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True
            ):
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    # Update response in real-time
                    response_placeholder.markdown(full_response + "▌")
            
            # Update final response
            response_placeholder.markdown(full_response)
        
        # Add assistant response to state
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def main():
    st.set_page_config(
        page_title="ChatGPT Multi-turn Chat",
        page_icon="💬",
        layout="wide"
    )

    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("💬 ChatGPT 멀티턴 스트리밍 채팅")

    # Initialize chat interface
    chat_interface = MultiTurnChatApp()

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("메시지를 입력하세요..."):
        chat_interface.chat_stream(prompt)

    # Clear chat button
    if st.sidebar.button("대화 지우기"):
        st.session_state.messages = []
        st.rerun()

    # Example messages in sidebar
    st.sidebar.markdown("### 예제 메시지")
    examples = [
        "안녕하세요! 당신은 누구인가요?",
        "인공지능에 대해 설명해주세요.",
        "이전 설명을 조금 더 자세히 해주시겠어요?"
    ]
    
    for example in examples:
        if st.sidebar.button(example):
            chat_interface.chat_stream(example)

if __name__ == "__main__":
    main()

