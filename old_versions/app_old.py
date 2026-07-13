import base64
import html
import io
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="교육 안내문 자동 생성기", page_icon="✉️", layout="wide")


# -----------------------------
# 기본 입력값 / 초기화 유틸
# -----------------------------
DEFAULT_CURRICULUM = [
    {"day": "1일차", "time": "10:00 ~ 12:00", "subject": "M1. 팀빌딩과 회고", "speaker": ""},
    {"day": "1일차", "time": "13:00 ~ 16:00", "subject": "M2. 이전부터 오늘까지 나", "speaker": ""},
    {"day": "1일차", "time": "16:00 ~ 18:00", "subject": "M3. 내일의 나 (경력 적응성의 관점)", "speaker": ""},
    {"day": "1일차", "time": "18:00 ~ 19:00", "subject": "석식 만찬", "speaker": ""},
    {"day": "2일차", "time": "09:00 ~ 12:00", "subject": "M4. HMS/RESPECT", "speaker": "사내강사"},
    {"day": "2일차", "time": "13:00 ~ 15:00", "subject": "M5. 잡 크래프팅과 일의 의미, 몰입", "speaker": ""},
    {"day": "2일차", "time": "15:00 ~ 17:00", "subject": "M6. 개인의 목표와 조직의 목표 align", "speaker": ""},
]

DEFAULT_CONTACTS = [
    {"role": "현장운영자 최유리 프로", "phone": "010-9522-4395"},
    {"role": "멀티캠퍼스 남은주 프로", "phone": "010-7791-9971"},
    {"role": "한솔그룹 최종범 책임", "phone": "010-5104-9658"},
]

DEFAULT_VALUES = {
    "company_name": "",
    "course_name": "멀티캠퍼스 입문 교육",
    "delivery_mode": "대면",
    "delivery_custom": "",
    "welcome_title": "입과를 환영합니다!",
    "welcome_body_text": "{교육명}\n강의에 입과하신 여러분 환영합니다! 해당 강의는 {운영방식}으로 진행되며,\n하기 내용을 사전에 꼭 확인하신 후 입과해주시길 부탁드립니다.",
    "time_notice_text": "특히, 교육 시작시간은 1일차 {1일차}시, 2일차 {2일차}시이니 일정 확인 부탁드립니다.",
    "main_color_picker": "#0088C9",
    "footer_color_picker": "#00A651",
    "curr_header_text_color_picker": "#FFFFFF",
    "use_custom_footer_color": False,
    "logo_position": "우측 상단",
    "logo_max_height": 52,
    "font_mode": "assets/fonts 폴더",
    "primary_font_select": "Malgun Gothic",
    "primary_font_custom": "Pretendard",
    "date_range": "6/16(월)~6/17(화)",
    "day1_time": "10",
    "day2_time": "9",
    "place_name": "스타필드 수원 타임체임버",
    "info_text": "- 숙소는 2인 1실로 제공될 예정이며 생수, 비누, 샴푸, 헤어드라이기, 냉장고, TV, 전화기, 비데, 유무선인터넷 등이 구비되어 있습니다.\n- 1일차 석식은 연수원 외부에서 진행될 예정이오니 참고 부탁드립니다.",
    "preview_scale_percent": 72,
    "export_file_name": "education_notice_photo_style",
    "captured_map_data_url": "",
    "captured_map_file_path": "",
    "last_map_capture_message": "",
}

WIDGET_KEYS_TO_CLEAR_ON_RESET = [
    "logo_file_uploader",
    "map_file_uploader",
    "curr_editor",
    "contacts_editor",
    "font_folder_select",
]


def init_defaults() -> None:
    for key, value in DEFAULT_VALUES.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if "curriculum" not in st.session_state:
        st.session_state.curriculum = [row.copy() for row in DEFAULT_CURRICULUM]
    if "contacts" not in st.session_state:
        st.session_state.contacts = [row.copy() for row in DEFAULT_CONTACTS]


def reset_all_fields() -> None:
    for key, value in DEFAULT_VALUES.items():
        st.session_state[key] = value
    st.session_state.curriculum = [row.copy() for row in DEFAULT_CURRICULUM]
    st.session_state.contacts = [row.copy() for row in DEFAULT_CONTACTS]
    for key in WIDGET_KEYS_TO_CLEAR_ON_RESET:
        st.session_state.pop(key, None)
    st.session_state.pop("last_captured_map_file", None)
    st.session_state.pop("captured_map_file_path", None)
    st.session_state.pop("last_map_capture_message", None)
    st.cache_data.clear()
    st.cache_resource.clear()



# -----------------------------
# 기본 유틸
# -----------------------------
def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=False)


def esc_attr(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize_bullet(line: str) -> str:
    line = str(line or "").strip()
    if line.startswith("-"):
        return line[1:].strip()
    return line


def to_records(data: object) -> list[dict]:
    """st.data_editor 반환값이 list 또는 DataFrame이어도 dict 리스트로 통일합니다."""
    if data is None:
        return []
    if hasattr(data, "to_dict"):
        try:
            records = data.to_dict("records")
            return [row for row in records if isinstance(row, dict)]
        except TypeError:
            pass
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


def file_to_data_url(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "image/png"
    return f"data:{mime_type};base64,{base64.b64encode(file_bytes).decode('ascii')}"


def get_captures_dir() -> Path:
    return Path(__file__).resolve().parent / "assets" / "captures"


def image_bytes_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    return f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def file_path_to_data_url(file_path: str) -> str:
    path = Path(str(file_path or "")).expanduser()
    if not file_path or not path.exists() or not path.is_file():
        return ""
    suffix = path.suffix.lower()
    mime_type = "image/png"
    if suffix in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif suffix == ".gif":
        mime_type = "image/gif"
    elif suffix == ".webp":
        mime_type = "image/webp"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def capture_naver_map_region(place_query: str, wait_seconds: float = 8.0) -> tuple[bool, str]:
    """
    Playwright headless Chromium으로 네이버 지도 검색 URL을 백그라운드에서 열고,
    1920 x 1080 viewport 기준 좌표 (585, 87)~(1785, 1047)를 잘라 저장합니다.

    v23 변경점:
    - 큰 base64 문자열을 session_state에 직접 저장하지 않고 파일 경로를 저장합니다.
    - Playwright clip 캡처 대신 전체 화면 캡처 후 Pillow로 crop합니다.
      네이버 지도처럼 로딩이 늦거나 canvas/WebGL 렌더링이 있는 화면에서 더 안정적입니다.
    - 캡처 결과 파일을 좌측 입력부에서 바로 썸네일로 확인할 수 있도록 합니다.
    """
    query = str(place_query or "").strip()
    if not query:
        return False, "교육 장소명을 먼저 입력해 주세요."

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return (
            False,
            "지도 자동 캡처에는 Playwright가 필요합니다. 터미널에서 `python -m pip install playwright` 실행 후, "
            "처음 한 번만 `python -m playwright install chromium`을 실행해 주세요.",
        )

    try:
        from PIL import Image, ImageStat
    except Exception:
        return (
            False,
            "지도 이미지를 좌표대로 자르려면 Pillow가 필요합니다. 터미널에서 `python -m pip install pillow`를 실행해 주세요.",
        )

    map_url = f"https://map.naver.com/p/search/{quote(query)}?c=15.00,0,0,0,dh"
    crop_box = (585, 87, 1785, 1047)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--window-size=1920,1080",
                    "--force-device-scale-factor=1",
                    "--hide-scrollbars",
                    "--disable-gpu",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                screen={"width": 1920, "height": 1080},
                device_scale_factor=1,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                ignore_https_errors=True,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()
            page.goto(map_url, wait_until="load", timeout=90000)

            # 네이버 지도는 지도 타일/검색 결과가 늦게 붙는 경우가 많아서 조금 넉넉히 기다립니다.
            try:
                page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            try:
                page.wait_for_selector("canvas, iframe, img, [class*=map], [class*=Map]", timeout=20000)
            except Exception:
                pass
            page.wait_for_timeout(int(max(4.0, float(wait_seconds)) * 1000))

            # 전체 viewport를 먼저 캡처한 뒤 지정 좌표로 crop합니다.
            screenshot_bytes = page.screenshot(type="png", full_page=False, animations="disabled")
            browser.close()

        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        width, height = image.size
        left, top, right, bottom = crop_box
        if width < right or height < bottom:
            return False, f"캡처 화면 크기가 예상보다 작습니다. 현재 캡처 크기: {width}x{height}, 필요 크기: 1785x1047"

        cropped = image.crop(crop_box)

        # 완전 백지/단색에 가까운 캡처인지 간단 점검합니다. 저장은 하되 안내 메시지에 표시합니다.
        stat = ImageStat.Stat(cropped.resize((120, 96)))
        avg_stddev = sum(stat.stddev) / len(stat.stddev)
        quality_note = ""
        if avg_stddev < 3:
            quality_note = " 다만 캡처 이미지가 거의 단색으로 감지됩니다. 네이버 지도 로딩/접근 차단 가능성이 있어 직접 첨부를 확인해 주세요."

        captures_dir = get_captures_dir()
        captures_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"naver_map_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = captures_dir / file_name
        cropped.save(file_path, format="PNG")

        st.session_state.captured_map_file_path = str(file_path)
        st.session_state.captured_map_data_url = ""
        st.session_state.last_captured_map_file = str(file_path)
        return True, f"지도 이미지를 자동 캡처해 미리보기에 적용했습니다. 저장 위치: {file_path}{quality_note}"
    except Exception as exc:
        return False, (
            "지도 자동 캡처에 실패했습니다. `python -m pip install playwright pillow` 및 "
            "`python -m playwright install chromium` 실행 여부를 확인해 주세요. "
            f"상세: {exc}"
        )


def is_valid_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", str(value or "").strip()))


def get_query_param(name: str) -> str:
    try:
        value = st.query_params.get(name, "")
        if isinstance(value, list):
            return str(value[0]) if value else ""
        return str(value or "")
    except Exception:
        try:
            params = st.experimental_get_query_params()
            value = params.get(name, [""])
            return str(value[0]) if value else ""
        except Exception:
            return ""


def css_font_stack(primary_font: str) -> str:
    clean = str(primary_font or "").strip()
    clean = clean.replace("'", "").replace('"', "").replace(";", "").replace("\\", "")
    if not clean:
        clean = "Malgun Gothic"
    return f"'{clean}', 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif"


FONT_EXTENSIONS = (".ttf", ".otf", ".woff", ".woff2")
FONT_MIME_TYPES = {
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}
FONT_FORMATS = {
    ".ttf": "truetype",
    ".otf": "opentype",
    ".woff": "woff",
    ".woff2": "woff2",
}


def get_fonts_dir() -> Path:
    return Path(__file__).resolve().parent / "assets" / "fonts"


@st.cache_data(show_spinner=False)
def list_font_files(fonts_dir_text: str) -> list[str]:
    fonts_dir = Path(fonts_dir_text)
    if not fonts_dir.exists() or not fonts_dir.is_dir():
        return []
    files: list[str] = []
    for ext in FONT_EXTENSIONS:
        files.extend(str(path) for path in fonts_dir.glob(f"*{ext}"))
        files.extend(str(path) for path in fonts_dir.glob(f"*{ext.upper()}"))
    return sorted(set(files), key=lambda x: Path(x).name.lower())


def font_family_from_file(font_path: str) -> str:
    name = Path(font_path).stem.strip()
    return re.sub(r"[^0-9A-Za-z가-힣 _.-]", "", name) or "CustomFont"


def sanitize_file_name(value: str) -> str:
    name = str(value or "").strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("._ ")
    return name or "education_notice_photo_style"


def build_embedded_font_css(font_path: str, font_family: str) -> str:
    path = Path(font_path)
    if not path.exists() or path.suffix.lower() not in FONT_EXTENSIONS:
        return ""
    try:
        font_bytes = path.read_bytes()
    except OSError:
        return ""
    suffix = path.suffix.lower()
    mime = FONT_MIME_TYPES.get(suffix, "font/ttf")
    font_format = FONT_FORMATS.get(suffix, "truetype")
    data_url = f"data:{mime};base64,{base64.b64encode(font_bytes).decode('ascii')}"
    safe_family = font_family.replace("'", "").replace('"', "").replace(";", "")
    return f"""
    <style>
    @font-face {{
        font-family: '{safe_family}';
        src: url('{data_url}') format('{font_format}');
        font-weight: 400 900;
        font-style: normal;
        font-display: swap;
    }}
    </style>
    """


HIGHLIGHT_LABELS = {
    "title": "제목/교육명",
    "welcome": "상단 안내 문구",
    "time": "교육 시작시간 강조 문구",
    "brand": "브랜드 컬러",
    "header_text": "섹션 제목/커리큘럼 헤더 글자색",
    "logo": "로고",
    "font": "폰트",
    "overview": "교육 개요",
    "location": "교육 장소",
    "curriculum": "커리큘럼",
    "notice": "안내 사항",
    "contact": "관련 문의",
}


def set_active_highlight(zone: str) -> None:
    # 입력 중인 영역 하이라이트 기능은 v16에서 제거했습니다.
    return None


def render_template_html(template: str, replacements: dict[str, str]) -> str:
    """사용자가 수정한 문구의 플레이스홀더만 HTML로 치환하고 나머지는 안전하게 escape합니다."""
    template = str(template or "")
    tokens = sorted(replacements.keys(), key=len, reverse=True)
    result = ""
    idx = 0
    while idx < len(template):
        matched_token = None
        for token in tokens:
            if template.startswith(token, idx):
                matched_token = token
                break
        if matched_token is not None:
            result += replacements[matched_token]
            idx += len(matched_token)
            continue

        char = template[idx]
        if char == "\n":
            result += "<br>"
        else:
            result += esc(char)
        idx += 1
    return result


# -----------------------------
# Streamlit UI 스타일
# -----------------------------
st.markdown(
    """
    <style>
    :root {
        --app-bg: #050505;
        --card-bg: #1B1B1B;
        --card-bg-strong: #222222;
        --field-bg: #2B2B2B;
        --field-bg-focus: #333333;
        --line: #3A3A3A;
        --line-strong: #5A5A5A;
        --text: #F7F7F7;
        --muted: #B8B8B8;
        --soft: #242424;
        --button-bg: #FFFFFF;
        --button-text: #111111;
    }

    .stApp {
        background: var(--app-bg);
        color: var(--text);
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1540px;
    }

    .main-title {
        font-size: 30px;
        font-weight: 850;
        color: var(--text);
        margin-bottom: 4px;
        letter-spacing: -0.7px;
    }

    .sub-title {
        font-size: 14px;
        color: var(--muted);
        margin-bottom: 22px;
    }

    /* 카드형 입력/출력 섹션 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card-bg);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 18px 42px rgba(0, 0, 0, 0.35);
        padding: 6px 6px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h4,
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--text);
        letter-spacing: -0.35px;
        margin-bottom: 0.25rem;
    }

    /* 일반 텍스트/라벨 */
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    label,
    .stRadio label,
    .stCheckbox label,
    .stSlider label,
    .stColorPicker label,
    .stFileUploader label {
        color: var(--text) !important;
    }

    [data-testid="stCaptionContainer"],
    .mini-help,
    small,
    .st-emotion-cache-1wmy9hl,
    .st-emotion-cache-ue6h4q {
        color: var(--muted) !important;
    }

    /* 입력창: 차콜 배경 */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border-color: var(--line-strong) !important;
        background-color: var(--field-bg) !important;
        color: var(--text) !important;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #FFFFFF !important;
        background-color: var(--field-bg-focus) !important;
        box-shadow: 0 0 0 1px #FFFFFF22 !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: var(--text) !important;
        caret-color: var(--text) !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9CA3AF !important;
    }

    /* 컬러피커/파일업로더/데이터에디터 보정 */
    [data-testid="stFileUploader"] section {
        background-color: var(--field-bg) !important;
        border: 1px dashed var(--line-strong) !important;
        border-radius: 14px !important;
        color: var(--text) !important;
    }

    [data-testid="stFileUploader"] section * {
        color: var(--text) !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stDataFrame"] div {
        border-color: var(--line) !important;
    }

    /* 버튼: 흰색 배경 + 검정 글씨 */
    div.stButton > button:first-child,
    .stDownloadButton > button {
        background-color: var(--button-bg);
        color: var(--button-text);
        border-radius: 12px;
        width: 100%;
        height: 44px;
        font-weight: 850;
        border: 1px solid var(--button-bg);
        box-shadow: none;
    }

    div.stButton > button:first-child p,
    .stDownloadButton > button p {
        color: var(--button-text) !important;
    }

    div.stButton > button:hover,
    .stDownloadButton > button:hover {
        background-color: #E5E5E5;
        color: #111111;
        border-color: #E5E5E5;
    }

    div.stButton > button:active,
    .stDownloadButton > button:active {
        background-color: #D4D4D4;
        color: #111111;
        border-color: #D4D4D4;
    }

    .naver-map-button {
        display: block;
        width: 100%;
        box-sizing: border-box;
        height: 44px;
        line-height: 42px;
        text-align: center;
        text-decoration: none !important;
        border-radius: 12px;
        border: 1px solid var(--button-bg);
        background: var(--button-bg);
        color: var(--button-text) !important;
        font-size: 14px;
        font-weight: 850;
        margin: 6px 0 8px 0;
    }

    .naver-map-button:hover {
        background: #E5E5E5;
        border-color: #E5E5E5;
        color: #111111 !important;
    }

    .capture-guide {
        margin: 6px 0 8px 0;
        padding: 10px 12px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: #111111;
        color: var(--muted);
        font-size: 12px;
        line-height: 18px;
    }

    .capture-guide strong {
        color: var(--text);
    }

    /* 탭 */
    [data-testid="stTabs"] button {
        color: var(--muted) !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--text) !important;
        font-weight: 850;
    }

    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background-color: #FFFFFF !important;
    }

    /* 미리보기 iframe 배경: 붉은 기 없는 쿨 그레이 */
    [data-testid="stTabs"] iframe {
        background-color: #EEF2F6 !important;
        border-radius: 14px;
    }

    hr {
        border-color: var(--line) !important;
    }

    .mini-help {
        color: var(--muted);
        font-size: 12px;
        line-height: 18px;
        margin-top: -4px;
    }


    /* 우측 미리보기 영역 고정 */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) {
        position: sticky;
        top: 18px;
        align-self: flex-start;
        max-height: calc(100vh - 28px);
        overflow-y: auto;
        padding-right: 4px;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2)::-webkit-scrollbar {
        width: 8px;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2)::-webkit-scrollbar-thumb {
        background: #4A4A4A;
        border-radius: 999px;
    }

    div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2)::-webkit-scrollbar-track {
        background: #111111;
    }

    /* 좌측 입력 설정 스크롤 패널 보정 */
    div[style*="overflow"]::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    div[style*="overflow"]::-webkit-scrollbar-thumb {
        background: #4A4A4A;
        border-radius: 999px;
    }

    div[style*="overflow"]::-webkit-scrollbar-track {
        background: #111111;
        border-radius: 999px;
    }

    /* 좌측 입력부 내부 카드 간격 압축 */
    div[data-testid="column"]:first-of-type [data-testid="stVerticalBlockBorderWrapper"] {
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">✉️ 교육 안내문 자동 생성기</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">필수 정보를 입력하면 아웃룩 메일 본문용 HTML과 PNG/JPG 이미지 안내문을 함께 생성합니다.</div>',
    unsafe_allow_html=True,
)


# -----------------------------
# 스포이드 컴포넌트
# -----------------------------
def eyedropper_component(target: str, label: str) -> None:
    safe_target = esc_attr(target)
    safe_label = esc(label)
    target_label = "메인 컬러" if target == "main" else "하단 컬러"
    components.html(
        f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
    body {{ margin: 0; padding: 0; background: transparent; font-family: Arial, sans-serif; }}
    .wrap {{ display: flex; align-items: flex-start; gap: 6px; min-height: 64px; flex-wrap: wrap; padding: 2px 0; box-sizing: border-box; overflow: visible; }}
    button {{
        height: 32px;
        padding: 0 10px;
        border-radius: 9px;
        border: 1px solid #FFFFFF;
        background: #FFFFFF;
        color: #111111 !important;
        font-size: 11px;
        font-weight: 800;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
    }}
    button:hover {{ background: #E5E5E5; }}
    .result {{ font-size: 12px; color: #B8B8B8; white-space: nowrap; line-height: 32px; }}
    #fallback button {{ margin-top: 0; }}
</style>
</head>
<body>
    <div class="wrap">
        <button onclick="pickColor()">🎯 {safe_label}</button>
        <span id="result" class="result">웹 화면 색상 추출</span>
        <span id="fallback"></span>
    </div>
<script>
const TARGET = '{safe_target}';
const TARGET_LABEL = '{target_label}';

function getParentDocument() {{
    try {{ return window.parent.document; }} catch (e) {{ return null; }}
}}

function setNativeInputValue(input, value) {{
    const win = input.ownerDocument.defaultView || window.parent || window;
    const descriptor = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value');
    if (descriptor && descriptor.set) {{
        descriptor.set.call(input, value);
    }} else {{
        input.value = value;
    }}
    input.dispatchEvent(new win.Event('input', {{ bubbles: true }}));
    input.dispatchEvent(new win.Event('change', {{ bubbles: true }}));
}}

function findColorPickerInput(doc) {{
    const pickers = Array.from(doc.querySelectorAll('[data-testid="stColorPicker"]'));
    const matchedPicker = pickers.find((picker) => {{
        const txt = picker.innerText || picker.textContent || '';
        return txt.indexOf(TARGET_LABEL) >= 0;
    }});

    if (matchedPicker) {{
        const matchedInput = matchedPicker.querySelector('input[id^="rc-editable-input-"], input[type="text"], input');
        if (matchedInput) return matchedInput;
    }}

    const visibleInputs = Array.from(doc.querySelectorAll('input[id^="rc-editable-input-"]'))
        .filter((input) => input.offsetParent !== null);
    if (TARGET === 'footer') return visibleInputs[1] || visibleInputs[0] || null;
    return visibleInputs[0] || null;
}}

function applyColorDirectlyToStreamlit(color) {{
    const doc = getParentDocument();
    if (!doc) return false;

    const input = findColorPickerInput(doc);
    if (!input) return false;

    try {{
        input.scrollIntoView({{ block: 'center', inline: 'nearest' }});
        input.focus();
        input.select && input.select();
        setNativeInputValue(input, color);

        const win = input.ownerDocument.defaultView || window.parent || window;
        input.dispatchEvent(new win.KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
        input.dispatchEvent(new win.KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', bubbles: true }}));
        input.blur();
        return true;
    }} catch (e) {{
        console.log(e);
        return false;
    }}
}}

function getStreamlitUrl() {{
    let baseUrl = document.referrer || '';
    try {{
        if (!baseUrl) baseUrl = window.top.location.href;
    }} catch (e) {{}}
    if (!baseUrl) baseUrl = window.location.href;
    return new URL(baseUrl);
}}

function buildApplyUrl(color) {{
    const url = getStreamlitUrl();
    url.searchParams.set('picked_target', TARGET);
    url.searchParams.set('picked_color', color);
    url.searchParams.set('picked_token', String(Date.now()));
    url.hash = '';
    return url.toString();
}}

function copyTextFallback(text) {{
    try {{
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        return true;
    }} catch (e) {{
        return false;
    }}
}}

async function copyColorCode(color) {{
    let ok = false;
    try {{
        await navigator.clipboard.writeText(color);
        ok = true;
    }} catch (e) {{
        ok = copyTextFallback(color);
    }}

    const resultEl = document.getElementById('result');
    if (ok) {{
        resultEl.textContent = color + ' 복사 완료';
    }} else {{
        resultEl.textContent = color + ' 복사 실패';
        alert('자동 복사가 막혔습니다. 색상 코드를 직접 복사해 주세요: ' + color);
    }}
}}

function showCopyButton(color) {{
    const fallbackEl = document.getElementById('fallback');
    fallbackEl.innerHTML = '';
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = '색상 코드 복사하기';
    button.onclick = function() {{ copyColorCode(color); }};
    fallbackEl.appendChild(button);
}}

async function pickColor() {{
    const resultEl = document.getElementById('result');
    if (!window.EyeDropper) {{
        resultEl.textContent = '현재 브라우저 미지원';
        alert('이 브라우저에서는 스포이드 기능을 지원하지 않습니다. Chrome 또는 Edge에서 실행해 주세요.');
        return;
    }}

    try {{
        const eyeDropper = new EyeDropper();
        const result = await eyeDropper.open();
        const color = result.sRGBHex;

        if (applyColorDirectlyToStreamlit(color)) {{
            resultEl.textContent = color + ' 입력창 적용 완료';
            return;
        }}

        resultEl.textContent = color + ' 추출 완료';
        showCopyButton(color);
    }} catch (error) {{
        resultEl.textContent = '취소됨';
    }}
}}
</script>
</body>
</html>
        """,
        height=92,
    )


# -----------------------------
# 안내문 HTML 빌더
# -----------------------------
def build_section_title(number: int, title: str, main_color: str, title_text_color: str = "#FFFFFF", zone: str = "") -> str:
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="{esc_attr(zone)} section-title brand header_text" style="margin: 0 0 14px 0; border-collapse: collapse;">
        <tr>
            <td style="width: 6px; background-color: {main_color}; font-size: 0; line-height: 0;">&nbsp;</td>
            <td style="background-color: {main_color}; color: {title_text_color}; padding: 8px 18px 8px 12px; font-size: 18px; line-height: 22px; font-weight: 700; letter-spacing: -0.3px;">
                {number}. {esc(title)}
            </td>
        </tr>
    </table>
    """


def build_bullet_rows(lines: list[str], text_color: str = "#343A40") -> str:
    rows = ""
    for line in lines:
        clean_line = normalize_bullet(line)
        if not clean_line:
            continue
        rows += f"""
        <tr>
            <td valign="top" style="width: 18px; padding: 0 8px 8px 0; font-size: 15px; color: {text_color}; line-height: 22px;">-</td>
            <td valign="top" style="padding: 0 0 8px 0; font-size: 15px; color: {text_color}; line-height: 22px; letter-spacing: -0.2px;">{esc(clean_line)}</td>
        </tr>
        """
    return rows or """
        <tr>
            <td style="font-size: 15px; color: #6B7280; line-height: 22px;">입력된 안내 사항이 없습니다.</td>
        </tr>
    """


def build_contact_rows(contacts: list[dict], text_color: str = "#343A40") -> str:
    rows = ""
    for contact in to_records(contacts):
        role = str(contact.get("role", "") or "").strip()
        phone = str(contact.get("phone", "") or "").strip()
        if not role and not phone:
            continue

        phone_html = f" <span style='color:{text_color};'>({esc(phone)})</span>" if phone else ""
        rows += f"""
        <tr>
            <td valign="top" style="width: 18px; padding: 0 8px 8px 0; font-size: 15px; color: {text_color}; line-height: 22px;">-</td>
            <td valign="top" style="padding: 0 0 8px 0; font-size: 15px; color: {text_color}; line-height: 22px;">
                <span style="font-weight: 700;">{esc(role)}</span>{phone_html}
            </td>
        </tr>
        """

    return rows or """
        <tr>
            <td style="font-size: 15px; color: #6B7280; line-height: 22px;">입력된 문의처가 없습니다.</td>
        </tr>
    """


def build_curriculum_rows(curriculum: list[dict]) -> str:
    rows = ""
    palette = {
        "1일차": "#DDF0FA",
        "2일차": "#DDF4E8",
        "3일차": "#F6EAD5",
    }

    for idx, row in enumerate(to_records(curriculum)):
        day = str(row.get("day", "") or "").strip()
        time = str(row.get("time", "") or "").strip()
        subject = str(row.get("subject", "") or "").strip()
        speaker = str(row.get("speaker", "") or "").strip()

        if not any([day, time, subject, speaker]):
            continue

        bg = palette.get(day, "#F3F4F6")
        if idx % 2 == 1 and day not in palette:
            bg = "#FAFAFA"

        rows += f"""
        <tr>
            <td style="padding: 13px 10px; border-bottom: 1px solid #D8DEE6; border-right: 1px solid #D8DEE6; background-color: #FFFFFF; font-size: 14px; color: #343A40; text-align: center; line-height: 20px; white-space: nowrap;">
                {esc(time)}
            </td>
            <td style="padding: 13px 10px; border-bottom: 1px solid #D8DEE6; border-right: 1px solid #D8DEE6; background-color: {bg}; font-size: 14px; color: #1F2933; text-align: center; line-height: 20px; font-weight: 700;">
                {esc(day)}
            </td>
            <td style="padding: 13px 14px; border-bottom: 1px solid #D8DEE6; border-right: 1px solid #D8DEE6; background-color: {bg}; font-size: 15px; color: #1F2933; line-height: 21px; font-weight: 700;">
                {esc(subject)}
            </td>
            <td style="padding: 13px 10px; border-bottom: 1px solid #D8DEE6; background-color: {bg}; font-size: 14px; color: #343A40; text-align: center; line-height: 20px;">
                {esc(speaker) if speaker else "-"}
            </td>
        </tr>
        """

    return rows or """
        <tr>
            <td colspan="4" style="padding: 18px 10px; border-bottom: 1px solid #D8DEE6; background-color: #FFFFFF; font-size: 14px; color: #6B7280; text-align: center;">
                입력된 커리큘럼이 없습니다.
            </td>
        </tr>
    """


def build_logo_image_html(logo_image_data_url: str, logo_max_height: int = 52) -> str:
    if not str(logo_image_data_url or "").strip():
        return ""
    return f"""
    <img src="{esc_attr(logo_image_data_url)}" alt="회사 로고" style="display: inline-block; max-height: {int(logo_max_height)}px; max-width: 240px; width: auto; height: auto; border: 0; outline: none; text-decoration: none;" />
    """


def build_logo_row(logo_image_data_url: str, logo_position: str, area: str, logo_max_height: int = 52) -> str:
    if not str(logo_image_data_url or "").strip():
        return ""

    is_top = "상단" in logo_position
    is_bottom = "하단" in logo_position
    if area == "top" and not is_top:
        return ""
    if area == "bottom" and not is_bottom:
        return ""

    align = "right" if "우측" in logo_position else "left"
    margin = "0 0 12px 0" if area == "top" else "18px 0 0 0"
    return f"""
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="logo" style="width: 100%; border-collapse: collapse; margin: {margin};">
        <tr>
            <td style="text-align: {align}; vertical-align: middle; height: {int(logo_max_height)}px;">
                {build_logo_image_html(logo_image_data_url, logo_max_height)}
            </td>
        </tr>
    </table>
    """


def build_final_mail_html(
    company_name: str,
    course_name: str,
    date_range: str,
    day1_time: str,
    day2_time: str,
    place_name: str,
    map_image_src: str,
    delivery_type: str,
    welcome_title: str,
    welcome_body_text: str,
    time_notice_text: str,
    edited_curriculum: list[dict],
    info_text: str,
    edited_contacts: list[dict],
    main_color: str,
    footer_color: str,
    section_text_color: str = "#343A40",
    curr_header_text_color: str = "#FFFFFF",
    logo_image_data_url: str = "",
    logo_position: str = "우측 상단",
    logo_max_height: int = 52,
    font_stack: str = "'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif",
    embedded_font_css: str = "",
) -> str:
    company_display = str(company_name or "").strip()
    full_course_name = f"{company_display} {course_name}".strip()
    curriculum_html = build_curriculum_rows(edited_curriculum)
    info_html = build_bullet_rows(info_text.split("\n"), text_color=section_text_color)
    contacts_html = build_contact_rows(edited_contacts, text_color=section_text_color)
    top_logo_html = build_logo_row(logo_image_data_url, logo_position, "top", logo_max_height)
    bottom_logo_html = build_logo_row(logo_image_data_url, logo_position, "bottom", logo_max_height)
    title_margin_top = "14px" if top_logo_html else "4px"

    template_replacements = {
        "{교육명}": f"<span style='font-weight: 800;'>{esc(full_course_name)}</span>",
        "{운영방식}": f"<span style='color: #C1121F; font-weight: 800;'>{esc(delivery_type)}</span>",
        "{1일차}": esc(day1_time),
        "{2일차}": esc(day2_time),
        "{회사명}": esc(company_display),
    }
    welcome_body_html = render_template_html(welcome_body_text, template_replacements)
    time_notice_html = render_template_html(time_notice_text, template_replacements)

    map_html = ""
    if str(map_image_src or "").strip():
        map_html = f"""
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="width: 100%; border-collapse: collapse; margin-top: 12px;">
            <tr>
                <td style="padding: 0;">
                    <img src="{esc_attr(map_image_src)}" alt="교육 장소 지도" style="display: block; width: 100%; max-width: 650px; height: auto; border: 1px solid #D8DEE6;" />
                </td>
            </tr>
        </table>
        """

    return f"""
<div id="mail-content" data-zone="font" style="width: 760px; max-width: 760px; margin: 0 auto; font-family: {font_stack}; background-color: #FFFFFF; color: #222222; border: 1px solid #E5E7EB; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.12);">
    {embedded_font_css}
    <div data-zone="brand" style="height: 18px; background-color: {main_color}; font-size: 0; line-height: 0;">&nbsp;</div>

    <div style="padding: 24px 38px 32px 38px;">
        {top_logo_html}

        <h1 data-zone="title" style="margin: {title_margin_top} 0 20px 0; text-align: center; font-size: 30px; line-height: 38px; font-weight: 800; color: #222222; letter-spacing: -1px;">
            {esc(full_course_name)}
        </h1>

        <div style="border-top: 1px dotted #999999; height: 1px; line-height: 1px; font-size: 0; margin: 0 0 18px 0;">&nbsp;</div>

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="welcome time" style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr>
                <td style="text-align: center; padding: 0 8px;">
                    <p style="margin: 0 0 12px 0; font-size: 22px; line-height: 30px; font-weight: 800; color: #222222;">
                        {esc(welcome_title)}
                    </p>
                    <p style="margin: 0; font-size: 16px; line-height: 24px; color: #343A40; letter-spacing: -0.3px;">
                        {welcome_body_html}
                    </p>
                    <p style="margin: 12px 0 0 0; font-size: 16px; line-height: 24px; color: #C1121F; font-weight: 800; letter-spacing: -0.3px;">
                        {time_notice_html}
                    </p>
                </td>
            </tr>
        </table>

        <div style="border-top: 1px dotted #999999; height: 1px; line-height: 1px; font-size: 0; margin: 0 0 26px 0;">&nbsp;</div>

        {build_section_title(1, "교육 개요", main_color, curr_header_text_color, "overview")}

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="overview" style="width: 100%; border-collapse: collapse; margin: 0 0 18px 0;">
            {build_bullet_rows([
                f"교육명 : {full_course_name}",
                f"교육일정 : {date_range}  *집합 교육 기준",
                "교육시간 : 하기 표 참고  ※ 강의 시작 10분 전까지 입실 부탁드립니다.",
            ], text_color=section_text_color)}
        </table>

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="curriculum" style="width: 100%; border-collapse: collapse; margin: 10px 0 34px 0; border-top: 1px solid #D8DEE6; border-left: 1px solid #D8DEE6;">
            <thead>
                <tr data-zone="curriculum brand header_text">
                    <th style="padding: 12px 10px; background-color: {main_color}; color: {curr_header_text_color}; font-size: 15px; line-height: 20px; font-weight: 700; text-align: center; border-right: 1px solid #74787C;">시간</th>
                    <th style="padding: 12px 10px; background-color: {main_color}; color: {curr_header_text_color}; font-size: 15px; line-height: 20px; font-weight: 700; text-align: center; border-right: 1px solid #74787C;">일차</th>
                    <th style="padding: 12px 10px; background-color: {main_color}; color: {curr_header_text_color}; font-size: 15px; line-height: 20px; font-weight: 700; text-align: center; border-right: 1px solid #74787C;">교육 내용</th>
                    <th style="padding: 12px 10px; background-color: {main_color}; color: {curr_header_text_color}; font-size: 15px; line-height: 20px; font-weight: 700; text-align: center;">강사/비고</th>
                </tr>
            </thead>
            <tbody>
                {curriculum_html}
            </tbody>
        </table>

        {build_section_title(2, "교육 장소", main_color, curr_header_text_color, "location")}

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="location" style="width: 100%; border-collapse: collapse; margin: 0 0 32px 0;">
            {build_bullet_rows([place_name], text_color=section_text_color)}
            <tr>
                <td colspan="2" style="padding: 0 0 0 26px;">
                    {map_html}
                </td>
            </tr>
        </table>

        {build_section_title(3, "안내 사항", main_color, curr_header_text_color, "notice")}

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="notice" style="width: 100%; border-collapse: collapse; margin: 0 0 30px 0;">
            {info_html}
        </table>

        {build_section_title(4, "관련 문의", main_color, curr_header_text_color, "contact")}

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="contact" style="width: 100%; border-collapse: collapse; margin: 0 0 10px 0;">
            {contacts_html}
        </table>

        {bottom_logo_html}
    </div>

    <div data-zone="brand" style="height: 18px; background-color: {footer_color}; font-size: 0; line-height: 0;">&nbsp;</div>
</div>
"""


def build_preview_component_html(final_mail_html: str, preview_scale: float, font_stack: str, export_base_name: str = "education_notice_photo_style") -> str:
    scale = max(0.45, min(1.0, float(preview_scale)))
    export_base_name_js = json.dumps(str(export_base_name or "education_notice_photo_style"), ensure_ascii=False)
    return (
        f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 14px 0 34px 0;
            background: #EEF2F6;
            font-family: {font_stack};
        }}
        .toolbar {{
            width: min(760px, calc(100vw - 28px));
            margin: 0 auto 10px auto;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            position: sticky;
            top: 0;
            z-index: 5;
            background: #EEF2F6;
            padding-bottom: 8px;
        }}
        .tool-btn {{
            border: 1px solid #111111;
            border-radius: 12px;
            height: 40px;
            font-size: 13px;
            font-weight: 800;
            color: #FFFFFF;
            background: #111111;
            cursor: pointer;
        }}
        .tool-btn:hover {{ background: #333333; }}
        .note {{
            width: min(760px, calc(100vw - 28px));
            margin: 0 auto 10px auto;
            font-size: 12px;
            line-height: 18px;
            color: #737373;
        }}
        .preview-area {{
            zoom: {scale};
        }}
        @supports not (zoom: 1) {{
            .preview-area {{
                transform: scale({scale});
                transform-origin: top center;
            }}
        }}
    </style>
</head>
<body>
    <div class="toolbar">
        <button class="tool-btn" onclick="copyMailContent()">📋 아웃룩 서식 복사</button>
        <button class="tool-btn" onclick="downloadImage('png')">🖼️ PNG 저장</button>
        <button class="tool-btn" onclick="downloadImage('jpeg')">🖼️ JPG 저장</button>
    </div>
    <div class="note">미리보기는 축소해서 보여주고, 저장 이미지는 원본 크기로 생성합니다.</div>
    <div class="preview-area">
"""
        + final_mail_html
        + """
    </div>
    <script>
        const EXPORT_BASE_NAME = """ + export_base_name_js + """;

        function getContent() {
            return document.getElementById('mail-content');
        }

        async function copyMailContent() {
            const content = getContent();
            if (!content) {
                alert('복사할 대상을 찾지 못했습니다.');
                return;
            }

            const htmlContent = content.outerHTML;
            const textContent = content.innerText;

            try {
                if (navigator.clipboard && window.ClipboardItem) {
                    await navigator.clipboard.write([
                        new ClipboardItem({
                            'text/html': new Blob([htmlContent], { type: 'text/html' }),
                            'text/plain': new Blob([textContent], { type: 'text/plain' })
                        })
                    ]);
                    alert('사진형 안내문 서식이 복사되었습니다. 아웃룩 본문에 Ctrl+V 하세요.');
                    return;
                }
            } catch (error) {
                console.log(error);
            }

            try {
                const range = document.createRange();
                range.selectNodeContents(content);
                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                document.execCommand('copy');
                selection.removeAllRanges();
                alert('사진형 안내문 서식이 복사되었습니다. 아웃룩 본문에 Ctrl+V 하세요.');
            } catch (error) {
                alert('복사에 실패했습니다. 미리보기 영역을 직접 드래그해서 복사해 주세요.');
            }
        }

        async function downloadImage(format) {
            const source = getContent();
            if (!source) {
                alert('저장할 안내문을 찾지 못했습니다.');
                return;
            }
            if (typeof html2canvas === 'undefined') {
                alert('이미지 저장 모듈을 불러오지 못했습니다. 인터넷 연결 후 다시 시도해 주세요.');
                return;
            }

            const clone = source.cloneNode(true);
            clone.id = 'mail-content-export';
            clone.style.margin = '0';

            const offscreen = document.createElement('div');
            offscreen.style.position = 'fixed';
            offscreen.style.left = '-10000px';
            offscreen.style.top = '0';
            offscreen.style.width = source.offsetWidth + 'px';
            offscreen.style.background = '#ffffff';
            offscreen.style.zIndex = '-1';
            offscreen.appendChild(clone);
            document.body.appendChild(offscreen);

            try {
                const canvas = await html2canvas(clone, {
                    scale: 2,
                    backgroundColor: '#ffffff',
                    useCORS: true,
                    allowTaint: false,
                    logging: false,
                    scrollX: 0,
                    scrollY: 0,
                    windowWidth: 1200,
                    windowHeight: clone.scrollHeight + 100
                });

                const mimeType = format === 'jpeg' ? 'image/jpeg' : 'image/png';
                const extension = format === 'jpeg' ? 'jpg' : 'png';
                const dataUrl = canvas.toDataURL(mimeType, 0.95);
                const link = document.createElement('a');
                link.download = EXPORT_BASE_NAME + '.' + extension;
                link.href = dataUrl;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (error) {
                console.error(error);
                alert('이미지 저장에 실패했습니다. 외부 웹 이미지 URL 대신 지도/로고 이미지를 첨부한 뒤 다시 저장해 주세요.');
            } finally {
                document.body.removeChild(offscreen);
            }
        }
    </script>
</body>
</html>
"""
    )


# -----------------------------
# 쿼리 파라미터 기반 스포이드 색상 반영
# -----------------------------
init_defaults()

picked_color = get_query_param("picked_color")
picked_target = get_query_param("picked_target")
picked_token = get_query_param("picked_token")
if is_valid_hex_color(picked_color) and picked_token and st.session_state.get("last_picked_token") != picked_token:
    if picked_target == "main":
        st.session_state.main_color_picker = picked_color
    elif picked_target == "footer":
        st.session_state.footer_color_picker = picked_color
        st.session_state.use_custom_footer_color = True
    st.session_state.last_picked_token = picked_token
    try:
        st.query_params.clear()
    except Exception:
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
    st.rerun()


SIDE_PANEL_HEIGHT = 920
PREVIEW_IFRAME_HEIGHT = 690

# -----------------------------
# 입력 / 출력 레이아웃
# -----------------------------
col_input, col_output = st.columns([0.9, 1.25], gap="large")

with col_input:
    st.subheader("입력 설정")

    with st.container(height=SIDE_PANEL_HEIGHT, border=False):

        with st.container(border=True):
            st.markdown("#### 기본 정보")
            company_name = st.text_input(
                "회사 이름",
                key="company_name",
                help="입력한 회사 이름이 그대로 표시됩니다. '그룹'은 자동으로 붙지 않습니다.",
            )
            course_name = st.text_input("교육 과정명", key="course_name")
            delivery_mode = st.selectbox(
                "운영 방식",
                ["대면", "비대면", "직접입력"],
                key="delivery_mode",
            )
            if delivery_mode == "직접입력":
                delivery_type = st.text_input(
                    "운영 방식 직접 입력",
                    key="delivery_custom",
                    placeholder="예: 하이브리드, 온라인 실시간, 집합",
                ).strip()
            else:
                delivery_type = delivery_mode

        with st.container(border=True):
            st.markdown("#### 상단 안내 문구")
            st.caption("사용 가능 치환값: {교육명}, {운영방식}, {1일차}, {2일차}, {회사명}")
            welcome_title = st.text_input("환영 제목", key="welcome_title")
            welcome_body_text = st.text_area("상단 안내 본문", key="welcome_body_text", height=110)
            time_notice_text = st.text_area("교육 시작시간 강조 문구", key="time_notice_text", height=80)
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                day1_time = st.text_input("1일차 시작 시간", key="day1_time")
            with col_t2:
                day2_time = st.text_input("2일차 시작 시간", key="day2_time")

        with st.container(border=True):
            st.markdown("#### 브랜드 컬러")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                main_color = st.color_picker("메인 컬러", key="main_color_picker")
                eyedropper_component("main", "메인 컬러 스포이드")
            with col_c2:
                use_custom_footer_color = st.checkbox("하단 컬러 별도 지정", key="use_custom_footer_color")
                if use_custom_footer_color:
                    footer_color = st.color_picker("하단 컬러", key="footer_color_picker")
                    eyedropper_component("footer", "하단 컬러 스포이드")
                else:
                    footer_color = main_color
                    st.caption("체크하지 않으면 하단 바도 메인 컬러를 사용합니다.")

            st.markdown("---")
            curr_header_text_color = st.color_picker(
                "섹션 제목/커리큘럼 헤더 글자색",
                key="curr_header_text_color_picker",
            )
            section_text_color = "#000000"
            st.caption("본문 글자색은 검정색으로 고정됩니다. 위 색상은 섹션 제목 박스와 커리큘럼 헤더 글자에 적용됩니다.")

        with st.container(border=True):
            st.markdown("#### 로고 / 폰트")
            logo_file = st.file_uploader(
                "회사 로고 이미지 첨부",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                help="첨부하지 않으면 로고 영역은 비워집니다. 회사명 텍스트 로고는 자동으로 표시하지 않습니다.",
                key="logo_file_uploader",
            )
            logo_image_data_url = file_to_data_url(logo_file)
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                logo_position = st.selectbox(
                    "로고 위치",
                    ["우측 상단", "좌측 상단", "우측 하단", "좌측 하단"],
                    key="logo_position",
                    help="로고 이미지를 첨부한 경우에만 적용됩니다.",
                )
            with col_l2:
                logo_max_height = st.slider("로고 크기 조절", min_value=28, max_value=90, step=2, key="logo_max_height")

            embedded_font_css = ""
            fonts_dir = get_fonts_dir()
            try:
                fonts_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            font_files = list_font_files(str(fonts_dir))
            if font_files:
                selected_font_file = st.selectbox(
                    "폰트 선택",
                    font_files,
                    format_func=lambda x: Path(x).name,
                    key="font_folder_select",
                )
                primary_font = font_family_from_file(selected_font_file)
                embedded_font_css = build_embedded_font_css(selected_font_file, primary_font)
            else:
                primary_font = "Malgun Gothic"
                st.warning("assets/fonts 폴더에 사용할 폰트 파일이 없습니다. 기본 폰트를 사용합니다.")
            font_stack = css_font_stack(primary_font)

        with st.container(border=True):
            st.markdown("#### 일정 및 장소")
            date_range = st.text_input("교육 일정 (예: 6/16(월)~6/17(화))", key="date_range")

            place_name = st.text_input("교육 장소명 및 주소", key="place_name")
            naver_map_query = quote(str(place_name or "").strip())
            naver_map_url = f"https://map.naver.com/p/search/{naver_map_query}?c=15.00,0,0,0,dh" if naver_map_query else "https://map.naver.com/p/search/"
            st.markdown(
                f'<a class="naver-map-button" href="{naver_map_url}" target="_blank" rel="noopener noreferrer">🗺️ 네이버 지도 바로가기</a>',
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="capture-guide">
                    <strong>네이버 지도 백그라운드 캡처</strong><br>
                    입력한 교육 장소명으로 네이버 지도 검색 화면을 백그라운드에서 열고, 1920×1080 화면 기준 좌표 (585, 87)~(1785, 1047) 영역을 PNG로 캡처해 지도 영역에 자동 적용합니다.
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_map_cap1, col_map_cap2 = st.columns([1, 1])
            with col_map_cap1:
                if st.button("📸 지도 자동 캡처", use_container_width=True):
                    with st.spinner("네이버 지도 검색 화면을 백그라운드에서 열고 캡처 중입니다. 지도 로딩 때문에 10~20초 정도 걸릴 수 있습니다..."):
                        ok, message = capture_naver_map_region(place_name)
                    st.session_state.last_map_capture_message = message
                    if ok:
                        st.success(message)
                    else:
                        st.error(message)
            with col_map_cap2:
                if st.button("🧹 캡처 지도 제거", use_container_width=True):
                    st.session_state.captured_map_data_url = ""
                    st.session_state.captured_map_file_path = ""
                    st.session_state.pop("last_captured_map_file", None)
                    st.session_state.last_map_capture_message = "캡처 지도를 제거했습니다."

            captured_map_path = st.session_state.get("captured_map_file_path", "") or st.session_state.get("last_captured_map_file", "")
            captured_map_data_url = file_path_to_data_url(captured_map_path) or st.session_state.get("captured_map_data_url", "")
            last_map_capture_message = st.session_state.get("last_map_capture_message", "")
            if last_map_capture_message:
                st.caption(last_map_capture_message)
            if captured_map_data_url:
                st.image(captured_map_data_url, caption="자동 캡처된 지도 이미지", use_container_width=True)
                st.caption("현재 지도 영역에는 자동 캡처 이미지가 적용됩니다. 다른 이미지를 직접 첨부하면 첨부 이미지가 우선 적용됩니다.")

            map_file = st.file_uploader(
                "지도 이미지 첨부",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                help="캡처 기능이 환경상 동작하지 않을 때는 직접 저장한 지도 이미지를 첨부해 주세요.",
                key="map_file_uploader",
            )
            map_image_src = file_to_data_url(map_file) or captured_map_data_url

        with st.container(border=True):
            st.markdown("#### 커리큘럼")
            
            edited_curr = st.data_editor(
                st.session_state.curriculum,
                num_rows="dynamic",
                column_config={
                    "day": "일차",
                    "time": "시간",
                    "subject": "교육 내용",
                    "speaker": "강사/비고",
                },
                width="stretch",
                key="curr_editor",
            )

        with st.container(border=True):
            st.markdown("#### 안내 사항 / 문의처")
            info_text = st.text_area("안내 사항 문구", key="info_text", height=120)

            edited_contacts = st.data_editor(
                st.session_state.contacts,
                num_rows="dynamic",
                column_config={"role": "소속 + 이름 + 직급", "phone": "연락처"},
                width="stretch",
                key="contacts_editor",
            )


final_mail_html = build_final_mail_html(
    company_name=company_name,
    course_name=course_name,
    date_range=date_range,
    day1_time=day1_time,
    day2_time=day2_time,
    place_name=place_name,
    map_image_src=map_image_src,
    delivery_type=delivery_type,
    welcome_title=welcome_title,
    welcome_body_text=welcome_body_text,
    time_notice_text=time_notice_text,
    edited_curriculum=edited_curr,
    info_text=info_text,
    edited_contacts=edited_contacts,
    main_color=main_color,
    footer_color=footer_color,
    section_text_color=section_text_color,
    curr_header_text_color=curr_header_text_color,
    logo_image_data_url=logo_image_data_url,
    logo_position=logo_position,
    logo_max_height=logo_max_height,
    font_stack=font_stack,
    embedded_font_css=embedded_font_css,
)


export_file_base = sanitize_file_name(st.session_state.get("export_file_name", DEFAULT_VALUES["export_file_name"]))


with col_output:
    st.subheader("출력 미리보기")

    with st.container(height=SIDE_PANEL_HEIGHT, border=False):
        tab_preview, tab_code = st.tabs(["👀 압축 미리보기", "💻 Raw HTML 소스코드"])

        with tab_preview:
            preview_scale_percent_for_render = st.session_state.get(
                "preview_scale_percent",
                DEFAULT_VALUES["preview_scale_percent"],
            )
            preview_scale = preview_scale_percent_for_render / 100

            components.html(
                build_preview_component_html(
                    final_mail_html,
                    preview_scale=preview_scale,
                    font_stack=font_stack,
                    export_base_name=export_file_base,
                ),
                height=PREVIEW_IFRAME_HEIGHT,
                scrolling=True,
            )

            with st.container(border=True):
                st.markdown("#### 내보내기 / 미리보기 설정")
                st.text_input(
                    "내보낼 파일 이름",
                    key="export_file_name",
                    help="확장자는 자동으로 붙습니다. 예: 멀티캠퍼스_입문교육_안내문",
                )
                col_p1, col_p2 = st.columns([1.4, 1])
                with col_p1:
                    st.caption("미리보기는 축소해서 보여주고, 저장 이미지는 원본 크기로 생성됩니다.")
                with col_p2:
                    st.slider("미리보기 배율", min_value=50, max_value=100, step=2, key="preview_scale_percent")

                col_d1, col_d2 = st.columns([1, 1])
                with col_d1:
                    st.download_button(
                        label="⬇️ HTML 파일 다운로드",
                        data=final_mail_html,
                        file_name=f"{export_file_base}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                with col_d2:
                    st.button("🔄 입력 내용 전체 초기화", on_click=reset_all_fields)

        with tab_code:
            st.text_area("생성된 HTML 소스코드 (텍스트 소스 보관용)", value=final_mail_html, height=760)
