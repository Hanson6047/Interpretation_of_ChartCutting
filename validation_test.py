"""
驗證測試腳本 - 詳細檢查 Caption 識別準確性

提供多種驗證方式來確認 Caption 處理的正確性
"""

import sys
import os
from pathlib import Path

# 設定 UTF-8 編碼輸出
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

def extract_raw_pdf_text(pdf_path):
    """提取 PDF 原始文字，用於人工比對"""
    import fitz
    
    text_by_page = {}
    try:
        pdf_doc = fitz.open(pdf_path)
        for page_num in range(len(pdf_doc)):
            page = pdf_doc.load_page(page_num)
            text = page.get_text()
            text_by_page[page_num + 1] = text
        pdf_doc.close()
    except Exception as e:
        print(f"❌ 提取PDF文字失敗: {e}")
    
    return text_by_page

def find_manual_captions(text_by_page):
    """手動搜尋 Caption 模式，用於對比"""
    import re
    
    manual_captions = []
    
    # 簡化的 Caption 搜尋模式
    patterns = [
        r'圖\s*(\d+[\.-]\d+|\d+)[:：]\s*(.+)',
        r'表\s*(\d+[\.-]\d+|\d+)[:：]\s*(.+)', 
        r'Figure\s*(\d+[\.-]\d+|\d+)[:：.]?\s*(.+)',
        r'Table\s*(\d+[\.-]\d+|\d+)[:：.]?\s*(.+)',
    ]
    
    for page_num, text in text_by_page.items():
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    caption_type = "figure" if "圖" in pattern or "Figure" in pattern else "table"
                    manual_captions.append({
                        'page': page_num,
                        'line': line_num + 1,
                        'number': match.group(1),
                        'text': match.group(2).strip(),
                        'type': caption_type,
                        'full_line': line,
                        'context_before': lines[max(0, line_num-1):line_num],
                        'context_after': lines[line_num+1:line_num+3]
                    })
    
    return manual_captions

def find_manual_references(text_by_page):
    """手動搜尋引用模式"""
    import re
    
    manual_refs = []
    
    patterns = [
        r'如圖\s*(\d+[\.-]\d+|\d+)',
        r'見圖\s*(\d+[\.-]\d+|\d+)', 
        r'參見?圖\s*(\d+[\.-]\d+|\d+)',
        r'圖\s*(\d+[\.-]\d+|\d+)\s*所?示',
        r'圖\s*(\d+[\.-]\d+|\d+)\s*中',
        r'as shown in Figure\s*(\d+[\.-]\d+|\d+)',
        r'see Figure\s*(\d+[\.-]\d+|\d+)',
    ]
    
    for page_num, text in text_by_page.items():
        lines = text.split('\n')
        for line_num, line in enumerate(lines):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    manual_refs.append({
                        'page': page_num,
                        'line': line_num + 1,
                        'number': match.group(1),
                        'full_match': match.group(0),
                        'context': line.strip(),
                        'position': match.span()
                    })
    
    return manual_refs

def compare_results(auto_pairs, manual_captions, manual_refs):
    """比較自動識別結果與手動搜尋結果"""
    
    print("\n🔍 詳細驗證分析")
    print("=" * 80)
    
    # 1. Caption 比較
    print(f"\n📊 Caption 比較:")
    print(f"自動識別: {len(auto_pairs)} 個")
    print(f"手動搜尋: {len(manual_captions)} 個")
    
    # 建立手動 Caption 的索引
    manual_caption_keys = set()
    for cap in manual_captions:
        key = f"{cap['type']}_{cap['number']}"
        manual_caption_keys.add(key)
    
    # 檢查自動識別的準確性
    auto_caption_keys = set()
    correct_matches = 0
    
    print(f"\n✅ 正確識別的 Caption:")
    for pair in auto_pairs:
        key = f"{pair.caption.caption_type}_{pair.caption.number}"
        auto_caption_keys.add(key)
        
        # 尋找匹配的手動 Caption
        matching_manual = None
        for manual_cap in manual_captions:
            manual_key = f"{manual_cap['type']}_{manual_cap['number']}"
            if manual_key == key:
                matching_manual = manual_cap
                break
        
        if matching_manual:
            correct_matches += 1
            print(f"  ✓ {key}: {pair.caption.text[:50]}...")
        else:
            print(f"  ❌ {key}: 可能是誤判 - {pair.caption.text[:50]}...")
    
    # 檢查遺漏的 Caption
    missed_captions = manual_caption_keys - auto_caption_keys
    if missed_captions:
        print(f"\n❌ 遺漏的 Caption:")
        for missed_key in missed_captions:
            for manual_cap in manual_captions:
                if f"{manual_cap['type']}_{manual_cap['number']}" == missed_key:
                    print(f"  ❌ {missed_key}: {manual_cap['text'][:50]}...")
                    break
    
    # 2. 引用比較
    print(f"\n📊 引用比較:")
    auto_ref_count = sum(len(pair.contexts) for pair in auto_pairs)
    print(f"自動識別: {auto_ref_count} 個")
    print(f"手動搜尋: {len(manual_refs)} 個")
    
    # 3. 準確率計算
    precision = correct_matches / len(auto_pairs) if auto_pairs else 0
    recall = correct_matches / len(manual_captions) if manual_captions else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n📈 性能指標:")
    print(f"準確率 (Precision): {precision:.3f} ({correct_matches}/{len(auto_pairs)})")
    print(f"召回率 (Recall): {recall:.3f} ({correct_matches}/{len(manual_captions)})")
    print(f"F1 分數: {f1_score:.3f}")
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'correct_matches': correct_matches,
        'total_auto': len(auto_pairs),
        'total_manual': len(manual_captions),
        'missed_captions': missed_captions
    }

def detailed_caption_analysis(auto_pairs, manual_captions):
    """詳細分析每個 Caption"""
    
    print(f"\n🔬 詳細 Caption 分析")
    print("=" * 80)
    
    print(f"\n📋 手動搜尋到的 Caption:")
    for i, cap in enumerate(manual_captions[:10], 1):  # 只顯示前10個
        print(f"{i:2d}. {cap['type']} {cap['number']} (頁{cap['page']})")
        print(f"    內容: {cap['text'][:80]}...")
        print(f"    完整行: {cap['full_line'][:100]}...")
        print()
    
    if len(manual_captions) > 10:
        print(f"... 還有 {len(manual_captions) - 10} 個 Caption")

def interactive_validation():
    """互動式驗證"""
    
    print(f"\n🤔 互動式驗證模式")
    print("=" * 80)
    print("現在將顯示自動識別的結果，請手動確認正確性...")
    
    try:
        from caption_extractor import PDFCaptionContextProcessor
        
        processor = PDFCaptionContextProcessor()
        test_pdf = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
        
        if not test_pdf.exists():
            print("❌ 測試檔案不存在")
            return
        
        pairs = processor.process_pdf(str(test_pdf))
        
        print(f"\n找到 {len(pairs)} 個配對結果")
        print("請逐一確認 (y=正確, n=錯誤, s=跳過, q=退出):")
        
        correct_count = 0
        total_checked = 0
        
        for i, pair in enumerate(pairs[:10], 1):  # 只檢查前10個
            print(f"\n--- 配對 {i}/{min(10, len(pairs))} ---")
            print(f"類型: {pair.caption.caption_type}")
            print(f"編號: {pair.caption.number}")
            print(f"頁數: {pair.caption.page_number}")
            print(f"內容: {pair.caption.text}")
            print(f"信心度: {pair.pairing_confidence:.3f}")
            
            if pair.contexts:
                print("引用:")
                for ctx in pair.contexts[:3]:  # 最多顯示3個引用
                    print(f"  - {ctx.text} (頁{ctx.page_number})")
            
            while True:
                response = input("這個結果正確嗎? [y/n/s/q]: ").lower().strip()
                if response in ['y', 'n', 's', 'q']:
                    break
                print("請輸入 y, n, s 或 q")
            
            if response == 'q':
                break
            elif response == 'y':
                correct_count += 1
                total_checked += 1
            elif response == 'n':
                total_checked += 1
            # s = 跳過，不計入統計
        
        if total_checked > 0:
            accuracy = correct_count / total_checked
            print(f"\n📊 人工驗證結果:")
            print(f"檢查數量: {total_checked}")
            print(f"正確數量: {correct_count}")
            print(f"人工準確率: {accuracy:.3f}")
        
    except Exception as e:
        print(f"❌ 互動式驗證發生錯誤: {e}")

def main():
    """主驗證函數"""
    
    print("🔍 Caption 處理結果驗證工具")
    print("=" * 80)
    
    test_pdf = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
    
    if not test_pdf.exists():
        print("❌ 測試檔案不存在")
        return
    
    # 1. 提取原始文字
    print("📄 提取PDF原始文字...")
    text_by_page = extract_raw_pdf_text(str(test_pdf))
    print(f"✅ 提取了 {len(text_by_page)} 頁文字")
    
    # 2. 手動搜尋 Caption 和引用
    print("🔍 手動搜尋 Caption...")
    manual_captions = find_manual_captions(text_by_page)
    print(f"✅ 手動找到 {len(manual_captions)} 個 Caption")
    
    print("🔍 手動搜尋引用...")
    manual_refs = find_manual_references(text_by_page)
    print(f"✅ 手動找到 {len(manual_refs)} 個引用")
    
    # 3. 自動處理
    print("🤖 執行自動處理...")
    try:
        from caption_extractor import PDFCaptionContextProcessor
        processor = PDFCaptionContextProcessor()
        auto_pairs = processor.process_pdf(str(test_pdf))
        print(f"✅ 自動識別 {len(auto_pairs)} 個配對結果")
    except Exception as e:
        print(f"❌ 自動處理失敗: {e}")
        return
    
    # 4. 比較結果
    metrics = compare_results(auto_pairs, manual_captions, manual_refs)
    
    # 5. 詳細分析
    detailed_caption_analysis(auto_pairs, manual_captions)
    
    # 6. 互動式驗證 (可選)
    print(f"\n❓ 是否進行互動式驗證? (y/n): ", end="")
    try:
        if input().lower().strip() == 'y':
            interactive_validation()
    except (EOFError, KeyboardInterrupt):
        print("\n程式結束")
    
    # 7. 總結
    print(f"\n🎯 驗證總結")
    print("=" * 80)
    if metrics['f1_score'] >= 0.8:
        print("✅ 識別品質: 優秀")
    elif metrics['f1_score'] >= 0.6:
        print("⚠️ 識別品質: 良好，可進行階段B")
    else:
        print("❌ 識別品質: 需要改進")
    
    print(f"F1分數: {metrics['f1_score']:.3f}")
    print(f"建議: {'可以進入階段B' if metrics['f1_score'] >= 0.5 else '建議先優化階段A'}")

if __name__ == "__main__":
    main()