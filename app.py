# ====================== app.py  ======================
import streamlit as st

# ────────────────── 0. 페이지 설정 (맨 첫줄 必) ──────────────────
st.set_page_config(
    page_title="PVD Search",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ────────────────── 1. 라이브러리 import ──────────────────
import pandas as pd
from streamlit_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

DATA_PATH = "data/___PVD 공정 데이터 APPS_1.xlsx"

# ────────────────── 2. 데이터 로드 (캐싱) ──────────────────
@st.cache_data(show_spinner="엑셀 불러오는 중...")
def load_data():
    raw = pd.read_excel(DATA_PATH, sheet_name="raw", engine="openpyxl").fillna("")
    ref = pd.read_excel(DATA_PATH, sheet_name="참조표2", engine="openpyxl").fillna("")
    return raw, ref

raw_df, ref_df = load_data()

# ────────────────── 3. 탭 레이아웃 ──────────────────
tab1, tab2 = st.tabs(["🔍 자재번호 검색", "🔍 재종 검색"])

# ═════════════════════ TAB 1 ═════════════════════
with tab1:
    st.subheader("자재번호 · 형번 · 재종 전역 검색")

    # 3-1. 검색어 입력
    query = st.text_input(
        "검색어 입력 (자재번호·형번·재종 등 아무거나)", placeholder="예: 1-02-, APKT1604, PC6510 ..."
    )

    # 3-2. 정렬·그룹화 요구조건
    view = (
        raw_df.sort_values(["코팅그룹", "자재번호"])
        [["자재번호", "형번", "재종", "코팅그룹"]]
        .copy()
    )

    # 3-3. 전역 문자열 필터
    if query:
        q = query.lower()
        mask = raw_df.apply(lambda r: q in " ".join(r.astype(str)).lower(), axis=1)
        view = raw_df.loc[mask, ["자재번호", "형번", "재종", "코팅그룹"]].copy()
        view = view.sort_values(["코팅그룹", "자재번호"])

    # 3-4. Ag-Grid 옵션
    gb = GridOptionsBuilder.from_dataframe(view)
    gb.configure_pagination(paginationPageSize=15)
    gb.configure_selection("single")
    # 그룹화(코팅그룹) 카드/덱 보기
    gb.configure_grid_options(
        groupDisplayType="groupRows",
        rowGroupPanelShow="never",
        columnDefs=[
            {"field": "코팅그룹", "rowGroup": True, "hide": True},
            {"field": "자재번호"},
            {"field": "형번"},
            {"field": "재종"},
        ],
    )
    grid = AgGrid(
        view,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        height=450,
    )

    # 3-5. 선택 행 상세
    sel_rows = grid["selected_rows"]
    if len(sel_rows) > 0:
        key = sel_rows[0]["자재번호"]
        detail_cols = [
            "자재번호",
            "형번",
            "재종",
            "전처리",
            "후처리",
            "핀",
            "스프링 종류",
            "스프링 개수",
            "간격",
            "줄",
        ]
        st.markdown("### 📄 상세 정보")
        st.dataframe(
            raw_df[raw_df["자재번호"] == key][detail_cols].T,
            use_container_width=True,
        )

# ═════════════════════ TAB 2 ═════════════════════
with tab2:
    st.subheader("재종 · 코팅그룹 상세 검색")

    # 4-1. 드롭다운 필터
    col1, col2 = st.columns(2)
    with col1:
        alloy_pick = st.selectbox("합금 선택", ["전체"] + sorted(ref_df["합금"].unique()))
    with col2:
        temp = ref_df if alloy_pick == "전체" else ref_df[ref_df["합금"] == alloy_pick]
        grade_pick = st.selectbox("재종 선택", ["전체"] + sorted(temp["재종"].unique()))

    # 4-2. 검색어 필터
    key2 = st.text_input("검색어 입력", placeholder="CX0824, TiAlN ...")

    filt = ref_df.copy()
    if alloy_pick != "전체":
        filt = filt[filt["합금"] == alloy_pick]
    if grade_pick != "전체":
        filt = filt[filt["재종"] == grade_pick]
    if key2:
        q2 = key2.lower()
        filt = filt[filt.apply(lambda r: q2 in " ".join(r.astype(str)).lower(), axis=1)]

    # 4-3. 정렬·그룹화
    view2 = (
        filt.sort_values(["박막명", "코팅그룹"])
        [["재종", "코팅그룹", "재종내역", "박막명"]]
        .copy()
    )

    gb2 = GridOptionsBuilder.from_dataframe(view2)
    gb2.configure_selection("single")
    gb2.configure_pagination(paginationPageSize=15)
    gb2.configure_grid_options(
        groupDisplayType="groupRows",
        rowGroupPanelShow="never",
        columnDefs=[
            {"field": "박막명", "rowGroup": True, "hide": True},
            {"field": "재종"},
            {"field": "코팅그룹"},
            {"field": "재종내역"},
        ],
    )
    grid2 = AgGrid(
        view2,
        gridOptions=gb2.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        height=450,
    )

    # 4-4. 상세 카드
    sel2 = grid2["selected_rows"]
    if len(sel2) > 0:
        sel_grade = sel2[0]["재종"]
        detail_cols2 = [
            "재종",
            "코팅그룹",
            "재종내역",
            "코팅재종그룹 내역",
            "박막명",
            "색상",
            "관리규격",
            "가용설비",
            "작업시간",
            "합금",
            "공정특이사항",
            "인선처리",
        ]
        st.markdown("### 📄 상세 정보")
        st.dataframe(
            ref_df[ref_df["재종"] == sel_grade][detail_cols2].T,
            use_container_width=True,
        )

# ────────────────── 5. 푸터 ──────────────────
st.caption("ⓒ 2025 Korloy DX · Powered by Streamlit Community Cloud 무료 플랜")
# ====================== /app.py ======================
