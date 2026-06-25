# ✉️ 교육 안내문 자동 생성기 (Education Guide Generator)

> **Streamlit 기반 교육 안내문 자동 생성 도구**
>
> 교육 운영자가 반복적으로 작성하던 교육 안내 메일을 **몇 분 만에 HTML + 이미지 형태로 자동 생성**할 수 있는 업무 자동화 프로젝트입니다.

---

# 📌 프로젝트 소개

매번 교육이 열릴 때마다...

* 교육 일정 입력
* 교육 장소 입력
* 커리큘럼 작성
* 지도 캡처
* 문의처 정리
* 메일 서식 작성

을 반복하는 것은 매우 번거롭습니다.

이 프로젝트는 이러한 반복 업무를 자동화하여 **Outlook 메일 본문용 HTML과 안내문 이미지를 한 번에 생성**합니다.

![alt text](image-1.png)
![alt text](image-2.png)

---

# ✨ 주요 기능

### 📝 교육 정보 입력

* 회사명
* 교육명
* 운영 방식
* 교육 일정
* 교육 시작 시간

---

### 📚 커리큘럼 편집

* Data Editor 기반 실시간 수정
* 행 추가/삭제
* 컬럼명 변경
* 자동 표 생성

---

### 🗺️ 네이버 지도 자동화

Playwright를 활용하여

✅ 지도 자동 캡처

✅ 도로명 주소 자동 추출

을 지원합니다.

별도의 캡처 프로그램 없이 안내문에 바로 사용할 수 있습니다.

---

### 🎨 디자인 커스터마이징

* 브랜드 컬러 변경
* 컬러 스포이드(EyeDropper API)
* 로고 삽입
* 폰트 변경
* 안내문 색상 변경

회사별 디자인에 맞춰 손쉽게 수정할 수 있습니다.

---

### 👀 실시간 미리보기

입력과 동시에

* HTML 안내문
* 최종 결과

를 실시간으로 확인할 수 있습니다.

---

### 📤 다양한 출력 방식

한 번 생성하면

📋 Outlook 메일 본문 복사

🖼️ PNG 저장

🖼️ JPG 저장

📄 HTML 다운로드

를 모두 지원합니다.

---

# 🛠️ 기술 스택

| 분야       | 사용 기술              |
| -------- | ------------------ |
| Frontend | Streamlit          |
| Language | Python             |
| HTML     | HTML/CSS           |
| 지도 자동화   | Playwright         |
| 이미지 처리   | Pillow             |
| 비동기      | ThreadPoolExecutor |
| 이미지 생성   | html2canvas        |
| 지도       | NAVER Map          |

---

# 📂 프로젝트 구조

```text
education-guide-generator
│
├── app.py
├── assets
│   ├── fonts
│   └── captures
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 실행 방법

### 1️⃣ 저장소 클론

```bash
git clone https://github.com/vixxbigs-dotcom/education-guide-generator.git
```

---

### 2️⃣ 가상환경 생성

```bash
python -m venv .venv
```

Windows

```bash
.venv\Scripts\activate
```

Mac/Linux

```bash
source .venv/bin/activate
```

---

### 3️⃣ 패키지 설치

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Playwright 설치

```bash
python -m playwright install chromium
```

---

### 5️⃣ 실행

```bash
streamlit run app.py
```

---

# 📸 주요 기능

* ✉️ 교육 안내문 자동 생성
* 🗺️ 네이버 지도 자동 캡처
* 📍 도로명 주소 자동 추출
* 🎨 브랜드 컬러 적용
* 🖼️ 로고 삽입
* 📋 Outlook HTML 복사
* 🖼️ PNG/JPG 저장
* 📄 HTML 다운로드
* 📚 커리큘럼 자동 표 생성

---

# 💡 개발 목적

반복적인 교육 운영 업무를 자동화하여

* 작업 시간을 단축하고
* 입력 오류를 줄이며
* 일관된 디자인의 안내문을 생성하는 것을 목표로 개발했습니다.

---

# 📄 License

Personal Project © 2026
