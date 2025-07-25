PDF ChatGPT 애플리케이션 실행 가이드
📋 프로젝트 구조
pdf-chatgpt/
├── app.py              # Streamlit 웹 애플리케이션 (Day 3)
├── day2_chatbot.py     # 기본 콘솔 애플리케이션 (Day 2)
├── ingest.py          # PDF 인덱싱 모듈
├── requirements.txt   # 필요한 패키지 목록
└── README.md         # 이 파일
🛠️ 설치 및 설정
1. 파이썬 환경 준비
bash
# Python 3.8+ 필요
python --version

# 가상환경 생성 (권장)
python -m venv pdf_chatgpt
source pdf_chatgpt/bin/activate  # Linux/Mac
# 또는
pdf_chatgpt\Scripts\activate     # Windows
2. 패키지 설치
bash
pip install -r requirements.txt
3. OpenAI API 키 준비
OpenAI 웹사이트에서 API 키를 발급받으세요
API 키는 sk-로 시작합니다
🚀 실행 방법
Day 2 실습: 콘솔 애플리케이션
bash
python day2_chatbot.py
OpenAI API 키 입력
PDF 파일 경로 입력
대화형으로 질문/답변
Day 3 실습: Streamlit 웹 애플리케이션
bash
streamlit run app.py
브라우저에서 http://localhost:8501 접속
사이드바에서 API 키 입력
PDF 파일 업로드 및 처리
웹 인터페이스에서 질문/답변
인덱싱 모듈 단독 사용
bash
# CLI로 PDF 인덱싱
python ingest.py document.pdf ./vectorstore

# 또는 환경변수로 API 키 설정
export OPENAI_API_KEY="your-api-key-here"
python ingest.py document.pdf ./vectorstore
📚 주요 기능
Day 2 기능
✅ PDF 파일 로드 및 텍스트 추출
✅ 텍스트 청크 분할
✅ OpenAI 임베딩 생성
✅ FAISS 벡터 스토어 구축
✅ 대화형 질의응답
✅ 출처 페이지 표시
✅ 대화 기록 유지
Day 3 추가 기능
✅ Streamlit 웹 인터페이스
✅ 파일 업로드 기능
✅ 실시간 처리 상태 표시
✅ 저장된 인덱스 로드
✅ 대화 기록 관리
✅ 반응형 웹 디자인
🔧 사용 팁
PDF 파일 요구사항
파일 형식: PDF (.pdf)
텍스트가 포함된 PDF (이미지만 있는 PDF는 OCR 필요)
파일 크기: 10MB 이하 권장
API 사용량 최적화
작은 청크 크기로 시작 (chunk_size=500)
필요시에만 새로운 인덱스 생성
생성된 벡터 스토어는 저장 후 재사용
성능 향상
GPU가 있는 경우 faiss-gpu 설치 고려
대용량 문서는 배치 처리 권장
메모리 부족시 청크 크기 줄이기
❗ 문제 해결
일반적인 오류
API 키 오류: OpenAI API 키 확인 및 잔액 확인
메모리 오류: 청크 크기를 줄이거나 파일 크기 축소
패키지 오류: pip install --upgrade package-name
PDF 로드 오류: PDF 파일 형식 및 텍스트 포함 확인
Windows 사용자
bash
# Windows에서 Magic 패키지 문제 시
pip install python-magic-bin
Mac 사용자
bash
# M1/M2 Mac에서 FAISS 설치 문제 시
conda install faiss-cpu -c conda-forge
🎯 학습 목표 달성 확인
Day 2 실습 완료 체크리스트
 LangChain으로 PDF 로드
 텍스트 분할 및 임베딩
 FAISS 벡터 스토어 생성
 ChatGPT와 연동한 질의응답
 출처 정보 표시
Day 3 실습 완료 체크리스트
 Streamlit 웹 애플리케이션 구현
 파일 업로드 기능
 ingest.py 모듈 활용
 웹 인터페이스에서 질의응답
 저장된 인덱스 로드 기능
🔄 다음 단계
이 실습을 완료했다면 다음을 시도해보세요:

다중 파일 업로드 지원
채팅 기록 저장/불러오기
다른 LLM 모델 통합 (Claude, Gemini 등)
음성 인식/합성 추가
문서 요약 기능 추가
📞 지원
문제가 발생하면:

에러 메시지 확인
Python 및 패키지 버전 확인
API 키 및 잔액 확인
파일 형식 및 크기 확인
즐거운 학습 되세요! 🎉

