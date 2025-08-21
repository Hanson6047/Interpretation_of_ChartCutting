#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段C基本測試腳本 - 測試Enhanced RAG Helper功能
使用Mock LLM模擬完整流程
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

def test_enhanced_rag_helper():
    """測試Enhanced RAG Helper的基本功能"""
    
    print("🧪 階段C測試：Enhanced RAG Helper")
    print("=" * 60)
    print("使用Mock LLM模擬完整流程...")
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
        
        # 測試PDF路徑
        pdf_path = project_root / "pdfFiles" / "計概第一章.pdf"
        
        if pdf_path.exists():
            print(f"\n📄 處理PDF: {pdf_path.name}")
            print("-" * 40)
            
            # 處理PDF並提取圖表描述
            enhanced_docs, chart_metadata = helper.process_pdf_with_charts(str(pdf_path))
            
            print(f"✅ 處理完成！")
            print(f"\n📊 處理結果:")
            print(f"   • 增強文檔數量: {len(enhanced_docs)}")
            print(f"   • 圖表元數據數量: {len(chart_metadata)}")
            
            # 分析增強文檔
            enhanced_count = len([d for d in enhanced_docs if d.metadata.get('enhanced', False)])
            total_charts = sum(d.metadata.get('chart_count', 0) for d in enhanced_docs)
            
            print(f"   • 包含圖表的文檔: {enhanced_count}")
            print(f"   • 總圖表引用數: {total_charts}")
            
            # 顯示前3個增強文檔的內容
            print(f"\n📋 增強文檔預覽:")
            for i, doc in enumerate(enhanced_docs[:3], 1):
                print(f"\n--- 文檔 {i} ---")
                print(f"頁面: {doc.metadata.get('page', 'unknown') + 1}")
                print(f"是否增強: {doc.metadata.get('enhanced', False)}")
                print(f"圖表數量: {doc.metadata.get('chart_count', 0)}")
                print(f"內容預覽: {doc.page_content[:150]}...")
                
                if doc.metadata.get('chart_references'):
                    print(f"圖表引用: {doc.metadata['chart_references']}")
                
                # 檢查是否包含圖表說明
                if "--- 本頁圖表說明 ---" in doc.page_content:
                    chart_section = doc.page_content.split("--- 本頁圖表說明 ---")[1][:200]
                    print(f"圖表說明片段: {chart_section}...")
            
            # 顯示圖表元數據
            print(f"\n📈 圖表元數據預覽:")
            for i, chart in enumerate(chart_metadata[:5], 1):
                print(f"\n--- 圖表 {i} ---")
                print(f"ID: {chart.chart_id}")
                print(f"類型: {chart.chart_type}")
                print(f"編號: {chart.chart_number}")
                print(f"頁面: {chart.page_number}")
                print(f"原始Caption: {chart.original_caption[:60]}...")
                print(f"生成描述: {chart.generated_description[:80]}...")
                print(f"信心度: {chart.confidence_score:.3f}")
            
            # 測試向量化準備
            print(f"\n🔄 測試向量化準備...")
            try:
                # 注意：這裡會嘗試建立向量資料庫，需要OpenAI API
                helper.load_and_prepare_enhanced(rebuild_index=True)
                print("✅ 向量資料庫建立成功")
            except Exception as e:
                print(f"⚠️ 向量化跳過 (需要OpenAI API): {str(e)[:100]}...")
            
        else:
            print(f"❌ PDF檔案不存在: {pdf_path}")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主測試函數"""
    test_enhanced_rag_helper()
    
    print("\n" + "=" * 60)
    print("🎯 階段C基本測試完成")

if __name__ == "__main__":
    main()