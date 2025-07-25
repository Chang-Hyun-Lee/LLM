import streamlit as st
import pandas as pd
from datetime import datetime as dt
import datetime

st.write('버튼을 눌러보세요.')

button = st.button('버튼')

if button:
    st.write('버튼이 눌렸습니다')

human = st.checkbox('사람이면 체크해주세요.')

if human:
    st.write('당신은 사람이군요!')

religion = st.radio(
    index=None,
    label='당신의 종교는 무엇입니까?',
    options=('기독교', '천주교', '불교', '기타', '무교')
)
     
if religion:
    st.write("당신의 종교는 *" + religion + "* 이군요!")     

school = st.selectbox(
    index=None,
    label='당신의 최종학력은 무엇입니까?',
    options=('대학원졸', '대졸', '고졸')
)

if school:
    st.write("당신의 최종학력은 :sparkle:" + school + ":sparkle: 이군요!")     

foods = st.multiselect(
    '당신이 가장 좋아하는 음식은 뭔가요?',
    ['돼지갈비', '소갈비', '스테이크', '생선회', '삼겹살', '김치찌개']
)

if len(foods) > 0:
    st.write(f'당신이 가장 좋아하는 음식은 {foods}입니다.')

bp = st.slider('혈압 범위를 지정해주세요.',
    6.0, 200.0, (90.0, 130.0))
st.write('이완기 혈압:', bp[0])
st.write('수축기 혈압:', bp[1])

birthday_time = st.slider(
    "당신의 출생년월일 시각을 알려주세요",
    min_value=dt(1950, 1, 1, 0, 0), 
    max_value=dt(2024, 3, 11, 12, 0),
    step=datetime.timedelta(hours=1),
    format="MM/DD/YY - HH:mm")
st.write(f"당신의 생년월일시는 {birthday_time}입니다.")

name = st.text_input(
    label='이름', 
    placeholder='당신의 이름을 입력해주세요.'
)
if name:
    st.write(f'안녕하세요 {name}씨!')

employee = st.number_input(
    label='당신의 회사 인원 수를 알려주세요.', 
    min_value=1, 
    max_value=300, 
    value=30,
    step=5
)
st.write(f'당신 회사의 인원수는 {employee}명입니다.')
