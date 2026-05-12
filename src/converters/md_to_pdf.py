"""
MD 转 PDF 转换器
使用 WeasyPrint 将 Markdown 转换为 PDF，支持表格、图片、中文
"""

import markdown
import re
import base64
import os
from pathlib import Path
from weasyprint import HTML, CSS

from .base import BaseConverter


class MDToPDFConverter(BaseConverter):
    """Markdown 转 PDF 转换器（增强版）"""

    input_extensions = [".md", ".markdown"]
    output_extension = ".pdf"

    # 增强的 CSS 样式
    ENHANCED_CSS = """
    @page {
        size: A4;
        margin: 2cm 2.5cm;
        @top-center {
            content: "格式转换器";
            font-size: 9pt;
            color: #666;
        }
        @bottom-center {
            content: "第 " counter(page) " 页";
            font-size: 9pt;
            color: #666;
        }
    }
    @page:first {
        @top-center { content: none; }
        @bottom-center { content: none; }
    }
    body {
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei",
                     "SimHei", "SimSun", serif;
        font-size: 11pt;
        line-height: 1.8;
        text-align: justify;
        color: #333;
    }
    h1 {
        font-size: 22pt;
        font-weight: bold;
        text-align: center;
        page-break-after: avoid;
        margin-top: 2em;
        margin-bottom: 1em;
        border-bottom: 2px solid #333;
        padding-bottom: 0.5em;
    }
    h1:first-of-type {
        margin-top: 0;
    }
    h2 {
        font-size: 18pt;
        font-weight: bold;
        page-break-after: avoid;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
    }
    h3 {
        font-size: 14pt;
        font-weight: bold;
        page-break-after: avoid;
        margin-top: 1.2em;
        margin-bottom: 0.6em;
    }
    h4, h5, h6 {
        font-size: 12pt;
        font-weight: bold;
        page-break-after: avoid;
        margin-top: 1em;
        margin-bottom: 0.5em;
    }
    p {
        text-indent: 2em;
        margin-top: 0.5em;
        margin-bottom: 0.5em;
    }
    strong, b {
        font-weight: bold;
    }
    em, i {
        font-style: italic;
    }
    code {
        font-family: "Consolas", "Source Code Pro", monospace;
        font-size: 9pt;
        background-color: #f5f5f5;
        padding: 2px 6px;
        border-radius: 3px;
        color: #c7254e;
    }
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 12px;
        overflow-x: auto;
        page-break-inside: avoid;
        margin: 1em 0;
    }
    pre code {
        background-color: transparent;
        padding: 0;
        color: #333;
    }
    blockquote {
        border-left: 4px solid #4a90d9;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #f9f9f9;
        color: #555;
    }
    blockquote p {
        text-indent: 0;
        margin: 0.3em 0;
    }
    ul, ol {
        margin: 1em 0;
        padding-left: 2em;
    }
    li {
        margin: 0.3em 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
        page-break-inside: avoid;
    }
    th {
        background-color: #f0f0f0;
        font-weight: bold;
        text-align: left;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px 12px;
    }
    tr:nth-child(even) {
        background-color: #fafafa;
    }
    img {
        max-width: 100%;
        height: auto;
        page-break-inside: avoid;
        text-align: center;
        margin: 1em 0;
    }
    hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 2em 0;
    }
    a {
        color: #4a90d9;
        text-decoration: none;
    }
    """

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将 Markdown 转换为 PDF

        Args:
            input_path: MD 文件路径
            output_path: PDF 文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        # 读取 MD 文件
        md_content = Path(input_path).read_text(encoding="utf-8")

        # 预处理：处理图片（转为 base64）
        md_content = self._process_images(md_content, input_path)

        # 转换为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=[
                "tables",
                "fenced_code",
                "codehilite",
                "toc",
                "nl2br",
                "sane_lists",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "guess_lang": False
                },
                "toc": {
                    "title": "目录"
                }
            }
        )

        # 构建完整 HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: "Noto Sans CJK SC", "Microsoft YaHei", "SimHei", serif; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

        # 写入 PDF
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        HTML(string=full_html).write_pdf(
            str(output),
            stylesheets=[CSS(string=self.ENHANCED_CSS)]
        )

        return True

    def _process_images(self, md_content: str, md_path: str) -> str:
        """
        处理 MD 中的图片路径，嵌入 base64 或保留 URL

        Args:
            md_content: MD 文件内容
            md_path: MD 文件路径（用于解析相对路径）

        Returns:
            str: 处理后的 MD 内容
        """
        md_dir = Path(md_path).parent

        def replace_image(match):
            alt_text = match.group(1)
            src = match.group(2)
            title = match.group(3) if match.group(3) else ""

            # 检查是否是本地图片
            if src.startswith(("http://", "https://", "data:")):
                return match.group(0)

            # 相对路径
            img_path = md_dir / src
            if img_path.exists():
                try:
                    with open(img_path, "rb") as f:
                        data = f.read()
                    ext = img_path.suffix.lower()
                    if ext == ".png":
                        mime = "image/png"
                    elif ext in [".jpg", ".jpeg"]:
                        mime = "image/jpeg"
                    elif ext == ".gif":
                        mime = "image/gif"
                    elif ext == ".svg":
                        mime = "image/svg+xml"
                    else:
                        mime = "image/png"

                    b64_data = base64.b64encode(data).decode("utf-8")
                    return f'![{alt_text}](data:{mime};base64,{b64_data})'
                except Exception:
                    pass

            return match.group(0)

        # 替换图片语法
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        return re.sub(pattern, replace_image, md_content)
