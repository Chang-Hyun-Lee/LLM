from langchain_community.tools.tavily_search import TavilySearchResults
search = TavilySearchResults(k=5)
search.invoke("판교 근처 이탈리안 레스토랑은 무엇이 있나?")

from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Streamlit 앱 정의
def main():
    client.api_key = os.getenv("OPENAI_API_KEY")
    assistant_id = "asst_vKsnmuZX2sUZI9vhdSAEVCKT"
    assitant = client.beta.assistants.retrieve(assistant_id)

    st.title("Multi-turn Chatbot with Streamlit and OpenAI Assistant with retrieval")

    thread = None
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id
    else:
        thread_id = st.session_state["thread_id"]
        thread = client.beta.threads.retrieve(thread_id)

    thread_messages = client.beta.threads.messages.list(thread.id, order="asc")
    for message in thread_messages.data:
        with st.chat_message(message.role):
            st.markdown(message.content[0].text.value)
    
    if user_input:= st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input"):
        with st.chat_message("user"):
            st.markdown(user_input)
        
        user_message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )        

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ''

            with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant_id, 
                instructions=user_input,
                event_handler=EventHandler(message_placeholder, full_response),
            ) as stream:
                stream.until_done()

            thread_messages = client.beta.threads.messages.list(thread.id, order="asc")
            message = thread_messages.data[-1].content[0].text.value
            message_placeholder.markdown(message)

if __name__ == "__main__":
    main()
