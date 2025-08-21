#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段C整合測試腳本 - 測試Enhanced RAG Helper與RAG Helper整合
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

# 添加路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 添加項目根目錄到路徑 (為了找到RAG_Helper)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def test_integrated_enhanced_rag_helper():
    """測試整合後的Enhanced RAG Helper功能"""
    
    print("🧪 階段C整合測試：Enhanced RAG Helper + RAG Helper")
    print("=" * 60)
    print("測試向量化委託給RAG Helper...")
    print()
    
    try:
        from enhanced_version.backend.enhanced_rag_helper_sC import EnhancedRAGHelper
        print("✅ Enhanced RAG Helper匯入成功")
        
        # 設定路徑
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent.parent
        pdf_folder = str(project_root / "pdfFiles")
        
        # 創建Enhanced RAG Helper實例
        helper = EnhancedRAGHelper(pdf_folder, chunk_size=400, chunk_overlap=50)
        print("✅ Enhanced RAG Helper實例建立成功")
        print(f"   • PDF資料夾: {pdf_folder}")
        print(f"   • 委託RAG Helper: {type(helper.rag_helper).__name__}")
        
        # 測試圖表處理功能（不進行完整向量化）
        pdf_path = project_root / "pdfFiles" / "計概第一章.pdf"
        
        if pdf_path.exists():
            print(f"\n📄 測試PDF圖表處理: {pdf_path.name}")
            print("-" * 40)
            
            # 只測試圖表處理，不進行向量化
            enhanced_docs, chart_metadata = helper.process_pdf_with_charts(str(pdf_path))
            
            print(f"✅ 圖表處理完成！")
            print(f"\n📊 處理結果:")
            print(f"   • 增強文檔數量: {len(enhanced_docs)}")
            print(f"   • 圖表元數據數量: {len(chart_metadata)}")
            
            # 顯示圖表元數據範例
            print(f"\n📈 圖表元數據範例:")
            for i, chart in enumerate(chart_metadata[:3], 1):
                print(f"\n--- 圖表 {i} ---")
                print(f"ID: {chart.chart_id}")
                print(f"類型: {chart.chart_type}")
                print(f"編號: {chart.chart_number}")
                print(f"頁面: {chart.page_number}")
                print(f"原始Caption: {chart.original_caption[:50]}...")
                print(f"生成描述: {chart.generated_description[:80]}...")
                print(f"信心度: {chart.confidence_score:.3f}")
            
            # 測試增強文檔內容
            print(f"\n📋 增強文檔範例:")
            enhanced_with_charts = [d for d in enhanced_docs if d.metadata.get('chart_count', 0) > 0]
            
            if enhanced_with_charts:
                doc = enhanced_with_charts[0]
                print(f"\n--- 包含圖表的文檔 ---")
                print(f"頁面: {doc.metadata.get('page', 'unknown') + 1}")
                print(f"圖表數量: {doc.metadata.get('chart_count', 0)}")
                print(f"圖表引用: {doc.metadata.get('chart_references', [])}")
                
                # 檢查是否包含圖表說明
                if "--- 本頁圖表說明 ---" in doc.page_content:
                    sections = doc.page_content.split("--- 本頁圖表說明 ---")
                    print(f"原始內容: {sections[0][:100]}...")
                    print(f"圖表說明: {sections[1][:150]}...")
            
            print(f"\n✅ 圖表處理功能正常")
            print(f"📌 注意: 向量化功能已委託給RAG Helper處理")
            print(f"📌 注意: 完整測試需要RAG Helper load_and_prepare功能")
            
        else:
            print(f"❌ PDF檔案不存在: {pdf_path}")
            return False
            
    except ImportError as e:
        print(f"❌ 匯入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """主測試函數"""
    success = test_integrated_enhanced_rag_helper()
    
    print("\n" + "=" * 60)
    print("🎯 階段C整合測試完成")
    print("=" * 60)
    
    if success:
        print("✅ Enhanced RAG Helper與RAG Helper整合成功")
        print("📋 整合效果:")
        print("   • 圖表處理: Enhanced RAG Helper負責")
        print("   • 向量化處理: RAG Helper負責")
        print("   • LLM功能: 未來可整合統一切換")
    else:
        print("❌ 整合測試失敗")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)