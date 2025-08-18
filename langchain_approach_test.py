"""
LangChain 圖表處理方法測試

測試 LangChain 內建工具處理相同PDF的效果，與自製模組對比
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# 設定 UTF-8 編碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# LangChain imports
try:
    from langchain_community.document_loaders import (
        UnstructuredPDFLoader,
        PyMuPDFLoader
    )
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI
    from langchain.schema import Document
    
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ LangChain 套件未完全安裝: {e}")
    LANGCHAIN_AVAILABLE = False


class LangChainImageProcessor:
    """使用 LangChain 內建工具的圖表處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process_with_unstructured(self, pdf_path: str) -> List[Document]:
        """使用 UnstructuredPDFLoader 處理PDF"""
        
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain 套件不可用")
        
        try:
            # 使用 elements 模式可以識別不同類型的內容
            loader = UnstructuredPDFLoader(pdf_path, mode="elements")
            documents = loader.load()
            
            # 分類不同類型的元素
            images = []
            tables = []
            texts = []
            
            for doc in documents:
                category = doc.metadata.get('category', 'unknown')
                
                if category == 'Image':
                    images.append(doc)
                elif category == 'Table':
                    tables.append(doc)
                else:
                    texts.append(doc)
            
            self.logger.info(f"Unstructured處理結果: {len(images)}圖像, {len(tables)}表格, {len(texts)}文字")
            
            return {
                'images': images,
                'tables': tables,  
                'texts': texts,
                'all': documents
            }
            
        except Exception as e:
            self.logger.error(f"UnstructuredPDFLoader 處理失敗: {e}")
            return {'images': [], 'tables': [], 'texts': [], 'all': []}
    
    def process_with_pymupdf(self, pdf_path: str) -> List[Document]:
        """使用 PyMuPDFLoader 處理PDF (對比用)"""
        
        try:
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            
            self.logger.info(f"PyMuPDF處理結果: {len(documents)} 個文檔")
            
            return documents
            
        except Exception as e:
            self.logger.error(f"PyMuPDFLoader 處理失敗: {e}")
            return []
    
    def analyze_elements(self, elements_result: Dict[str, List[Document]]) -> Dict[str, Any]:
        """分析元素識別結果"""
        
        analysis = {
            'summary': {},
            'image_analysis': [],
            'table_analysis': [],
            'potential_captions': []
        }
        
        # 統計概要
        for key, docs in elements_result.items():
            if key != 'all':
                analysis['summary'][key] = len(docs)
        
        # 分析圖像元素
        for img_doc in elements_result.get('images', []):
            analysis['image_analysis'].append({
                'content': img_doc.page_content[:100] + "..." if len(img_doc.page_content) > 100 else img_doc.page_content,
                'metadata': img_doc.metadata,
                'page': img_doc.metadata.get('page_number', 'unknown')
            })
        
        # 分析表格元素
        for table_doc in elements_result.get('tables', []):
            analysis['table_analysis'].append({
                'content': table_doc.page_content[:100] + "..." if len(table_doc.page_content) > 100 else table_doc.page_content,
                'metadata': table_doc.metadata,
                'page': table_doc.metadata.get('page_number', 'unknown')
            })
        
        # 在文字中尋找可能的Caption
        import re
        caption_patterns = [
            r'圖\s*\d+[\.-]?\d*[：:].*',
            r'表\s*\d+[\.-]?\d*[：:].*',
            r'Figure\s*\d+[\.-]?\d*[：:.].*',
            r'Table\s*\d+[\.-]?\d*[：:.].*'
        ]
        
        for text_doc in elements_result.get('texts', []):
            content = text_doc.page_content
            for pattern in caption_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    analysis['potential_captions'].append({
                        'text': match,
                        'page': text_doc.metadata.get('page_number', 'unknown'),
                        'source': 'text_element'
                    })
        
        return analysis


def compare_approaches():
    """對比LangChain方法與自製方法"""
    
    print("🔄 開始對比 LangChain 方法與自製方法...")
    
    # 測試檔案
    test_pdf = Path("ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf")
    
    if not test_pdf.exists():
        print("❌ 測試PDF不存在")
        return
    
    # 1. LangChain方法測試
    print("\n📊 測試 LangChain UnstructuredPDFLoader...")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain 不可用，跳過測試")
        return
    
    try:
        processor = LangChainImageProcessor()
        
        # UnstructuredPDFLoader 測試
        unstructured_result = processor.process_with_unstructured(str(test_pdf))
        analysis = processor.analyze_elements(unstructured_result)
        
        print(f"✅ Unstructured 處理完成:")
        print(f"   圖像元素: {analysis['summary'].get('images', 0)} 個")
        print(f"   表格元素: {analysis['summary'].get('tables', 0)} 個") 
        print(f"   文字元素: {analysis['summary'].get('texts', 0)} 個")
        print(f"   潛在Caption: {len(analysis['potential_captions'])} 個")
        
        # 顯示發現的Caption
        if analysis['potential_captions']:
            print(f"\n🔍 發現的潛在Caption:")
            for i, caption in enumerate(analysis['potential_captions'][:5], 1):
                print(f"   {i}. {caption['text']} (頁 {caption['page']})")
        
        # 顯示圖像元素
        if analysis['image_analysis']:
            print(f"\n🖼️ 圖像元素分析:")
            for i, img in enumerate(analysis['image_analysis'][:3], 1):
                print(f"   {i}. 頁{img['page']}: {img['content']}")
        
        # 顯示表格元素  
        if analysis['table_analysis']:
            print(f"\n📋 表格元素分析:")
            for i, table in enumerate(analysis['table_analysis'][:3], 1):
                print(f"   {i}. 頁{table['page']}: {table['content']}")
        
    except Exception as e:
        print(f"❌ LangChain 測試失敗: {e}")
        return
    
    # 2. 對比自製方法 (如果可用)
    print(f"\n🔄 對比自製方法結果...")
    
    try:
        # 調用現有的自製方法
        from caption_extractor import PDFCaptionContextProcessor
        
        custom_processor = PDFCaptionContextProcessor()
        custom_results = custom_processor.process_pdf(str(test_pdf))
        
        print(f"✅ 自製方法處理完成:")
        print(f"   識別Caption: {len(custom_results)} 個")
        
        # 統計分析
        custom_stats = custom_processor.get_processing_stats(custom_results)
        print(f"   信心度範圍: {custom_stats['confidence_stats']['min']:.3f} - {custom_stats['confidence_stats']['max']:.3f}")
        print(f"   平均信心度: {custom_stats['confidence_stats']['avg']:.3f}")
        
    except ImportError:
        print("⚠️ 自製方法模組不可用")
    except Exception as e:
        print(f"❌ 自製方法測試失敗: {e}")
    
    # 3. 結論和建議
    print(f"\n🎯 對比分析結論:")
    print(f"════════════════════════════════")
    
    # 這裡可以根據實際結果給出建議
    print("✅ LangChain 優勢:")
    print("   - 自動元素分類 (圖像/表格/文字)")
    print("   - 成熟的PDF解析能力")
    print("   - 與多模態RAG整合")
    
    print("✅ 自製方法優勢:")  
    print("   - 針對性Caption識別")
    print("   - 上下文配對能力")
    print("   - 可客製化信心度評估")
    
    print("\n💡 建議策略:")
    print("   可考慮混合使用: LangChain負責元素識別，自製方法負責精準配對")


def test_multimodal_integration():
    """測試多模態整合可能性"""
    
    print(f"\n🔬 測試多模態整合可能性...")
    
    # 這裡可以測試LangChain的多模態RAG功能
    # 由於需要額外設置，先提供架構概念
    
    print("💭 多模態整合概念:")
    print("   1. 使用UnstructuredPDFLoader識別元素")
    print("   2. 對圖像元素使用Vision API生成描述")  
    print("   3. 將描述與原文一起向量化")
    print("   4. 檢索時支援圖文混合結果")
    
    print("\n⚠️ 注意事項:")
    print("   - 需要Vision API (GPT-4V)")
    print("   - 成本考量 (API調用費用)")
    print("   - 處理速度 (網路API延遲)")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 LangChain 圖表處理方法測試")
    print("=" * 50)
    
    # 執行對比測試
    compare_approaches()
    
    # 測試多模態整合
    test_multimodal_integration()
    
    print(f"\n✅ 測試完成！")
    print("根據測試結果決定最適合的技術路線。")