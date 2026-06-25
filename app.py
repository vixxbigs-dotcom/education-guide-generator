import streamlit as st

# 1. 페이지 기본 설정 및 스타일 (깔끔하고 세련된 사내 툴 느낌)
st.set_page_config(page_title="교육 안내문 자동 생성기", page_icon="✉️", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #0F172A; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #64748B; margin-bottom: 25px; }
    div.stButton > button:first-child { background-color: #0F172A; color: white; border-radius: 4px; width: 100%; height: 45px; font-weight: bold; border: none; }
    div.stButton > button:hover { background-color: #334155; color: white; }
    /* 복사 버튼 전용 스타일 */
    .copy-btn {
        background-color: #475569;
        color: white;
        border: none;
        padding: 12px 20px;
        font-size: 15px;
        font-weight: bold;
        border-radius: 4px;
        cursor: pointer;
        width: 100%;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .copy-btn:hover { background-color: #1E293B; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">✉️ 교육 안내문 자동 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">필수 정보를 입력하면 아웃룩 메일용 깨지지 않는 표준 HTML 템플릿을 생성합니다.</div>', unsafe_allow_html=True)

# 초기화 버튼 기능 구현을 위한 세션 상태 관리
if "form_reset" not in st.session_state:
    st.session_state.form_reset = False

# 2. 좌측: 입력 폼 영역 / 우측: 결과 출력 및 미리보기 영역 분할
col_input, col_output = st.columns([1, 1])

with col_input:
    st.subheader("📝 정보 입력")
    
    # [기초 정보]
    company_name = st.text_input("회사 이름", value="" if st.session_state.form_reset else "우리")
    course_name = st.text_input("교육 과정명", value="" if st.session_state.form_reset else "경력입문 교육")
    
    # [일정 및 시간 정보]
    st.markdown("---")
    st.markdown("**⏰ 일정 및 시간 세팅**")
    date_range = st.text_input("교육 일정 (예: 10/12(월)~10/13(화))", value="" if st.session_state.form_reset else "10/12(월)~10/13(화)")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        day1_time = st.text_input("1일차 시작 시간", value="" if st.session_state.form_reset else "10")
    with col_t2:
        day2_time = st.text_input("2일차 시작 시간", value="" if st.session_state.form_reset else "9")
        
    # [장소 및 지도 정보]
    st.markdown("---")
    st.markdown("**📍 장소 세팅**")
    place_name = st.text_input("교육 장소명 및 주소", value="" if st.session_state.form_reset else "그룹 연수원 대강당 (서울시 중구 ...)")
    map_image_url = st.text_input("지도 이미지 URL (웹 링크 형태)", value="" if st.session_state.form_reset else "https://images.unsplash.com/photo-1524661135339-9140b0078723?auto=format&fit=crop&w=600&q=80")

    # [동적 입력 1: 커리큘럼 표 표형식 생성]
    st.markdown("---")
    st.markdown("**📅 커리큘럼 세팅 (표 형식)**")
    
    if "curriculum" not in st.session_state or st.session_state.form_reset:
        st.session_state.curriculum = [
            {"day": "1일차", "time": "10:00 ~ 12:00", "subject": "경력사원 마인드셋", "speaker": "홍길동 강사"},
            {"day": "1일차", "time": "13:00 ~ 17:00", "subject": "사내 시스템 및 프로세스 이해", "speaker": "김철수 프로"},
            {"day": "2일차", "time": "09:00 ~ 12:00", "subject": "협업 및 소통 시너지", "speaker": "이영희 파트너"}
        ]
        
    edited_curr = st.data_editor(
        st.session_state.curriculum, 
        num_rows="dynamic", 
        column_config={
            "day": "일차", "time": "시간", "subject": "과정 내용", "speaker": "강사/담당자"
        },
        width="stretch",
        key="curr_editor"
    )

    # [동적 입력 2: 관련 문의 담당자 유동적 조절]
    st.markdown("---")
    st.markdown("**📞 관련 문의 담당자 세팅**")
    
    if "contacts" not in st.session_state or st.session_state.form_reset:
        st.session_state.contacts = [
            {"role": "인재개발팀 김화평 프로", "phone": "010-1234-5678"},
            {"role": "인재개발팀 이가은 프로", "phone": "010-9876-5432"}
        ]
        
    edited_contacts = st.data_editor(
        st.session_state.contacts,
        num_rows="dynamic",
        column_config={"role": "소속 + 이름 + 직급", "phone": "연락처"},
        width="stretch",
        key="contacts_editor"
    )
    
    # [안내 사항 텍스트 박스]
    st.markdown("---")
    st.markdown("**ℹ️ 안내 사항**")
    info_text = st.text_area("안내 사항 문구", value="" if st.session_state.form_reset else "- 숙소는 2인 1실로 제공될 예정이며 생수, 비누, 샴푸, 헤어드라이기 등이 구비되어 있습니다.\n- 1일차 석식은 연수원 외부에서 진행될 예정이오니 참고 부탁드립니다.")

    # 초기화 플래그 리셋 처리
    if st.session_state.form_reset:
        st.session_state.form_reset = False
        st.clear_caches()
        st.rerun()

# 3. 레퍼런스 스타일을 적용한 아웃룩 호환 100% Inline CSS HTML 빌드업
table_rows_html = ""
for row in edited_curr:
    if row.get("day") or row.get("subject"):
        table_rows_html += f"""
        <tr style="border-bottom: 1px solid #E2E8F0;">
            <td style="padding: 12px 8px; font-size: 13px; color: #64748B; text-align: center;">{row.get('day','')}</td>
            <td style="padding: 12px 8px; font-size: 13px; color: #64748B; text-align: center;">{row.get('time','')}</td>
            <td style="padding: 12px 8px; font-size: 13px; color: #0F172A; font-weight: 500; text-align: left;">{row.get('subject','')}</td>
            <td style="padding: 12px 8px; font-size: 13px; color: #64748B; text-align: center;">{row.get('speaker','')}</td>
        </tr>
        """

contacts_html = ""
for contact in edited_contacts:
    if contact.get("role"):
        contacts_html += f"""
        <p style="margin: 4px 0; font-size: 13px; color: #475569;">
            <span style="color: #0F172A; font-weight: bold; margin-right: 8px;">· {contact.get('role','')}</span> {contact.get('phone','')}
        </p>
        """

info_html_lines = "".join([f"<p style='margin: 6px 0; font-size: 13px; color: #334155; padding-left: 10px; text-indent: -10px;'>{line}</p>" for line in info_text.split('\n') if line])

# 대기업 양식 특유의 미니멀 정갈한 HTML structure
final_mail_html = f"""
<div id="mail-content" style="max-width: 620px; margin: 0 auto; font-family: 'Malgun Gothic', '맑은 고딕', sans-serif; line-height: 1.6; color: #0F172A; padding: 10px; background-color: #FFFFFF;">
    
    <div style="margin-bottom: 30px;">
        <p style="margin: 0 0 4px 0; font-size: 13px; color: #64748B; letter-spacing: 0.5px; font-weight: bold;">{company_name}그룹 교육공지</p>
        <h2 style="margin: 0 0 12px 0; font-size: 24px; color: #0F172A; font-weight: bold; letter-spacing: -0.5px;">{company_name}그룹 {course_name} 입과 안내</h2>
        <p style="margin: 0; font-size: 14px; color: #334155;">
            강의에 입과하신 여러분 환영합니다! 해당 강의는 대면으로 진행되며,<br>
            하기 내용을 사전에 꼭 확인하신 후 입과해주시길 부탁드립니다.
        </p>
    </div>

    <div style="border-top: 1px solid #0F172A; border-bottom: 1px solid #0F172A; padding: 12px 5px; margin-bottom: 35px;">
        <p style="margin: 0; font-size: 13px; color: #0F172A; font-weight: bold;">
            ※ 교육 시작시간: <span style="color: #0F172A; text-decoration: underline;">1일차 {day1_time}시 / 2일차 {day2_time}시</span> (일정을 반드시 확인해 주세요)
        </p>
    </div>

    <div style="margin-bottom: 35px;">
        <div style="width: 100%; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px; height: 12px; text-align: left;">
            <span style="background-color: #FFFFFF; padding-right: 10px; font-size: 14px; color: #0F172A; font-weight: bold; line-height: 24px;">교육 개요</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; margin-left: 4px;">
            <tr>
                <td style="width: 20%; padding: 5px 0; font-size: 13px; color: #64748B; font-weight: bold;">· 교육명</td>
                <td style="padding: 5px 0; font-size: 13px; color: #0F172A; font-weight: bold;">{company_name}그룹 {course_name}</td>
            </tr>
            <tr>
                <td style="padding: 5px 0; font-size: 13px; color: #64748B; font-weight: bold;">· 교육 일정</td>
                <td style="padding: 5px 0; font-size: 13px; color: #0F172A;">{date_range} <span style="font-size: 11px; color: #64748B;">(집합교육 기준)</span></td>
            </tr>
            <tr>
                <td style="padding: 5px 0; font-size: 13px; color: #64748B; font-weight: bold;">· 교육 시간</td>
                <td style="padding: 5px 0; font-size: 13px; color: #0F172A;">하단 상세 커리큘럼 참조 <span style="font-size: 11px; color: #475569; font-weight: 500;">(강의 시작 10분 전까지 입실 바랍니다.)</span></td>
            </tr>
        </table>
    </div>

    <div style="margin-bottom: 35px;">
        <div style="width: 100%; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px; height: 12px; text-align: left;">
            <span style="background-color: #FFFFFF; padding-right: 10px; font-size: 14px; color: #0F172A; font-weight: bold; line-height: 24px;">상세 커리큘럼</span>
        </div>
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
            <thead>
                <tr style="border-bottom: 2px solid #0F172A;">
                    <th style="padding: 10px 8px; font-size: 13px; color: #0F172A; font-weight: bold; text-align: center; width: 12%;">일차</th>
                    <th style="padding: 10px 8px; font-size: 13px; color: #0F172A; font-weight: bold; text-align: center; width: 28%;">시간</th>
                    <th style="padding: 10px 8px; font-size: 13px; color: #0F172A; font-weight: bold; text-align: left;">과정 내용</th>
                    <th style="padding: 10px 8px; font-size: 13px; color: #0F172A; font-weight: bold; text-align: center; width: 20%;">비고</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>

    <div style="margin-bottom: 35px;">
        <div style="width: 100%; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px; height: 12px; text-align: left;">
            <span style="background-color: #FFFFFF; padding-right: 10px; font-size: 14px; color: #0F172A; font-weight: bold; line-height: 24px;">교육 장소</span>
        </div>
        <p style="margin: 0 0 10px 4px; font-size: 13px; color: #0F172A; font-weight: 500;">{place_name}</p>
        {"<div style='margin: 10px 0 0 4px;'><img src='" + map_image_url + "' alt='지도' style='max-width: 100%; height: auto; border: 1px solid #E2E8F0;' /></div>" if map_image_url else ""}
    </div>

    <div style="margin-bottom: 35px; border: 1px solid #E2E8F0; padding: 18px; background-color: #F8FAFC;">
        <h4 style="margin: 0 0 10px 0; font-size: 13px; color: #0F172A; font-weight: bold;">💡 주요 안내 사항</h4>
        {info_html_lines}
    </div>

    <div style="border-top: 1px solid #E2E8F0; padding-top: 20px; margin-bottom: 10px;">
        <h4 style="margin: 0 0 10px 0; font-size: 13px; color: #0F172A; font-weight: bold;">📞 관련 문의</h4>
        <div style="padding-left: 4px;">
            {contacts_html}
        </div>
    </div>
</div>
"""

# 4. 우측: 결과 출력부 화면 구성
with col_output:
    st.subheader("🖥️ 출력부 (미리보기 및 HTML 복사)")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        js_copy_script = f"""
        <button class="copy-btn" onclick="copyMailContent()">📋 원클릭 고급 서식 복사하기</button>
        
        <script>
        function copyMailContent() {{
            var container = document.parent.document.getElementById("mail-content");
            if (!container) {{
                container = document.getElementById("mail-content");
            }}
            
            if (container) {{
                var range = document.createRange();
                range.selectNodeContents(container);
                var selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                
                try {{
                    document.execCommand('copy');
                    alert('🎉 고급형 메일 서식이 클립보드에 복사되었습니다! 아웃룩 본문에 Ctrl+V 하세요.');
                }} catch (err) {{
                    alert('복사에 실패했습니다. 미리보기 영역을 직접 드래그 복사해 주세요.');
                }}
                selection.removeAllRanges();
            }} else {{
                alert('복사할 대상을 찾지 못했습니다. 우측 화면을 직접 드래그해 주세요.');
            }}
        }}
        </script>
        """
        st.html(f"<div style='height: 60px;'>{js_copy_script}</div>")
        
    with col_btn2:
        if st.button("🔄 입력 내용 전체 초기화"):
            st.session_state.form_reset = True
            st.rerun()
            
    tab_preview, tab_code = st.tabs(["👀 아웃룩 발송 화면 미리보기", "💻 Raw HTML 소스코드"])
    
    with tab_preview:
        st.markdown("<p style='font-size:12px; color:#475569;'>※ 복사 버튼을 활용하시거나, 아래 렌더링 영역을 전체 마우스 드래그하여 아웃룩 본문에 붙여넣으셔도 서식이 깔끔하게 복사됩니다.</p>", unsafe_allow_html=True)
        st.html(final_mail_html)
        
    with tab_code:
        st.text_area("생성된 HTML 소스코드 (텍스트 소스 보관용)", value=final_mail_html, height=500)