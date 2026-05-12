"""
格式转换器 - GUI 界面 (Gradio)
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到 path (在 Gradio 导入之前)
sys.path.insert(0, os.path.dirname(__file__))

import gradio as gr

from converters.pdf_converter import PDFToMDConverter
from converters.docx_converter import DOCXToMDConverter
from converters.txt_converter import TXTToMDConverter
from converters import get_pdf_to_md_converter

# MD 转换器（weasyprint 可选，python-docx 必需）
MDToPDFConverter = None
MDToDOCXConverter = None

try:
    from converters.md_to_pdf import MDToPDFConverter
except (ImportError, OSError):
    pass  # weasyprint 未安装或系统库缺失

try:
    from converters.md_to_docx import MDToDOCXConverter
except (ImportError, OSError):
    pass  # python-docx 未安装


def convert_file(file, output_format):
    """转换单个文件"""
    if file is None:
        return None

    # 读取上传的文件
    input_path = Path(file.name)
    input_ext = input_path.suffix.lower()

    # 生成输出文件名
    output_name = input_path.stem

    try:
        if input_ext == ".pdf":
            converter = get_pdf_to_md_converter(str(input_path))
            if output_format == "MD":
                output_path = f"/tmp/{output_name}.md"
                converter.convert(str(input_path), output_path)
                return output_path

        elif input_ext == ".docx":
            converter = DOCXToMDConverter()
            if output_format == "MD":
                output_path = f"/tmp/{output_name}.md"
                converter.convert(str(input_path), output_path)
                return output_path

        elif input_ext in [".txt", ".text"]:
            converter = TXTToMDConverter()
            if output_format == "MD":
                output_path = f"/tmp/{output_name}.md"
                converter.convert(str(input_path), output_path)
                return output_path

        elif input_ext in [".md", ".markdown"]:
            if output_format == "PDF":
                if not MDToPDFConverter:
                    return f"错误: MD→PDF 需要安装 weasyprint (pip install weasyprint)"
                converter = MDToPDFConverter()
                output_path = f"/tmp/{output_name}.pdf"
                converter.convert(str(input_path), output_path)
                return output_path

            elif output_format == "DOCX":
                if not MDToDOCXConverter:
                    return f"错误: MD→DOCX 需要安装 python-docx"
                converter = MDToDOCXConverter()
                output_path = f"/tmp/{output_name}.docx"
                converter.convert(str(input_path), output_path)
                return output_path

    except Exception as e:
        return f"错误: {str(e)}"

    return None


# Gradio 界面
demo = gr.Interface(
    fn=convert_file,
    inputs=[
        gr.File(label="选择文件", file_types=[".pdf", ".docx", ".txt", ".md", ".markdown"]),
        gr.Radio(["MD", "PDF", "DOCX"], label="输出格式", value="MD"),
    ],
    outputs=gr.File(label="下载文件"),
    title="格式转换器",
    description="支持 PDF、DOCX、TXT 转换为 MD，MD 转换为 PDF、DOCX",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
