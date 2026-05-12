# DocBridge

**OCR機能を内置した、轻量のドキュメントフォーマット変換ツール。**

PDF、DOCX、DOC、TXTとMarkdown間の双方向変換に対応。スキャン文書や画像ベースのPDFからテキストを自動検出・抽出できます。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 機能

- **マルチフォーマット変換** — PDF、DOCX、DOC、TXT ↔ Markdown、Markdown → PDF/DOCX
- **スマートOCR** — スキャン文書・画像ベースPDFのテキストを自動認識
- **3種類のインターフェース** — デスクトップGUI（PyQt5）、Web GUI（Gradio）、CLI
- **バッチ処理** — フォルダ再帰スキャン対応
- **クロスプラットフォーム** — Windows、Linux、macOS

---

## 対応フォーマット

| 入力 | 出力 | 説明 |
|-----|-----|------|
| PDF | MD | テキスト/ベクターフォントPDFは自動処理 |
| PDF | MD | **スキャン/画像ベースPDFはOCR自動認識** |
| DOCX | MD | Word文書 |
| DOC | MD | 旧形式Word |
| TXT | MD | プレーンテキスト |
| MD | PDF | WeasyPrintが必要 |
| MD | DOCX | Word文書 |

---

## クイックスタート

### 環境要件

- Python 3.11+
- Windows 10/11 / Linux / macOS

### 依存関係のインストール

```bash
pip install -r requirements.txt
```

### ワンクリック起動（Windows）

`start.bat` をダブルクリックでデスクトップGUIを起動。

### その他の起動方法

```bash
# デスクトップGUI（推奨）
python src/gui_qt.py

# Webインターフェース
python src/gui.py

# コマンドライン
python -m src.cli convert input.pdf output.md
python -m src.cli batch "*.pdf" ./output/
```

---

## OCRの動作原理

PDFが**画像ベース（スキャン）**または**ベクターフォント異常**と判定された場合、OCRモードに自動切り替え：

1. **自動検出** — PDFの文字量を分析し、1ページ平均100文字未満でOCRをトリガー
2. **ページ描画** — PyMuPDFで各ページを150 DPI高解像度画像として描画
3. **文字認識** — RapidOCRが画像からテキストを抽出（中国語・英語・多言語対応）
4. **構造再構成** — 読取順序でテキストブロックを整理、見出し/リスト/段落を識別
5. **出力** — 構造化されたMarkdownファイルを生成

---

## プロジェクト構造

```
DocBridge/
├── src/
│   ├── converters/          # 変換コアモジュール
│   ├── cli.py              # CLIエントリーポイント
│   ├── gui.py              # Gradio Webインターフェース
│   └── gui_qt.py           # PyQt5 デスクトップインターフェース
├── tests/                  # テストファイル
├── docs/                   # ドキュメント
├── requirements.txt        # Python依存関係
├── start.bat               # Windows起動スクリプト
└── README.md
```

---

## ライセンス

MIT License — 詳細は [LICENSE](LICENSE)
