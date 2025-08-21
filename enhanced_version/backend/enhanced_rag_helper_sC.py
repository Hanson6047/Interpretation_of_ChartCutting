#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段C：增強型RAG助手 - 整合圖表描述與文字內容
"""

import os
import sys
import glob
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# LangChain 相關套件
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# 導入我們的模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from enhanced_version.backend.caption_extractor_sA import PDFCaptionContextProcessor
from enhanced_version.backend.llm_description_generator_v2_sB import LLMDescriptionGeneratorV2, DescriptionRequest

# 導入組長的RAG Helper
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))
from RAG_Helper import RAGHelper

@dataclass
class ChartMetadata:
    """圖表元數據"""
    chart_id: str
    chart_type: str  # '圖' 或 '表'
    chart_number: str
    original_caption: str
    generated_description: str
    page_number: int
    confidence_score: float
    source_file: str

@dataclass
class EnhancedDocument:
    """增強文檔 - 包含圖表資訊"""
    content: str
    metadata: Dict[str, Any]
    chart_references: List[str] = None  # 關聯的圖表ID列表

class EnhancedRAGHelper:
    """增強型RAG助手 - 支援圖文混合檢索"""
    
    def __init__(self, pdf_folder: str, chunk_size: int = 300, chunk_overlap: int = 50):
        self.pdf_folder = pdf_folder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 初始化組長的RAG Helper
        self.rag_helper = RAGHelper(
            pdf_folder=pdf_folder,
            chunk_size=chunk_size, 
            chunk_overlap=chunk_overlap
        )
        
        # RAG 組件 (委託給RAG Helper)
        self.vectorstore = None
        self.retrieval_chain = None
        
        # 圖表處理組件 (Enhanced RAG Helper專屬)
        self.caption_processor = PDFCaptionContextProcessor()
        self.description_generator = LLMDescriptionGeneratorV2("mock")
        
        # 圖表資料庫 (Enhanced RAG Helper專屬)
        self.chart_metadata: Dict[str, ChartMetadata] = {}
        self.enhanced_documents: List[EnhancedDocument] = []
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("增強型RAG助手初始化完成")
    
    def process_pdf_with_charts(self, pdf_path: str) -> Tuple[List[Document], List[ChartMetadata]]:
        """處理PDF並提取圖表描述"""
        
        self.logger.info(f"開始處理PDF: {pdf_path}")
        
        # 步驟1：提取Caption (階段A)
        caption_pairs = self.caption_processor.process_pdf(pdf_path)
        self.logger.info(f"找到 {len(caption_pairs)} 個Caption")
        
        # 步驟2：生成描述 (階段B)
        description_requests = []
        for pair in caption_pairs:
            caption = pair.caption  # 修正：使用正確的屬性名
            contexts = pair.contexts  # 修正：使用正確的屬性名
            
            # 準備相關內文
            related_context = []
            if contexts:
                # 從多個context中提取相關段落
                for ctx in contexts[:3]:  # 最多取前3個context
                    if hasattr(ctx, 'surrounding_text'):
                        related_context.append(ctx.surrounding_text[:200])
            
            request = DescriptionRequest(
                caption_text=caption.text,
                caption_type=caption.caption_type,
                caption_number=caption.number,
                related_context=related_context,
                page_number=caption.page_number
            )
            description_requests.append(request)
        
        # 批次生成描述
        if description_requests:
            self.logger.info(f"開始生成 {len(description_requests)} 個圖表描述")
            description_results = self.description_generator.batch_generate_descriptions(description_requests)
        else:
            description_results = []
        
        # 步驟3：建立圖表元數據
        chart_metadata_list = []
        filename = os.path.basename(pdf_path)
        
        for i, result in enumerate(description_results):
            if result.success:
                chart_id = f"{filename}_chart_{i+1}"
                request = description_requests[i]
                
                metadata = ChartMetadata(
                    chart_id=chart_id,
                    chart_type=request.caption_type,
                    chart_number=request.caption_number,
                    original_caption=request.caption_text,
                    generated_description=result.generated_description,
                    page_number=request.page_number,
                    confidence_score=result.confidence_score,
                    source_file=filename
                )
                chart_metadata_list.append(metadata)
                self.chart_metadata[chart_id] = metadata
        
        # 步驟4：載入原始PDF文字內容
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        original_documents = loader.load()
        
        # 步驟5：創建增強文檔 (將圖表描述整合到文字中)
        enhanced_documents = self._create_enhanced_documents(original_documents, chart_metadata_list)
        
        self.logger.info(f"PDF處理完成：{len(enhanced_documents)} 個文檔，{len(chart_metadata_list)} 個圖表")
        
        return enhanced_documents, chart_metadata_list
    
    def _create_enhanced_documents(self, original_documents: List[Document], 
                                 chart_metadata_list: List[ChartMetadata]) -> List[Document]:
        """創建增強文檔 - 將圖表描述整合到原始文字中"""
        
        enhanced_docs = []
        
        for doc in original_documents:
            page_num = doc.metadata.get('page', 0) + 1  # PDF loader的page從0開始
            
            # 找到這一頁的圖表
            page_charts = [chart for chart in chart_metadata_list 
                          if chart.page_number == page_num]
            
            enhanced_content = doc.page_content
            chart_refs = []
            
            # 在文檔末尾添加圖表描述
            if page_charts:
                enhanced_content += "\n\n--- 本頁圖表說明 ---\n"
                for chart in page_charts:
                    chart_section = f"\n{chart.chart_type} {chart.chart_number}：{chart.original_caption}\n"
                    chart_section += f"詳細描述：{chart.generated_description}\n"
                    enhanced_content += chart_section
                    chart_refs.append(chart.chart_id)
            
            # 創建增強文檔
            enhanced_doc = Document(
                page_content=enhanced_content,
                metadata={
                    **doc.metadata,
                    'enhanced': True,
                    'chart_count': len(page_charts),
                    'chart_references': chart_refs
                }
            )
            enhanced_docs.append(enhanced_doc)
        
        return enhanced_docs
    
    def load_and_prepare_enhanced(self, rebuild_index: bool = False):
        """載入並準備增強型向量資料庫 - 委託給RAG Helper處理向量化"""
        
        metadata_path = "chart_metadata.json"
        
        # 檢查是否需要重建索引
        if not rebuild_index and os.path.exists(metadata_path):
            self.logger.info("載入現有的圖表元數據...")
            
            # 載入圖表元數據
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_data = json.load(f)
                self.chart_metadata = {
                    chart_id: ChartMetadata(**data) 
                    for chart_id, data in metadata_data.items()
                }
            
            self.logger.info(f"載入完成：{len(self.chart_metadata)} 個圖表元數據")
        else:
            # 重建索引 - 先處理圖表描述
            self.logger.info("建立增強型文檔...")
            
            all_enhanced_docs = []
            all_chart_metadata = []
            
            # 處理所有PDF檔案，生成增強文檔
            pdf_files = glob.glob(os.path.join(self.pdf_folder, "*.pdf"))
            
            for pdf_path in pdf_files:
                try:
                    enhanced_docs, chart_metadata = self.process_pdf_with_charts(pdf_path)
                    all_enhanced_docs.extend(enhanced_docs)
                    all_chart_metadata.extend(chart_metadata)
                except Exception as e:
                    self.logger.error(f"處理 {pdf_path} 時發生錯誤: {e}")
                    continue
            
            if not all_enhanced_docs:
                raise ValueError("沒有成功處理任何PDF檔案")
            
            # 保存圖表元數據
            with open(metadata_path, 'w', encoding='utf-8') as f:
                metadata_dict = {chart_id: asdict(metadata) 
                               for chart_id, metadata in self.chart_metadata.items()}
                json.dump(metadata_dict, f, ensure_ascii=False, indent=2)
            
            # 將增強文檔寫入pdf_folder，讓RAG Helper處理
            temp_enhanced_folder = os.path.join(self.pdf_folder, "enhanced_docs")
            os.makedirs(temp_enhanced_folder, exist_ok=True)
            
            for i, doc in enumerate(all_enhanced_docs):
                temp_file = os.path.join(temp_enhanced_folder, f"enhanced_doc_{i}.txt")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(doc.page_content)
            
            self.logger.info(f"增強文檔準備完成：{len(all_enhanced_docs)} 個文檔，{len(self.chart_metadata)} 個圖表")
        
        # 委託RAG Helper進行向量化
        self.logger.info("委託RAG Helper進行向量化...")
        import asyncio
        
        # 創建新的RAG Helper實例專門處理增強文檔
        enhanced_rag = RAGHelper(
            pdf_folder=self.pdf_folder,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        asyncio.run(enhanced_rag.load_and_prepare(['.pdf', '.txt']))
        
        # 獲取RAG Helper的vectorstore
        self.vectorstore = enhanced_rag.vectorstore
        self.rag_helper = enhanced_rag  # 更新引用
        
        self.logger.info("增強型RAG系統準備完成")
    
    def setup_enhanced_retrieval_chain(self):
        """設定增強型檢索鏈 - 保持圖表支援特性"""
        
        if not self.vectorstore:
            raise ValueError("請先執行 load_and_prepare_enhanced()")
        
        # 使用Mock LLM用於測試 (未來可整合到RAG Helper的LLM切換功能)
        from enhanced_version.backend.llm_providers_sB import LLMManager, LLMRequest
        
        class MockChatLLM:
            """模擬ChatLLM用於測試"""
            def __init__(self):
                self.llm_manager = LLMManager("mock")
            
            def invoke(self, messages):
                # 提取提示詞
                prompt = ""
                for msg in messages:
                    if hasattr(msg, 'content'):
                        prompt += msg.content + "\n"
                    else:
                        prompt += str(msg) + "\n"
                
                request = LLMRequest(prompt=prompt, max_tokens=500)
                response = self.llm_manager.generate(request)
                
                class MockMessage:
                    def __init__(self, content):
                        self.content = content
                
                return MockMessage(response.content if response.success else "無法生成回應")
        
        llm = MockChatLLM()  # 使用Mock LLM
        
        # 創建檢索器 - 使用RAG Helper提供的vectorstore
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"k": 5}  # 檢索前5個最相關的段落
        )
        
        # 增強的提示詞模板 - 專門支援圖表資訊
        system_prompt = (
            "你是一個基於增強型 RAG 系統的計算機概論家教，能夠同時理解文字內容和圖表資訊。"
            "請參考以下提供的內容來回答問題，包括文字說明和圖表描述。"
            "當回答涉及圖表時，請特別說明圖表的內容和意義。"
            "用詞上請多使用正向鼓勵的詞語，並基於現有問題延伸出更多相關的問題。"
            "請針對問題舉出簡單好懂的比喻或例子。"
            "如果內容中包含圖表描述，請善用這些資訊來豐富你的回答。"
            "如果不知道如何回答問題，請說出來。"
            "如果問題和計算機概論無關，請將主題拉回計算機概論。"
            "使用 LaTeX 時，請使用 $ 符號作為塊級公式。"
            "請用繁體中文回答。\n\n"
            "{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # 創建文檔合併鏈和檢索鏈
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        self.retrieval_chain = create_retrieval_chain(retriever, question_answer_chain)
        
        self.logger.info("增強型檢索鏈設定完成 (向量化委託給RAG Helper，圖表功能保留)")
    
    def ask_enhanced(self, query: str) -> Tuple[str, List[Document], List[ChartMetadata]]:
        """增強型問答 - 返回答案、相關文檔和相關圖表"""
        
        if not self.retrieval_chain:
            raise ValueError("請先執行 setup_enhanced_retrieval_chain()")
        
        try:
            # 執行檢索和問答
            result = self.retrieval_chain.invoke({"input": query})
            answer = result["answer"]
            context_docs = result["context"]
            
            # 找出相關的圖表
            related_charts = []
            for doc in context_docs:
                chart_refs = doc.metadata.get('chart_references', [])
                for chart_id in chart_refs:
                    if chart_id in self.chart_metadata:
                        chart = self.chart_metadata[chart_id]
                        if chart not in related_charts:
                            related_charts.append(chart)
            
            return answer, context_docs, related_charts
            
        except Exception as e:
            self.logger.error(f"問答過程中發生錯誤: {e}")
            raise e
    
    def get_chart_by_id(self, chart_id: str) -> Optional[ChartMetadata]:
        """根據ID獲取圖表元數據"""
        return self.chart_metadata.get(chart_id)
    
    def list_all_charts(self) -> List[ChartMetadata]:
        """列出所有圖表"""
        return list(self.chart_metadata.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取系統統計資訊"""
        chart_types = {}
        for chart in self.chart_metadata.values():
            chart_types[chart.chart_type] = chart_types.get(chart.chart_type, 0) + 1
        
        return {
            "total_charts": len(self.chart_metadata),
            "chart_types": chart_types,
            "llm_provider": self.description_generator.get_current_provider(),
            "vectorstore_available": self.vectorstore is not None,
            "retrieval_chain_ready": self.retrieval_chain is not None
        }

if __name__ == "__main__":
    # 基本測試
    pdf_folder = "../../pdfFiles"
    rag = EnhancedRAGHelper(pdf_folder)
    
    print("增強型RAG助手測試")
    print(f"PDF資料夾: {pdf_folder}")
    
    # 載入和準備
    try:
        rag.load_and_prepare_enhanced(rebuild_index=False)
        rag.setup_enhanced_retrieval_chain()
        
        # 顯示統計資訊
        stats = rag.get_statistics()
        print(f"\n系統統計: {stats}")
        
        # 測試問答
        query = "什麼是算盤？"
        print(f"\n測試問題: {query}")
        answer, docs, charts = rag.ask_enhanced(query)
        print(f"回答: {answer[:200]}...")
        print(f"相關圖表數量: {len(charts)}")
        
    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()