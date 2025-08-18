#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段A功能測試腳本 - Caption識別與圖文配對驗證
"""

import sys
import os

# 直接導入本地模組
from caption_extractor import PDFCaptionContextProcessor

def test_stage_a_functionality():
    """測試階段A的Caption識別功能"""
    
    print("🧪 開始測試階段A功能：Caption識別與圖文配對")
    print("=" * 60)
    
    # 測試檔案路徑 (使用相對於專案根目錄的路徑)
    test_files = [
        "../../pdfFiles/計概第一章.pdf",
        "../../pdfFiles/計概第二章.pdf"
    ]
    
    processor = PDFCaptionContextProcessor()
    
    for pdf_file in test_files:
        if os.path.exists(pdf_file):
            print(f"\n📄 測試檔案: {pdf_file}")
            print("-" * 40)
            
            try:
                # 執行Caption識別
                result = processor.process_pdf(pdf_file)
                
                # 顯示統計結果
                print(f"📊 處理統計:")
                print(f"   • 找到圖表Caption: {len(result.caption_pairs)}個")
                print(f"   • 圖片相關: {len([p for p in result.caption_pairs if p.caption_info.caption_type == '圖'])}")
                print(f"   • 表格相關: {len([p for p in result.caption_pairs if p.caption_info.caption_type == '表'])}")
                
                # 顯示前5個識別結果
                print(f"\n🔍 識別結果預覽 (前5個):")
                for i, pair in enumerate(result.caption_pairs[:5]):
                    caption = pair.caption_info
                    print(f"   {i+1}. {caption.caption_type} {caption.number}: {caption.title}")
                    print(f"      位置: 第{caption.page}頁")
                    print(f"      信心度: {caption.confidence:.2f}")
                    if pair.context_info:
                        print(f"      相關內文: {len(pair.context_info.related_paragraphs)}段")
                    print()
                
                # 顯示內文引用統計
                if result.context_references:
                    print(f"📝 內文引用統計: 找到{len(result.context_references)}個引用")
                    for ref in result.context_references[:3]:
                        print(f"   • 第{ref['page']}頁: {ref['text'][:50]}...")
                
                print(f"\n✅ {pdf_file} 測試完成")
                
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
    
    from caption_extractor import CaptionPatterns
    
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
    
    # 測試Caption模式
    test_caption_patterns()
    
    # 測試完整功能
    test_stage_a_functionality()