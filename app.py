import streamlit as st               # ① 먼저 import
st.set_page_config(                  
    page_title="PVD Search",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd                  # ③ 이후 나머지 import
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"

# ---------- 1) 데이터 로드 ----------
@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    # 결측치는 빈 문자열로 치환하여 검색 누락 방지
    return (raw.fillna(""), ref.fillna(""))

raw_df, ref_df = load_data()


# ---------- 2) 탭 UI ----------
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# -------------------------------------------------
# ----------------- TAB 1 : 자재번호 검색 -----------------
with tab1:
    st.subheader("자재번호·형번·재종 전역 검색")

    query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")
    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])

    if query:
        mask = raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
        view = raw_sorted.loc[mask]
    else:
        view = raw_sorted

    # 📌 표시 컬럼 교체
    cols_show = ["자재번호", "형번", "CB", "재종", "전처리", "후처리",
                 "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]
    gb = GridOptionsBuilder.from_dataframe(view[cols_show])
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    grid = AgGrid(view[cols_show], gridOptions=gb.build(), height=550)

# -------------------------------------------------
# ----------------- TAB 2 : 재종 검색 -----------------
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

    # 📌 표시 컬럼 교체
    cols2_show = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
                  "색상", "관리규격", "가용설비", "작업시간", "합금",
                  "공정특이사항", "인선처리"]
    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2_show])
    gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    grid2 = AgGrid(filt[cols2_show], gridOptions=gb2.build(), height=550)

# ---------- 3) 푸터 ----------
st.caption("ⓒ 2025 Korloy DX · Streamlit Community Cloud")
