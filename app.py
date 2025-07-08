# PVD Search App – login + auto column width (char-based)
import streamlit as st
st.set_page_config(page_title="PVD Search", layout="wide", initial_sidebar_state="collapsed")

import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# ── 0. 로그인 ───────────────────────────────────────────
import hashlib
from datetime import datetime, timedelta
import extra_streamlit_components as stx
# 기존: from extra_streamlit_components import CookieManager

cookie_mgr = stx.CookieManager()


VALID_USERS = {"Korloy": "19660611"}             # 계정 1개
COOKIE_NAME   = "pvd_auth"                       # 쿠키 키
COOKIE_TTL    = 30                               # 유지 일수 (필요 시 조정)
FIXED_TOKEN   = hashlib.sha256("Korloy|19660611".encode()).hexdigest()

cookie_mgr: CookieManager = CookieManager(prefix="pvd")   # prefix로 충돌 방지

# 1) 쿠키 확인 → 세션 인증 플래그 세팅
if "authenticated" not in st.session_state:
    cookies = cookie_mgr.get_all()
    if cookies.get(COOKIE_NAME) == FIXED_TOKEN:
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

# 2) 로그인/로그아웃 함수
def login():
    uid = st.session_state["__uid"].strip()
    pw  = st.session_state["__pw"].strip()
    if VALID_USERS.get(uid) == pw:
        st.session_state.authenticated = True
        # 쿠키 만료 시각 지정
        expires = (datetime.utcnow() + timedelta(days=COOKIE_TTL)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        cookie_mgr.set(COOKIE_NAME, FIXED_TOKEN, expires=expires)    # 쿠키 저장
        st.success("로그인 성공! 🎉")
        st.rerun()
    else:
        st.error("ID 또는 비밀번호가 틀렸습니다. 대소문자를 확인해 주세요.")

def logout():
    st.session_state.authenticated = False
    cookie_mgr.delete(COOKIE_NAME)          # 쿠키 삭제 → 완전 로그아웃
    st.rerun()

# 3) UI
if not st.session_state.authenticated:
    st.title("🔐 PVD Search ‒ Login")
    st.text_input("ID",        key="__uid")
    st.text_input("Password",  key="__pw", type="password")
    st.button("로그인", on_click=login)
    st.stop()

st.sidebar.button("🔓 로그아웃", on_click=logout)


# VALID_USERS = {"Korloy": "19660611"}
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# def login():
#     if VALID_USERS.get(st.session_state["__uid"].strip()) == st.session_state["__pw"].strip():
#         st.session_state.authenticated = True
#         st.success("로그인 성공! 🎉")
#         st.rerun()
#     else:
#         st.error("ID 또는 비밀번호가 틀렸습니다. 대소문자를 확인해 주세요.")

# def logout():
#     st.session_state.authenticated = False
#     st.rerun()

# if not st.session_state.authenticated:
#     st.title("🔐 PVD Search ‒ Login")
#     st.text_input("ID", key="__uid")
#     st.text_input("Password", type="password", key="__pw")
#     st.button("로그인", on_click=login)
#     st.stop()

# st.sidebar.button("🔓 로그아웃", on_click=logout)

# ── 1. 데이터 로드 ──────────────────────────────────────
DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"
@st.cache_data
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    return raw.fillna(""), ref.fillna("")
raw_df, ref_df = load_data()

# ── 유틸 : 폭 계산 ──────────────────────────────────────
def calc_widths(df: pd.DataFrame, cols, px_per_char=10, margin=30, min_px=120, max_px=600):
    out = {}
    for c in cols:
        max_len = max(df[c].astype(str).str.len().max(), len(c))
        out[c] = int(min(max_len * px_per_char + margin, max_px))
        if out[c] < min_px:
            out[c] = min_px
    return out

# ── 2. UI 탭 ────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# ─ TAB 1 ───────────────────────────────────────────────
with tab1:
    st.subheader("자재번호·형번·재종 전역 검색")
    query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")

    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
    if query:
        mask = raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
        view = raw_sorted.loc[mask]
    else:
        view = raw_sorted


    cols1 = ["자재번호", "형번", "CB", "박막명", "재종", "코팅그룹", "합금", "가용설비", "관리규격", "RUN TIME(분)", "전처리", "후처리",
             "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

    gb1 = GridOptionsBuilder.from_dataframe(view[cols1])
    for col, w in calc_widths(view, cols1).items():
        gb1.configure_column(col, width=w)
    gb1.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

    AgGrid(
        view[cols1].astype(str),
        gridOptions=gb1.build(),
        height=550,
        fit_columns_on_grid_load=False
    )

# ─ TAB 2 ───────────────────────────────────────────────
with tab2:
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

    cols2 = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
             "색상", "관리규격", "가용설비", "작업시간", "합금",
             "공정특이사항", "인선처리"]

    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2])
    for col, w in calc_widths(filt, cols2).items():
        gb2.configure_column(col, width=w)
    gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

    AgGrid(
        filt[cols2].astype(str),
        gridOptions=gb2.build(),
        height=550,
        fit_columns_on_grid_load=False
    )

# ─ 푸터 ────────────────────────────────────────────────
st.caption("ⓒ made by. 연삭코팅기술팀 홍재민 선임 · 2025 Korloy DX")
