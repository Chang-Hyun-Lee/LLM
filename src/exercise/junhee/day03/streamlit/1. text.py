import streamlit as st

st.title('Streamlit text')

# https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/
st.title('스마일 :sunglasses:')

st.header('이것은 헤더입니다')

st.subheader('이것은 subheader 입니다')

st.caption('캡션')

code = '''
def sample_func():
    print("Sample 함수")
'''
st.code(code, language="python")

st.text('ChatGPT 개발 교육 과정입니다.')

st.markdown('## 마크다운 ## ** 마크다운 **')
