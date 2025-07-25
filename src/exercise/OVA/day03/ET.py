import streamlit as st
import time
from gtts import gTTS
import io

# 페이지 설정
st.set_page_config(
    page_title="AI-OPIC.COM - 다이어트 주제 연습",
    page_icon="🏃‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 음성 재생 함수
@st.cache_data
def text_to_audio(text, lang='en'):
    """텍스트를 음성으로 변환 (캐시 적용)"""
    try:
        # 마크다운 형식 제거
        clean_text = text.replace('**', '').replace('*', '')
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except Exception as e:
        return None

def play_audio_button(text, button_text="🔊 듣기", key=None):
    """음성 재생 버튼 생성"""
    if st.button(button_text, key=key, use_container_width=True):
        audio_bytes = text_to_audio(text)
        if audio_bytes:
            st.audio(audio_bytes, format='audio/mp3')
        else:
            st.warning("음성 생성 실패. 인터넷 연결을 확인해주세요.")

# CSS 스타일
st.markdown("""
<style>
    .main {
        padding-top: 20px;
    }
    
    .main-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        margin-bottom: 10px;
        font-weight: bold;
    }
    
    .main-header h3 {
        font-size: 1.2rem;
        opacity: 0.9;
        font-weight: normal;
    }
    
    .question-card {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        margin: 20px 0;
        border: 1px solid #e0e0e0;
    }
    
    .level-badge {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 25px;
        color: white;
        font-weight: bold;
        margin-bottom: 20px;
        font-size: 1.1rem;
    }
    
    .im1-badge {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    }
    
    .im2-badge {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    }
    
    .strategy-box {
        background: linear-gradient(135deg, #e8f4f8 0%, #f0f9ff 100%);
        padding: 25px;
        border-radius: 15px;
        border-left: 5px solid #17a2b8;
        margin: 20px 0;
    }
    
    .strategy-box h3 {
        color: #17a2b8;
        margin-bottom: 15px;
        font-size: 1.3rem;
    }
    
    .toc-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .toc-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .answer-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 4px solid #28a745;
    }
    
    .question-section {
        background: #fff3cd;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# 문제 데이터
questions_data = [
    {
        'level': 'IM1',
        'category': '01 묘사/설명',
        'topic': '다이어트 경험과 건강 관리',
        'question': 'Have you ever been on a diet? What methods do you use to maintain a healthy weight?',
        'answer': 'Yes, I have tried dieting several times, though I prefer to think of it as maintaining a healthy lifestyle rather than strict dieting. I focus on eating balanced meals with plenty of vegetables, lean proteins, and whole grains while limiting processed foods. I try to drink lots of water and avoid sugary drinks most of the time. For exercise, I go to the gym 3-4 times per week and do a combination of cardio and strength training. I also track my portions and try not to eat late at night. The key for me is consistency rather than extreme restrictions that are hard to maintain long-term.',
        'strategies': [
            '건강한 관점: "healthy lifestyle rather than strict dieting" 등 균형잡힌 접근',
            '식단 관리: "balanced meals", "vegetables, lean proteins" 등 구체적 식단',
            '수분 섭취: "drink lots of water", "avoid sugary drinks" 등 기본 수칙',
            '운동 루틴: "gym 3-4 times per week", "cardio and strength training" 등 구체적 운동',
            '지속가능성: "consistency rather than extreme restrictions" 등 현실적 접근'
        ]
    },
    {
        'level': 'IM1',
        'category': '02 루틴/습관',
        'topic': '식단과 운동 관리 루틴',
        'question': 'What is your daily routine for eating and exercising? How do you stay motivated?',
        'answer': 'I start my day with a protein-rich breakfast like eggs or Greek yogurt to keep me full longer. For lunch and dinner, I fill half my plate with vegetables and include lean protein and complex carbs. I meal prep on Sundays to avoid unhealthy food choices during busy weekdays. I exercise early in the morning because I have more energy and it is harder to make excuses. To stay motivated, I track my progress with photos and measurements rather than just relying on the scale. I also reward myself with non-food treats like new workout clothes when I reach small goals.',
        'strategies': [
            '아침 식사: "protein-rich breakfast", "eggs or Greek yogurt" 등 영양학적 접근',
            '식판 구성: "fill half plate with vegetables" 등 시각적 가이드',
            '사전 준비: "meal prep on Sundays" 등 계획적 식단 관리',
            '운동 타이밍: "early in the morning" 등 효율적 시간 선택',
            '동기 부여: "track progress with photos", "non-food treats" 등 지속 방법'
        ]
    },
    {
        'level': 'IM2',
        'category': '03 롤플레이',
        'topic': '다이어트 시작 조언하기',
        'question': 'Your friend wants to start a diet but feels overwhelmed. What practical advice would you give them?',
        'answer': 'I would tell them to start with small, manageable changes rather than completely overhauling their lifestyle overnight. Begin by drinking more water and eating one extra serving of vegetables daily. Set realistic goals like losing 1-2 pounds per week instead of aiming for dramatic results. I would recommend keeping a food diary for a week to understand their current eating patterns. Find physical activities they enjoy - it does not have to be the gym; dancing, hiking, or swimming work too. Most importantly, do not aim for perfection - having an occasional treat will not ruin progress. Focus on building habits that can be maintained for life rather than quick fixes.',
        'strategies': [
            '점진적 변화: "small, manageable changes" 등 부담 없는 시작',
            '구체적 행동: "drinking more water", "one extra serving vegetables" 등 명확한 지침',
            '현실적 목표: "1-2 pounds per week" 등 달성 가능한 목표',
            '자기 인식: "keeping food diary" 등 현재 상태 파악',
            '유연한 접근: "do not aim for perfection" 등 완벽주의 경계'
        ]
    },
    {
        'level': 'IM2',
        'category': '04 과거경험',
        'topic': '다이어트 성공과 실패 경험',
        'question': 'Tell me about a time when you struggled with dieting or weight management. What did you learn?',
        'answer': 'A few years ago, I tried an extremely restrictive low-carb diet because I wanted quick results for a wedding. For the first month, I lost weight rapidly and felt very motivated. However, I started feeling constantly tired and irritable because I was not getting enough energy. Eventually, I gave up and gained back all the weight plus a few extra pounds. This experience taught me that extreme diets are not sustainable and often lead to a cycle of restriction and overeating. I learned to focus on gradual lifestyle changes instead of dramatic short-term fixes. Now I understand that consistency beats perfection every time.',
        'strategies': [
            '구체적 다이어트: "extremely restrictive low-carb diet" 등 명확한 방법',
            '초기 성공: "lost weight rapidly", "felt motivated" 등 처음의 희망',
            '부작용 경험: "constantly tired and irritable" 등 신체적 문제',
            '리바운드 현상: "gained back all weight plus extra" 등 전형적 실패',
            '교훈 도출: "extreme diets not sustainable", "consistency beats perfection" 등 학습'
        ]
    },
    {
        'level': 'IM2',
        'category': '05 비교',
        'topic': '운동 vs 식단 조절 비교',
        'question': 'Which is more important for weight loss: exercise or controlling your diet? What do you think?',
        'answer': 'While both are important, I believe diet plays a more crucial role in weight loss than exercise alone. The saying "you cannot out-exercise a bad diet" is really true - it is much easier to consume calories than burn them. For example, a donut has 300 calories but you would need to run for 30 minutes to burn that off. However, exercise is essential for overall health and helps build muscle, boost metabolism, and improve mood. The best approach combines both - using diet to create a calorie deficit and exercise to maintain muscle mass and improve fitness. Diet might be 70 percent and exercise 30 percent of the weight loss equation, but both are necessary for long-term health and maintaining results.',
        'strategies': [
            '주장의 명확성: "diet plays more crucial role" 등 분명한 입장',
            '인용구 활용: "you cannot out-exercise bad diet" 등 격언 사용',
            '구체적 예시: "donut 300 calories", "run 30 minutes" 등 비교 사례',
            '운동의 가치: "essential for overall health" 등 운동 중요성 인정',
            '수치화된 비율: "diet 70 percent, exercise 30 percent" 등 정량적 표현'
        ]
    },
    {
        'level': 'IM2',
        'category': '06 돌발주제',
        'topic': '다이어트 문화와 사회적 압박',
        'question': 'What do you think about society\'s pressure to be thin? Is diet culture becoming too extreme?',
        'answer': 'I think modern diet culture has become problematic in many ways, especially with social media promoting unrealistic body standards. The constant pressure to be thin can lead to unhealthy relationships with food and negative self-image, particularly among young people. Extreme diet trends and quick fix solutions are often promoted without considering long-term health consequences. However, I also believe encouraging healthy habits is important given rising obesity rates and related health problems. The key is focusing on health rather than appearance and promoting body acceptance while still supporting wellness. Education about nutrition and balanced living should replace the obsession with being thin. We need to shift toward celebrating diverse body types and emphasizing overall well-being.',
        'strategies': [
            '문제 인식: "modern diet culture has become problematic" 등 비판적 시각',
            '사회적 영향: "social media promoting unrealistic standards" 등 현실적 원인',
            '부정적 결과: "unhealthy relationships with food" 등 피해 사례',
            '균형잡힌 접근: "encouraging healthy habits is important" 등 건설적 대안',
            '미래 지향적: "celebrating diverse body types" 등 이상적 방향성'
        ]
    }
]

# 세션 상태 초기화
if 'current_topic' not in st.session_state:
    st.session_state.current_topic = 0
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = {}
if 'show_strategy' not in st.session_state:
    st.session_state.show_strategy = {}

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>🏃‍♀️ AI-OPIC.COM</h1>
    <h3>다이어트 주제 콤보형 문제 연습 (음성 지원)</h3>
</div>
""", unsafe_allow_html=True)

# 사이드바 네비게이션
with st.sidebar:
    st.markdown("### 📚 학습 목차")
    
    if st.button("🏠 전체 목차 보기", use_container_width=True):
        st.session_state.current_topic = -1
        st.rerun()
    
    st.markdown("---")
    
    for i, data in enumerate(questions_data):
        topic_button = f"{i+1}. {data['topic']}"
        if st.button(topic_button, key=f"nav_{i}", use_container_width=True):
            st.session_state.current_topic = i
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 🔊 음성 기능")
    st.info("🎵 각 질문과 답변을 영어로 들을 수 있습니다!")

# 메인 콘텐츠
if st.session_state.current_topic == -1:
    # 전체 목차 페이지
    st.markdown("## 📖 다이어트 주제 학습 목차")
    st.markdown("원하는 주제를 클릭하여 학습을 시작하세요!")
    
    # 2열로 배치
    col1, col2 = st.columns(2)
    
    for i, data in enumerate(questions_data):
        with col1 if i % 2 == 0 else col2:
            with st.container():
                st.markdown(f"""
                <div class="toc-card">
                    <h4 style="color: #667eea; margin-bottom: 10px;">{data['category']}</h4>
                    <h3 style="color: #2c3e50; margin-bottom: 10px;">{data['topic']}</h3>
                    <p style="color: #666; margin-bottom: 0;"><strong>레벨:</strong> {data['level']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"▶️ {data['topic']} 학습하기", key=f"toc_btn_{i}", use_container_width=True):
                    st.session_state.current_topic = i
                    st.rerun()

else:
    # 개별 문제 페이지
    if 0 <= st.session_state.current_topic < len(questions_data):
        data = questions_data[st.session_state.current_topic]
        topic_idx = st.session_state.current_topic
        
        # 레벨 배지
        level_class = "im1-badge" if data['level'] == 'IM1' else "im2-badge"
        st.markdown(f"""
        <div class="level-badge {level_class}">
            {data['category']} - 문제 {topic_idx + 1}/6 ({data['level']})
        </div>
        """, unsafe_allow_html=True)
        
        # 주제 제목
        st.markdown(f"## {data['topic']}")
        
        # 질문 섹션
        st.markdown("### 🎤 Question")
        
        with st.container():
            st.markdown(f"""
            <div class="question-section">
                <h4 style="margin-bottom: 15px;">🗣️ {data['question']}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            # 질문 듣기 버튼
            col1, col2 = st.columns([3, 1])
            with col2:
                play_audio_button(data['question'], "🔊 질문 듣기", f"q_audio_{topic_idx}")
        
        # 답안 보기/숨기기
        answer_key = f"answer_{topic_idx}"
        if answer_key not in st.session_state.show_answer:
            st.session_state.show_answer[answer_key] = False
        
        if st.button(
            "💡 모범 답안 보기" if not st.session_state.show_answer[answer_key] else "📖 모범 답안 숨기기",
            key=f"toggle_answer_{topic_idx}",
            type="primary",
            use_container_width=True
        ):
            st.session_state.show_answer[answer_key] = not st.session_state.show_answer[answer_key]
            st.rerun()
        
        # 모범 답안 표시
        if st.session_state.show_answer[answer_key]:
            st.markdown("### 💡 Model Answer")
            
            with st.container():
                st.markdown(f"""
                <div class="answer-section">
                    <p style="line-height: 1.6; margin-bottom: 0;">{data['answer']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 답안 듣기 버튼
                col1, col2 = st.columns([3, 1])
                with col2:
                    play_audio_button(data['answer'], "🔊 답안 듣기", f"a_audio_{topic_idx}")
        
        # 전략 분석 보기/숨기기
        strategy_key = f"strategy_{topic_idx}"
        if strategy_key not in st.session_state.show_strategy:
            st.session_state.show_strategy[strategy_key] = False
        
        if st.button(
            "🎯 고득점 전략 보기" if not st.session_state.show_strategy[strategy_key] else "📚 전략 분석 숨기기",
            key=f"toggle_strategy_{topic_idx}",
            use_container_width=True
        ):
            st.session_state.show_strategy[strategy_key] = not st.session_state.show_strategy[strategy_key]
            st.rerun()
        
        # 전략 분석 표시
        if st.session_state.show_strategy[strategy_key]:
            st.markdown("""
            <div class="strategy-box">
                <h3>🎯 고득점 전략 분석</h3>
            </div>
            """, unsafe_allow_html=True)
            
            for i, strategy in enumerate(data['strategies']):
                st.markdown(f"**{i+1}.** {strategy}")
        
        # 네비게이션 버튼
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if topic_idx > 0:
                if st.button("⬅️ 이전 문제", use_container_width=True):
                    st.session_state.current_topic = topic_idx - 1
                    st.rerun()
        
        with col2:
            if st.button("📋 전체 목차로", use_container_width=True):
                st.session_state.current_topic = -1
                st.rerun()
        
        with col3:
            if topic_idx < len(questions_data) - 1:
                if st.button("다음 문제 ➡️", use_container_width=True):
                    st.session_state.current_topic = topic_idx + 1
                    st.rerun()

# 하단 정보
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 30px;">
    <p>🌟 <strong>AI-OPIC.COM</strong>에서 제공하는 실전 OPIC 연습 🌟</p>
    <p>🎵 <strong>음성 지원</strong> | 📱 <strong>모바일 최적화</strong> | 🚀 <strong>Streamlit 기반</strong></p>
    <p><small>💡 인터넷 연결이 필요합니다 (Google TTS 사용)</small></p>
</div>
""", unsafe_allow_html=True)