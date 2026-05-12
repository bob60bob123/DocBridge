"""
格式转换器 - 命令行界面
支持批量转换、进度显示、多种输出格式
"""

import click
import glob
import os
import sys
from pathlib import Path
from typing import Dict, Type, List, Tuple
from tqdm import tqdm

from converters.base import BaseConverter
from converters.pdf_converter import PDFToMDConverter
from converters.docx_converter import DOCXToMDConverter
from converters.doc_converter import DOCToMDConverter
from converters.txt_converter import TXTToMDConverter
from converters import get_pdf_to_md_converter

# MD 转换器（weasyprint 可选）
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


def _get_pdf_converter(input_path: str = None) -> BaseConverter:
    """获取适合的PDF转MD转换器（自动检测图片型PDF）"""
    return get_pdf_to_md_converter(input_path)


# 转换器注册表（PDF使用工厂函数，延迟获取）
TO_MD_CONVERTERS: Dict[str, callable] = {
    ".pdf": _get_pdf_converter,
    ".docx": lambda _: DOCXToMDConverter(),
    ".doc": lambda _: DOCToMDConverter(),
    ".txt": lambda _: TXTToMDConverter(),
}

MD_CONVERTERS: Dict[str, Type[BaseConverter]] = {}

if MDToPDFConverter:
    MD_CONVERTERS[".pdf"] = MDToPDFConverter
if MDToDOCXConverter:
    MD_CONVERTERS[".docx"] = MDToDOCXConverter


def get_converter(input_ext: str, output_ext: str = ".md",
                  input_path: str = None) -> BaseConverter:
    """根据文件扩展名获取转换器"""
    input_ext = input_ext.lower()

    # MD 转其他格式
    if input_ext in [".md", ".markdown"]:
        if output_ext in MD_CONVERTERS:
            return MD_CONVERTERS[output_ext]()
        if output_ext == ".pdf" and not MDToPDFConverter:
            raise ValueError("MD→PDF 需要安装 weasyprint: pip install weasyprint")
        if output_ext == ".docx" and not MDToDOCXConverter:
            raise ValueError("MD→DOCX 需要安装 python-docx")
        raise ValueError(f"不支持从 MD 转换到 {output_ext}")

    # 其他格式转 MD
    if output_ext == ".md":
        if input_ext in TO_MD_CONVERTERS:
            factory = TO_MD_CONVERTERS[input_ext]
            return factory(input_path)
        raise ValueError(f"不支持的输入格式: {input_ext}")

    raise ValueError(f"不支持的转换: {input_ext} -> {output_ext}")


def convert_file(input_path: str, output_path: str, output_format: str = None) -> Tuple[bool, str]:
    """
    转换单个文件

    Returns:
        Tuple[bool, str]: (是否成功, 消息)
    """
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        input_ext = input_path.suffix.lower()

        # 自动检测输出格式
        if output_path.suffix == "":
            if input_ext in [".md", ".markdown"]:
                output_ext = output_format or ".pdf"
                output_path = output_path.with_suffix(output_ext)
            else:
                output_path = output_path.with_suffix(".md")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 获取转换器
        try:
            converter = get_converter(input_ext, output_path.suffix.lower(),
                                     input_path=str(input_path))
        except Exception as e:
            return False, f"✗ 获取转换器失败: {e}"

        # 执行转换
        converter.convert(str(input_path), str(output_path))
        return True, f"✓ {output_path.name}"

    except FileNotFoundError:
        return False, f"✗ 文件不存在"
    except ValueError as e:
        return False, f"✗ 格式不支持: {e}"
    except Exception as e:
        return False, f"✗ 转换失败: {str(e)}"


def batch_convert(input_pattern: str, output_dir: str, output_format: str = ".md",
                   recursive: bool = False, extensions: List[str] = None) -> Dict:
    """
    批量转换文件

    Args:
        input_pattern: 文件匹配模式
        output_dir: 输出目录
        output_format: 输出格式
        recursive: 是否递归搜索子目录
        extensions: 指定扩展名过滤

    Returns:
        Dict: 转换统计
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 收集文件
    if recursive:
        files = []
        for ext in (extensions or ["*"]):
            if ext == "*":
                pattern = f"**/*"
            else:
                pattern = f"**/*{ext}"
            files.extend(glob.glob(os.path.join(input_pattern, pattern), recursive=True))
        # 去重
        files = list(set(files))
    else:
        files = glob.glob(input_pattern)

    if not files:
        return {"success": 0, "failed": 0, "errors": ["未找到匹配的文件"]}

    # 过滤文件
    if extensions:
        files = [f for f in files if Path(f).suffix.lower() in [f".{ext.lstrip('.')}" for ext in extensions]]

    files.sort()

    # 统计
    success = 0
    failed = 0
    errors = []

    # 进度条
    with tqdm(total=len(files), desc="转换进度", unit="file",
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

        for file in files:
            file_path = Path(file)
            output_file = output_path / file_path.stem

            ok, msg = convert_file(file, str(output_file), output_format)

            if ok:
                success += 1
            else:
                failed += 1
                errors.append(msg)

            pbar.update(1)
            pbar.set_postfix_str(f"成功: {success}, 失败: {failed}")

    return {"success": success, "failed": failed, "errors": errors}


def list_supported_formats():
    """列出所有支持的格式"""
    formats = {
        "输入格式 (→ MD)": {
            "PDF": ".pdf",
            "Word 文档": ".docx",
            "老版 Word": ".doc",
            "文本文件": ".txt",
        },
        "输出格式 (MD →)": {
            "PDF": ".pdf",
            "Word 文档": ".docx",
        }
    }
    return formats


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """格式转换器 - 支持 PDF、DOCX、DOC、TXT 与 MD 之间的相互转换

    示例:
        convert input.pdf output.md
        convert input.md output.pdf
        batch "*.pdf" ./output/
        batch "*.docx" ./md_files/ -f md
    """
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", required=False, type=click.Path())
@click.option("-f", "--format", "output_format", type=click.Choice(["md", "pdf", "docx"]),
              help="指定输出格式")
def convert(input_file: str, output_file: str, output_format: str):
    """转换单个文件

    INPUT_FILE: 输入文件路径
    OUTPUT_FILE: 输出文件路径（可选，自动生成）

    示例:
        converter.exe convert input.pdf output.md
        converter.exe convert input.md output.pdf
        converter.exe convert input.docx  # 自动生成 output.md
    """
    input_path = Path(input_file)

    if not output_file:
        # 自动生成输出文件名
        if input_path.suffix.lower() in [".md", ".markdown"]:
            output_file = str(input_path.with_suffix(".pdf"))
        else:
            output_file = str(input_path.with_suffix(".md"))

    ok, msg = convert_file(input_file, output_file)
    click.echo(msg)

    if not ok:
        sys.exit(1)


@cli.command()
@click.argument("pattern", help="文件匹配模式，如 '*.pdf' 或 './docs/'")
@click.argument("output_dir", help="输出目录")
@click.option("-f", "--format", "output_format",
              type=click.Choice(["md", "pdf", "docx", "all"]),
              default="md", help="输出格式 (默认: md)")
@click.option("-r", "--recursive", is_flag=True,
              help="递归搜索子目录")
@click.option("-e", "--extensions", multiple=True,
              help="指定扩展名过滤，如 -e pdf -e docx")
@click.option("-v", "--verbose", is_flag=True,
              help="显示详细错误信息")
def batch(pattern: str, output_dir: str, output_format: str,
          recursive: bool, extensions: tuple, verbose: bool):
    """批量转换文件

    PATTERN: 文件匹配模式或目录
    OUTPUT_DIR: 输出目录

    示例:
        converter.exe batch "*.pdf" ./output/
        converter.exe batch "*.docx" ./md_files/ -f md
        converter.exe batch ./documents/ ./output/ -r -e pdf -e docx
    """
    # 确定输出格式
    if output_format == "all":
        output_format = None  # 保持原格式转换

    # 批量转换
    result = batch_convert(
        pattern,
        output_dir,
        output_format=f".{output_format}" if output_format else None,
        recursive=recursive,
        extensions=list(extensions) if extensions else None
    )

    # 显示结果
    click.echo("\n" + "=" * 50)
    click.echo(f"批量转换完成")
    click.echo(f"  成功: {result['success']}")
    click.echo(f"  失败: {result['failed']}")

    if verbose and result['errors']:
        click.echo("\n错误详情:")
        for error in result['errors']:
            click.echo(f"  {error}")

    if result['failed'] > 0:
        sys.exit(1)


@cli.command()
def info():
    """显示支持的格式"""
    formats = list_supported_formats()

    click.echo("=" * 50)
    click.echo("格式转换器 v0.2.0")
    click.echo("=" * 50)

    click.echo("\n📥 输入格式 (转换为 MD):")
    for name, ext in formats["输入格式 (→ MD)"].items():
        click.echo(f"  {name:15} {ext}")

    click.echo("\n📤 输出格式 (MD 转换为):")
    for name, ext in formats["输出格式 (MD →)"].items():
        click.echo(f"  {name:15} {ext}")

    click.echo("\n📋 转换矩阵:")
    click.echo("  PDF  → MD  ✓ (文字型/扫描件自动识别)")
    click.echo("  DOCX → MD  ✓")
    click.echo("  DOC  → MD  ✓ (需要 antiword 或 LibreOffice)")
    click.echo("  TXT  → MD  ✓")
    click.echo("  MD   → PDF ✓")
    click.echo("  MD   → DOCX ✓")
    click.echo("\n🔍 图片型PDF(扫描件): 使用 RapidOCR 自动识别文字")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", "output_dir", type=click.Path(),
              help="图片输出目录")
def extract_images(input_file: str, output_dir: str):
    """从 PDF 中提取图片

    INPUT_FILE: PDF 文件路径
    OUTPUT_DIR: 图片输出目录（默认: ./images/）
    """
    if not output_dir:
        output_dir = "./images/"

    try:
        converter = PDFToMDConverter()
        images = converter.extract_images(input_file, output_dir)

        click.echo(f"✓ 成功提取 {len(images)} 张图片:")
        for img in images:
            click.echo(f"  {img}")
    except Exception as e:
        click.echo(f"✗ 提取失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
