import os
from pdf_classifier import classify_pdf_type


def test_pdf_classifier():
    """測試 PDF 分類器功能"""
    
    print("=== PDF 分類器測試 ===\n")
    
    # 測試用 PDF 檔案列表 (請替換為你的實際檔案)
    test_files = [
        "四_中英文摘要與關鍵詞.pdf",    # 數位生成的PDF
        "test_pdf_dat/免修標準對照表(112學年度修訂).pdf",    # 掃描型PDF
        "test_pdf_data/深圳參訪心得.pdf"       # 混合內容PDF
    ]
    
    for pdf_file in test_files:
        print(f"測試檔案: {pdf_file}")
        
        if not os.path.exists(pdf_file):
            print(f"  ❌ 檔案不存在，跳過測試\n")
            continue
            
        try:
            result = classify_pdf_type(pdf_file)
            
            print(f"  📄 PDF 類型: {result['type']}")
            print(f"  📝 文字頁面數量: {len(result['text_pages'])}")
            print(f"  🖼️  圖片頁面數量: {len(result['image_pages'])}")
            print(f"  📝 文字頁面: {result['text_pages']}")
            print(f"  🖼️  圖片頁面: {result['image_pages']}")
            
            # 簡單驗證
            total_pages = len(result['text_pages']) + len(result['image_pages'])
            if total_pages > 0:
                text_ratio = len(result['text_pages']) / total_pages
                print(f"  📊 文字頁面比例: {text_ratio:.2%}")
                
                if result['type'] == 'digital' and text_ratio >= 0.5:
                    print("  ✅ 分類結果合理")
                elif result['type'] == 'scanned' and text_ratio < 0.5:
                    print("  ✅ 分類結果合理")
                else:
                    print("  ⚠️  分類結果需要人工確認")
            else:
                print("  ⚠️  無法分析頁面內容")
                
        except Exception as e:
            print(f"  ❌ 測試失敗: {e}")
            
        print()


def interactive_test():
    """互動式測試"""
    print("=== 互動式測試 ===")
    
    while True:
        pdf_path = input("\n請輸入PDF檔案路徑 (輸入 'q' 退出): ").strip()
        
        if pdf_path.lower() == 'q':
            break
            
        if not pdf_path:
            continue
            
        try:
            result = classify_pdf_type(pdf_path)
            
            print(f"\n分析結果:")
            print(f"  類型: {result['type']}")
            print(f"  總頁數: {len(result['text_pages']) + len(result['image_pages'])}")
            print(f"  文字頁面: {result['text_pages']}")
            print(f"  圖片頁面: {result['image_pages']}")
            
        except Exception as e:
            print(f"錯誤: {e}")


def quick_test():
    """快速測試 - 檢查當前目錄的PDF檔案"""
    print("=== 快速測試 (當前目錄PDF檔案) ===\n")
    
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("當前目錄沒有找到PDF檔案")
        return
        
    for pdf_file in pdf_files[:3]:  # 只測試前3個檔案
        print(f"分析: {pdf_file}")
        try:
            result = classify_pdf_type(pdf_file)
            print(f"  類型: {result['type']}")
            print(f"  文字頁: {len(result['text_pages'])}, 圖片頁: {len(result['image_pages'])}")
        except Exception as e:
            print(f"  錯誤: {e}")
        print()


if __name__ == "__main__":
    # 選擇測試方式
    print("選擇測試方式:")
    print("1. 預設測試檔案")
    print("2. 互動式測試") 
    print("3. 快速測試當前目錄")
    
    choice = input("請選擇 (1-3): ").strip()
    
    if choice == "1":
        test_pdf_classifier()
    elif choice == "2":
        interactive_test()
    elif choice == "3":
        quick_test()
    else:
        print("無效選擇，執行快速測試...")
        quick_test()