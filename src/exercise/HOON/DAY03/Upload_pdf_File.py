import streamlit as st
import PyPDF2

# 1. Streamlit 앱 기본 설정 및 제목
st.set_page_config(
    page_title="Streamlit PDF 파일 업로드 앱",
    page_icon="📑",
    layout="centered"
)

st.title("📑 PDF 파일 업로드 및 내용 추출 데모 📑")
st.write("아래에서 PDF 파일을 업로드하시면 그 내용을 추출하여 보여드릴게요!")


# 2. PDF 파일 (.pdf) 업로드
st.header("1. PDF 파일 업로드 (.pdf)")
uploaded_pdf_file = st.file_uploader(
    "PDF 파일을 업로드해 주세요",
    type=["pdf"], # PDF 파일만 허용
    key="pdf_uploader"
)

if uploaded_pdf_file is not None:
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_pdf_file)
        
        num_pages = len(pdf_reader.pages)
        st.info(f"✨ PDF 파일이 성공적으로 업로드되었습니다! 총 {num_pages} 페이지입니다.")
        
        st.subheader("2. 추출된 PDF 내용 미리보기 (첫 2페이지)")
        extracted_text = ""
        pages_to_show = min(num_pages, 2) 

        for i in range(pages_to_show):
            page = pdf_reader.pages[i]
            extracted_text += page.extract_text()
            
        if extracted_text:
            # 텍스트가 너무 길 경우 앞 부분만 보여주고, 텍스트 에어리어 높이 조절
            st.text_area("PDF 내용", extracted_text[:2000] + "..." if len(extracted_text) > 2000 else extracted_text, height=300)
            st.success("PDF 내용 추출 완료!")
            if len(extracted_text) > 2000:
                st.caption(f"(내용이 너무 길어서 앞 {2000}자만 보여드립니다. 전체 내용은 내부적으로 추출되었습니다.)")
        else:
            st.warning("PDF에서 텍스트를 추출하지 못했습니다. (이미지 기반 PDF이거나 텍스트가 없는 페이지일 수 있습니다.)")

    except Exception as e:
        st.error(f"🚨 PDF 파일을 처리하는 중 오류가 발생했습니다: {e}")
        st.warning("혹시 암호화된 PDF 파일이거나 손상된 파일일 수 있습니다. PyPDF2가 텍스트를 추출할 수 없는 PDF도 있습니다.")

else:
    st.info("👆 PDF 파일을 기다리고 있어요...")

st.markdown("---")
st.write("이제 업로드된 PDF 파일의 텍스트 내용을 AI에게 전달하거나 다른 분석에 활용할 수 있답니다!")