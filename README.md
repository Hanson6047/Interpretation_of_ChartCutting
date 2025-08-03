# PDF 類型分類器 (PDF Type Classifier)

自動判斷 PDF 檔案是數位生成還是掃描型的 Python 工具。

## 功能特點

- 🔍 **智慧分析**：自動識別 PDF 檔案類型（數位 vs 掃描）
- 📊 **詳細報告**：提供每頁的分類資訊和統計摘要
- 🚀 **批量處理**：支援目錄批量分析，可遞迴搜尋
- 🔧 **系統整合**：易於整合到更大的文件處理系統
- 📈 **進度追蹤**：即時顯示處理進度和成功率

## 安裝

### 1. 克隆專案
```bash
git clone <your-repo-url>
cd Interpretation_of_ChartCutting
```

### 2. 建立虛擬環境 (建議)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 命令列使用

#### 分析當前目錄所有 PDF
```bash
python pdf_classifier.py
```

#### 分析指定目錄
```bash
python pdf_classifier.py /path/to/pdf/folder
```

#### 分析單一檔案
```bash
python pdf_classifier.py single_file.pdf
```

### 2. Python 程式中使用

```python
from pdf_classifier import classify_pdf_type, batch_classify_pdfs

# 分析單一檔案
result = classify_pdf_type("example.pdf")
print(f"PDF 類型: {result['type']}")
print(f"文字頁面: {result['text_pages']}")
print(f"圖片頁面: {result['image_pages']}")

# 批量分析
results = batch_classify_pdfs("pdf_folder/")
for file_path, classification in results.items():
    print(f"{file_path}: {classification['type']}")
```

### 3. 系統整合

```python
from integration_example import DocumentProcessor

processor = DocumentProcessor()

# 根據 PDF 類型選擇處理策略
result = processor.process_document("document.pdf")
print(f"處理方法: {result['method']}")
```

## 輸出格式

函式回傳的字典格式：

```python
{
    "type": "digital" | "scanned",     # PDF 類型
    "text_pages": [1, 2, 3],           # 包含文字的頁數
    "image_pages": [4, 5, 6]           # 主要為圖片的頁數
}
```

## 檔案結構

```
├── pdf_classifier.py          # 主要分類功能
├── test_pdf_classifier.py     # 測試工具
├── integration_example.py     # 系統整合範例
├── requirements.txt           # 依賴套件
└── README.md                 # 本說明文件
```

## 測試

### 執行測試程式
```bash
python test_pdf_classifier.py
```

### 測試選項
1. **預設測試** - 測試指定檔案清單
2. **互動式測試** - 手動輸入檔案路徑
3. **快速測試** - 自動掃描當前目錄

### 建議的測試資料夾結構
```
test_pdfs/
├── digital/       # 數位PDF (Word轉檔、純文字)
├── scanned/       # 掃描PDF (紙本掃描)  
├── mixed/         # 混合PDF (文字+圖片)
└── edge_cases/    # 特殊情況 (空檔、損壞檔)
```

## 分類邏輯

### 數位 PDF 特徵
- 可選取的文字內容
- 檔案大小相對較小
- 文字清晰，無掃描雜訊

### 掃描 PDF 特徵  
- 文字為圖片形式
- 檔案大小較大
- 可能包含掃描雜訊或歪斜

### 判斷準則
- 文字量 > 50 字符：視為有意義文字
- 圖片覆蓋率 > 30%：考慮為圖片頁面
- 綜合評估文字與圖片比例決定最終分類

## 系統需求

- Python 3.7+
- PyMuPDF (fitz) 1.24.0+
- Windows/macOS/Linux

## 常見問題

### Q: 無法正確識別某些 PDF？
A: 可能是特殊格式或保護的 PDF，請檢查檔案是否可正常開啟。

### Q: 中文字符顯示問題？
A: 程式已包含 UTF-8 編碼設定，如仍有問題請檢查終端機編碼設定。

### Q: 大檔案處理很慢？
A: 建議先用 `batch_classify_pdfs` 進行批量分析，獲得概覽後再針對特定檔案進行詳細處理。

## 授權

本專案為開源專案，歡迎使用和貢獻。

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案！