import streamlit as st
import streamlit_authenticator as stauth

# ---------- 0) 로그인 기능 설정 ----------
# 사용자 정보
names = ["korloy"]
usernames = ["korloy"]
passwords = ["19660611"]

# 해시된 비번 생성 (실제 서비스시엔 미리 해시해서 secrets에 저장 권장)
hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {
    "usernames": {
        usernames[i]: {"name": names[i], "password": hashed_passwords[i]}
        for i in range(len(usernames))
    }
}

# Authenticate 객체 생성
authenticator = stauth.Authenticate(
    credentials,
    cookie_name="pvd_app_cookie",
    key="abcdef",             # 쿠키 암호화 키 (임의 문자열)
    cookie_expiry_days=1
)

# 로그인 UI
name, auth_status, username = authenticator.login("로그인", "main")

if auth_status is False:
    st.error("아이디/비밀번호가 틀렸음")
    st.stop()
elif auth_status is None:
    st.info("로그인 필요함")
    st.stop()

# ---------- 1) 페이지 설정 및 기본 import ----------
authenticator.logout("로그아웃", "sidebar")   # 사이드바에 로그아웃 버튼
st.set_page_config(
    page_title="PVD Search",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"

# ---------- 2) 데이터 로드 ----------
@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    return raw.fillna(""), ref.fillna("")

raw_df, ref_df = load_data()

# ---------- 3) 탭 UI ----------
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

with tab1:
    st.subheader("자재번호·형번·재종 전역 검색")
    query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")
    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
    if query:
        mask = raw_sorted.apply(
            lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1
        )
        view = raw_sorted.loc[mask]
    else:
        view = raw_sorted

    cols_show = [
        "자재번호", "형번", "CB", "재종", "전처리", "후처리",
        "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"
    ]
    gb = GridOptionsBuilder.from_dataframe(view[cols_show])
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    AgGrid(view[cols_show], gridOptions=gb.build(), height=550)

with tab2:
    st.subheader("재종·코팅그룹 상세 검색")
    col1, col2 = st.columns(2)
    with col1:
        alloy_pick = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()))
    with col2:
        temp = ref_df if alloy_pick == "전체" else ref_df[ref_df["합금"] == alloy_pick]
        grade_pick = st.selectbox("재종 선택", ["전체"] + sorted(temp["재종"].unique()))

    key2 = st.text_input("검색어 입력", placeholder="CX0824, TiAlN ...")
    filt = ref_df.copy()
    if alloy_pick != "전체":
        filt = filt[filt["합금"] == alloy_pick]
    if grade_pick != "전체":
        filt = filt[filt["재종"] == grade_pick]
    if key2:
        filt = filt[filt.apply(
            lambda r: key2.lower() in " ".join(r.astype(str)).lower(), axis=1
        )]

    filt = filt.sort_values(["박막명", "코팅그룹"])
    cols2_show = [
        "재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
        "색상", "관리규격", "가용설비", "작업시간", "합금",
        "공정특이사항", "인선처리"
    ]
    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2_show])
    gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    AgGrid(filt[cols2_show], gridOptions=gb2.build(), height=550)

# ---------- 4) 푸터 ----------
st.caption("ⓒ 2025 Korloy DX · Streamlit Community Cloud")
