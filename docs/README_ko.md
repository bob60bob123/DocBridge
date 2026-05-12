# DocBridge

**OCR 기능이 내장된 가벼운 문서 형식 변환 도구.**

PDF, DOCX, DOC, TXT와 Markdown 간의 양방향 변환을 지원합니다. 스캔 문서 및 이미지 기반 PDF에서 텍스트를 자동으로 감지하고 추출할 수 있습니다.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 주요 기능

- **다양한 형식 지원** — PDF, DOCX, DOC, TXT ↔ Markdown, Markdown → PDF/DOCX
- **스마트 OCR** — 스캔 문서 및 이미지 기반 PDF의 텍스트를 자동 인식
- **3가지 인터페이스** — 데스크톱 GUI(PyQt5), 웹 GUI(Gradio), CLI
- **일괄 처리** — 폴더 재귀 스캔 지원
- **크로스 플랫폼** — Windows, Linux, macOS

---

## 지원 형식

| 입력 | 출력 | 설명 |
|-----|-----|------|
| PDF | MD | 텍스트/벡터 폰트 PDF는 자동 처리 |
| PDF | MD | **스캔/이미지 기반 PDF는 OCR 자동 인식** |
| DOCX | MD | Word 문서 |
| DOC | MD | 레거시 Word 형식 |
| TXT | MD | 일반 텍스트 |
| MD | PDF | WeasyPrint 필요 |
| MD | DOCX | Word 문서 |

---

## 빠른 시작

### 환경 요구사항

- Python 3.11+
- Windows 10/11 / Linux / macOS

### 의존성 설치

```bash
pip install -r requirements.txt
```

### 원클릭 실행 (Windows)

`start.bat` 더블클릭으로 데스크톱 GUI 실행.

### 기타 실행 방법

```bash
# 데스크톱 GUI (권장)
python src/gui_qt.py

# 웹 인터페이스
python src/gui.py

#命令行
python -m src.cli convert input.pdf output.md
python -m src.cli batch "*.pdf" ./output/
```

---

## OCR 동작 원리

PDF가 **이미지 기반(스캔)** 또는 **벡터 폰트 이상**으로 감지되면 자동으로 OCR 모드로 전환:

1. **자동 감지** — PDF 텍스트 함량 분석, 페이지당 평균 100자 미만 시 OCR 트리거
2. **페이지 렌더링** — PyMuPDF로 각 페이지를 150 DPI 고해상도 이미지로 렌더링
3. **텍스트 인식** — RapidOCR이 이미지에서 텍스트 추출(중국어, 영어, 다국어 지원)
4. **구조 재구성** — 읽기 순서로 텍스트 블록 정리, 제목/목록/단락 식별
5. **출력** — 구조화된 Markdown 파일 생성

---

## 라이선스

MIT License — 자세한 내용은 [LICENSE](LICENSE) 참고
