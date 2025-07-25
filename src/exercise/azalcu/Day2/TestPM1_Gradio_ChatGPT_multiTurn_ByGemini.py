import gradio as gr
import openai
import base64
import io
from PIL import Image

# --- 전역 변수 ---
client = None

# --- API 키 설정 함수 ---
def set_api_key(api_key):
    """API 키를 설정합니다."""
    global client
    if not api_key or not api_key.startswith("sk-"):
        client = None
        return ("유효한 OpenAI API 키를 입력하세요.", gr.update(visible=True))
    try:
        client = openai.OpenAI(api_key=api_key)
        client.models.list()  # API 키 유효성 검증
        return ("✅ API 키가 성공적으로 설정되었습니다!", gr.update(visible=False))
    except Exception as e:
        client = None
        return (f"❌ API 키 인증 오류: {e}", gr.update(visible=True))

# --- 이미지 인코딩 함수 ---
def encode_image(pil_image):
    """PIL 이미지를 Base64로 인코딩합니다."""
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# --- 대화 스트림 함수 ---
def chat_stream(message, image, chatbot_display, api_history):
    """
    사용자 입력과 대화 기록을 받아 스트리밍 응답을 생성하고, 입력창을 비웁니다.
    - chatbot_display: 화면에 보이는 채팅 내역 (HTML 포함)
    - api_history: OpenAI API와 통신하기 위한 순수한 데이터 내역
    """
    message = message or ""
    yield chatbot_display, api_history, None, ""

    if not client:
        chatbot_display.append([message, "❌ 먼저 유효한 OpenAI API 키를 설정해주세요."])
        yield chatbot_display, api_history, None, ""
        return

    try:
        api_messages = list(api_history)
        
        if image:
            base64_image = encode_image(image)
            content_parts = []

            if message.strip():
                content_parts.append({"type": "text", "text": message.strip()})

            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

            api_messages.append({"role": "user", "content": content_parts})

        else:
            api_messages.append({"role": "user", "content": message})

        display_message = message
        if image:
            base64_image_display = encode_image(image)
            img_html = f'<img src="data:image/jpeg;base64,{base64_image_display}" style="max-width: 150px; max-height: 150px; display: block; margin-bottom: 10px;">'
            display_message = f"{img_html}{message}" if message else img_html
        
        chatbot_display.append([display_message, ""])

        if image:
            chatbot_display[-1][1] = "🖼️ 이미지를 처리 중입니다... 잠시만 기다려주세요..."
            yield chatbot_display, api_history, None, ""

        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=api_messages,
            stream=True,
            max_tokens=2048
        )

        full_response = ""
        for i, chunk in enumerate(stream):
            content = chunk.choices[0].delta.content
            if content:
                if i == 0 and image:
                    chatbot_display[-1][1] = ""
                full_response += content
                chatbot_display[-1][1] = full_response
                yield chatbot_display, api_history, None, ""

        api_history.append(api_messages[-1])
        api_history.append({"role": "assistant", "content": full_response})

    except Exception as e:
        error_message = f"❌ 오류 발생: {e}"
        chatbot_display[-1][1] = error_message
        yield chatbot_display, api_history, None, ""

# --- Gradio 인터페이스 구성 ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    api_history = gr.State([])

    gr.Markdown("## 🤖 Gradio 멀티모달 챗봇 (최종 완성본)")
    gr.Markdown("좌측에 OpenAI API 키를 입력하고, 이미지(선택)와 메시지를 보내 대화를 시작하세요.")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### API 설정")
            api_key_input = gr.Textbox(label="OpenAI API Key", placeholder="sk-...", type="password")
            api_status = gr.Markdown("API 키를 입력하세요.")
            set_key_button = gr.Button("API 키 설정", variant="primary")
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(label="대화창", height=600, render_markdown=True, bubble_full_width=False)
            with gr.Row():
                image_input = gr.Image(type="pil", label="이미지 업로드", height=150, scale=1)
                chat_input = gr.Textbox(label="메시지 입력", placeholder="질문을 입력하세요.", scale=4)
            submit_button = gr.Button("전송", variant="primary")

    set_key_button.click(
        fn=set_api_key,
        inputs=[api_key_input],
        outputs=[api_status, api_key_input]
    )

    submit_listener = [chat_input, image_input, chatbot, api_history]
    output_components = [chatbot, api_history, image_input, chat_input]

    chat_input.submit(
        fn=chat_stream,
        inputs=submit_listener,
        outputs=output_components
    )

    submit_button.click(
        fn=chat_stream,
        inputs=submit_listener,
        outputs=output_components
    )

# --- 웹 서버 실행 ---
demo.launch(inbrowser=True)
