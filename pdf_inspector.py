"""
PDF 內容檢查器 - 查看實際的PDF結構和文字內容
"""

import sys
import fitz  # PyMuPDF
import re
from pathlib import Path

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

def get_block_font_info(block):
    """取得區塊的字體資訊"""
    font_info = {}
    
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            if not font_info and span.get("font"):
                font_info = {
                    'font': span.get('font', ''),
                    'size': span.get('size', 0),
                    'flags': span.get('flags', 0)
                }
                break
        if font_info:
            break
    
    return font_info

def inspect_pdf_content():
    """檢查PDF的實際內容"""
    
    pdf_path = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
    
    if not pdf_path.exists():
        print("❌ PDF檔案不存在")
        return
    
    print("🔍 PDF 內容檢查")
    print("=" * 60)
    
    try:
        pdf_doc = fitz.open(str(pdf_path))
        
        # 檢查前3頁的詳細內容
        for page_num in range(min(3, len(pdf_doc))):
            page = pdf_doc.load_page(page_num)
            
            print(f"\n📄 第 {page_num + 1} 頁內容:")
            print("-" * 40)
            
            # 方法1: 取得純文字
            text = page.get_text()
            lines = text.split('\n')
            
            print("🔤 純文字內容 (前20行):")
            for i, line in enumerate(lines[:20]):
                if line.strip():
                    print(f"{i+1:2d}: {line}")
            
            if len(lines) > 20:
                print(f"... 還有 {len(lines) - 20} 行")
            
            # 方法2: 取得帶格式的文字區塊
            print(f"\n📝 文字區塊分析:")
            blocks = page.get_text("dict")
            
            caption_candidates = []
            
            for block_num, block in enumerate(blocks.get("blocks", [])):
                if "lines" not in block:
                    continue
                
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                
                block_text = block_text.strip()
                if not block_text:
                    continue
                
                # 檢查是否可能是Caption
                if any(keyword in block_text for keyword in ["圖", "表", "Figure", "Table"]):
                    caption_candidates.append({
                        'block_num': block_num,
                        'text': block_text,
                        'bbox': block["bbox"],
                        'font_info': get_block_font_info(block)
                    })
            
            if caption_candidates:
                print(f"📊 可能的Caption候選 ({len(caption_candidates)}個):")
                for i, candidate in enumerate(caption_candidates):
                    print(f"  {i+1}. {candidate['text'][:80]}...")
                    print(f"     位置: {candidate['bbox']}")
                    if candidate['font_info']:
                        print(f"     字體: {candidate['font_info']}")
            else:
                print("❌ 本頁沒有發現Caption候選項")
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"❌ 檢查PDF時發生錯誤: {e}")

def search_specific_patterns():
    """搜尋特定的文字模式"""
    
    pdf_path = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
    
    if not pdf_path.exists():
        return
    
    print(f"\n🔍 特定模式搜尋")
    print("=" * 60)
    
    try:
        pdf_doc = fitz.open(str(pdf_path))
        
        # 搜尋包含數字的行
        number_lines = []
        figure_lines = []
        
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            text = page.get_text()
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # 搜尋包含數字和可能是Caption的行
                
                # 包含 圖/表 + 數字的行
                if re.search(r'[圖表]\s*\d', line):
                    figure_lines.append({
                        'page': page_num + 1,
                        'line': line_num + 1,
                        'text': line
                    })
                
                # 包含連續數字的行（可能是編號）
                if re.search(r'\d+[-\.]\d+', line):
                    number_lines.append({
                        'page': page_num + 1,
                        'line': line_num + 1, 
                        'text': line
                    })
        
        print(f"📊 包含'圖/表+數字'的行 ({len(figure_lines)}個):")
        for item in figure_lines[:10]:
            print(f"  頁{item['page']}: {item['text']}")
        
        print(f"\n📊 包含數字編號的行 ({len(number_lines)}個，顯示前10個):")
        for item in number_lines[:10]:
            print(f"  頁{item['page']}: {item['text']}")
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"❌ 模式搜尋時發生錯誤: {e}")

def compare_with_auto_results():
    """對比自動識別的結果"""
    
    print(f"\n🤖 對比自動識別結果")
    print("=" * 60)
    
    try:
        from caption_extractor import PDFCaptionContextProcessor
        
        processor = PDFCaptionContextProcessor()
        pdf_path = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
        
        pairs = processor.process_pdf(str(pdf_path))
        
        print(f"自動識別了 {len(pairs)} 個結果，讓我們看看前10個:")
        
        for i, pair in enumerate(pairs[:10], 1):
            print(f"\n{i:2d}. Caption: {pair.caption.caption_type} {pair.caption.number}")
            print(f"    頁數: {pair.caption.page_number}")  
            print(f"    內容: {pair.caption.text}")
            print(f"    信心度: {pair.pairing_confidence:.3f}")
            
            # 檢查這個Caption是否合理
            caption_text = pair.caption.text
            
            # 簡單的合理性檢查
            reasonable = True
            reasons = []
            
            if len(caption_text) < 10:
                reasonable = False
                reasons.append("內容太短")
            
            if not any(char.isalpha() for char in caption_text):
                reasonable = False
                reasons.append("沒有文字內容")
            
            if caption_text.count('(') != caption_text.count(')'):
                reasons.append("可能截斷不完整")
            
            print(f"    合理性: {'✅' if reasonable else '❌'} {' '.join(reasons)}")
            
    except Exception as e:
        print(f"❌ 對比時發生錯誤: {e}")

def extract_sample_pages():
    """提取樣本頁面的完整內容"""
    
    print(f"\n📋 完整頁面內容樣本")
    print("=" * 60)
    
    pdf_path = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
    
    if not pdf_path.exists():
        return
    
    try:
        pdf_doc = fitz.open(str(pdf_path))
        
        # 只看第2頁（通常有比較多內容）
        if len(pdf_doc) >= 2:
            page = pdf_doc.load_page(1)  # 第2頁 (索引1)
            
            print("第2頁完整內容:")
            print("-" * 40)
            
            text = page.get_text()
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    # 標記可能的Caption行
                    marker = ""
                    if re.search(r'圖\s*\d', line):
                        marker = " 📊"
                    elif re.search(r'表\s*\d', line):  
                        marker = " 📋"
                    elif re.search(r'\d+[\.-]\d+', line):
                        marker = " 🔢"
                    
                    print(f"{i+1:3d}: {line}{marker}")
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"❌ 提取頁面內容時發生錯誤: {e}")

def main():
    """主檢查函數"""
    
    print("🔍 開始檢查PDF內容和Caption識別結果...")
    
    # 1. 檢查PDF基本內容
    inspect_pdf_content()
    
    # 2. 搜尋特定模式
    search_specific_patterns()
    
    # 3. 提取完整頁面樣本
    extract_sample_pages()
    
    # 4. 對比自動識別結果
    compare_with_auto_results()
    
    print(f"\n🎯 診斷總結")
    print("=" * 60)
    print("基於上述分析，我們可以判斷:")
    print("1. PDF的實際Caption格式是什麼")
    print("2. 自動識別是否準確")
    print("3. 需要如何調整我們的演算法")

if __name__ == "__main__":
    main()