#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段A功能測試腳本 - Caption識別與圖文配對驗證
"""

import sys
import os
from pathlib import Path

# 設定 UTF-8 編碼輸出，解決 Windows emoji 顯示問題
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        # 如果 reconfigure 不支援，嘗試其他方法
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 添加路徑並導入本地模組
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from enhanced_version.backend.caption_extractor_sA import PDFCaptionContextProcessor

def test_stage_a_functionality():
    """測試階段A的Caption識別功能"""
    
    print("🧪 開始測試階段A功能：Caption識別與圖文配對")
    print("=" * 60)
    
    # 測試檔案路徑 (動態計算相對路徑)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    test_files = [
        project_root / "pdfFiles" / "計概第一章.pdf",
        project_root / "pdfFiles" / "計概第二章.pdf"
    ]
    
    processor = PDFCaptionContextProcessor()
    
    for pdf_file in test_files:
        if pdf_file.exists():
            filename = pdf_file.name
            print(f"\n📄 測試檔案: {filename}")
            print("-" * 40)
            
            try:
                # 執行Caption識別
                result = processor.process_pdf(str(pdf_file))
                
                # 顯示統計結果 (result是配對列表)
                print(f"📊 處理統計:")
                print(f"   • 找到圖表Caption: {len(result)}個")
                print(f"   • 圖片相關: {len([p for p in result if p.caption.caption_type == 'figure'])}")
                print(f"   • 表格相關: {len([p for p in result if p.caption.caption_type == 'table'])}")
                
                # 顯示前5個識別結果
                print(f"\n🔍 識別結果預覽 (前5個):")
                for i, pair in enumerate(result[:5]):
                    caption = pair.caption
                    print(f"   {i+1}. {caption.caption_type} {caption.number}: {caption.text[:50]}...")
                    print(f"      位置: 第{caption.page_number}頁")
                    print(f"      信心度: {pair.pairing_confidence:.2f}")
                    print(f"      相關內文: {len(pair.contexts)}段")
                    print()
                
                # 顯示內文引用統計
                total_contexts = sum(len(pair.contexts) for pair in result)
                if total_contexts > 0:
                    print(f"\n📝 內文引用統計: 找到{total_contexts}個引用")
                    with_contexts = len([p for p in result if len(p.contexts) > 0])
                    print(f"   • 有引用的Caption: {with_contexts}個")
                
                print(f"\n✅ {filename} 測試完成")
                
            except Exception as e:
                print(f"❌ 測試失敗: {str(e)}")
        else:
            print(f"⚠️  檔案不存在: {pdf_file}")
    
    print("\n" + "=" * 60)
    print("🎯 階段A功能測試完成")

def test_caption_patterns():
    """測試Caption識別模式"""
    
    print("\n🔧 測試Caption識別模式")
    print("-" * 30)
    
    from enhanced_version.backend.caption_extractor_sA import CaptionPatterns
    
    test_cases = [
        "圖1-1 中國的算盤",
        "ʩ 圖1-1 中國的算盤", 
        "表2.3 統計數據",
        "Figure 1.1 Computer Architecture",
        "圖 3.5：資料處理流程",
        "表一、基本資料"
    ]
    
    patterns = CaptionPatterns()
    
    for test_text in test_cases:
        match = patterns.find_caption_match(test_text)
        if match:
            print(f"✅ '{test_text}' → 類型:{match['type']}, 編號:{match['number']}, 標題:{match['title']}")
        else:
            print(f"❌ '{test_text}' → 未識別")

if __name__ == "__main__":
    # 設置編碼
    if sys.platform == "win32":
        import locale
        locale.setlocale(locale.LC_ALL, 'zh_TW.UTF-8')
    
    print("🚀 階段A功能測試腳本")
    print("測試範圍: Caption識別、圖文配對、內文引用搜尋")
    print()
    
    print("📝 跳過模式測試，直接測試完整功能")
    print()
    
    # 測試完整功能
    test_stage_a_functionality()