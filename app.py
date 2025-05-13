# ───────────────────────────────────────────────────────
# PVD Search App  ‒ with VERY simple in-app authentication
# ID : korloy      PW : 19660611
# ───────────────────────────────────────────────────────
import streamlit as st
st.set_page_config(page_title="PVD Search",
                   layout="wide",
                   initial_sidebar_state="collapsed")

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
# ───────────────────────────────────────────────────────
# ▼ 0. 간단 로그인 로직  (세션 상태에 토큰 저장)
# ───────────────────────────────────────────────────────
VALID_USERS = {"korloy": "19660611"}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    """로그인 버튼 콜백"""
    uid = st.session_state["__uid"].strip()
    pw  = st.session_state["__pw"].strip()
    if VALID_USERS.get(uid) == pw:
        st.session_state.authenticated = True
        st.success("로그인 성공! 🎉")
        st.experimental_rerun()
    else:
        st.error("ID 또는 비밀번호가 잘못됐음!")

def logout():
    st.session_state.authenticated = False
    st.experimental_rerun()

# ───────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.title("🔐 PVD Search ‒ Login")
    st.text_input("ID", key="__uid")
    st.text_input("Password", type="password", key="__pw")
    st.button("로그인", on_click=login)
    st.stop()                # 로그인 전엔 아래 코드 실행 안 됨
# ───────────────────────────────────────────────────────

# ▼ (옵션) 로그아웃 버튼
st.sidebar.button("🔓 로그아웃", on_click=logout)

# ───────────────────────────────────────────────────────
# ▼ 1. 데이터 로드
# ───────────────────────────────────────────────────────
DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"

@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    return raw.fillna(""), ref.fillna("")

raw_df, ref_df = load_data()

# ───────────────────────────────────────────────────────
# ▼ 2. 탭 UI
# ───────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# ── TAB 1 : 자재번호 검색
with tab1:
    st.subheader("자재번호·형번·재종 전역 검색")
    query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")

    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
    view = raw_sorted if not query else raw_sorted[
        raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
    ]

    cols_show = ["자재번호", "형번", "CB", "재종", "전처리", "후처리",
                 "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

    gb = GridOptionsBuilder.from_dataframe(view[cols_show])
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    AgGrid(view[cols_show], gridOptions=gb.build(), height=550)

# ── TAB 2 : 재종 검색
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
    if alloy_pick != "전체": filt = filt[filt["합금"] == alloy_pick]
    if grade_pick != "전체": filt = filt[filt["재종"] == grade_pick]
    if key2: filt = filt[filt.apply(lambda r: key2.lower() in " ".join(r.astype(str)).lower(), axis=1)]

    filt = filt.sort_values(["박막명", "코팅그룹"])

    cols2_show = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
                  "색상", "관리규격", "가용설비", "작업시간", "합금",
                  "공정특이사항", "인선처리"]

    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2_show])
    gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    AgGrid(filt[cols2_show], gridOptions=gb2.build(), height=550)

# ───────────────────────────────────────────────────────
st.caption("ⓒ 2025 Korloy DX · Streamlit Community Cloud")
