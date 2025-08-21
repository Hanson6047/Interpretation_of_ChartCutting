"""
快速測試腳本 - 驗證 Caption 擷取功能

用於快速驗證階段A的實作是否正確運作
"""

import sys
import os
import logging
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

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_caption_extraction():
    """測試 Caption 擷取功能"""
    print("=" * 60)
    print("🧪 Caption 擷取功能快速測試")
    print("=" * 60)
    
    try:
        # 添加路徑並匯入模組
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        
        from enhanced_version.backend.caption_extractor_sA import PDFCaptionContextProcessor
        print("✅ 模組匯入成功")
        
        # 建立處理器
        processor = PDFCaptionContextProcessor(
            context_window=200,
            min_caption_length=5,
            confidence_threshold=0.3
        )
        print("✅ 處理器建立成功")
        
        # 測試 PDF 路徑 (動態計算相對路徑)
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent.parent
        test_pdf_path = project_root / "pdfFiles" / "計概第一章.pdf"
        
        if not test_pdf_path.exists():
            print(f"❌ 測試 PDF 檔案不存在: {test_pdf_path}")
            # 嘗試其他檔案
            pdf_dir = Path("ignore_file/test_pdf_data/sys_check_digital")
            if pdf_dir.exists():
                pdf_files = list(pdf_dir.glob("*.pdf"))
                if pdf_files:
                    test_pdf_path = pdf_files[0]
                    print(f"🔄 使用替代檔案: {test_pdf_path.name}")
                else:
                    print("❌ 找不到任何 PDF 檔案")
                    return False
            else:
                print("❌ 測試目錄不存在")
                return False
        
        print(f"📁 測試檔案: {test_pdf_path.name}")
        
        # 執行處理
        print("\n🔄 開始處理 PDF...")
        pairs = processor.process_pdf(str(test_pdf_path))
        
        print(f"✅ 處理完成，找到 {len(pairs)} 個配對結果")
        
        # 顯示結果
        if pairs:
            print("\n📊 處理結果詳情:")
            for i, pair in enumerate(pairs, 1):
                print(f"\n--- 配對 {i} ---")
                print(f"Caption: {pair.caption.caption_type} {pair.caption.number}")
                print(f"內容: {pair.caption.text[:100]}...")
                print(f"頁數: {pair.caption.page_number}")
                print(f"引用數量: {len(pair.contexts)}")
                print(f"信心度: {pair.pairing_confidence:.3f}")
                
                if pair.contexts:
                    print("相關引用:")
                    for j, context in enumerate(pair.contexts[:2], 1):  # 只顯示前2個
                        print(f"  {j}. {context.text} (頁 {context.page_number})")
        else:
            print("⚠️ 沒有找到任何 Caption 配對結果")
        
        # 統計資訊
        stats = processor.get_processing_stats(pairs)
        print(f"\n📈 統計資訊:")
        print(f"總配對數: {stats['total_pairs']}")
        if 'types_distribution' in stats:
            print(f"類型分布: {stats['types_distribution']}")
        if 'confidence_stats' in stats:
            conf = stats['confidence_stats']
            print(f"信心度範圍: {conf['min']:.3f} - {conf['max']:.3f} (平均: {conf['avg']:.3f})")
        
        return True
        
    except ImportError as e:
        print(f"❌ 匯入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 處理過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pattern_matching():
    """測試正則表達式模式"""
    print("\n" + "=" * 60)
    print("🧪 正則表達式模式測試")
    print("=" * 60)
    
    try:
        from modules.pdf_Cutting_TextReplaceImage.enhanced_version.backend.caption_extractor_sA import CaptionExtractor
        
        extractor = CaptionExtractor()
        
        # 測試 Caption 模式
        test_captions = [
            "圖 1：測試圖片說明",
            "表 2.1：統計資料表",
            "Figure 3: Test image description",
            "圖表 4.2：流程圖說明",
            "圖片 5 顯示結果",
        ]
        
        print("測試 Caption 識別:")
        for text in test_captions:
            found = False
            for pattern in extractor.caption_patterns:
                match = pattern.search(text)
                if match:
                    groups = match.groups()
                    number = f"{groups[0]}.{groups[1]}" if groups[1] else groups[0]
                    print(f"✅ '{text}' -> 編號: {number}, 內容: {groups[2]}")
                    found = True
                    break
            if not found:
                print(f"❌ '{text}' -> 無匹配")
        
        # 測試引用模式
        test_references = [
            "如圖 1 所示，結果很明顯",
            "參見表 2.1 的統計數據",
            "見圖表 3 的詳細說明",
            "as shown in Figure 4",
        ]
        
        print("\n測試引用識別:")
        for text in test_references:
            found = False
            for pattern in extractor.reference_patterns:
                match = pattern.search(text)
                if match:
                    groups = match.groups()
                    number = f"{groups[0]}.{groups[1]}" if len(groups) > 1 and groups[1] else groups[0]
                    print(f"✅ '{text}' -> 引用編號: {number}")
                    found = True
                    break
            if not found:
                print(f"❌ '{text}' -> 無匹配")
        
        return True
        
    except Exception as e:
        print(f"❌ 模式測試發生錯誤: {e}")
        return False


def main():
    """主測試函式"""
    print("🚀 開始快速驗證階段A功能...")
    
    # 測試1: 模式匹配
    pattern_ok = test_pattern_matching()
    
    # 測試2: 實際PDF處理
    pdf_ok = test_caption_extraction()
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 測試結果總結")
    print("=" * 60)
    print(f"正則表達式模式: {'✅ 通過' if pattern_ok else '❌ 失敗'}")
    print(f"PDF 處理功能: {'✅ 通過' if pdf_ok else '❌ 失敗'}")
    
    overall_result = pattern_ok and pdf_ok
    print(f"\n🎯 整體結果: {'✅ 階段A功能正常' if overall_result else '❌ 需要修正'}")
    
    return overall_result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)