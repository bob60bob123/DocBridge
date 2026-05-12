"""
DOC 转 MD 转换器
支持老版 .doc 格式，使用 antiword 或 LibreOffice 辅助
"""

import subprocess
import re
from pathlib import Path
from typing import Optional

from .base import BaseConverter


class DOCToMDConverter(BaseConverter):
    """DOC 转 Markdown 转换器（老版格式）"""

    input_extensions = [".doc"]
    output_extension = ".md"

    def __init__(self):
        self._has_antiword = self._check_antiword()
        self._has_libreoffice = self._check_libreoffice()

    def _check_antiword(self) -> bool:
        """检查 antiword 是否安装"""
        try:
            result = subprocess.run(
                ["antiword", "-h"],
                capture_output=True,
                timeout=5
            )
            return result.returncode in [0, 1]  # antiword 返回 1 表示 help
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_libreoffice(self) -> bool:
        """检查 LibreOffice 是否安装"""
        try:
            result = subprocess.run(
                ["libreoffice", "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def convert(self, input_path: str, output_path: str) -> bool:
        """
        将 DOC 转换为 Markdown

        Args:
            input_path: DOC 文件路径
            output_path: MD 文件路径

        Returns:
            bool: 转换是否成功
        """
        self.validate(input_path)

        text = self._extract_text(input_path)
        if text is None:
            raise RuntimeError(
                "无法提取 DOC 文件内容。"
                "请安装 antiword (sudo apt install antiword) "
                "或 LibreOffice"
            )

        # 处理文本，转换为 Markdown 格式
        md_content = self._process_text(text)

        # 写入文件
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")

        return True

    def _extract_text(self, input_path: str) -> Optional[str]:
        """提取 DOC 文件文本"""
        # 优先使用 antiword（更快）
        if self._has_antiword:
            try:
                result = subprocess.run(
                    ["antiword", input_path],
                    capture_output=True,
                    timeout=30,
                    encoding="utf-8",
                    errors="replace"
                )
                if result.stdout:
                    return result.stdout
            except subprocess.SubprocessError:
                pass

        # 备选：使用 LibreOffice 转换为 txt
        if self._has_libreoffice:
            return self._extract_via_libreoffice(input_path)

        return None

    def _extract_via_libreoffice(self, input_path: str) -> Optional[str]:
        """通过 LibreOffice 提取文本"""
        try:
            # 使用 LibreOffice 转换为 txt
            result = subprocess.run(
                [
                    "libreoffice", "--headless", "--convert-to", "txt:Text",
                    "--outdir", "/tmp", input_path
                ],
                capture_output=True,
                timeout=60
            )

            # 读取转换后的文件
            txt_path = Path("/tmp") / (Path(input_path).stem + ".txt")
            if txt_path.exists():
                text = txt_path.read_text(encoding="utf-8", errors="replace")
                txt_path.unlink()  # 删除临时文件
                return text
        except subprocess.SubprocessError:
            pass

        return None

    def _process_text(self, text: str) -> str:
        """
        处理提取的文本，转换为 Markdown 格式

        Args:
            text: 原始文本

        Returns:
            str: Markdown 格式文本
        """
        lines = text.split("\n")
        result_lines = []
        in_list = False

        for line in lines:
            stripped = line.strip()

            # 跳过空行
            if not stripped:
                if in_list:
                    result_lines.append("")
                    in_list = False
                continue

            # 检测列表项（各种模式）
            list_match = re.match(r"^[\-\*\+]\s+(.*)$", stripped)
            if list_match:
                result_lines.append(f"- {list_match.group(1)}")
                in_list = True
                continue

            numbered_match = re.match(r"^\d+[\.\)]\s+(.*)$", stripped)
            if numbered_match:
                result_lines.append(f"1. {numbered_match.group(1)}")
                in_list = True
                continue

            # 检测标题（全是英文大写或特定模式）
            if re.match(r"^[A-Z][A-Z\s]+$", stripped) and len(stripped) < 50:
                result_lines.append(f"## {stripped}")
                continue

            # 检测可能是标题的行（短行，非列表）
            if len(stripped) < 60 and not stripped.endswith((". ", ",", "。")):
                # 可能是一级标题
                if re.match(r"^[一二三四五六七八九十]+[、\.．]", stripped[:4]):
                    result_lines.append(f"## {stripped}")
                    continue

            # 普通段落
            if not stripped.startswith("#"):
                result_lines.append(stripped)
            else:
                result_lines.append(stripped)

        return "\n".join(result_lines)
