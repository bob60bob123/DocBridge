"""
TXT 转 MD 转换器
简单的文本转换，保留基本格式
"""

from pathlib import Path

from .base import BaseConverter


class TXTToMDConverter(BaseConverter):
    """TXT 转 Markdown 转换器"""

    input_extensions = [".txt", ".text"]
    output_extension = ".md"

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将 TXT 转换为 Markdown

        Args:
            input_path: TXT 文件路径
            output_path: MD 文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        # 读取文本
        text = Path(input_path).read_text(encoding="utf-8")

        # 简单处理：保留段落
        lines = []
        paragraphs = text.split("\n\n")

        for para in paragraphs:
            para = para.strip()
            if para:
                lines.append(para)
                lines.append("")

        # 写入文件
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(lines), encoding="utf-8")

        return True
