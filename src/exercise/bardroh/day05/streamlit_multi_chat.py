# pip install git+https://github.com/huggingface/transformers.git

import os
import streamlit as st
import openai
from huggingface_hub import HfApi, login

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer
from threading import Thread
import torch

@st.cache_resource
def get_model_and_tokenizer(model_id):

    login(token=os.getenv("HUGGINGFACE_TOKEN"))    
#    bnb_config = BitsAndBytesConfig(
#        load_in_4bit=True,
#        bnb_4bit_use_double_quant=True,
#        bnb_4bit_quant_type="nf4",
#        bnb_4bit_compute_dtype=torch.bfloat16
#    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
 #       quantization_config=bnb_config,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    return model, tokenizer

def chat_with_bot(model, tokenizer, new_messages):
    messages = [
        {
            "role": "system",
#            "content": "You are helpful assitant. You need to answer to user's question politely."
            "content": "당신은 친절한 어시스턴트입니다. 사용자의 질문에 친절하게 대답하세요."
        }
    ]
    messages.extend(new_messages)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True) 
    inputs = tokenizer([prompt], return_tensors="pt").to("cuda")
    streamer = TextIteratorStreamer(tokenizer)

    generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=1024)
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    return streamer, len(prompt)

# Streamlit 앱 정의
def main():
    st.title("Multi-turn Chatbot with Streamlit and Local LLM")
    st.chat_input(placeholder="대화를 입력해주세요.", key="chat_input")

    model, tokenizer = get_model_and_tokenizer("Qwen/Qwen2.5-1.5B-Instruct")

    if "messages" not in st.session_state:
        st.session_state.messages = []        

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.session_state["chat_input"]:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content":user_input})

        gen, length = chat_with_bot(model, tokenizer, st.session_state.messages)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_length = 0
            full_response = ""
            is_first_printable_chunk = True
            for chunk in gen:
                full_length += len(chunk)
                if full_length > length:
                    if is_first_printable_chunk:
                        remains = full_length - length
                        chunk = chunk[-remains:]
                        is_first_printable_chunk = False
                    chunk = chunk.replace("<|im_end|>", "")
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content":full_response})

if __name__ == "__main__":
    main()
