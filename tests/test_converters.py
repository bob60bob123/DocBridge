"""
格式转换器 - 单元测试
"""

import pytest
import tempfile
import os
from pathlib import Path

# 添加 src 目录到 path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from converters.base import BaseConverter
from converters.txt_converter import TXTToMDConverter
from converters.pdf_converter import PDFToMDConverter
from converters.docx_converter import DOCXToMDConverter
from converters.md_to_pdf import MDToPDFConverter
from converters.md_to_docx import MDToDOCXConverter


class TestBaseConverter:
    """测试转换器基类"""

    def test_validate_file_not_found(self):
        """测试文件不存在时的验证"""
        class TestConverter(BaseConverter):
            input_extensions = [".txt"]
            output_extension = ".md"

            def convert(self, input_path, output_path):
                return True

        converter = TestConverter()

        with pytest.raises(FileNotFoundError):
            converter.validate("/nonexistent/file.txt")

    def test_validate_invalid_extension(self):
        """测试无效扩展名"""
        class TestConverter(BaseConverter):
            input_extensions = [".txt"]
            output_extension = ".md"

            def convert(self, input_path, output_path):
                return True

        converter = TestConverter()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"test")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="不支持的格式"):
                converter.validate(temp_path)
        finally:
            os.unlink(temp_path)

    def test_get_supported_extensions(self):
        """测试获取支持的扩展名"""
        class TestConverter(BaseConverter):
            input_extensions = [".txt", ".text"]
            output_extension = ".md"

            def convert(self, input_path, output_path):
                return True

        converter = TestConverter()
        assert converter.get_supported_extensions() == [".txt", ".text"]


class TestTXTToMDConverter:
    """测试 TXT 转 MD 转换器"""

    def test_basic_conversion(self):
        """测试基本转换"""
        converter = TXTToMDConverter()

        # 创建临时 TXT 文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("第一段文字\n\n第二段文字")
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".md")

        try:
            result = converter.convert(input_path, output_path)
            assert result is True
            assert Path(output_path).exists()

            content = Path(output_path).read_text(encoding="utf-8")
            assert "第一段文字" in content
            assert "第二段文字" in content
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_empty_file(self):
        """测试空文件"""
        converter = TXTToMDConverter()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".md")

        try:
            result = converter.convert(input_path, output_path)
            assert result is True
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestMDToPDFConverter:
    """测试 MD 转 PDF 转换器"""

    def test_basic_markdown_to_pdf(self):
        """测试基本 Markdown 转 PDF"""
        converter = MDToPDFConverter()

        # 创建临时 MD 文件
        md_content = """# 标题

这是第一段文字。

## 二级标题

这是第二段文字。

- 列表项1
- 列表项2

| 表头1 | 表头2 |
|-------|-------|
| 内容1 | 内容2 |
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(md_content)
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".pdf")

        try:
            result = converter.convert(input_path, output_path)
            assert result is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestMDToDOCXConverter:
    """测试 MD 转 DOCX 转换器"""

    def test_basic_markdown_to_docx(self):
        """测试基本 Markdown 转 DOCX"""
        converter = MDToDOCXConverter()

        # 创建临时 MD 文件
        md_content = """# 主标题

这是正文内容。

## 二级标题

- 列表项1
- 列表项2

> 引用文本

```
代码块
```
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(md_content)
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".docx")

        try:
            result = converter.convert(input_path, output_path)
            assert result is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_markdown_with_table(self):
        """测试带表格的 Markdown"""
        converter = MDToDOCXConverter()

        md_content = """| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| D   | E   | F   |
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(md_content)
            input_path = f.name

        output_path = tempfile.mktemp(suffix=".docx")

        try:
            result = converter.convert(input_path, output_path)
            assert result is True
            assert Path(output_path).exists()
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestDOCXToMDConverter:
    """测试 DOCX 转 MD 转换器"""

    def test_docx_structure(self):
        """测试 DOCX 基本结构"""
        converter = DOCXToMDConverter()

        # 验证转换器属性
        assert ".docx" in converter.input_extensions
        assert converter.output_extension == ".md"

    def test_supported_extensions(self):
        """测试支持的扩展名"""
        converter = DOCXToMDConverter()
        exts = converter.get_supported_extensions()
        assert ".docx" in exts


class TestPDFToMDConverter:
    """测试 PDF 转 MD 转换器"""

    def test_pdf_structure(self):
        """测试 PDF 转换器结构"""
        converter = PDFToMDConverter()

        assert ".pdf" in converter.input_extensions
        assert converter.output_extension == ".md"

    def test_supported_extensions(self):
        """测试支持的扩展名"""
        converter = PDFToMDConverter()
        exts = converter.get_supported_extensions()
        assert ".pdf" in exts


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
