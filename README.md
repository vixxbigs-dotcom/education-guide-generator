🌍 Live Demo
🔗 [https://vixxbigs-dotcom.github.io/newsletter-automation/](https://education-guide-generator-hqc7rk2uxappau4bettiix8.streamlit.app/)✉️ 교육 안내문 생성 도구

## ✉️ 교육 안내문 생성 도구

### Education Guide Generator

> Streamlit 기반 교육 안내문 자동 생성 도구
> 반복적으로 작성하던 교육 안내 메일을 **HTML, PNG, JPG 형태로 빠르게 생성**할 수 있도록 만든 업무 자동화 프로젝트입니다.
> 
<img width="4000" height="2250" alt="교육안내 문설명_pages-to-jpg-0006" src="https://github.com/user-attachments/assets/1b9d13a7-db9d-4842-acbd-5f9d64023a8d" />
<img width="4000" height="2250" alt="교육안내 문설명_pages-to-jpg-0008" src="https://github.com/user-attachments/assets/d0c59f40-d147-4aa8-abbe-17d303dcd1e9" />

---

## 📌 프로젝트 소개

교육 운영 업무에서는 매 과정마다 안내 메일을 반복해서 작성해야 합니다.

교육명, 일정, 장소, 커리큘럼, 문의처, 지도 이미지, 안내사항 등을 매번 수동으로 입력하고 서식을 맞추는 과정은 시간이 오래 걸리고, 담당자마다 결과물의 디자인도 달라질 수 있습니다.

이 프로젝트는 이러한 반복 작업을 줄이기 위해 제작한 **교육 안내문 자동 생성기**입니다.

사용자는 입력 폼에 필요한 정보를 입력하고, 실시간 미리보기를 확인한 뒤, Outlook 메일 본문용 HTML 또는 이미지 파일로 안내문을 내보낼 수 있습니다.

---

## ✨ 주요 기능

### 📝 교육 안내문 정보 입력

* 회사명
* 교육 과정명
* 운영 방식
* 교육 일정
* 교육 시작 시간
* 교육 장소
* 안내 사항
* 관련 문의처

입력한 내용은 우측 미리보기에 자동 반영됩니다.

---

### 📚 커리큘럼 표 편집

* Streamlit Data Editor 기반 커리큘럼 편집
* 행 추가 및 삭제
* 표 헤더명 수정
* 입력값 기반 HTML 표 자동 생성

교육 일정표를 별도로 디자인하지 않아도, 입력값을 기준으로 안내문 안에 정리된 표가 생성됩니다.

---

### 🗺️ 장소 정보 및 지도 이미지 관리

* 교육 장소 검색어 입력
* 안내문에 표시할 장소 문구 직접 수정
* 지도 이미지 직접 첨부
* 네이버 지도 바로가기 제공
* Playwright 기반 지도 캡처 및 주소 추출 기능 지원

> 지도 자동 캡처 및 도로명 주소 추출 기능은 네이버 지도 페이지 로딩 상태에 따라 속도와 성공 여부가 달라질 수 있습니다.
> 실무 사용 시에는 지도 이미지를 직접 첨부하는 방식이 가장 안정적입니다.

---

### 🎨 디자인 커스터마이징

* 브랜드 메인 컬러 설정
* 하단 포인트 컬러 설정
* 컬러박스 내 글자색 변경
* 로고 이미지 첨부
* 로고 위치 조정
* 폰트 선택
* `assets/fonts` 폴더 기반 커스텀 폰트 사용

회사나 과정별 디자인 톤에 맞게 안내문 스타일을 조정할 수 있습니다.

---

### 👀 실시간 미리보기

입력한 내용은 우측 미리보기 영역에서 바로 확인할 수 있습니다.

* HTML 안내문 미리보기
* 출력 결과 확인
* 미리보기 배율 조정
* 우측 미리보기 영역 고정

수정 결과를 즉시 확인하면서 안내문을 완성할 수 있습니다.

---

### 📤 출력 기능

생성된 안내문은 다양한 방식으로 내보낼 수 있습니다.

* Outlook 메일 본문용 HTML 복사
* HTML 파일 다운로드
* PNG 이미지 저장
* JPG 이미지 저장
* 내보낼 파일명 직접 지정

---

## 🛠️ 기술 스택

| 구분                 | 사용 기술                 |
| ------------------ | --------------------- |
| Language           | Python                |
| Web UI             | Streamlit             |
| Markup             | HTML / CSS            |
| Table Editor       | Streamlit Data Editor |
| Browser Automation | Playwright            |
| Image Processing   | Pillow                |
| Frontend Capture   | html2canvas           |
| Async Processing   | ThreadPoolExecutor    |
| Map                | NAVER Map             |

---

## 📂 프로젝트 구조

```text
education-guide-generator/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── assets/
    ├── fonts/
    │   └── 사용자 폰트 파일
    │
    └── captures/
        └── 자동 생성된 지도 캡처 이미지
```

---

## 🚀 실행 방법

### 1. 저장소 클론

```bash
git clone https://github.com/vixxbigs-dotcom/education-guide-generator.git
cd education-guide-generator
```

---

### 2. 가상환경 생성

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac / Linux:

```bash
source .venv/bin/activate
```

---

### 3. 패키지 설치

```bash
python -m pip install -r requirements.txt
```

---

### 4. Playwright 브라우저 설치

지도 자동 캡처 기능을 사용할 경우 아래 명령어를 실행합니다.

```bash
python -m playwright install chromium
```

지도 자동 캡처 기능을 사용하지 않고, 지도 이미지를 직접 첨부할 경우 이 단계는 생략할 수 있습니다.

---

### 5. 앱 실행

```bash
python -m streamlit run app.py
```

---

## 🔤 커스텀 폰트 사용 방법

프로젝트 폴더 안에 아래와 같이 폰트 파일을 넣으면 앱에서 선택할 수 있습니다.

```text
assets/
└── fonts/
    ├── NanumGothic.ttf
    ├── NanumSquare.ttf
    └── Pretendard-Regular.ttf
```

지원 확장자:

```text
.ttf / .otf / .woff / .woff2
```

> 단, Outlook 메일 본문에서는 수신자 PC 환경에 따라 커스텀 폰트가 기본 글꼴로 대체될 수 있습니다.
> 메일 발송용으로는 `맑은 고딕`, `Arial`, `Pretendard`처럼 일반적으로 사용 가능한 글꼴을 권장합니다.

---

## 🖼️ 지도 이미지 사용 안내

지도 이미지는 두 가지 방식으로 사용할 수 있습니다.

### 1. 직접 첨부 방식

네이버 지도에서 원하는 화면을 직접 캡처한 뒤, 앱의 지도 이미지 첨부 영역에 업로드합니다.

가장 안정적이고 빠른 방식입니다.

### 2. 자동 캡처 방식

Playwright를 활용해 네이버 지도 화면을 자동으로 열고 캡처합니다.

다만 네이버 지도 페이지 로딩 속도, 네트워크 상태, 브라우저 환경에 따라 시간이 오래 걸릴 수 있습니다.

---

## 💡 개발 목적

이 프로젝트는 교육 운영자가 반복적으로 수행하는 안내문 작성 업무를 자동화하기 위해 개발되었습니다.

주요 목표는 다음과 같습니다.

* 교육 안내 메일 작성 시간 단축
* 반복 입력 업무 최소화
* 안내문 디자인 일관성 확보
* Outlook 메일 발송용 HTML 생성
* 이미지 파일 형태의 안내문 저장 지원
* 비개발자도 사용할 수 있는 입력 기반 자동화 도구 구현

---

## 🔮 개선 예정 사항

* 네이버 지역 검색 API 연동
* 검색 결과 후보 카드 UI 제공
* 선택한 장소 기반 도로명 주소 자동 입력
* Static Map API 기반 지도 이미지 생성
* Playwright 지도 캡처 기능 경량화 또는 선택 기능화
* 코드 모듈화 및 유지보수 구조 개선

---

## 📄 License

Personal Project © 2026
