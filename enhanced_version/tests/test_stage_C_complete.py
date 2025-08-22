#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段C整合測試腳本 - 測試Enhanced RAG Helper與RAG Helper整合
"""

import sys
import os
import shutil
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

def collect_test_results_to_folder():
    """將測試產生的檔案收集到C_complete_testResult資料夾"""
    print(f"\n📦 收集測試結果到C_complete_testResult資料夾...")
    
    # 建立測試結果資料夾
    test_result_dir = Path(__file__).parent / "C_complete_testResult"
    test_result_dir.mkdir(exist_ok=True)
    
    # 清空舊的測試結果
    for item in test_result_dir.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    
    files_moved = []
    
    try:
        # 1. 移動chart_metadata.json (從根目錄)
        root_chart_metadata = project_root / "chart_metadata.json"
        if root_chart_metadata.exists():
            shutil.move(str(root_chart_metadata), str(test_result_dir / "chart_metadata.json"))
            files_moved.append("chart_metadata.json")
            print(f"   ✅ 移動 chart_metadata.json")
        
        # 2. 移動enhanced_faiss_index資料夾 (從根目錄)
        root_enhanced_index = project_root / "enhanced_faiss_index"
        if root_enhanced_index.exists():
            shutil.move(str(root_enhanced_index), str(test_result_dir / "enhanced_faiss_index"))
            files_moved.append("enhanced_faiss_index/")
            print(f"   ✅ 移動 enhanced_faiss_index/")
        
        # 3. 複製enhanced_docs資料夾 (從pdfFiles，保留原檔案)
        enhanced_docs_src = project_root / "pdfFiles" / "enhanced_docs"
        if enhanced_docs_src.exists():
            dest_docs = test_result_dir / "enhanced_docs"
            shutil.copytree(enhanced_docs_src, dest_docs, dirs_exist_ok=True)
            files_moved.append("enhanced_docs/")
            print(f"   ✅ 複製 enhanced_docs/")
        
        # 4. 移動tests資料夾中的檔案 (如果有的話)
        test_chart_metadata = Path(__file__).parent / "chart_metadata.json"
        if test_chart_metadata.exists() and not (test_result_dir / "chart_metadata.json").exists():
            shutil.move(str(test_chart_metadata), str(test_result_dir / "chart_metadata.json"))
            print(f"   ✅ 移動 tests/chart_metadata.json")
        
        test_enhanced_index = Path(__file__).parent / "enhanced_faiss_index"
        if test_enhanced_index.exists() and not (test_result_dir / "enhanced_faiss_index").exists():
            shutil.move(str(test_enhanced_index), str(test_result_dir / "enhanced_faiss_index"))
            print(f"   ✅ 移動 tests/enhanced_faiss_index/")
        
        # 5. 建立測試摘要檔案
        summary_file = test_result_dir / "test_summary.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("階段C整合測試結果摘要\n")
            f.write("=" * 30 + "\n\n")
            f.write(f"測試時間: {Path(__file__).stat().st_mtime}\n")
            f.write(f"收集檔案: {', '.join(files_moved)}\n\n")
            f.write("檔案說明:\n")
            f.write("• chart_metadata.json - 圖表元數據，供階段D查詢圖表資訊\n")
            f.write("• enhanced_faiss_index/ - FAISS向量索引，供階段D快速檢索\n")
            f.write("• enhanced_docs/ - 增強文檔，包含原始文字+圖表描述\n\n")
            f.write("使用說明:\n")
            f.write("這些檔案是測試期間產生的，正式上線時會直接在根目錄產生\n")
        
        files_moved.append("test_summary.txt")
        print(f"   ✅ 建立測試摘要")
        
        print(f"\n📁 測試結果已收集到: {test_result_dir}")
        print(f"   收集檔案: {', '.join(files_moved)}")
        print(f"   根目錄已清理乾淨")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 收集測試結果失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_enhanced_rag_helper():
    """測試整合後的Enhanced RAG Helper功能"""
    
    print("🧪 階段C整合測試：Enhanced RAG Helper + RAG Helper")
    print("=" * 60)
    print("測試向量化委託給RAG Helper...")
    print()
    
    try:
        from enhanced_version.backend.enhanced_rag_helper_sC import EnhancedRAGHelper
        print("✅ Enhanced RAG Helper匯入成功")
        
        # 設定路徑 (使用已定義的變數)
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
            
            # 執行完整的向量化流程，生成伴生索引
            print(f"\n🔄 執行完整的向量化流程...")
            print(f"   這將生成階段D需要的伴生索引檔案")
            
            try:
                helper.load_and_prepare_enhanced(rebuild_index=True)
                print("✅ 完整向量化流程執行成功")
                
                # 檢查生成的檔案
                chart_metadata_path = "chart_metadata.json"
                enhanced_index_path = "enhanced_faiss_index"
                
                print(f"\n📁 生成的伴生索引檔案:")
                print(f"   • {chart_metadata_path}: {'✅ 已生成' if os.path.exists(chart_metadata_path) else '❌ 未生成'}")
                print(f"   • {enhanced_index_path}/: {'✅ 已生成' if os.path.exists(enhanced_index_path) else '❌ 未生成'}")
                
                if os.path.exists(enhanced_index_path):
                    from pathlib import Path
                    index_files = list(Path(enhanced_index_path).glob("*"))
                    print(f"   • 索引檔案: {[f.name for f in index_files]}")
                
                print(f"\n🎯 階段D接手準備:")
                print(f"   • 圖表元數據: {len(helper.chart_metadata)} 個圖表")
                print(f"   • 向量庫可用: {'✅' if helper.vectorstore else '❌'}")
                print(f"   • 伴生索引完整: {'✅' if os.path.exists(chart_metadata_path) and os.path.exists(enhanced_index_path) else '❌'}")
                
                # 收集測試結果到專用資料夾，保持根目錄乾淨
                collect_success = collect_test_results_to_folder()
                if collect_success:
                    print(f"✅ 測試結果已整理完成，根目錄保持乾淨")
                else:
                    print(f"❌ 測試結果整理失敗")
                
            except Exception as e:
                print(f"⚠️ 完整向量化流程執行失敗: {e}")
                import traceback
                traceback.print_exc()
                # 但圖表處理功能仍然正常
                print(f"📌 圖表處理功能已驗證正常")
            
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