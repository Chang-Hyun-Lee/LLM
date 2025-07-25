# 스트림

import gradio as gr
import random
import time

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
    
    messages=[h
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

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history):
        return "", history + [[user_message, None]]

    def bot(history):
        gen = create_generator(history)
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