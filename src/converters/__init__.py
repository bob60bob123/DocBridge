"""
转换器模块
支持格式：
  PDF/DOCX/DOC/TXT → MD
  MD → PDF/DOCX
  图片型PDF → MD（OCR）
"""

from .base import BaseConverter
from .pdf_converter import PDFToMDConverter
from .docx_converter import DOCXToMDConverter
from .doc_converter import DOCToMDConverter
from .txt_converter import TXTToMDConverter

# MD 转换器（weasyprint/python-docx 可选，Windows 上可能不可用）
MDToPDFConverter = None
MDToDOCXConverter = None

try:
    from .md_to_pdf import MDToPDFConverter
except (ImportError, OSError):
    pass  # weasyprint 未安装或 Windows 系统库缺失

try:
    from .md_to_docx import MDToDOCXConverter
except (ImportError, OSError):
    pass  # python-docx 未安装

# OCR转换器（可选依赖，RapidOCR）
OCRPDFConverter = None

try:
    from .ocr_pdf_converter import OCRPDFConverter
except (ImportError, OSError):
    pass  # RapidOCR 未安装


def get_ocr_converter():
    """获取OCR转换器实例（延迟加载）"""
    global OCRPDFConverter
    if OCRPDFConverter is not None:
        return OCRPDFConverter()
    return None


def is_image_pdf(input_path: str) -> bool:
    """检测PDF是否为图片型（扫描件）或字体编码异常的PDF
    
    返回 True 表示应该使用 OCR 处理：
    - 完全没有文字页面（扫描件）
    - 文字页面极少
    - 提取的文字过短（疑似矢量字体编码异常）
    """
    try:
        import fitz
        doc = fitz.open(input_path)
        page_count = len(doc)
        total_chars = 0
        text_pages = 0
        
        for page in doc:
            text = page.get_text().strip()
            if text and len(text) > 5:
                text_pages += 1
                total_chars += len(text)
        
        doc.close()
        
        if page_count == 0:
            return False
        
        # 页面极少，或每页平均字符很少（矢量字体PDF特征）
        if text_pages < page_count * 0.3:
            return True
        
        # 每页平均字符异常少（<100字符/页），很可能是矢量字体乱码
        avg_chars = total_chars / page_count
        if avg_chars < 100:
            return True
        
        return False
    except Exception:
        return False


def get_pdf_to_md_converter(input_path: str = None):
    """
    获取适合的PDF转MD转换器
    自动检测PDF类型：
    - 文字型PDF：使用PyMuPDF直接提取文本
    - 图片型PDF（扫描件）：使用OCR识别
    """
    if input_path and is_image_pdf(input_path):
        ocr = get_ocr_converter()
        if ocr is not None:
            return ocr
        # OCR不可用时降级到文本提取
    return PDFToMDConverter()


__all__ = [
    "BaseConverter",
    "PDFToMDConverter",
    "DOCXToMDConverter",
    "DOCToMDConverter",
    "TXTToMDConverter",
    "MDToPDFConverter",
    "MDToDOCXConverter",
    "OCRPDFConverter",
    "get_ocr_converter",
    "is_image_pdf",
    "get_pdf_to_md_converter",
]
