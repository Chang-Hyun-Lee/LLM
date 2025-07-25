import gradio as gr
from openai import OpenAI
import os
from typing import List, Tuple

# OpenAI API 키 설정
# 환경변수에서 API 키를 가져오거나 직접 입력
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

class ChatBot:
    def __init__(self):
        # 대화 기록을 저장할 리스트 (멀티턴을 위함)
        self.conversation_history = []
        
    def add_message(self, role: str, content: str):
        """대화 기록에 메시지 추가"""
        self.conversation_history.append({"role": role, "content": content})
        
    def clear_history(self):
        """대화 기록 초기화"""
        self.conversation_history = []
        
    def get_response_streaming(self, message: str):
        """스트리밍 방식으로 ChatGPT 응답 생성"""
        # 사용자 메시지를 대화 기록에 추가
        self.add_message("user", message)
        
        try:
            # OpenAI API 호출 (스트리밍) - 새로운 1.0+ 버전
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                stream=True,
                max_tokens=1000,
                temperature=0.7
            )
            
            # 스트리밍 응답 처리
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield full_response
                        
            # 완성된 응답을 대화 기록에 추가
            self.add_message("assistant", full_response)
            
        except Exception as e:
            error_msg = f"오류가 발생했습니다: {str(e)}"
            yield error_msg

# ChatBot 인스턴스 생성
chatbot = ChatBot()

def respond(message: str, history: List[Tuple[str, str]]):
    """Gradio 챗봇 응답 함수"""
    if not message.strip():
        return history, ""
    
    # 스트리밍 응답 생성
    response_generator = chatbot.get_response_streaming(message)
    
    # 새로운 대화 쌍을 history에 추가
    new_history = history + [[message, ""]]
    
    # 스트리밍으로 응답 업데이트
    for partial_response in response_generator:
        new_history[-1][1] = partial_response
        yield new_history, ""
    
    return new_history, ""

def clear_conversation():
    """대화 기록 초기화"""
    chatbot.clear_history()
    return [], ""

# Gradio 인터페이스 설정
with gr.Blocks(title="멀티턴 ChatGPT 챗봇", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 멀티턴 ChatGPT 챗봇")
    gr.Markdown("ChatGPT와 연속적인 대화를 나눠보세요! (스트리밍 지원)")
    
    # 채팅 인터페이스
    chatbot_ui = gr.Chatbot(
        label="채팅창",
        height=500,
        show_label=True,
        show_copy_button=True
    )
    
    with gr.Row():
        msg_input = gr.Textbox(
            label="메시지 입력",
            placeholder="ChatGPT에게 메시지를 입력하세요...",
            lines=2,
            max_lines=5,
            scale=4
        )
        
        with gr.Column(scale=1):
            send_btn = gr.Button("전송", variant="primary")
            clear_btn = gr.Button("대화 초기화", variant="secondary")
    
    # API 키 설정 (선택사항)
    with gr.Accordion("설정", open=False):
        api_key_input = gr.Textbox(
            label="OpenAI API Key", 
            placeholder="sk-...",
            type="password",
            info="API 키를 입력하면 해당 키로 요청을 보냅니다."
        )
        
        def update_api_key(api_key):
            global client
            if api_key.strip():
                client = OpenAI(api_key=api_key)
                return "API 키가 업데이트되었습니다."
            return "API 키를 입력해주세요."
        
        api_key_input.change(
            fn=update_api_key,
            inputs=[api_key_input],
            outputs=[gr.Textbox(label="상태", visible=False)]
        )
    
    # 이벤트 핸들러 설정
    send_btn.click(
        fn=respond,
        inputs=[msg_input, chatbot_ui],
        outputs=[chatbot_ui, msg_input],
        show_progress=True
    )
    
    msg_input.submit(
        fn=respond,
        inputs=[msg_input, chatbot_ui],
        outputs=[chatbot_ui, msg_input],
        show_progress=True
    )
    
    clear_btn.click(
        fn=clear_conversation,
        outputs=[chatbot_ui, msg_input]
    )
    
    # 사용법 안내
    with gr.Accordion("📖 사용법", open=False):
        gr.Markdown("""
        ### 기능 설명:
        - **멀티턴 대화**: 이전 대화 내용을 기억하며 연속적인 대화 가능
        - **스트리밍**: 실시간으로 응답이 생성되는 모습을 확인 가능
        - **대화 초기화**: 새로운 주제로 대화를 시작하고 싶을 때 사용
        
        ### 사용 방법:
        1. OpenAI API 키를 설정에서 입력 (필수)
        2. 메시지 입력창에 질문이나 대화 내용 작성
        3. '전송' 버튼 클릭 또는 Enter 키로 메시지 전송
        4. ChatGPT의 응답을 실시간으로 확인
        
        ### 주의사항:
        - OpenAI API 키가 필요합니다
        - 인터넷 연결이 필요합니다
        - API 사용량에 따라 요금이 부과될 수 있습니다
        """)

if __name__ == "__main__":
    # 서버 실행
    demo.launch(
        server_name="0.0.0.0",  # 외부 접속 허용
        server_port=7860,       # 포트 번호
        share=True,             # 공유 링크 생성
        debug=True              # 디버그 모드
    )