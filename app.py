import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="3M 입고 일정 캘린더 관리 시스템", layout="wide")

st.title("📦 3M 입고 일정 캘린더 자동 생성기")
st.markdown("사무실 직원 공유용 실무 대시보드 | 취소 건 빨간색 강조 및 오늘 기준 정렬")

# 세션 스테이트 초기화
if 'model_mapping' not in st.session_state:
    st.session_state.model_mapping = {}

if 'expand_days' not in st.session_state:
    st.session_state.expand_days = 0 

if 'show_past' not in st.session_state:
    st.session_state.show_past = False

# 사이드바 설정
st.sidebar.header("⚙️ 설정 및 공유 안내")
st.sidebar.info(
    "💡 **사무실 직원 공유 방법**\n"
    "1. Streamlit Cloud에 배포하면 사내 전용 웹 링크(URL)가 생성됩니다.\n"
    "2. 직원들은 링크로 접속해 최신 엑셀을 업로드하고 실시간으로 일정을 확인할 수 있습니다."
)

uploaded_file = st.sidebar.file_uploader("📁 원본 주문 엑셀 파일 업로드 (.xlsx)", type=["xlsx"])

# 대한민국 법정 공휴일 및 명칭 정의 (2026년 기준)
HOLIDAYS_2026_INFO = {
    "2026-01-01": "신정",
    "2026-02-16": "설날 연휴",
    "2026-02-17": "설날",
    "2026-02-18": "설날 연휴",
    "2026-03-01": "삼일절",
    "2026-03-02": "대체공휴일",
    "2026-05-05": "어린이날",
    "2026-05-24": "부처님오신날",
    "2026-05-25": "대체공휴일",
    "2026-06-06": "현충일",
    "2026-08-15": "광복절",
    "2026-08-17": "대체공휴일",
    "2026-09-24": "추석 연휴",
    "2026-09-25": "추석",
    "2026-09-26": "추석 연휴",
    "2026-10-03": "개천절",
    "2026-10-05": "대체공휴일",
    "2026-10-09": "한글날",
    "2026-12-25": "크리스마스"
}

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    def extract_short_model(desc):
        if not isinstance(desc, str):
            return "기타"
        if desc in st.session_state.model_mapping:
            return st.session_state.model_mapping[desc]
        parts = desc.split(',')
        main_part = parts[0].replace("3M™", "").replace("3M", "").strip()
        return main_part

    df['단축모델명'] = df['제품 설명'].apply(extract_short_model)
    
    def determine_target_date(row):
        h_req = pd.to_datetime(row.get('헤더 납품요청일'), errors='coerce')
        latest_del = pd.to_datetime(row.get('최신 예상 배송일'), errors='coerce')
        
        if pd.isna(h_req) and pd.isna(latest_del):
            return pd.NaT
        if pd.isna(h_req):
            return latest_del
        if pd.isna(latest_del):
            return h_req
            
        if latest_del > h_req:
            return latest_del
        else:
            return h_req

    df['기준일자'] = df.apply(determine_target_date, axis=1)
    
    df_filtered = df[df['실제 출고일'].isna()].copy()
    df_filtered = df_filtered.dropna(subset=['기준일자'])
    df_filtered['기준일자_str'] = df_filtered['기준일자'].dt.strftime('%Y-%m-%d')

    tab1, tab2, tab3 = st.tabs(["📅 입고 캘린더 메인", "🏷️ 모델명 매핑 관리", "📋 파싱된 원본 데이터"])
    
    with tab1:
        col_left, col_right = st.columns([7, 3])
        
        with col_left:
            st.subheader("🗓️ 입고 일정 캘린더 (오늘 기준 정렬)")
            
            base_date = datetime(2026, 11, 18) # 오늘 기준일자
            
            c_b1, c_b2, c_b3 = st.columns([2, 2, 2])
            with c_b1:
                past_btn_label = "📂 과거 이력 숨기기" if st.session_state.show_past else "📁 과거 이력 펼쳐보기 (최근 7일)"
                if st.button(past_btn_label):
                    st.session_state.show_past = not st.session_state.show_past
                    st.rerun()
            with c_b2:
                if st.button("➕ 이후 일정 10일 더 펼치기"):
                    st.session_state.expand_days += 1
                    st.rerun()
            with c_b3:
                if st.session_state.expand_days > 0 or st.session_state.show_past:
                    if st.button("🔄 기본 보기로 초기화"):
                        st.session_state.expand_days = 0
                        st.session_state.show_past = False
                        st.rerun()

            weekdays_kr = {'Mon': '월', 'Tue': '화', 'Wed': '수', 'Thu': '목', 'Fri': '금', 'Sat': '토', 'Sun': '일'}
            
            past_date_list = []
            if st.session_state.show_past:
                past_date_list = [base_date - timedelta(days=i) for i in range(7, 0, -1)]
            
            future_days_range = 10 + (st.session_state.expand_days * 10)
            future_date_list = [base_date + timedelta(days=i) for i in range(future_days_range)]
            
            display_date_list = past_date_list + future_date_list

            st.markdown("---")
            
            def render_date_card(d):
                d_str = d.strftime('%Y-%m-%d')
                w_eng = d.strftime('%a')
                w_kr = weekdays_kr.get(w_eng, w_eng)
                
                is_sat = (w_eng == 'Sat')
                is_sun = (w_eng == 'Sun')
                holiday_name = HOLIDAYS_2026_INFO.get(d_str, None)
                
                date_title = f"**{d.strftime('%m/%d')} ({w_kr})**"
                if d_str == base_date.strftime('%Y-%m-%d'):
                    date_title = f"⭐ **{d.strftime('%m/%d')} ({w_kr}) [오늘]**"
                    
                if is_sun or holiday_name:
                    h_text = f" ({holiday_name})" if holiday_name else ""
                    date_title = f":red[**{d.strftime('%m/%d')} ({w_kr}){h_text}**]"
                    if d_str == base_date.strftime('%Y-%m-%d'):
                        date_title = f":red[⭐ **{d.strftime('%m/%d')} ({w_kr}) [오늘]{h_text}**]"
                elif is_sat:
                    date_title = f":blue[**{d.strftime('%m/%d')} ({w_kr})**]"
                    if d_str == base_date.strftime('%Y-%m-%d'):
                        date_title = f":blue[⭐ **{d.strftime('%m/%d')} ({w_kr}) [오늘]**]"
                
                day_items = df_filtered[df_filtered['기준일자_str'] == d_str]
                
                with st.container(border=True):
                    col_d1, col_d2, col_d3 = st.columns([2, 6, 1])
                    with col_d1:
                        st.markdown(date_title)
                    with col_d2:
                        if not day_items.empty:
                            for _, row in day_items.iterrows():
                                m_name = row['단축모델명']
                                qty = row['출고 예정 수량 (PGI 전)']
                                uom = row['단위 (UOM)']
                                
                                # 취소 상태 판별 (라인 상태 또는 전체 주문 상태에 '취소' 단어가 포함된 경우)
                                line_status = str(row.get('라인 상태', ''))
                                total_status = str(row.get('전체 주문 상태', ''))
                                is_cancelled = ('취소' in line_status) or ('취소' in total_status)
                                
                                if is_cancelled:
                                    st.markdown(f":red[• **[취소됨]** {m_name} / {qty} {uom}]")
                                else:
                                    st.markdown(f"• {m_name} / {qty} {uom}")
                        else:
                            st.markdown("-")
                    with col_d3:
                        st.markdown(f"**{len(day_items)}건**")

            if st.session_state.show_past and past_date_list:
                st.markdown("### 📂 [과거 이력 내역]")
                for d in past_date_list:
                    render_date_card(d)
                st.markdown("---")
                st.markdown("### 📅 [오늘 및 향후 입고 일정]")

            for d in future_date_list:
                render_date_card(d)
            
            st.markdown("---")
            st.subheader("📌 범위 외 잔여 및 익월 입고 예정 일정")
            max_future_date = future_date_list[-1]
            future_items = df_filtered[df_filtered['기준일자'] > max_future_date]
            if not future_items.empty:
                summary_future = future_items[['기준일자_str', '단축모델명', '출고 예정 수량 (PGI 전)', '단위 (UOM)', '납품처 이름']].copy()
                summary_future.columns = ['예정일자', '단축모델명', '수량', '단위', '납품처']
                st.dataframe(summary_future, use_container_width=True)
            else:
                st.info("현재 표시된 기간 이후의 추가 입고 예정 건이 없습니다.")

            st.markdown("---")
            st.download_button(
                label="📥 현재 정리된 캘린더/일정표 엑셀로 다운로드",
                data=uploaded_file.getvalue(),
                file_name="입고일정표_정리완료.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_right:
            st.markdown("### 🔍 제품별 입고 일정 검색")
            st.markdown("<p style='font-size: 13px; color: #666;'>특정 제품의 예정된 입고 일정을 전부 조회합니다. (지난 일정 제외)</p>", unsafe_allow_html=True)
            
            unique_models = sorted(df_filtered['단축모델명'].dropna().unique().tolist())
            selected_model = st.selectbox("조회할 제품 선택", options=["-- 전체 제품 선택 --"] + unique_models)
            
            if selected_model != "-- 전체 제품 선택 --":
                today_str = base_date.strftime('%Y-%m-%d')
                product_schedules = df_filtered[(df_filtered['단축모델명'] == selected_model) & (df_filtered['기준일자_str'] >= today_str)]
                product_schedules = product_schedules.sort_values(by='기준일자')
                
                st.markdown(f"**📦 [{selected_model}] 입고 예정 내역 ({len(product_schedules)}건)**")
                
                if not product_schedules.empty:
                    for _, prow in product_schedules.iterrows():
                        p_date = prow['기준일자_str']
                        p_qty = prow['출고 예정 수량 (PGI 전)']
                        p_uom = prow['단위 (UOM)']
                        p_client = prow['납품처 이름']
                        
                        line_status = str(prow.get('라인 상태', ''))
                        total_status = str(prow.get('전체 주문 상태', ''))
                        is_cancelled = ('취소' in line_status) or ('취소' in total_status)
                        
                        if is_cancelled:
                            st.info(f"📅 **{p_date}**\n\n- 수량: :red[**[취소됨] {p_qty} {p_uom}**]\n- 납품처: {p_client}")
                        else:
                            st.info(f"📅 **{p_date}**\n\n- 수량: **{p_qty} {p_uom}**\n- 납품처: {p_client}")
                else:
                    st.warning("해당 제품의 향후 입고 예정 일정이 없습니다.")
            else:
                st.info("위에서 제품을 선택하시면 예정된 모든 입고 일정이 이 곳에 표시됩니다.")

    with tab2:
        st.subheader("🏷️ 단축 모델명 매핑 관리 (직접 수정)")
        unique_descs = df['제품 설명'].dropna().unique()
        mapping_data = []
        for desc in unique_descs:
            current_short = st.session_state.model_mapping.get(desc, extract_short_model(desc))
            mapping_data.append({"제품 설명": desc, "지정된 단축 모델명": current_short})
            
        map_df = pd.DataFrame(mapping_data)
        edited_df = st.data_editor(map_df, key="model_editor", num_rows="dynamic", use_container_width=True)
        
        if st.button("💾 매핑 변경사항 저장"):
            new_mapping = {}
            for _, row in edited_df.iterrows():
                new_mapping[row['제품 설명']] = row['지정된 단축 모델명']
            st.session_state.model_mapping = new_mapping
            st.success("모델명 매핑이 저장되었습니다!")

    with tab3:
        st.subheader("📋 파싱된 전체 주문 데이터")
        st.dataframe(df_filtered[['고객 이름', '납품처 이름', '3M 주문 번호', '단축모델명', '출고 예정 수량 (PGI 전)', '단위 (UOM)', '헤더 납품요청일', '최신 예상 배송일', '기준일자_str', '라인 상태']], use_container_width=True)

else:
    st.warning("⚠️ 좌측 사이드바에서 원본 엑셀 파일을 업로드해 주세요.")