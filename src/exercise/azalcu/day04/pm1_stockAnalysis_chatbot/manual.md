# AI 주식 분석기 실행 매뉴얼

이 문서는 **AI 주식 분석기**를 설치하고 실행하는 방법을 단계별로 안내합니다.

## 1. 프로젝트 소개

본 프로젝트는 사용자가 사이드바에서 주식 종목과 기간을 선택하여 분석을 요청하면, 해당 주식의 데이터 기반 리포트와 주가 차트를 제공합니다. 또한, 생성된 리포트를 바탕으로 AI에게 추가적인 질문을 할 수 있는 웹 애플리케이션입니다.

-   **주요 기술**: Streamlit, LangChain, OpenAI API, pykrx

## 2. 사전 준비 사항

-   **Python**: 버전 3.8 이상 ([설치 링크](https://www.python.org/downloads/))
-   **OpenAI API Key**: ChatGPT API 사용을 위한 키 ([발급 링크](https://platform.openai.com/account/api-keys))

## 3. 설치 및 실행 방법

### 1단계: 프로젝트 폴더 및 파일 준비

컴퓨터에 `stock_analyzer` 라는 이름의 폴더를 만들고, 그 안에 아래 파일들을 준비합니다.

```
stock_analyzer/
├── .streamlit/
│   └── secrets.toml  <-- (2단계에서 생성)
├── app.py
└── stock_tool.py
```

### 2단계: OpenAI API 키 설정

1.  프로젝트 폴더(`stock_analyzer/`) 안에 `.streamlit`이라는 새 폴더를 만듭니다.
2.  `.streamlit` 폴더 안에 `secrets.toml`이라는 파일을 생성합니다.
3.  `secrets.toml` 파일을 열어 아래 내용을 복사하고, `YOUR_API_KEY_HERE` 부분을 **자신의 OpenAI API 키로 반드시 교체**합니다.

    ```toml
    # .streamlit/secrets.toml
    OPENAI_API_KEY = "YOUR_API_KEY_HERE"
    ```

### 3단계: 필요 라이브러리 설치

터미널을 열어 `cd` 명령어로 프로젝트 폴더(`stock_analyzer/`)로 이동한 뒤, 아래 명령어를 실행하여 필요한 라이브러리를 모두 설치합니다.

```bash
pip install streamlit langchain langchain-openai pykrx pandas openai
```

### 4단계: 애플리케이션 실행

1.  터미널이 프로젝트 폴더를 가리키고 있는지 확인합니다.
2.  아래 명령어를 입력하여 애플리케이션을 실행합니다.

    ```bash
    streamlit run app.py
    ```

3.  명령어를 실행하면 자동으로 웹 브라우저가 열리면서 "AI 주식 분석기" 화면이 나타납니다.

## 4. 사용 방법

1.  웹 페이지 왼쪽의 **사이드바**에서 **'분석할 종목명'**을 입력하고, **'분석 기간'**을 슬라이더로 조절합니다.
2.  **[📊 주가 분석 실행]** 버튼을 클릭합니다.
3.  잠시 후, 화면에 데이터 기반의 **기본 분석 리포트**와 **주가 차트**가 나타납니다.
4.  결과 하단에 있는 **'AI에게 추가 질문하기'** 입력창에 생성된 리포트에 대한 궁금한 점을 질문하고 Enter 키를 누르면 AI의 답변을 받을 수 있습니다.

## 5. 문제 해결 FAQ (자주 묻는 질문)

**Q: 웹 페이지에 아무것도 안 뜨거나 오류 메시지만 표시돼요!**

A: 이 문제의 가장 흔한 원인은 **API 키 설정 오류**입니다. 아래 순서대로 확인해주세요.
    1.  **`.streamlit/secrets.toml` 파일 위치 확인**: `stock_analyzer/.streamlit/secrets.toml` 경로가 정확한지 확인하세요.
    2.  **API 키 값 확인**: `secrets.toml` 파일에 `OPENAI_API_KEY = "sk-..."` 형식으로 키가 올바르게 입력되었는지, 앞뒤에 공백은 없는지 확인하세요.
    3.  **라이브러리 설치 확인**: 3단계의 `pip install` 명령어가 오류 없이 완료되었는지 확인하세요.
    4.  **터미널 로그 확인**: `streamlit run app.py`를 실행한 터미널 창에 나타나는 에러 메시지를 확인하면 정확한 원인을 알 수 있습니다.

**Q: "종목명을 찾을 수 없습니다" 오류가 발생해요.**

A: 입력한 종목명이 한국거래소(KRX)에 상장된 정확한 이름인지 확인해주세요. (예: `삼성전자 O`, `삼성 전자 X`)