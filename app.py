# PVD Search App – v2.0 (UI/UX Improved)
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# ── CONFIG ────────────────────────────────────────────────
# [개선] 페이지 설정을 맨 위로 이동시키고, 아이콘 추가
st.set_page_config(
    page_title="PVD 공정 데이터 검색 시스템",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 1. 데이터 로드 & 유틸리티 ────────────────────────────────
# [개선] 데이터 로딩 부분을 위로 올려 가독성 확보
DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"

@st.cache_data
def load_data():
    """엑셀 데이터를 로드하고 캐시에 저장함"""
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
    # 공백이나 결측치를 빈 문자열로 일관성 있게 처리
    return raw.fillna(""), ref.fillna("")

# [유지] 컬럼 너비 계산 유틸리티는 유용하므로 그대로 사용
def calc_widths(df: pd.DataFrame, cols, px_per_char=10, margin=30, min_px=100, max_px=500):
    """컬럼 내용 길이에 맞춰 동적으로 너비를 계산함"""
    out = {}
    for c in cols:
        # 컬럼명 길이와 데이터 최대 길이를 모두 고려
        max_len = max(df[c].astype(str).str.len().max(), len(c))
        # 최적 너비 계산 (최소/최대값 제한)
        width = int(min(max_len * px_per_char + margin, max_px))
        out[c] = max(width, min_px)
    return out


# ── 데이터 로딩 실행 ──────────────────────────────────────────
try:
    raw_df, ref_df = load_data()
except FileNotFoundError:
    st.error(f"'{DATA_PATH}' 파일을 찾을 수 없음. 경로를 확인해 주세요.")
    st.stop()


# ── 2. UI 본문 ────────────────────────────────────────────
# [개선] 로그인 로직 전체 제거 및 앱 제목/설명 추가
st.title("🤖 PVD 공정 데이터 검색 시스템")
st.caption("자재번호, 재종, 코팅그룹 등 다양한 조건으로 공정 데이터를 검색할 수 있습니다.")

tab1, tab2 = st.tabs(["**🔍 통합 검색**", "**⚙️ 상세 조건 검색**"])

# ─ TAB 1: 통합 검색 ──────────────────────────────────────
with tab1:
    # [개선] 검색 영역을 컨테이너로 묶어 시각적 구분 강화
    with st.container(border=True):
        st.subheader("자재번호 · 형번 · 재종 전역 검색")
        query = st.text_input(
            "검색어 입력",
            placeholder="예: (대문자) 1-02-..., APKT1604, PC6510 등 여러 키워드를 띄어쓰기로 검색 가능",
            help="입력한 모든 키워드가 포함된 행을 검색합니다."
        )

    # 검색 로직: 띄어쓰기로 구분된 모든 키워드를 포함해야 함
    raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
    if query:
        # [개선] 검색어를 공백으로 분리하여 모든 키워드가 포함된 행만 찾도록 로직 변경 (AND 조건)
        keywords = query.lower().split()
        mask = raw_sorted.apply(
            lambda r: all(keyword in " ".join(r.astype(str)).lower() for keyword in keywords),
            axis=1
        )
        view = raw_sorted.loc[mask]
    else:
        view = raw_sorted.head(100) # [개선] 초기 로딩 시 전체가 아닌 상위 100개만 표시하여 속도 개선

    # [개선] 검색 결과 수를 표시하여 사용자 편의성 증대
    st.info(f"총 **{len(view)}** 건의 결과가 검색되었습니다.")

    cols1 = ["자재번호", "형번", "CB", "박막명", "재종", "코팅그룹", "합금", "가용설비", "관리규격", "RUN TIME(분)", "전처리", "후처리",
             "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

    gb1 = GridOptionsBuilder.from_dataframe(view[cols1])
    # [개선] 모든 컬럼에 공통 옵션 (정렬, 필터, 리사이즈) 기본 적용
    gb1.configure_default_column(
        resizable=True, filterable=True, sortable=True, editable=False,
    )
    # [개선] 수동 너비 계산은 그대로 유지하여 초기 뷰 최적화
    for col, w in calc_widths(view, cols1).items():
        gb1.configure_column(col, width=w)
    gb1.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    # [개선] 그리드 높이 동적 조정 및 테마 적용
    grid_height = min(550, (len(view) + 1) * 30 + 45)
    AgGrid(
        view[cols1].astype(str),
        gridOptions=gb1.build(),
        height=grid_height,
        fit_columns_on_grid_load=False,
        theme='streamlit', # 'balham', 'alpine' 등 다른 테마도 가능
        allow_unsafe_jscode=True, # 테마 적용 등 일부 기능에 필요할 수 있음
    )


# ─ TAB 2: 상세 조건 검색 ──────────────────────────────────
with tab2:
    # [개선] 필터 영역을 컨테이너로 묶고 레이아웃 조정
    with st.container(border=True):
        st.subheader("재종 · 코팅그룹 상세 검색")
        key2 = st.text_input("검색어 입력", placeholder="예: (대문자) CX0824, PVD22 ...", key="keyword_search")
        c1, c2 = st.columns(2)
        with c1:
            alloy_pick = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()), key="alloy_picker")
        with c2:
            # 합금 선택에 따라 재종 목록 동적 변경
            filtered_grades = ref_df if alloy_pick == "전체" else ref_df[ref_df["합금"] == alloy_pick]
            grade_pick = st.selectbox("코팅 재종 선택", ["전체"] + sorted(filtered_grades["재종"].unique()), key="grade_picker")

    # 필터링 로직
    filt = ref_df.copy()
    if alloy_pick != "전체": filt = filt[filt["합금"] == alloy_pick]
    if grade_pick != "전체": filt = filt[filt["재종"] == grade_pick]
    if key2:
        keywords2 = key2.lower().split()
        mask2 = filt.apply(
            lambda r: all(k in " ".join(r.astype(str)).lower() for k in keywords2),
            axis=1
        )
        filt = filt[mask2]

    filt = filt.sort_values(["박막명", "코팅그룹"])

    st.info(f"총 **{len(filt)}** 건의 결과가 검색되었습니다.")

    cols2 = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
             "색상", "관리규격", "가용설비", "작업시간", "합금", "공정특이사항", "인선처리"]

    gb2 = GridOptionsBuilder.from_dataframe(filt[cols2])
    gb2.configure_default_column(resizable=True, filterable=True, sortable=True, editable=False)
    for col, w in calc_widths(filt, cols2).items():
        gb2.configure_column(col, width=w)
    gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)
    
    grid_height_2 = min(550, (len(filt) + 1) * 30 + 45)
    AgGrid(
        filt[cols2].astype(str),
        gridOptions=gb2.build(),
        height=grid_height_2,
        fit_columns_on_grid_load=False,
        theme='streamlit',
        allow_unsafe_jscode=True,
    )

# ── 3. 푸터 ────────────────────────────────────────────────
st.divider()
st.caption("ⓒ 2025 Korloy DX. All rights reserved. (ver 2.0)")





# # PVD Search App – login + auto column width (char-based)
# import streamlit as st
# st.set_page_config(page_title="PVD Search", layout="wide", initial_sidebar_state="collapsed")

# import pandas as pd
# from st_aggrid import AgGrid, GridOptionsBuilder

# # ── 0. 로그인 ───────────────────────────────────────────
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

# # ── 1. 데이터 로드 ──────────────────────────────────────
# DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"
# @st.cache_data
# def load_data():
#     raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl")
#     ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl")
#     return raw.fillna(""), ref.fillna("")
# raw_df, ref_df = load_data()

# # ── 유틸 : 폭 계산 ──────────────────────────────────────
# def calc_widths(df: pd.DataFrame, cols, px_per_char=10, margin=30, min_px=120, max_px=600):
#     out = {}
#     for c in cols:
#         max_len = max(df[c].astype(str).str.len().max(), len(c))
#         out[c] = int(min(max_len * px_per_char + margin, max_px))
#         if out[c] < min_px:
#             out[c] = min_px
#     return out

# # ── 2. UI 탭 ────────────────────────────────────────────
# tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# # ─ TAB 1 ───────────────────────────────────────────────
# with tab1:
#     st.subheader("자재번호·형번·재종 전역 검색")
#     query = st.text_input("검색어 입력", placeholder="예: 1-02-, APKT1604, PC6510 ...")

#     raw_sorted = raw_df.sort_values(["코팅그룹", "자재번호"])
#     if query:
#         mask = raw_sorted.apply(lambda r: query.lower() in " ".join(r.astype(str)).lower(), axis=1)
#         view = raw_sorted.loc[mask]
#     else:
#         view = raw_sorted


#     cols1 = ["자재번호", "형번", "CB", "박막명", "재종", "코팅그룹", "합금", "가용설비", "관리규격", "RUN TIME(분)", "전처리", "후처리",
#              "핀", "스프링 종류", "스프링 개수", "간격", "줄", "IS 개수(개/줄)"]

#     gb1 = GridOptionsBuilder.from_dataframe(view[cols1])
#     for col, w in calc_widths(view, cols1).items():
#         gb1.configure_column(col, width=w)
#     gb1.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

#     AgGrid(
#         view[cols1].astype(str),
#         gridOptions=gb1.build(),
#         height=550,
#         fit_columns_on_grid_load=False
#     )

# # ─ TAB 2 ───────────────────────────────────────────────
# with tab2:
#     st.subheader("재종·코팅그룹 상세 검색")
#     c1, c2 = st.columns(2)
#     with c1:
#         alloy_pick = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()))
#     with c2:
#         tmp = ref_df if alloy_pick == "전체" else ref_df[ref_df["합금"] == alloy_pick]
#         grade_pick = st.selectbox("재종 선택", ["전체"] + sorted(tmp["재종"].unique()))

#     key2 = st.text_input("검색어 입력", placeholder="CX0824, TiAlN ...")

#     filt = ref_df.copy()
#     if alloy_pick != "전체": filt = filt[filt["합금"] == alloy_pick]
#     if grade_pick != "전체": filt = filt[filt["재종"] == grade_pick]
#     if key2: filt = filt[filt.apply(lambda r: key2.lower() in " ".join(r.astype(str)).lower(), axis=1)]

#     filt = filt.sort_values(["박막명", "코팅그룹"])

#     cols2 = ["재종", "코팅그룹", "재종내역", "코팅재종그룹 내역", "박막명",
#              "색상", "관리규격", "가용설비", "작업시간", "합금",
#              "공정특이사항", "인선처리"]

#     gb2 = GridOptionsBuilder.from_dataframe(filt[cols2])
#     for col, w in calc_widths(filt, cols2).items():
#         gb2.configure_column(col, width=w)
#     gb2.configure_pagination(paginationAutoPageSize=False, paginationPageSize=20)

#     AgGrid(
#         filt[cols2].astype(str),
#         gridOptions=gb2.build(),
#         height=550,
#         fit_columns_on_grid_load=False
#     )

# # ─ 푸터 ────────────────────────────────────────────────
# st.caption("ⓒ made by. 연삭코팅기술팀 홍재민 선임 · 2025 Korloy DX")
