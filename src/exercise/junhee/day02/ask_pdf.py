from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

#embeddings = HuggingFaceEmbeddings()
embeddings = OpenAIEmbeddings()

# Facebook AI Research에서 개발한 벡터 유사도 검색 및 클러스터링 라이브러리
from langchain.vectorstores import FAISS
db = FAISS.load_local("shower", embeddings=embeddings, allow_dangerous_deserialization=True)

# 스트림

import gradio as gr
import random
import time

import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def create_generator(text):
    content = "당신은 친절한 어시스턴트입니다. 주어진 데이터를 보고 사용자에 친절하게 대답하세요.\n" 
    content += "*" * 50
    docs = db.similarity_search(text)
    for doc in docs:
        content += doc.page_content + "\n"
        content += "*" * 50
        
    messages = [
        {
          "role": "system",
          "content": content
        },
        {
          "role": "user",
          "content": text
        },
    ]

    gen = openai.chat.completions.create(
      model="gpt-4o-mini",
      messages=messages,
      temperature=0.5,
      max_tokens=512,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stream=True
    )
    return gen

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        gen = create_generator(history[-1][0])
        history[-1][1] = ""
        while True:
            response = next(gen)
            delta = response.choices[0].delta
            if delta.content is not None:
                history[-1][1] += delta.content
            else:
                break
            yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)
    
demo.queue()
demo.launch(server_name='0.0.0.0')
