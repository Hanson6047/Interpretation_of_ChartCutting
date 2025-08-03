# 大系統整合範例

from pdf_classifier import classify_pdf_type, batch_classify_pdfs

class DocumentProcessor:
    """文件處理系統範例 - 展示如何將PDF分類器整合到更大的系統中"""
    
    def __init__(self):
        self.processed_files = {}
        self.stats = {"digital": 0, "scanned": 0, "errors": 0}
    
    def process_document(self, file_path: str):
        """處理單一文件 - 根據PDF類型選擇不同處理策略"""
        try:
            # 1. 先判斷PDF類型
            pdf_info = classify_pdf_type(file_path)
            
            # 2. 根據類型選擇處理策略
            if pdf_info['type'] == 'digital':
                self.stats["digital"] += 1
                return self._process_digital_pdf(file_path, pdf_info)
            else:
                self.stats["scanned"] += 1
                return self._process_scanned_pdf(file_path, pdf_info)
                
        except Exception as e:
            self.stats["errors"] += 1
            return {"error": str(e), "file": file_path}
    
    def _process_digital_pdf(self, file_path, pdf_info):
        """處理數位PDF - 可直接提取文字進行分析"""
        print(f"📄 數位PDF: {file_path}")
        # 在真實系統中，這裡會呼叫文字提取和NLP分析
        return {
            "method": "direct_text_extraction",
            "priority": "high",  # 數位PDF處理速度快
            "info": pdf_info,
            "next_steps": ["text_analysis", "keyword_extraction", "content_indexing"]
        }
    
    def _process_scanned_pdf(self, file_path, pdf_info):
        """處理掃描PDF - 需要OCR處理"""
        print(f"🖼️  掃描PDF: {file_path}")
        # 在真實系統中，這裡會呼叫OCR服務
        return {
            "method": "ocr_required", 
            "priority": "low",   # OCR處理較耗時
            "info": pdf_info,
            "next_steps": ["ocr_processing", "text_correction", "content_indexing"]
        }
    
    def batch_process(self, directory: str):
        """批量處理 - 適合處理大量文件"""
        print(f"批量處理目錄: {directory}")
        
        # 先批量分類所有PDF
        classifications = batch_classify_pdfs(directory)
        
        # 再根據分類結果進行處理
        for file_path, classification in classifications.items():
            if "error" not in classification:
                processed = self.process_document(file_path)
                self.processed_files[file_path] = processed
        
        return self.processed_files
    
    def get_processing_queue(self, directory: str):
        """生成處理佇列 - 優先處理數位PDF"""
        classifications = batch_classify_pdfs(directory)
        
        digital_queue = []
        scanned_queue = []
        
        for file_path, result in classifications.items():
            if "error" not in result:
                if result['type'] == 'digital':
                    digital_queue.append(file_path)
                else:
                    scanned_queue.append(file_path)
        
        # 數位PDF優先處理
        return digital_queue + scanned_queue
    
    def print_stats(self):
        """顯示處理統計"""
        total = sum(self.stats.values())
        print(f"\n=== 處理統計 ===")
        print(f"總檔案: {total}")
        print(f"數位PDF: {self.stats['digital']}")
        print(f"掃描PDF: {self.stats['scanned']}")
        print(f"錯誤檔案: {self.stats['errors']}")


# 使用範例和測試
if __name__ == "__main__":
    # 創建處理器實例
    processor = DocumentProcessor()
    
    print("=== PDF 分類器系統整合測試 ===\n")
    
    # 測試1: 單檔處理
    print("1. 單檔處理測試:")
    try:
        # 如果當前目錄有PDF檔案，會進行測試
        import glob
        pdf_files = glob.glob("*.pdf")
        
        if pdf_files:
            result = processor.process_document(pdf_files[0])
            print(f"   結果: {result}")
        else:
            print("   跳過 - 當前目錄無PDF檔案")
    except Exception as e:
        print(f"   錯誤: {e}")
    
    # 測試2: 批量處理
    print("\n2. 批量處理測試:")
    try:
        # 測試當前目錄
        results = processor.batch_process(".")
        print(f"   處理了 {len(results)} 個檔案")
        processor.print_stats()
    except Exception as e:
        print(f"   錯誤: {e}")
    
    # 測試3: 處理佇列
    print("\n3. 處理佇列測試:")
    try:
        queue = processor.get_processing_queue(".")
        print(f"   處理順序: {[os.path.basename(f) for f in queue[:3]]}")  # 只顯示前3個
    except Exception as e:
        print(f"   錯誤: {e}")
    
    print("\n=== 整合測試完成 ===")
    print("在真實系統中，你可以:")
    print("- 匯入 DocumentProcessor 類別")
    print("- 呼叫 process_document() 處理單檔")
    print("- 呼叫 batch_process() 批量處理")
    print("- 根據 PDF 類型選擇不同的處理流程")