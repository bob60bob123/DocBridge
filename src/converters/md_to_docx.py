"""
MD 转 DOCX 转换器
使用 python-docx 将 Markdown 转换为 Word 文档，支持表格、图片、复杂格式
"""

import re
import base64
import markdown
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path

from .base import BaseConverter


class MDToDOCXConverter(BaseConverter):
    """Markdown 转 DOCX 转换器（增强版）"""

    input_extensions = [".md", ".markdown"]
    output_extension = ".docx"

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将 Markdown 转换为 DOCX

        Args:
            input_path: MD 文件路径
            output_path: DOCX 文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        # 读取 MD 文件
        md_content = Path(input_path).read_text(encoding="utf-8")

        # 创建 DOCX 文档
        doc = Document()

        # 设置默认样式
        self._setup_styles(doc)

        # 解析并写入
        self._parse_and_write(doc, md_content, input_path)

        # 写入文件
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output))

        return True

    def _setup_styles(self, doc: Document):
        """设置文档默认样式"""
        # 设置默认字体
        style = doc.styles["Normal"]
        style.font.name = "宋体"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        style.font.size = Pt(11)

        # 设置标题样式
        for i in range(1, 10):
            try:
                heading_style = doc.styles[f"Heading {i}"]
                heading_style.font.name = "黑体"
                heading_style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
                heading_style.font.size = Pt(16 - i)
                heading_style.font.bold = True
            except KeyError:
                pass

    def _parse_and_write(self, doc: Document, md_content: str, md_path: str):
        """解析 MD 内容并写入 DOCX"""
        md_dir = Path(md_path).parent

        lines = md_content.split("\n")
        i = 0
        in_code_block = False
        code_buffer = []
        code_language = ""

        while i < len(lines):
            line = lines[i]

            # 代码块处理
            if line.strip().startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_language = line.strip()[3:] or ""
                    code_buffer = []
                else:
                    # 结束代码块
                    self._add_code_block(doc, code_buffer, code_language)
                    in_code_block = False
                    code_buffer = []
                i += 1
                continue

            if in_code_block:
                code_buffer.append(line)
                i += 1
                continue

            # 表格处理
            if "|" in line and line.strip().startswith("|"):
                # 收集所有表格行
                table_lines = []
                while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                self._add_table(doc, table_lines)
                continue

            # 标题处理
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                self._add_heading(doc, text, level)
                i += 1
                continue

            # 分割线
            if line.strip() in ("---", "***", "___"):
                self._add_horizontal_rule(doc)
                i += 1
                continue

            # 列表处理
            list_item = self._parse_list_item(line)
            if list_item:
                self._add_list_item(doc, list_item["text"], list_item["ordered"], list_item["start"])
                i += 1
                continue

            # 引用块处理
            if line.strip().startswith(">"):
                # 收集引用块
                quote_lines = []
                while i < len(lines) and (lines[i].strip().startswith(">") or lines[i].strip() == ""):
                    if lines[i].strip().startswith(">"):
                        quote_lines.append(lines[i].strip().lstrip(">").strip())
                    elif quote_lines:  # 引用块中的空行
                        quote_lines.append("")
                    i += 1
                self._add_blockquote(doc, quote_lines)
                continue

            # 图片处理
            img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            if img_match:
                alt_text = img_match.group(1)
                src = img_match.group(2)
                self._add_image(doc, src, alt_text, md_dir)
                i += 1
                continue

            # 普通段落
            if line.strip():
                self._add_paragraph(doc, line)

            i += 1

    def _add_heading(self, doc: Document, text: str, level: int):
        """添加标题"""
        if level > 9:
            level = 9
        p = doc.add_heading(text, level=level)
        p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    def _add_paragraph(self, doc: Document, text: str, bold=False, italic=False):
        """添加段落"""
        p = doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        p.paragraph_format.line_spacing = 1.5
        return p

    def _add_code_block(self, doc: Document, lines: list, language: str):
        """添加代码块"""
        p = doc.add_paragraph()
        run = p.add_run("\n".join(lines))
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.line_spacing = 1.2
        # 设置背景色（通过 XML）
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), "f5f5f5")
        p._p.get_or_add_pPr().append(shading)

    def _add_list_item(self, doc: Document, text: str, ordered: bool, start_num: int = None):
        """添加列表项"""
        style = "List Number" if ordered else "List Bullet"
        p = doc.add_paragraph(text, style=style)
        p.paragraph_format.left_indent = Cm(0.75)

    def _parse_list_item(self, line: str) -> dict:
        """解析列表项"""
        # 无序列表
        match = re.match(r"^[\-\*\+]\s+(.*)$", line.strip())
        if match:
            return {"text": match.group(1), "ordered": False, "start": None}

        # 有序列表
        match = re.match(r"^(\d+)[\.\)]\s+(.*)$", line.strip())
        if match:
            return {"text": match.group(2), "ordered": True, "start": int(match.group(1))}

        return None

    def _add_blockquote(self, doc: Document, lines: list):
        """添加引用块"""
        for line in lines:
            p = doc.add_paragraph(line)
            p.paragraph_format.left_indent = Cm(1)
            p.paragraph_format.line_spacing = 1.5
            # 添加竖线
            shading = OxmlElement("w:pBdr")
            left_border = OxmlElement("w:left")
            left_border.set(qn("w:val"), "single")
            left_border.set(qn("w:sz"), "12")
            left_border.set(qn("w:space"), "10")
            left_border.set(qn("w:color"), "4a90d9")
            shading.append(left_border)
            p._p.get_or_add_pPr().append(shading)

    def _add_horizontal_rule(self, doc: Document):
        """添加分割线"""
        p = doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "999999")
        pBdr.append(bottom)
        pPr.append(pBdr)

    def _add_table(self, doc: Document, table_lines: list):
        """添加表格"""
        if len(table_lines) < 2:
            return

        # 解析表格
        rows = []
        for line in table_lines:
            # 移除首尾 | 并分割
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)

        # 创建表格
        table = doc.add_table(rows=len(rows), cols=len(rows[0]))
        table.style = "Table Grid"

        for i, row_data in enumerate(rows):
            row = table.rows[i]
            for j, cell_text in enumerate(row_data):
                cell = row.cells[j]
                cell.text = cell_text

                # 表头样式
                if i == 0:
                    run = cell.paragraphs[0].runs[0]
                    run.bold = True
                    shading = OxmlElement("w:shd")
                    shading.set(qn("w:fill"), "f0f0f0")
                    cell._tc.get_or_add_tcPr().append(shading)

        doc.add_paragraph()  # 表格后空行

    def _add_image(self, doc: Document, src: str, alt_text: str, md_dir: Path):
        """添加图片"""
        # 检查是否是本地图片
        if src.startswith(("http://", "https://")):
            # 尝试下载远程图片（简单处理）
            return

        img_path = md_dir / src
        if not img_path.exists():
            # 添加图片引用文本
            p = doc.add_paragraph(f"[图片: {alt_text}]")
            p.italic = True
            return

        try:
            # 添加图片
            p = doc.add_paragraph()
            run = p.add_run()
            run.add_picture(str(img_path), width=Inches(4))
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

            # 添加图片说明
            if alt_text:
                caption = doc.add_paragraph(alt_text)
                caption.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                caption.runs[0].italic = True
                caption.runs[0].font.size = Pt(9)
        except Exception:
            # 添加占位文本
            p = doc.add_paragraph(f"[图片: {alt_text}]")
            p.italic = True
