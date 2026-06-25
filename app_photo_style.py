import base64
import html
import io
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
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
    "road_address": "",
    "display_place_name": "스타필드 수원 타임체임버",
    "display_road_address": "",
    "display_location_text": "스타필드 수원 타임체임버",
    "last_address_fetch_message": "",
    "selected_map_capture_variant": "일반 크기 (1200×960)",
    "naver_background_message": "",
    "naver_map_background_message": "",
    "naver_address_background_message": "",
    "curriculum_title": "상세 커리큘럼",
    "curriculum_columns_text": "시간, 일차, 교육 내용, 강사/비고",
    "curriculum_column_defs": [
        {"column_name": "시간"},
        {"column_name": "일차"},
        {"column_name": "교육 내용"},
        {"column_name": "강사/비고"},
    ],
    "info_text": "- 숙소는 2인 1실로 제공될 예정이며 생수, 비누, 샴푸, 헤어드라이기, 냉장고, TV, 전화기, 비데, 유무선인터넷 등이 구비되어 있습니다.\n- 1일차 석식은 연수원 외부에서 진행될 예정이오니 참고 부탁드립니다.",
    "preview_scale_percent": 72,
    "export_file_name": "education_notice_photo_style",
    "captured_map_data_url": "",
    "captured_map_file_path": "",
    "captured_map_files": {},
    "last_map_capture_message": "",
}

WIDGET_KEYS_TO_CLEAR_ON_RESET = [
    "logo_file_uploader",
    "map_file_uploader",
    "curr_editor",
    "curriculum_column_defs_editor",
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
    st.session_state.pop("captured_map_files", None)
    st.session_state.pop("last_map_capture_message", None)
    st.session_state.pop("naver_combined_future", None)
    st.session_state.pop("naver_combined_started_at", None)
    st.session_state.pop("naver_map_future", None)
    st.session_state.pop("naver_map_started_at", None)
    st.session_state.pop("naver_address_future", None)
    st.session_state.pop("naver_address_started_at", None)
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

    map_url = f"https://map.naver.com/p/search/{quote(query)}?c=16.00,0,0,0,dh"
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



def _find_text_in_all_frames(page, selector: str, timeout_ms: int = 2500) -> str:
    """현재 페이지와 모든 iframe에서 selector의 첫 번째 텍스트를 찾습니다."""
    for frame in page.frames:
        try:
            locator = frame.locator(selector).first
            if locator.count() > 0:
                text = locator.inner_text(timeout=timeout_ms).strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


def _wait_for_frame_by_name(page, frame_name: str, timeout_ms: int = 18000):
    """네이버 지도 iframe은 늦게 붙는 경우가 많아서 이름 기준으로 반복 탐색합니다."""
    deadline = time.time() + (timeout_ms / 1000)
    while time.time() < deadline:
        try:
            frame = page.frame(name=frame_name)
            if frame:
                return frame
        except Exception:
            pass
        try:
            page.wait_for_timeout(250)
        except Exception:
            time.sleep(0.25)
    return None


def _extract_korean_road_address(text: str) -> str:
    """네이버 지도 상세/검색 결과 텍스트에서 도로명 주소처럼 보이는 한 줄을 추출합니다."""
    raw = str(text or "")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    province_pattern = r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)"
    road_pattern = re.compile(province_pattern + r"[^\n]{0,90}?(?:로|길)\s*\d+(?:[\-\d]*)?(?:\s*[^\n]{0,45})?")
    for line in lines:
        if any(token in line for token in ["복사", "전화", "영업", "리뷰", "사진", "거리뷰", "출발", "도착"]):
            continue
        match = road_pattern.search(line)
        if match:
            address = match.group(0).strip()
            address = re.sub(r"\s+", " ", address)
            return address
    match = road_pattern.search(raw)
    if match:
        return re.sub(r"\s+", " ", match.group(0).strip())
    return ""


def _try_click_locator(locator, timeout_ms: int = 7000) -> bool:
    """React 이벤트 기반 href='#' 버튼 클릭을 여러 방식으로 시도합니다."""
    try:
        locator.wait_for(state="visible", timeout=timeout_ms)
    except Exception:
        return False

    try:
        locator.scroll_into_view_if_needed(timeout=timeout_ms)
    except Exception:
        pass

    click_methods = [
        lambda: locator.click(timeout=timeout_ms),
        lambda: locator.click(timeout=timeout_ms, force=True),
        lambda: locator.dispatch_event("click", timeout=timeout_ms),
        lambda: locator.evaluate("el => el.click()", timeout=timeout_ms),
        lambda: locator.press("Enter", timeout=timeout_ms),
    ]
    for method in click_methods:
        try:
            method()
            return True
        except Exception:
            continue
    return False


def _click_first_naver_place_result(page) -> tuple[bool, str]:
    """
    네이버 지도 검색 결과 첫 번째 항목을 클릭합니다.
    검색 결과의 a 태그 href는 대부분 '#': 실제 상세 이동은 React click handler로 처리됩니다.
    그래서 href를 읽지 않고, 제목/썸네일/role=button 요소를 실제 클릭합니다.
    """
    search_frame = _wait_for_frame_by_name(page, "searchIframe", timeout_ms=22000)
    candidate_frames = []
    if search_frame:
        candidate_frames.append(search_frame)
    candidate_frames.extend([frame for frame in page.frames if frame not in candidate_frames])

    selectors = [
        "#_pcmap_list_scroll_container > ul > li:nth-child(1) a.U70Fj",
        "#_pcmap_list_scroll_container > ul > li:nth-child(1) a.place_thumb",
        "#_pcmap_list_scroll_container > ul > li:nth-child(1) a[role='button']",
        "#_pcmap_list_scroll_container > ul > li:nth-child(1) [role='button']",
        "li.VLTHu:nth-child(1) a.U70Fj",
        "li.VLTHu:nth-child(1) a.place_thumb",
        "li:nth-child(1) a.U70Fj",
        "li:nth-child(1) a.place_thumb",
        "li:nth-child(1) [role='button']",
        "a.U70Fj:has(span.YwYLL)",
        "span.YwYLL",
    ]

    last_error = ""
    for frame in candidate_frames:
        for selector in selectors:
            try:
                locator = frame.locator(selector).first
                if locator.count() <= 0:
                    continue
                if _try_click_locator(locator):
                    return True, f"첫 번째 검색 결과를 클릭했습니다. selector={selector}"
            except Exception as exc:
                last_error = str(exc)
                continue

    # 최후 fallback: DOM 좌표로 첫 번째 결과 제목 위치를 클릭합니다.
    # searchIframe 안의 locator bounding_box는 메인 페이지 좌표로 변환되어 반환됩니다.
    try:
        if search_frame:
            locator = search_frame.locator("#_pcmap_list_scroll_container > ul > li:nth-child(1)").first
            locator.wait_for(state="visible", timeout=5000)
            box = locator.bounding_box(timeout=5000)
            if box:
                page.mouse.click(box["x"] + min(160, box["width"] / 2), box["y"] + min(42, box["height"] / 2))
                return True, "첫 번째 검색 결과를 좌표 클릭했습니다."
    except Exception as exc:
        last_error = str(exc)

    return False, f"첫 번째 검색 결과 클릭에 실패했습니다. {last_error}".strip()


def _extract_road_address_from_loaded_naver(page) -> str:
    """entryIframe 우선, 이후 전체 iframe에서 주소를 찾습니다."""
    target_frames = []
    entry_frame = _wait_for_frame_by_name(page, "entryIframe", timeout_ms=18000)
    if entry_frame:
        target_frames.append(entry_frame)
    target_frames.extend([frame for frame in page.frames if frame not in target_frames])

    selectors = [
        "#app-root div.place_section_content div.O8qbU.tQY7D div a span.pz7wy",
        "#app-root span.pz7wy",
        "span.pz7wy",
        "a span.pz7wy",
        "[class*='O8qbU'] [class*='pz7wy']",
    ]

    for _ in range(10):
        for frame in target_frames:
            for selector in selectors:
                try:
                    locator = frame.locator(selector).first
                    if locator.count() <= 0:
                        continue
                    text = locator.inner_text(timeout=1500).strip()
                    address = _extract_korean_road_address(text) or text
                    if address and ("로" in address or "길" in address):
                        return re.sub(r"\s+", " ", address.strip())
                except Exception:
                    continue
        try:
            page.wait_for_timeout(700)
        except Exception:
            time.sleep(0.7)

    for frame in target_frames:
        try:
            body_text = frame.locator("body").inner_text(timeout=2500)
            address = _extract_korean_road_address(body_text)
            if address:
                return address
        except Exception:
            continue

    return ""


def fetch_naver_road_address(place_query: str, wait_seconds: float = 5.0) -> tuple[bool, str]:
    """
    네이버 지도 검색 결과의 첫 번째 장소 상세 페이지에서 도로명 주소를 가져옵니다.
    v25 변경점:
    - href='#'를 링크로 해석하지 않고 실제 React click handler를 실행합니다.
    - 썸네일보다 제목 링크(a.U70Fj)를 우선 클릭합니다.
    - searchIframe/entryIframe 로딩을 더 오래 기다립니다.
    - 실패 시 디버그용 스크린샷/HTML을 assets/captures에 저장합니다.
    """
    query = str(place_query or "").strip()
    if not query:
        return False, "교육 장소명을 먼저 입력해 주세요."

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False, "도로명 주소 가져오기에는 Playwright가 필요합니다. `python -m pip install playwright` 및 `python -m playwright install chromium`을 실행해 주세요."

    map_url = f"https://map.naver.com/p/search/{quote(query)}?c=16.00,0,0,0,dh"
    debug_dir = get_captures_dir()
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            page.goto(map_url, wait_until="domcontentloaded", timeout=70000)
            page.wait_for_timeout(int(max(3.0, float(wait_seconds)) * 1000))

            clicked, click_message = _click_first_naver_place_result(page)
            if not clicked:
                try:
                    page.screenshot(path=str(debug_dir / f"address_click_failed_{stamp}.png"), full_page=True)
                except Exception:
                    pass
                try:
                    (debug_dir / f"address_click_failed_{stamp}.html").write_text(page.content(), encoding="utf-8")
                except Exception:
                    pass
                browser.close()
                return False, click_message

            # entryIframe이 붙고 상세 DOM이 그려질 시간을 줍니다.
            page.wait_for_timeout(2500)
            address = _extract_road_address_from_loaded_naver(page)

            if not address:
                try:
                    page.screenshot(path=str(debug_dir / f"address_extract_failed_{stamp}.png"), full_page=True)
                except Exception:
                    pass
                try:
                    frames_dump = []
                    for frame in page.frames:
                        frame_name = getattr(frame, "name", "") or "no_name"
                        frame_url = getattr(frame, "url", "") or ""
                        try:
                            frame_text = frame.locator("body").inner_text(timeout=1000)[:4000]
                        except Exception:
                            frame_text = ""
                        frames_dump.append(f"\n--- FRAME: {frame_name} ---\nURL: {frame_url}\n{frame_text}")
                    (debug_dir / f"address_extract_failed_{stamp}.txt").write_text("\n".join(frames_dump), encoding="utf-8")
                except Exception:
                    pass

            browser.close()

        if address:
            return True, address.strip()
        return False, (
            "첫 번째 검색 결과 상세 화면까지는 클릭했지만 도로명 주소를 찾지 못했습니다. "
            "assets/captures 폴더의 address_extract_failed 파일을 확인해 주세요."
        )
    except Exception as exc:
        return False, f"도로명 주소 가져오기에 실패했습니다. 상세: {exc}"


def fetch_road_address_callback() -> None:
    ok, result = fetch_naver_road_address(st.session_state.get("place_name", ""))
    if ok:
        st.session_state.road_address = result
        # 가져온 주소는 검색용 주소 필드와 안내문 표시 주소 필드에 같이 넣어줍니다.
        # 이후 사용자가 안내문 표시 주소만 별도로 수정할 수 있습니다.
        st.session_state.display_road_address = result
        place_for_display = str(st.session_state.get("place_name", "") or "").strip()
        if not str(st.session_state.get("display_place_name", "")).strip():
            st.session_state.display_place_name = place_for_display
        if place_for_display:
            st.session_state.display_location_text = f"{place_for_display}  ({result})"
        else:
            st.session_state.display_location_text = result
        st.session_state.last_address_fetch_message = f"도로명 주소를 가져왔습니다: {result}"
    else:
        st.session_state.last_address_fetch_message = result



def capture_naver_map_variants(place_query: str, wait_seconds: float = 1.8) -> dict:
    """네이버 지도 검색 화면만 빠르게 캡처합니다. 주소 추출 로직을 실행하지 않아 상대적으로 빠릅니다."""
    query = str(place_query or "").strip()
    if not query:
        return {"ok": False, "message": "교육 장소명 / 검색어를 먼저 입력해 주세요.", "map_file_paths": {}}

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {"ok": False, "message": "지도 캡처에는 Playwright가 필요합니다. `python -m pip install playwright` 및 `python -m playwright install chromium`을 실행해 주세요.", "map_file_paths": {}}

    try:
        from PIL import Image, ImageStat
    except Exception:
        return {"ok": False, "message": "지도 이미지를 자르려면 Pillow가 필요합니다. `python -m pip install pillow`를 실행해 주세요.", "map_file_paths": {}}

    map_url = f"https://map.naver.com/p/search/{quote(query)}?c=16.00,0,0,0,dh"
    crop_boxes = get_capture_boxes()
    captures_dir = get_captures_dir()
    captures_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
            page.goto(map_url, wait_until="domcontentloaded", timeout=45000)
            try:
                page.wait_for_selector("iframe#searchIframe, canvas, [class*=map], [class*=Map]", timeout=9000)
            except Exception:
                pass
            # 지도 타일이 붙을 최소 시간만 기다립니다. 주소 추출보다 빠른 캡처 전용 경로입니다.
            page.wait_for_timeout(int(max(1.0, float(wait_seconds)) * 1000))
            screenshot_bytes = page.screenshot(type="png", full_page=False, animations="disabled")
            browser.close()

        image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
        width, height = image.size
        map_file_paths = {}
        blank_notes = []
        for variant_name, crop_box in crop_boxes.items():
            left, top, right, bottom = crop_box
            if width < right or height < bottom:
                continue
            cropped = image.crop(crop_box)
            stat = ImageStat.Stat(cropped.resize((120, 96)))
            avg_stddev = sum(stat.stddev) / len(stat.stddev)
            safe_name = "small" if "작은" in variant_name else "normal"
            file_path = captures_dir / f"naver_map_capture_{safe_name}_{stamp}.png"
            cropped.save(file_path, format="PNG")
            map_file_paths[variant_name] = str(file_path)
            if avg_stddev < 3:
                blank_notes.append(variant_name)

        if not map_file_paths:
            return {"ok": False, "message": f"지도 캡처 화면 크기가 예상보다 작습니다. 현재 {width}x{height}입니다.", "map_file_paths": {}}

        message = "지도 이미지를 2가지 크기로 캡처했습니다."
        if blank_notes:
            message += " 단색에 가까운 캡처가 있어 확인이 필요합니다: " + ", ".join(blank_notes)
        return {"ok": True, "message": message, "map_file_paths": map_file_paths}
    except Exception as exc:
        return {"ok": False, "message": f"지도 이미지 가져오기에 실패했습니다. 상세: {exc}", "map_file_paths": {}}


def fetch_naver_road_address_result(place_query: str, wait_seconds: float = 2.5) -> dict:
    """주소만 별도로 가져옵니다. 실패해도 지도 캡처에는 영향을 주지 않도록 dict로 반환합니다."""
    ok, result = fetch_naver_road_address(place_query, wait_seconds=wait_seconds)
    if ok:
        query = str(place_query or "").strip()
        return {
            "ok": True,
            "road_address": result.strip(),
            "display_location_text": format_location_line(query, result),
            "message": f"도로명 주소를 가져왔습니다: {result.strip()}",
        }
    return {"ok": False, "road_address": "", "display_location_text": "", "message": result}


def start_naver_map_background_job() -> None:
    query = str(st.session_state.get("place_name", "") or "").strip()
    if not query:
        st.session_state.naver_map_background_message = "교육 장소명 / 검색어를 먼저 입력해 주세요."
        return
    future = st.session_state.get("naver_map_future")
    if future is not None and not future.done():
        st.session_state.naver_map_background_message = "이미 지도 이미지 가져오기가 실행 중입니다. 잠시 후 결과를 확인해 주세요."
        return
    executor = get_naver_executor()
    st.session_state.naver_map_future = executor.submit(capture_naver_map_variants, query, 1.8)
    st.session_state.naver_map_started_at = time.time()
    st.session_state.naver_map_background_message = "지도 이미지 가져오기를 백그라운드에서 시작했습니다. 다른 입력 작업을 계속할 수 있습니다."


def start_naver_address_background_job() -> None:
    query = str(st.session_state.get("place_name", "") or "").strip()
    if not query:
        st.session_state.naver_address_background_message = "교육 장소명 / 검색어를 먼저 입력해 주세요."
        return
    future = st.session_state.get("naver_address_future")
    if future is not None and not future.done():
        st.session_state.naver_address_background_message = "이미 도로명 주소 가져오기가 실행 중입니다. 잠시 후 결과를 확인해 주세요."
        return
    executor = get_naver_executor()
    st.session_state.naver_address_future = executor.submit(fetch_naver_road_address_result, query, 2.5)
    st.session_state.naver_address_started_at = time.time()
    st.session_state.naver_address_background_message = "도로명 주소 가져오기를 백그라운드에서 시작했습니다. 다른 입력 작업을 계속할 수 있습니다."


def poll_split_naver_jobs() -> None:
    map_future = st.session_state.get("naver_map_future")
    if map_future is not None:
        if not map_future.done():
            started = st.session_state.get("naver_map_started_at", time.time())
            elapsed = int(time.time() - started)
            st.session_state.naver_map_background_message = f"지도 이미지 가져오는 중... 약 {elapsed}초 경과."
        else:
            try:
                result = map_future.result()
            except Exception as exc:
                result = {"ok": False, "message": f"지도 이미지 백그라운드 작업 오류: {exc}", "map_file_paths": {}}
            st.session_state.pop("naver_map_future", None)
            if result.get("map_file_paths"):
                st.session_state.captured_map_files = result["map_file_paths"]
                selected = st.session_state.get("selected_map_capture_variant", "일반 크기 (1200×960)")
                chosen_path = result["map_file_paths"].get(selected) or result["map_file_paths"].get("일반 크기 (1200×960)") or next(iter(result["map_file_paths"].values()))
                st.session_state.captured_map_file_path = chosen_path
                st.session_state.captured_map_data_url = ""
                st.session_state.last_captured_map_file = chosen_path
                st.session_state.last_map_capture_message = "지도 이미지를 2가지 크기로 자동 캡처했습니다. 아래에서 사용할 크기를 선택할 수 있습니다."
            st.session_state.naver_map_background_message = result.get("message", "지도 이미지 작업이 완료되었습니다.")

    address_future = st.session_state.get("naver_address_future")
    if address_future is not None:
        if not address_future.done():
            started = st.session_state.get("naver_address_started_at", time.time())
            elapsed = int(time.time() - started)
            st.session_state.naver_address_background_message = f"도로명 주소 가져오는 중... 약 {elapsed}초 경과."
        else:
            try:
                result = address_future.result()
            except Exception as exc:
                result = {"ok": False, "message": f"도로명 주소 백그라운드 작업 오류: {exc}", "road_address": "", "display_location_text": ""}
            st.session_state.pop("naver_address_future", None)
            if result.get("road_address"):
                st.session_state.road_address = result["road_address"]
                st.session_state.last_address_fetch_message = f"도로명 주소를 가져왔습니다: {result['road_address']}"
            if result.get("display_location_text"):
                st.session_state.display_location_text = result["display_location_text"]
            st.session_state.naver_address_background_message = result.get("message", "도로명 주소 작업이 완료되었습니다.")


@st.cache_resource
def get_naver_executor() -> ThreadPoolExecutor:
    """네이버 지도/주소 자동화 작업을 백그라운드에서 실행합니다."""
    return ThreadPoolExecutor(max_workers=2)


def get_capture_boxes() -> dict[str, tuple[int, int, int, int]]:
    return {
        "작은 크기 (1000×800)": (685, 167, 1685, 967),
        "일반 크기 (1200×960)": (585, 87, 1785, 87 + 960),
    }


def format_location_line(place: str, address: str) -> str:
    clean_place = str(place or "").strip()
    clean_address = str(address or "").strip()
    if clean_place and clean_address:
        return f"{clean_place}  ({clean_address})"
    return clean_place or clean_address


def capture_naver_map_and_address(place_query: str, wait_seconds: float = 3.0) -> dict:
    """
    네이버 지도 검색 URL을 한 번만 열어서 지도 이미지 2종(작은/일반)을 먼저 캡처하고,
    그 다음 첫 번째 결과를 클릭해 도로명 주소를 가져옵니다.
    """
    query = str(place_query or "").strip()
    if not query:
        return {"ok": False, "message": "교육 장소명을 먼저 입력해 주세요."}

    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {"ok": False, "message": "Playwright가 필요합니다. `python -m pip install playwright` 및 `python -m playwright install chromium`을 실행해 주세요."}

    try:
        from PIL import Image, ImageStat
    except Exception:
        return {"ok": False, "message": "Pillow가 필요합니다. `python -m pip install pillow`를 실행해 주세요."}

    map_url = f"https://map.naver.com/p/search/{quote(query)}?c=16.00,0,0,0,dh"
    crop_boxes = get_capture_boxes()
    debug_dir = get_captures_dir()
    debug_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "ok": False,
        "message": "",
        "map_file_path": "",
        "map_file_paths": {},
        "road_address": "",
        "display_location_text": "",
    }

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
            page.goto(map_url, wait_until="domcontentloaded", timeout=50000)

            # 지도/검색 UI가 최소한 붙을 때까지만 기다립니다. 오래 기다리는 networkidle은 피합니다.
            try:
                page.wait_for_selector("iframe#searchIframe, canvas, [class*=map], [class*=Map]", timeout=12000)
            except Exception:
                pass
            page.wait_for_timeout(int(max(2.0, float(wait_seconds)) * 1000))

            # 1) 상세 클릭 전, 지도 화면을 먼저 1회 캡처한 뒤 두 크기로 잘라 저장합니다.
            screenshot_bytes = page.screenshot(type="png", full_page=False, animations="disabled")
            image = Image.open(io.BytesIO(screenshot_bytes)).convert("RGB")
            width, height = image.size
            blank_notes = []
            for variant_name, crop_box in crop_boxes.items():
                left, top, right, bottom = crop_box
                if width >= right and height >= bottom:
                    cropped = image.crop(crop_box)
                    stat = ImageStat.Stat(cropped.resize((120, 96)))
                    avg_stddev = sum(stat.stddev) / len(stat.stddev)
                    safe_name = "small" if "작은" in variant_name else "normal"
                    file_name = f"naver_map_capture_{safe_name}_{stamp}.png"
                    file_path = debug_dir / file_name
                    cropped.save(file_path, format="PNG")
                    result["map_file_paths"][variant_name] = str(file_path)
                    if not result["map_file_path"] and "일반" in variant_name:
                        result["map_file_path"] = str(file_path)
                    if avg_stddev < 3:
                        blank_notes.append(variant_name)
                else:
                    result["message"] += f"{variant_name} 캡처 화면 크기가 부족합니다. 현재 {width}x{height}. "
            if not result["map_file_path"] and result["map_file_paths"]:
                result["map_file_path"] = next(iter(result["map_file_paths"].values()))
            if blank_notes:
                result["message"] += "일부 지도 이미지가 거의 단색으로 감지됩니다: " + ", ".join(blank_notes) + ". "

            # 2) 지도 캡처 이후 첫 번째 검색 결과 클릭 → 상세 주소 추출
            clicked, click_message = _click_first_naver_place_result(page)
            if clicked:
                page.wait_for_timeout(1600)
                address = _extract_road_address_from_loaded_naver(page)
                if address:
                    result["road_address"] = address.strip()
                    result["display_location_text"] = format_location_line(query, address)
                else:
                    try:
                        frames_dump = []
                        for frame in page.frames:
                            frame_name = getattr(frame, "name", "") or "no_name"
                            frame_url = getattr(frame, "url", "") or ""
                            try:
                                frame_text = frame.locator("body").inner_text(timeout=800)[:2500]
                            except Exception:
                                frame_text = ""
                            frames_dump.append(f"\n--- FRAME: {frame_name} ---\nURL: {frame_url}\n{frame_text}")
                        (debug_dir / f"combined_address_extract_failed_{stamp}.txt").write_text("\n".join(frames_dump), encoding="utf-8")
                    except Exception:
                        pass
                    result["message"] += "상세 화면에서 도로명 주소를 찾지 못했습니다. "
            else:
                result["message"] += click_message + " "

            browser.close()

        if result["map_file_paths"] or result["road_address"]:
            result["ok"] = True
            details = []
            if result["map_file_paths"]:
                details.append("지도 2종 캡처 완료")
            if result["road_address"]:
                details.append(f"주소 가져오기 완료: {result['road_address']}")
            result["message"] = (" / ".join(details) + (" " + result["message"] if result["message"] else "")).strip()
        else:
            result["ok"] = False
            result["message"] = result["message"] or "지도 캡처와 도로명 주소 가져오기에 모두 실패했습니다."
        return result
    except Exception as exc:
        return {"ok": False, "message": f"지도/주소 동시 가져오기에 실패했습니다. 상세: {exc}"}


def start_naver_background_job() -> None:
    query = str(st.session_state.get("place_name", "") or "").strip()
    if not query:
        st.session_state.naver_background_message = "교육 장소명 / 검색어를 먼저 입력해 주세요."
        return
    future = st.session_state.get("naver_combined_future")
    if future is not None and not future.done():
        st.session_state.naver_background_message = "이미 지도/주소 가져오기가 실행 중입니다. 잠시 후 결과를 확인해 주세요."
        return
    executor = get_naver_executor()
    st.session_state.naver_combined_future = executor.submit(
        capture_naver_map_and_address,
        query,
        2.6,
    )
    st.session_state.naver_background_message = "지도 캡처와 도로명 주소 가져오기를 백그라운드에서 시작했습니다. 다른 입력값을 계속 수정해도 됩니다."
    st.session_state.naver_combined_started_at = time.time()


def poll_naver_background_job() -> None:
    future = st.session_state.get("naver_combined_future")
    if future is None:
        return
    if not future.done():
        started = st.session_state.get("naver_combined_started_at", time.time())
        elapsed = int(time.time() - started)
        st.session_state.naver_background_message = f"지도/주소 가져오는 중... 약 {elapsed}초 경과. 다른 입력 작업을 계속할 수 있습니다."
        return
    try:
        result = future.result()
    except Exception as exc:
        result = {"ok": False, "message": f"백그라운드 작업 오류: {exc}"}
    st.session_state.pop("naver_combined_future", None)
    if result.get("map_file_paths"):
        st.session_state.captured_map_files = result["map_file_paths"]
        selected = st.session_state.get("selected_map_capture_variant", "일반 크기 (1200×960)")
        chosen_path = result["map_file_paths"].get(selected) or result.get("map_file_path") or next(iter(result["map_file_paths"].values()))
        st.session_state.captured_map_file_path = chosen_path
        st.session_state.captured_map_data_url = ""
        st.session_state.last_captured_map_file = chosen_path
        st.session_state.last_map_capture_message = "지도 이미지를 2가지 크기로 자동 캡처했습니다. 아래에서 사용할 크기를 선택할 수 있습니다."
    elif result.get("map_file_path"):
        st.session_state.captured_map_file_path = result["map_file_path"]
        st.session_state.captured_map_data_url = ""
        st.session_state.last_captured_map_file = result["map_file_path"]
        st.session_state.last_map_capture_message = "지도 이미지를 자동 캡처해 미리보기에 적용했습니다."
    if result.get("road_address"):
        st.session_state.road_address = result["road_address"]
        st.session_state.last_address_fetch_message = f"도로명 주소를 가져왔습니다: {result['road_address']}"
    if result.get("display_location_text"):
        st.session_state.display_location_text = result["display_location_text"]
    st.session_state.naver_background_message = result.get("message", "작업이 완료되었습니다.")


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
    "header_text": "컬러박스 내 글자색",
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

    .mini-loading {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 8px 0 10px 0;
        padding: 9px 11px;
        border: 1px solid #3A3A3A;
        border-radius: 12px;
        background: #141414;
        color: #D6D6D6;
        font-size: 12px;
        line-height: 18px;
    }

    .mini-spinner {
        width: 14px;
        height: 14px;
        border: 2px solid #565656;
        border-top-color: #FFFFFF;
        border-radius: 50%;
        display: inline-block;
        animation: mini-spin 0.8s linear infinite;
        flex: 0 0 auto;
    }

    @keyframes mini-spin {
        to { transform: rotate(360deg); }
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


def parse_curriculum_columns(columns_text: str) -> list[str]:
    """쉼표 또는 줄바꿈으로 입력한 커리큘럼 열 이름을 정리합니다."""
    raw = str(columns_text or "").replace("\n", ",")
    columns = []
    for part in raw.split(","):
        col = part.strip()
        if col and col not in columns:
            columns.append(col)
    return columns or ["시간", "일차", "교육 내용", "강사/비고"]




def parse_curriculum_column_defs(column_defs: object) -> list[str]:
    """data_editor에서 편집한 열 이름 목록을 실제 커리큘럼 컬럼명으로 변환합니다."""
    columns = []
    for row in to_records(column_defs):
        col = str(row.get("column_name", "") or row.get("열 이름", "") or row.get("name", "")).strip()
        if col and col not in columns:
            columns.append(col)
    return columns or ["시간", "일차", "교육 내용", "강사/비고"]


def _cell_value_by_column(row: dict, column: str) -> str:
    aliases = {
        "시간": ["시간", "time"],
        "일차": ["일차", "day"],
        "교육 내용": ["교육 내용", "과정 내용", "subject"],
        "강사/비고": ["강사/비고", "비고", "강사", "speaker"],
    }
    keys = aliases.get(column, [column])
    for key in keys:
        if key in row and str(row.get(key, "") or "").strip():
            return str(row.get(key, "") or "").strip()
    return str(row.get(column, "") or "").strip()


def normalize_curriculum_for_columns(curriculum: list[dict], columns: list[str]) -> list[dict]:
    records = []
    for row in to_records(curriculum):
        normalized = {column: _cell_value_by_column(row, column) for column in columns}
        if any(str(value or "").strip() for value in normalized.values()):
            records.append(normalized)
    if not records:
        records = [{column: "" for column in columns}]
    return records


def build_curriculum_header(columns: list[str], main_color: str, text_color: str) -> str:
    header_cells = ""
    total = len(columns)
    for idx, column in enumerate(columns):
        border = "border-right: 1px solid #74787C;" if idx < total - 1 else ""
        header_cells += f"""
                    <th style="padding: 12px 10px; background-color: {main_color}; color: {text_color}; font-size: 15px; line-height: 20px; font-weight: 700; text-align: center; {border}">{esc(column)}</th>"""
    return f"""
                <tr data-zone="curriculum brand header_text">{header_cells}
                </tr>"""


def build_curriculum_rows(curriculum: list[dict], columns: list[str] | None = None) -> str:
    columns = columns or ["시간", "일차", "교육 내용", "강사/비고"]
    rows = ""
    normalized_records = normalize_curriculum_for_columns(curriculum, columns)

    for row in normalized_records:
        if not any(str(row.get(column, "") or "").strip() for column in columns):
            continue
        cells = ""
        for idx, column in enumerate(columns):
            value = _cell_value_by_column(row, column)
            is_long_text = any(token in column for token in ["내용", "주제", "과정", "비고", "메모"])
            align = "left" if is_long_text else "center"
            weight = "700" if is_long_text else "500"
            border = "border-right: 1px solid #D8DEE6;" if idx < len(columns) - 1 else ""
            cells += f"""
            <td style="padding: 13px 10px; border-bottom: 1px solid #D8DEE6; {border} background-color: #FFFFFF; font-size: 14px; color: #1F2933; text-align: {align}; line-height: 20px; font-weight: {weight};">
                {esc(value) if value else "-"}
            </td>"""
        rows += f"""
        <tr>{cells}
        </tr>
        """

    return rows or f"""
        <tr>
            <td colspan="{len(columns)}" style="padding: 18px 10px; border-bottom: 1px solid #D8DEE6; background-color: #FFFFFF; font-size: 14px; color: #6B7280; text-align: center;">
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
    road_address: str,
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
    curriculum_columns_text: str = "시간, 일차, 교육 내용, 강사/비고",
    curriculum_title: str = "상세 커리큘럼",
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
    location_lines = []
    for location_part in [place_name, road_address]:
        for location_line in str(location_part or "").splitlines():
            clean_location_line = location_line.strip()
            if clean_location_line and clean_location_line not in location_lines:
                location_lines.append(clean_location_line)
    curriculum_columns = parse_curriculum_columns(curriculum_columns_text)
    curriculum_header_html = build_curriculum_header(curriculum_columns, main_color, curr_header_text_color)
    curriculum_html = build_curriculum_rows(edited_curriculum, curriculum_columns)
    curriculum_title_html = ""
    if str(curriculum_title or "").strip():
        curriculum_title_html = f"""
        <p style="margin: 4px 0 8px 0; font-size: 15px; line-height: 21px; color: #222222; font-weight: 800;">{esc(curriculum_title)}</p>
        """
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

        {curriculum_title_html}
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="curriculum" style="width: 100%; border-collapse: collapse; margin: 10px 0 34px 0; border-top: 1px solid #D8DEE6; border-left: 1px solid #D8DEE6; background-color: #FFFFFF;">
            <thead>
                {curriculum_header_html}
            </thead>
            <tbody style="background-color: #FFFFFF;">
                {curriculum_html}
            </tbody>
        </table>

        {build_section_title(2, "교육 장소", main_color, curr_header_text_color, "location")}

        <table role="presentation" cellspacing="0" cellpadding="0" border="0" data-zone="location" style="width: 100%; border-collapse: collapse; margin: 0 0 32px 0;">
            {build_bullet_rows(location_lines, text_color=section_text_color)}
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
poll_split_naver_jobs()

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
            st.markdown("#### 장소")

            place_name = st.text_input("교육 장소명 / 검색어", key="place_name")

            naver_map_query = quote(str(place_name or "").strip())
            naver_map_url = f"https://map.naver.com/p/search/{naver_map_query}?c=16.00,0,0,0,dh" if naver_map_query else "https://map.naver.com/p/search/"
            st.markdown(
                f'<a class="naver-map-button" href="{naver_map_url}" target="_blank" rel="noopener noreferrer">🗺️ 네이버 지도 바로가기</a>',
                unsafe_allow_html=True,
            )

            col_auto1, col_auto2 = st.columns(2)
            with col_auto1:
                st.button(
                    "🖼️ 지도 이미지 가져오기",
                    use_container_width=True,
                    on_click=start_naver_map_background_job,
                    help="주소 추출 없이 지도 화면만 캡처합니다. 두 가지 크기를 동시에 저장하므로 기존 통합 기능보다 빠르게 끝날 가능성이 큽니다.",
                )
            with col_auto2:
                st.button(
                    "📍 도로명 주소 가져오기",
                    use_container_width=True,
                    on_click=start_naver_address_background_job,
                    help="첫 번째 검색 결과를 클릭해 도로명 주소만 가져옵니다. 네이버 상세 페이지 로딩 때문에 지도 캡처보다 오래 걸릴 수 있습니다.",
                )

            if st.button("🧹 지도/주소 결과 비우기", use_container_width=True):
                st.session_state.road_address = ""
                st.session_state.captured_map_data_url = ""
                st.session_state.captured_map_file_path = ""
                st.session_state.pop("last_captured_map_file", None)
                st.session_state.pop("captured_map_files", None)
                st.session_state.pop("naver_map_future", None)
                st.session_state.pop("naver_address_future", None)
                st.session_state.last_map_capture_message = "캡처 지도를 제거했습니다."
                st.session_state.last_address_fetch_message = "도로명 주소를 비웠습니다."
                st.session_state.naver_map_background_message = "지도 결과를 비웠습니다."
                st.session_state.naver_address_background_message = "주소 결과를 비웠습니다."

            map_background_message = st.session_state.get("naver_map_background_message", "")
            if map_background_message:
                st.caption(map_background_message)
            if st.session_state.get("naver_map_future") is not None:
                st.markdown(
                    '<div class="mini-loading"><span class="mini-spinner"></span><span>지도 이미지를 가져오는 중입니다. 다른 입력 작업을 계속할 수 있습니다.</span></div>',
                    unsafe_allow_html=True,
                )

            address_background_message = st.session_state.get("naver_address_background_message", "")
            if address_background_message:
                st.caption(address_background_message)
            if st.session_state.get("naver_address_future") is not None:
                st.markdown(
                    '<div class="mini-loading"><span class="mini-spinner"></span><span>도로명 주소를 가져오는 중입니다. 다른 입력 작업을 계속할 수 있습니다.</span></div>',
                    unsafe_allow_html=True,
                )

            road_address = st.text_input(
                "가져온 도로명 주소",
                key="road_address",
                help="네이버 지도에서 자동으로 가져온 주소입니다. 최종 안내문 문구는 아래 '안내문 표시 내용'에서 직접 수정할 수 있습니다.",
            )
            last_address_fetch_message = st.session_state.get("last_address_fetch_message", "")
            if last_address_fetch_message:
                st.caption(last_address_fetch_message)

            captured_map_files = st.session_state.get("captured_map_files", {}) or {}
            if captured_map_files:
                variant_options = [name for name in ["작은 크기 (1000×800)", "일반 크기 (1200×960)"] if name in captured_map_files]
                variant_options += [name for name in captured_map_files.keys() if name not in variant_options]
                selected_variant = st.selectbox(
                    "사용할 지도 이미지 크기",
                    variant_options,
                    key="selected_map_capture_variant",
                    help="자동 캡처 시 두 가지 크기로 저장됩니다. 여기서 안내문에 넣을 이미지를 고르면 됩니다.",
                )
                captured_map_path = captured_map_files.get(selected_variant, "")
                st.session_state.captured_map_file_path = captured_map_path
                st.session_state.last_captured_map_file = captured_map_path
            else:
                captured_map_path = st.session_state.get("captured_map_file_path", "") or st.session_state.get("last_captured_map_file", "")
            captured_map_data_url = file_path_to_data_url(captured_map_path) or st.session_state.get("captured_map_data_url", "")
            last_map_capture_message = st.session_state.get("last_map_capture_message", "")
            if last_map_capture_message:
                st.caption(last_map_capture_message)
            if captured_map_data_url:
                st.image(captured_map_data_url, caption="자동 캡처된 지도 이미지", use_container_width=True)
                st.caption("현재 지도 영역에는 선택한 자동 캡처 이미지가 적용됩니다. 다른 이미지를 직접 첨부하면 첨부 이미지가 우선 적용됩니다.")

            display_location_text = st.text_area(
                "안내문 표시 내용",
                key="display_location_text",
                height=80,
                help="최종 HTML/이미지 안내문의 교육 장소 영역에 들어갈 문구입니다. 예: 멀티캠퍼스 선릉  (서울 강남구 선릉로 428)",
            )

            map_file = st.file_uploader(
                "지도 이미지 첨부",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                help="캡처 기능이 환경상 동작하지 않을 때는 직접 저장한 지도 이미지를 첨부해 주세요.",
                key="map_file_uploader",
            )
            map_image_src = file_to_data_url(map_file) or captured_map_data_url

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
            date_range = st.text_input("교육 일정 (예: 6/16(월)~6/17(화))", key="date_range")
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
                "컬러박스 내 글자색",
                key="curr_header_text_color_picker",
            )
            section_text_color = "#000000"
            st.caption("본문 글자색은 검정색으로 고정됩니다. 위 색상은 브랜드 컬러 박스 안의 글자에 적용됩니다.")

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
            st.markdown("#### 커리큘럼")
            curriculum_title = st.text_input("커리큘럼 표 이름", key="curriculum_title")
            curriculum_columns_text = st.text_area(
                "표 헤더명",
                key="curriculum_columns_text",
                height=88,
                help="쉼표 또는 줄바꿈으로 열 이름을 입력하세요. 예: 시간, 일차, 교육 내용, 강사/비고. 줄을 추가/삭제하면 표 열도 같이 추가/삭제됩니다.",
            )
            curriculum_columns = parse_curriculum_columns(curriculum_columns_text)
            st.session_state.curriculum_column_defs = [{"column_name": col} for col in curriculum_columns]

            curriculum_editor_data = normalize_curriculum_for_columns(st.session_state.curriculum, curriculum_columns)
            edited_curr = st.data_editor(
                curriculum_editor_data,
                num_rows="dynamic",
                column_order=curriculum_columns,
                column_config={column: column for column in curriculum_columns},
                width="stretch",
                key="curr_editor",
            )
            st.session_state.curriculum = to_records(edited_curr)

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
    place_name=display_location_text,
    road_address="",
    map_image_src=map_image_src,
    delivery_type=delivery_type,
    welcome_title=welcome_title,
    welcome_body_text=welcome_body_text,
    time_notice_text=time_notice_text,
    edited_curriculum=edited_curr,
    curriculum_columns_text=curriculum_columns_text,
    curriculum_title=curriculum_title,
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
