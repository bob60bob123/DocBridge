"""
PDF 转 MD 转换器
使用 PyMuPDF 提取文本，智能识别标题、列表、表格结构
"""

import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict

from .base import BaseConverter


class PDFToMDConverter(BaseConverter):
    """PDF 转 Markdown 转换器（增强版）"""

    input_extensions = [".pdf"]
    output_extension = ".md"

    def __init__(self):
        self._page_count = 0
        self._current_heading_level = 0

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将 PDF 转换为 Markdown

        Args:
            input_path: PDF 文件路径
            output_path: MD 文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        doc = fitz.open(input_path)
        self._page_count = len(doc)

        lines = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_content = self._extract_page_content(page, page_num)
            lines.extend(page_content)
            lines.append("")  # 页面之间空行

        doc.close()

        # 合并并清理
        md_content = self._post_process(lines)

        # 写入 MD 文件
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")

        return True

    def _extract_page_content(self, page: fitz.Page, page_num: int) -> List[str]:
        """提取单个页面的内容"""
        lines = []
        lines.append(f"## 第 {page_num + 1} 页\n")

        # 获取文本块
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))  # 按 y, x 排序

        for block in blocks:
            if block[5] == 0:  # 文本块
                text = self._clean_text(block[4])
                if text.strip():
                    # 检测文本类型
                    text_type = self._detect_text_type(text, block)

                    if text_type == "heading":
                        level = self._detect_heading_level(text, block)
                        lines.append(f"{'#' * level} {text}\n")
                    elif text_type == "list_item":
                        lines.append(f"- {text}")
                    elif text_type == "table":
                        # 表格处理（简化）
                        lines.append(text)
                    else:
                        lines.append(text)
                        lines.append("")

        # 提取链接
        links = page.get_links()
        if links:
            lines.append("\n### 链接\n")
            for link in links:
                if link.get("uri"):
                    lines.append(f"- [{link['uri']}]({link['uri']})")

        return lines

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r"\s+", " ", text)
        # 移除特殊字符
        text = text.strip()
        return text

    def _detect_text_type(self, text: str, block: Tuple) -> str:
        """
        检测文本类型

        Returns:
            str: 'heading', 'list_item', 'table', 'paragraph'
        """
        # 跳过太短的文本
        if len(text) < 2:
            return "skip"

        # 检测列表项
        list_patterns = [
            r"^[\-\*\+]\s+",
            r"^\d+[\.\)]\s+",
            r"^[a-z][\.\)]\s+",
            r"^[A-Z][\.\)]\s+",
        ]
        for pattern in list_patterns:
            if re.match(pattern, text):
                return "list_item"

        # 检测表格（多行多列的模式）
        if "│" in text or "├" in text or "┌" in text:
            return "table"

        # 检测标题特征：短行、字体大、以特定字符结尾
        if len(text) < 100:
            # 获取字体大小（从 block 元数据）
            font_size = self._estimate_font_size(block)
            if font_size > 12:  # 假设正文字体 10-12pt
                return "heading"

        return "paragraph"

    def _estimate_font_size(self, block: Tuple) -> float:
        """估算字体大小"""
        # block 格式: (x0, y0, x1, y1, text, block_no, block_type)
        # 使用高度估算
        height = block[3] - block[1]
        # 假设 1pt ≈ 1.33 pixels at 96 DPI
        return height * 0.75

    def _detect_heading_level(self, text: str, block: Tuple) -> int:
        """检测标题级别"""
        font_size = self._estimate_font_size(block)

        if font_size > 20:
            return 1
        elif font_size > 16:
            return 2
        elif font_size > 14:
            return 3
        else:
            return 4

    def _post_process(self, lines: List[str]) -> str:
        """后处理：合并段落、清理"""
        result = []
        prev_line = ""
        prev_type = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 标题直接添加
            if line.startswith("#"):
                # 标题之间保持空行
                if prev_line and not prev_line.startswith("#"):
                    result.append("")
                result.append(line)
                prev_line = line
                prev_type = "heading"
                continue

            # 列表项直接添加
            if line.startswith("-"):
                result.append(line)
                prev_line = line
                prev_type = "list"
                continue

            # 链接直接添加
            if line.startswith("["):
                result.append(line)
                prev_line = line
                prev_type = "link"
                continue

            # 分割线
            if line.startswith("---"):
                result.append(line)
                prev_line = line
                prev_type = "divider"
                continue

            # 段落：与前一行合并
            if prev_type == "paragraph":
                result[-1] = result[-1] + " " + line
            else:
                result.append(line)

            prev_line = line
            prev_type = "paragraph"

        return "\n".join(result)

    def extract_images(self, input_path: str, output_dir: str) -> List[str]:
        """
        从 PDF 中提取图片

        Args:
            input_path: PDF 文件路径
            output_dir: 图片输出目录

        Returns:
            List[str]: 提取的图片路径列表
        """
        self.validate(input_path)

        doc = fitz.open(input_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)

                # 保存图片
                img_file = output_path / f"page{page_num + 1}_img{img_index + 1}.png"
                if pix.n - pix.alpha < 4:  # RGB
                    pix.save(str(img_file))
                else:  # CMYK，转换
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    pix.save(str(img_file))

                image_paths.append(str(img_file))

        doc.close()
        return image_paths

    def extract_tables(self, input_path: str) -> List[List[List[str]]]:
        """
        从 PDF 中提取表格

        Args:
            input_path: PDF 文件路径

        Returns:
            List[List[List[str]]]: 每页的表格列表
        """
        self.validate(input_path)

        doc = fitz.open(input_path)
        all_tables = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            tables = page.extract_tables()
            all_tables.append(tables if tables else [])

        doc.close()
        return all_tables

    def tables_to_markdown(self, tables: List[List[List[str]]]) -> List[str]:
        """将提取的表格转换为 Markdown 格式"""
        md_tables = []

        for page_tables in tables:
            for table in page_tables:
                if not table:
                    continue

                md_lines = []
                header = table[0]
                md_lines.append("| " + " | ".join(header) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

                for row in table[1:]:
                    md_lines.append("| " + " | ".join(row) + " |")

                md_tables.append("\n".join(md_lines))

        return md_tables
