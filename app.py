# PVD Search App – login + list/detail toggle
import streamlit as st
st.set_page_config(page_title="PVD Search", layout="wide", initial_sidebar_state="collapsed")

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# ── 0. 로그인 ───────────────────────────────────────────
VALID_USERS = {"Korloy": "19660611"}
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    if VALID_USERS.get(st.session_state["__uid"].strip()) == st.session_state["__pw"].strip():
        st.session_state.authenticated = True
        st.success("로그인 성공! 🎉")
        st.rerun()
    else:
        st.error("ID 또는 비밀번호가 틀렸습니다. 대소문자를 확인해 주세요.")

def logout():
    st.session_state.authenticated = False
    # 상세 보기 상태도 초기화
    st.session_state.pop("detail1", None)
    st.session_state.pop("detail2", None)
    st.rerun()

if not st.session_state.authenticated:
    st.title("🔐 PVD Search ‒ Login")
    st.text_input("ID", key="__uid")
    st.text_input("Password", type="password", key="__pw")
    st.button("로그인", on_click=login)
    st.stop()

st.sidebar.button("🔓 로그아웃", on_click=logout)

# ── 1. 데이터 로드 ──────────────────────────────────────
DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"
@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    return raw.fillna(""), ref.fillna("")
raw_df, ref_df = load_data()

# ── 유틸 : 컬럼 폭 계산 ──────────────────────────────────
def calc_widths(df, cols, px_per_char=10, margin=30, min_px=120, max_px=600):
    out = {}
    for c in cols:
        m = max(df[c].astype(str).str.len().max(), len(c))
        out[c] = min(max(m * px_per_char + margin, min_px), max_px)
    return out

# ── 상세공통: 세로 카드 형태로 보여주기 ──────────────────
def show_detail(row: dict, cols: list, back_key: str):
    st.button("◀ 뒤로가기", on_click=lambda: st.session_state.pop(back_key), key=f"back_{back_key}")
    for c in cols:
        st.markdown(f"**{c}**")
        st.write(row.get(c, ""))

# ── 2. UI 탭 ────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# ─ TAB 1 : 자재번호 검색 ────────────────────────────────
with tab1:
    detail_key = "detail1"
    detail_cols = ["자재번호", "형번", "CB", "코팅그룹", "박막명", "재종", "합금", "재종내역",
                   "가용설비", "관리규격", "RUN TIME(분)", "전처리", "후처리",
                   "공정특이사항", "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

    # 이미 상세화면이면 바로 보여주고 종료
    if detail_key in st.session_state:
        show_detail(st.session_state[detail_key], detail_cols, detail_key)
    else:
        st.subheader("자재번호·형번·재종 전역 검색")
        query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")

        raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
        view = raw_sorted if not query else raw_sorted[
            raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
        ]

        list_cols = ["자재번호", "형번", "CB", "재종", "전처리", "후처리",
                     "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

        gb1 = GridOptionsBuilder.from_dataframe(view[list_cols])
        for col, w in calc_widths(view, list_cols).items():
            gb1.configure_column(col, width=w)
        gb1.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb1.configure_selection("single")   # 행 선택 켜기

        grid_resp = AgGrid(
            view[list_cols].astype(str),
            gridOptions=gb1.build(),
            height=550,
            fit_columns_on_grid_load=False,
            key="grid1"
        )

        # 선택 시 상세로 전환
        if grid_resp["selected_rows"]:
            st.session_state[detail_key] = grid_resp["selected_rows"][0]
            st.rerun()

# ─ TAB 2 : 재종 검색 ───────────────────────────────────
with tab2:
    detail_key = "detail2"
    detail_cols = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
                   "색상", "관리규격", "가용설비", "작업시간", "합금",
                   "공정특이사항", "인선처리"]

    if detail_key in st.session_state:
        show_detail(st.session_state[detail_key], detail_cols, detail_key)
    else:
        st.subheader("재종·코팅그룹 상세 검색")
        c1, c2 = st.columns(2)
        with c1:
            alloy_pick = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()))
        with c2:
            tmp = ref_df if alloy_pick == "전체" else ref_df[ref_df["합금"] == alloy_pick]
            grade_pick = st.selectbox("재종 선택", ["전체"] + sorted(tmp["재종"].unique()))

        key2 = st.text_input("검색어 입력", placeholder="CX0824, TiAlN ...")

        filt = ref_df.copy()
        if alloy_pick != "전체": filt = filt[filt["합금"] == alloy_pick]
        if grade_pick != "전체": filt = filt[filt["재종"] == grade_pick]
        if key2: filt = filt[filt.apply(lambda r: key2.lower() in " ".join(r.astype(str)).lower(), axis=1)]
        filt = filt.sort_values(["박막명", "코팅그룹"])

        list_cols2 = ["재종", "코팅그룹", "재종내역", "박막명",
                      "색상", "관리규격", "가용설비", "작업시간", "합금",
                      "공정특이사항", "인선처리"]

        gb2 = GridOptionsBuilder.from_dataframe(filt[list_cols2])
        for col, w in calc_widths(filt, list_cols2).items():
            gb2.configure_column(col, width=w)
        gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
        gb2.configure_selection("single")

        grid2 = AgGrid(
            filt[list_cols2].astype(str),
            gridOptions=gb2.build(),
            height=550,
            fit_columns_on_grid_load=False,
            key="grid2"
        )

        if grid2["selected_rows"]:
            st.session_state[detail_key] = grid2["selected_rows"][0]
            st.rerun()

# ─ 푸터 ────────────────────────────────────────────────
st.caption("ⓒ made by. 연삭코팅기술팀 홍재민 선임 · 2025 Korloy DX")
