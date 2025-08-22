# PDF 圖表自動切割工具 設定說明

## 🚀 快速開始

### 1. 創建虛擬環境

```bash
# 在項目根目錄執行
python -m venv pdf_cutting_env

# Windows (PowerShell)
pdf_cutting_env\Scripts\Activate.ps1

# Windows (CMD)
pdf_cutting_env\Scripts\activate.bat

# macOS/Linux
source pdf_cutting_env/bin/activate
```

### 2. 安裝依賴套件

```bash
# 切換到 pdf_Cutting_TextReplaceImage 目錄
cd modules/pdf_Cutting_TextReplaceImage

# 安裝依賴
pip install -r requirements.txt
```

### 3. 準備測試PDF檔案

將你的PDF檔案放在以下位置：
- `pdfFiles/` - 主要PDF檔案
- `pdfFiles/multi_data/sys_check_digital/` - 數位PDF檔案  
- `pdfFiles/multi_data/sys_check_scanned/` - 掃描PDF檔案

### 4. 執行腳本

```bash
# 確保在 modules/pdf_Cutting_TextReplaceImage 目錄下
python test_image_cutting_runner.py
```

## 📖 使用方法

### 互動式選擇（預設）
```bash
python test_image_cutting_runner.py
```
會顯示所有可用PDF檔案，讓你選擇要處理的檔案。

選擇方式：
- 單一檔案：`1`
- 範圍選擇：`1-3`  
- 多檔案選擇：`1,3,5`
- 全部檔案：`all`
- 取消：直接按 Enter

### 其他使用方式

```bash
# 列出所有可用PDF檔案
python test_image_cutting_runner.py --list

# 處理所有檔案
python test_image_cutting_runner.py --all  

# 處理指定檔案
python test_image_cutting_runner.py "../../pdfFiles/計概第一章.pdf"

# 顯示使用說明
python test_image_cutting_runner.py --help
```

## 📁 輸出結果

處理完成後，結果會儲存在：
```
modules/pdf_Cutting_TextReplaceImage/test_ImageCut_result/
├── PDF檔案1/
│   ├── chart_page1_img1.png
│   ├── chart_page1_img2.png
│   └── PDF檔案1_metadata.json
└── PDF檔案2/
    ├── chart_page1_img1.png
    └── PDF檔案2_metadata.json
```

## 🔧 故障排除

### 問題1：ModuleNotFoundError: No module named 'fitz'
**解決方案：**
```bash
pip install PyMuPDF
```

### 問題2：找不到PDF檔案
**解決方案：**
- 確保PDF檔案放在正確的資料夾位置
- 使用 `--list` 查看可用的PDF檔案

### 問題3：權限錯誤
**解決方案：**
- 確保對輸出目錄有寫入權限
- Windows用戶可能需要以系統管理員身分執行

### 問題4：輸出資料夾在錯誤位置
**解決方案：**
- 確保在 `modules/pdf_Cutting_TextReplaceImage/` 目錄下執行腳本
- 不要在項目根目錄執行

## 📋 依賴套件

- PyMuPDF >= 1.24.0

## 🤝 組員協作

1. 每位組員需要自己建立虛擬環境並安裝依賴
2. PDF檔案需要各自準備（不在git中）
3. 輸出結果資料夾(`test_ImageCut_result`)不會同步到git