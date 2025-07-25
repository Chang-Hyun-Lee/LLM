import streamlit as st
import os
import tempfile
from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from ingest import process_pdf

# API Key 직접 설정
os.environ["OPENAI_API_KEY"] = "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"

# Page config
st.set_page_config(page_title="PDF QA System", page_icon="📚")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "chain" not in st.session_state:
    st.session_state.chain = None

# Title
st.title("📚 PDF Document QA System")

# File uploader
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file:
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

        # Process the PDF and create index
        with st.spinner("Processing PDF..."):
            try:
                process_pdf(tmp_path)
                st.success("PDF processed successfully!")
                
                # Load the vectorstore using FAISS
                embeddings = OpenAIEmbeddings()
                st.session_state.vectorstore = FAISS.load_local(
                    "faiss_index", 
                    embeddings,
                    allow_dangerous_deserialization=True  # Only use if you trust the source
                )
                
                # Create the chain
                memory = ConversationBufferMemory(
                    memory_key="chat_history",
                    return_messages=True
                )
                
                st.session_state.chain = ConversationalRetrievalChain.from_llm(
                    llm=ChatOpenAI(temperature=0),
                    retriever=st.session_state.vectorstore.as_retriever(),
                    memory=memory,
                )
                
            except Exception as e:
                st.error(f"Error processing PDF: {str(e)}")
            
            # Clean up temp file
            os.unlink(tmp_path)

# Chat interface
if st.session_state.chain:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the PDF"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chain({"question": prompt})
                response_text = response["answer"]
                st.write(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

else:
    st.info("Please upload a PDF file to start the conversation.")