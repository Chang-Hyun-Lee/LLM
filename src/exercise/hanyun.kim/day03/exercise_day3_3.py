# 실습 #1: Streamlit과 Assistant API를 이용하여 세션을 유지하는 멀티턴 챗봇을 만드시오. 
# 단 Assistant는 미리 만들어서 id를 얻어둔다. (시간이 된다면) stream 기능을 추가한다.
# asst_vKsnmuZX2sUZI9vhdSAEVCKT

import streamlit as st
import os
from dotenv import load_dotenv
from openai import OpenAI
import random
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


thread = client.beta.threads.create()
print ('--->\n',thread.id,'<---\n')

message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="안녕하세요."
)

thread_messages = client.beta.threads.messages.list(thread.id)
print('--->\n',thread_messages.data,'<---\n')


run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id="asst_vKsnmuZX2sUZI9vhdSAEVCKT",
  instructions="친절하게 사실을 바탕으로 답변해 주세요."
)


import time

while run.status != "completed"  :
    run = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
    )
    time.sleep(1)


messages = client.beta.threads.messages.list(
  thread_id=thread.id
)


thread_messages = client.beta.threads.messages.list(thread.id)
print(thread_messages.data)


print(thread_messages.data[0].role)
print(thread_messages.data[0].content[0].text.value)
