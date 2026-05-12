"""
转换器基类
所有转换器继承此基类，统一接口
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseConverter(ABC):
    """转换器抽象基类"""

    # 输入格式（子类覆盖）
    input_extensions: List[str] = []
    # 输出格式（子类覆盖）
    output_extension: str = ""

    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> bool:
        """
        执行转换

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径

        Returns:
            bool: 转换是否成功
        """
        pass

    def validate(self, file_path: str) -> bool:
        """
        验证文件是否存在且格式正确

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件是否有效
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        if not path.is_file():
            raise ValueError(f"不是有效文件: {file_path}")
        if path.suffix.lower() not in self.input_extensions:
            raise ValueError(
                f"不支持的格式: {path.suffix}，支持的格式: {self.input_extensions}"
            )
        return True

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """获取支持的输入格式列表"""
        return cls.input_extensions

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.input_extensions} -> {self.output_extension}>"
