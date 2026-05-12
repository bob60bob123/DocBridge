"""
格式转换器 - PyQt5 GUI 界面
原生桌面应用程序
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# 添加 src 目录到 path (在 PyQt5 导入之前)
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox, QProgressBar,
    QTextEdit, QGroupBox, QCheckBox, QMessageBox, QScrollArea,
    QFrame, QListWidget, QListWidgetItem, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

from converters.pdf_converter import PDFToMDConverter
from converters.docx_converter import DOCXToMDConverter
from converters.doc_converter import DOCToMDConverter
from converters.txt_converter import TXTToMDConverter
from converters import get_pdf_to_md_converter

# MD 转换器（weasyprint 可选，python-docx 必需）
MDToPDFConverter = None
MDToDOCXConverter = None

try:
    from converters.md_to_pdf import MDToPDFConverter
except (ImportError, OSError):
    pass  # weasyprint 未安装或系统库缺失时 MD→PDF 不可用

try:
    from converters.md_to_docx import MDToDOCXConverter
except ImportError:
    pass  # python-docx 未安装时 MD→DOCX 不可用


# 转换器映射（非PDF使用实例，PDF使用工厂函数）
CONVERTERS: Dict[str, object] = {
    ".pdf": None,  # 使用 get_pdf_to_md_converter 动态获取
    ".docx": DOCXToMDConverter(),
    ".doc": DOCToMDConverter(),
    ".txt": TXTToMDConverter(),
}

MD_CONVERTERS: Dict[str, object] = {}

if MDToPDFConverter:
    MD_CONVERTERS[".pdf"] = MDToPDFConverter
if MDToDOCXConverter:
    MD_CONVERTERS[".docx"] = MDToDOCXConverter


class ConversionThread(QThread):
    """转换线程，防止 GUI 冻结"""
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool, str)  # success, message
    log = pyqtSignal(str)  # log message

    def __init__(self, files: List[str], output_dir: str, output_format: str):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.output_format = output_format

    def run(self):
        success_count = 0
        fail_count = 0
        converter = None  # 初始化

        total = len(self.files)
        for i, file_path in enumerate(self.files):
            self.progress.emit(i + 1, total)
            converter = None  # 每次循环重置

            try:
                input_path = Path(file_path)
                input_ext = input_path.suffix.lower()
                output_path = Path(self.output_dir) / input_path.stem

                if input_ext in [".md", ".markdown"]:
                    if self.output_format in MD_CONVERTERS:
                        converter = MD_CONVERTERS[self.output_format]()
                        output_path = output_path.with_suffix(self.output_format)
                    else:
                        self.log.emit(f"不支持的输出格式: {input_ext} -> {self.output_format}")
                        fail_count += 1
                        continue
                else:
                    if self.output_format == ".md":
                        if input_ext == ".pdf":
                            converter = get_pdf_to_md_converter(str(input_path))
                        else:
                            converter = CONVERTERS.get(input_ext)
                        if converter:
                            output_path = output_path.with_suffix(".md")
                    else:
                        self.log.emit(f"不支持的转换: {input_ext} -> {self.output_format}")
                        fail_count += 1
                        continue

                if converter is None:
                    self.log.emit(f"找不到转换器: {file_path}")
                    fail_count += 1
                    continue

                converter.convert(str(input_path), str(output_path))
                self.log.emit(f"✓ {input_path.name} -> {output_path.name}")
                success_count += 1

            except Exception as e:
                self.log.emit(f"✗ {file_path}: {str(e)}")
                fail_count += 1

        self.finished.emit(
            fail_count == 0,
            f"完成: {success_count} 成功, {fail_count} 失败"
        )


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.files: List[str] = []
        self.output_format = ".md"
        self.init_ui()

    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("格式转换器 v0.2.0")
        self.setMinimumSize(700, 500)

        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("格式转换器")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # 文件选择区域
        file_group = self._create_file_group()
        main_layout.addWidget(file_group)

        # 转换设置区域
        settings_group = self._create_settings_group()
        main_layout.addWidget(settings_group)

        # 进度区域
        progress_group = self._create_progress_group()
        main_layout.addWidget(progress_group)

        # 日志区域
        log_group = self._create_log_group()
        main_layout.addWidget(log_group)

        # 按钮区域
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)

    def _create_file_group(self) -> QGroupBox:
        """创建文件选择区域"""
        group = QGroupBox("文件选择")
        layout = QVBoxLayout()

        # 文件列表
        self.file_list_widget = QListWidget()
        self.file_list_widget.setMinimumHeight(100)
        layout.addWidget(self.file_list_widget)

        # 按钮行
        btn_layout = QHBoxLayout()

        self.add_files_btn = QPushButton("添加文件")
        self.add_files_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton("添加文件夹")
        self.add_folder_btn.clicked.connect(self.add_folder)
        btn_layout.addWidget(self.add_folder_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_files)
        btn_layout.addWidget(self.clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _create_settings_group(self) -> QGroupBox:
        """创建设置区域"""
        group = QGroupBox("转换设置")
        layout = QHBoxLayout()

        # 输入格式说明
        layout.addWidget(QLabel("转换方向:"))

        # 转换类型
        self.convert_type_combo = QComboBox()
        self.convert_type_combo.addItems([
            "PDF/DOCX/DOC/TXT → MD",
            "MD → PDF",
            "MD → DOCX"
        ])
        self.convert_type_combo.currentIndexChanged.connect(self.on_convert_type_changed)
        layout.addWidget(self.convert_type_combo)

        layout.addStretch()

        # 输出目录
        layout.addWidget(QLabel("输出目录:"))
        self.output_dir_label = QLabel("未选择")
        self.output_dir_label.setMinimumWidth(200)
        layout.addWidget(self.output_dir_label)

        self.output_dir_btn = QPushButton("选择...")
        self.output_dir_btn.clicked.connect(self.select_output_dir)
        layout.addWidget(self.output_dir_btn)

        group.setLayout(layout)
        return group

    def _create_progress_group(self) -> QGroupBox:
        """创建进度区域"""
        group = QGroupBox("进度")
        layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        group.setLayout(layout)
        return group

    def _create_log_group(self) -> QGroupBox:
        """创建日志区域"""
        group = QGroupBox("日志")
        layout = QVBoxLayout()

        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(120)
        layout.addWidget(self.log_widget)

        group.setLayout(layout)
        return group

    def _create_button_layout(self) -> QHBoxLayout:
        """创建按钮区域"""
        layout = QHBoxLayout()

        self.start_btn = QPushButton("开始转换")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_conversion)
        layout.addWidget(self.stop_btn)

        layout.addStretch()

        self.about_btn = QPushButton("关于")
        self.about_btn.clicked.connect(self.show_about)
        layout.addWidget(self.about_btn)

        return layout

    def add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择文件",
            "",
            "所有支持的文件 (*.pdf *.docx *.doc *.txt *.md *.markdown);;所有文件 (*)"
        )

        if files:
            for file in files:
                if file not in self.files:
                    self.files.append(file)
                    self.file_list_widget.addItem(Path(file).name)
            self.log(f"已添加 {len(files)} 个文件")

    def add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", "")

        if folder:
            # 搜索所有支持的文件
            search_exts = ["*.pdf", "*.docx", "*.doc", "*.txt", "*.md", "*.markdown"]
            found_files = []

            for ext in search_exts:
                found_files.extend(Path(folder).rglob(ext))

            for file in found_files:
                file_str = str(file)
                if file_str not in self.files:
                    self.files.append(file_str)
                    self.file_list_widget.addItem(file.name)

            self.log(f"已添加文件夹中的 {len(found_files)} 个文件")

    def clear_files(self):
        """清空文件列表"""
        self.files.clear()
        self.file_list_widget.clear()
        self.progress_bar.setValue(0)
        self.log("已清空文件列表")

    def select_output_dir(self):
        """选择输出目录"""
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录", "")
        if folder:
            self.output_dir_label.setText(folder)
            self.log(f"输出目录: {folder}")

    def on_convert_type_changed(self, index: int):
        """转换类型改变"""
        if index == 0:
            self.output_format = ".md"
        elif index == 1:
            self.output_format = ".pdf"
        elif index == 2:
            self.output_format = ".docx"

    def start_conversion(self):
        """开始转换"""
        if not self.files:
            QMessageBox.warning(self, "提示", "请先添加文件")
            return

        output_dir = self.output_dir_label.text()
        if output_dir == "未选择":
            QMessageBox.warning(self, "提示", "请选择输出目录")
            return

        # 确保输出目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 禁用开始按钮
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 启动转换线程
        self.thread = ConversionThread(self.files, output_dir, self.output_format)
        self.thread.progress.connect(self.on_progress)
        self.thread.finished.connect(self.on_finished)
        self.thread.log.connect(self.log)
        self.thread.start()

    def stop_conversion(self):
        """停止转换"""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            self.log("已停止转换")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_progress(self, current: int, total: int):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_finished(self, success: bool, message: str):
        """转换完成"""
        self.log(message)
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "完成", message)

    def log(self, message: str):
        """添加日志"""
        self.log_widget.append(message)
        # 滚动到底部
        self.log_widget.verticalScrollBar().setValue(
            self.log_widget.verticalScrollBar().maximum()
        )

    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            self,
            "关于",
            "格式转换器 v0.2.0\n\n"
            "支持 PDF、DOCX、DOC、TXT 与 MD 之间的相互转换\n\n"
            "依赖库:\n"
            "  - PyMuPDF (PDF 处理)\n"
            "  - python-docx (Word 处理)\n"
            "  - WeasyPrint (PDF 生成)\n"
            "  - PyQt5 (GUI)\n\n"
            "2024"
        )


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
