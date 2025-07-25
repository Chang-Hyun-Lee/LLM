import streamlit as st

st.title("간단한 테스트")

with st.sidebar:
    st.header("테스트 영역")
    test_upload = st.file_uploader("파일 선택", type=["pdf"])
    
    if test_upload is not None:
        st.write("파일이 업로드되었습니다!")