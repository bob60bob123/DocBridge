"""
图片型PDF转MD转换器（OCR版）
使用 PyMuPDF 渲染页面为图片，再用 RapidOCR 识别文字并保留布局结构
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

from .base import BaseConverter


class OCRPDFConverter(BaseConverter):
    """
    OCR方式将PDF（尤其是扫描件/图片型PDF）转换为Markdown

    工作流程：
    1. 用 PyMuPDF 将每页 PDF 渲染为高清 PNG 图片
    2. 用 RapidOCR 对图片进行文字识别（支持多语言）
    3. 按阅读顺序（从上到下、从左到右）重组文字块
    4. 智能识别标题、段落、列表等结构
    5. 输出结构化的 Markdown
    """

    input_extensions = [".pdf"]
    output_extension = ".md"

    def __init__(self, lang: str = "ch"):
        """
        初始化OCR转换器

        Args:
            lang: OCR语言，'ch'中文，'en'英文，'ch_sim'简体中文，'ja'日语等
                  RapidOCR支持多语言自动检测，默认中文优先
        """
        self.lang = lang
        self._rapid_ocr = None  # 延迟初始化

    @property
    def rapid_ocr(self):
        """延迟加载 RapidOCR 实例"""
        if self._rapid_ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self._rapid_ocr = RapidOCR(det_use_cuda=False, rec_use_cuda=False)
        return self._rapid_ocr

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将图片型PDF转换为Markdown

        Args:
            input_path: PDF文件路径
            output_path: MD文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        doc = fitz.open(input_path)
        page_count = len(doc)

        all_results = []
        for page_num in range(page_count):
            page = doc[page_num]
            # 渲染页面为图片（150 DPI，适合OCR）
            mat = fitz.Matrix(150/72, 150/72)
            pix = page.get_pixmap(matrix=mat)
            # pix.samples 是原始像素字节，按 RGB 排列
            # .copy() 确保持有独立副本，防止 pix 释放后数据失效
            img_np = np.frombuffer(pix.samples, dtype=np.uint8).copy()
            img_np = img_np.reshape(pix.height, pix.width, pix.n)

            # OCR识别
            result, elapsed = self.rapid_ocr(img_np)
            page_results = self._process_page_result(result, page_num + 1)
            all_results.extend(page_results)

        doc.close()

        # 生成Markdown
        md_content = self._build_markdown(all_results)

        # 写入文件
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        return True

    def _process_page_result(
        self, result: List, page_num: int
    ) -> List[dict]:
        """
        处理单页OCR结果，按阅读顺序排序并分类

        Returns:
            List of dicts: [{"text": str, "type": str, "page": int, "y": float, "x": float}]
        """
        if not result:
            return []

        items = []
        for line in result:
            # RapidOCR result: [box, text, score]
            box, text, score = line
            if not text or score < 0.3:
                continue

            # 取文本框中心坐标
            x_center = (box[0][0] + box[2][0]) / 2
            y_center = (box[0][1] + box[2][1]) / 2

            # 识别文本类型
            text_type = self._classify_text(text, score)

            items.append({
                "text": text.strip(),
                "type": text_type,
                "page": page_num,
                "y": y_center,
                "x": x_center,
                "score": score,
                "box": box,
            })

        # 按阅读顺序排序：先按y（行），再按x（列）
        items.sort(key=lambda i: (i["page"], round(i["y"] / 30) * 30, i["x"]))
        return items

    def _classify_text(self, text: str, score: float) -> str:
        """根据文本特征判断类型"""
        text = text.strip()
        if not text:
            return "skip"

        # 纯数字/符号行可能是页码或表格分隔
        if len(text) < 3 and (text.isdigit() or text in "-—–"):
            if score > 0.9:
                return "page_number"

        # 列表项特征
        list_patterns = [
            r"^[\-\*\+]\s+",
            r"^\d+[\\.、\)）]",
            r"^[a-zA-Z][\\.、\)）]\s+",
            r"^[一二三四五六七八九十]+[\\.、\)）]",
            r"^[\u25a0\u25b6\u25cf]\s+",
        ]
        for p in list_patterns:
            import re
            if re.match(p, text):
                return "list_item"

        # 标题特征：短行、较大字体（OCR会返回box大小，但我们用文字特征判断）
        if len(text) < 60 and not text.endswith(("。", ".", ",", "，", ";", "；", ":", "：")):
            # 全角句号结尾少可能是标题
            if 2 < len(text) < 40:
                return "heading"

        return "paragraph"

    def _build_markdown(self, items: List[dict]) -> str:
        """将OCR结果构建为Markdown"""
        lines = []
        prev_type = ""
        same_type_group = []

        def flush_group():
            nonlocal same_type_group, prev_type
            if not same_type_group:
                return
            if prev_type == "heading":
                # 合并相邻标题
                for i, item in enumerate(same_type_group):
                    level = min(len(item["text"]) // 10 + 1, 3)
                    prefix = "#" * level
                    lines.append(f"{prefix} {item['text']}")
                    lines.append("")
            elif prev_type == "list_item":
                for item in same_type_group:
                    text = item["text"]
                    # 去掉已有的列表标记
                    import re
                    text = re.sub(r"^[\-\*\+]\s+", "", text)
                    text = re.sub(r"^\d+[\\.、\)）]\s+", "", text)
                    text = re.sub(r"^[a-zA-Z][\\.、\)）]\s+", "", text)
                    text = re.sub(r"^[\u25a0\u25b6\u25cf]\s+", "", text)
                    lines.append(f"- {text}")
            elif prev_type == "paragraph":
                # 合并相邻段落
                merged = " ".join(item["text"] for item in same_type_group)
                lines.append(merged)
                lines.append("")
            same_type_group = []

        for item in items:
            if item["type"] == "skip" or item["type"] == "page_number":
                continue

            if item["type"] != prev_type:
                flush_group()
                prev_type = item["type"]

            same_type_group.append(item)

        flush_group()

        # 清理多余空行
        result = "\n".join(lines)
        import re
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip() + "\n"

    def get_pdf_info(self, input_path: str) -> dict:
        """获取PDF基本信息"""
        doc = fitz.open(input_path)
        info = {
            "page_count": len(doc),
            "is_image_pdf": self._detect_image_pdf(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
        }
        doc.close()
        return info

    def _detect_image_pdf(self, doc: fitz.Document) -> bool:
        """检测是否为纯图片型PDF（扫描件）"""
        text_pages = 0
        for page in doc:
            text = page.get_text().strip()
            if text and len(text) > 50:
                text_pages += 1

        # 如果大部分页面几乎没有文字，则是图片型PDF
        return text_pages < len(doc) * 0.3
