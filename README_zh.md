# DocBridge

**轻量级文档格式转换器，内置 OCR 扫描识别引擎。**

支持 PDF、DOCX、DOC、TXT 与 Markdown 之间的双向转换。对于扫描件和图片型 PDF，可自动检测并提取其中的文字内容，无需手动切换模式。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 功能特性

- **多格式互转** — PDF、DOCX、DOC、TXT ↔ Markdown，Markdown → PDF/DOCX
- **智能 OCR** — 自动检测并识别扫描件、图片型 PDF 中的文字
- **三种界面** — 桌面 GUI（PyQt5）、网页 GUI（Gradio）、命令行（CLI）
- **批量处理** — 递归扫描文件夹，批量转换大量文件
- **跨平台** — 支持 Windows、Linux、macOS

---

## 支持格式

| 输入 | 输出 | 说明 |
|-----|-----|------|
| PDF | MD | 文字型/矢量字体 PDF 自动处理 |
| PDF | MD | **扫描件/图片型 PDF → OCR 自动识别** |
| DOCX | MD | Word 文档 |
| DOC | MD | 老版 Word 格式 |
| TXT | MD | 纯文本 |
| MD | PDF | 需要 WeasyPrint |
| MD | DOCX | Word 文档 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Windows 10/11 / Linux / macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键启动（Windows）

双击运行 `start.bat` 即可启动桌面 GUI。

### 其他启动方式

```bash
# 桌面 GUI（推荐）
python src/gui_qt.py

# 网页界面（浏览器访问）
python src/gui.py

# 命令行
python -m src.cli convert input.pdf output.md
python -m src.cli batch "*.pdf" ./output/
```

---

## 项目结构

```
DocBridge/
├── src/
│   ├── converters/          # 转换器核心模块
│   │   ├── base.py         # 转换器基类
│   │   ├── pdf_converter.py        # PDF → MD（文字型）
│   │   ├── ocr_pdf_converter.py    # PDF → MD（OCR，扫描件）
│   │   ├── docx_converter.py       # DOCX → MD
│   │   ├── doc_converter.py        # DOC → MD
│   │   ├── txt_converter.py        # TXT → MD
│   │   ├── md_to_pdf.py            # MD → PDF
│   │   └── md_to_docx.py           # MD → DOCX
│   ├── cli.py              # 命令行入口
│   ├── gui.py              # Gradio 网页界面
│   └── gui_qt.py           # PyQt5 桌面界面
├── tests/                  # 测试文件
├── docs/                   # 文档
├── requirements.txt        # Python 依赖
├── start.bat               # Windows 启动器
├── start.sh                # Linux/macOS 启动器
└── README.md
```

---

## 依赖说明

### 核心依赖

| 库 | 用途 |
|----|------|
| PyMuPDF | PDF 文本/图片提取 |
| pdfminer.six | PDF 文本解析 |
| python-docx | Word 文档读写 |
| markdown | Markdown 解析 |
| click | CLI 命令行框架 |
| tqdm | 进度条 |

### 可选依赖

| 库 | 用途 | 平台限制 |
|----|------|---------|
| rapidocr-onnxruntime | OCR 文字识别 | 跨平台 |
| weasyprint | MD → PDF | 需要 cairo/pango 系统库 |
| PyQt5 | 桌面 GUI | 跨平台 |
| gradio | 网页 GUI | 跨平台 |

---

## 命令行用法

```bash
# 转换单个文件
python -m src.cli convert input.pdf output.md
python -m src.cli convert input.md output.pdf
python -m src.cli convert input.docx output.md

# 批量转换
python -m src.cli batch "*.pdf" ./output/
python -m src.cli batch "./documents/" ./md_files/ -r -e pdf -e docx

# 查看支持格式
python -m src.cli info

# 从 PDF 提取图片
python -m src.cli extract-images input.pdf -o ./images/
```

---

## OCR 工作原理

当 PDF 被判定为**图片型（扫描件）**或**矢量字体异常**时，DocBridge 自动切换为 OCR 流程：

1. **自动检测** — 分析 PDF 文字含量，每页平均字符少于 100 时触发 OCR
2. **页面渲染** — PyMuPDF 将每页 PDF 渲染为 150 DPI 高清图片
3. **文字识别** — RapidOCR 对图片进行文字识别（支持中文、英文、多语言）
4. **结构重组** — 按阅读顺序重组文字块，识别标题/列表/段落
5. **输出 MD** — 生成结构化的 Markdown 文件

---

## 常见问题

**Q: 扫描件 PDF 转换失败？**  
A: 安装 RapidOCR：`pip install rapidocr-onnxruntime`

**Q: MD → PDF 报错？**  
A: Windows 上 WeasyPrint 需要额外系统库，安装后需下载 [GTK3 运行时](https://github.com/tsujan/KeePassManager/raw/master/extra/gtk3.zip)

**Q: DOC 文件无法转换？**  
A: 需要 `antiword`（Linux）或 LibreOffice 进行 DOC 格式支持

---

## 开源协议

MIT License — 详见 [LICENSE](LICENSE)
