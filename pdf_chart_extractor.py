# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import os
import sys
import json
from typing import Dict, List, Tuple
from datetime import datetime

# 設置控制台編碼支援Unicode
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


class PDFChartExtractor:
    """PDF 圖表萃取器 - 提取 PDF 中的圖片並儲存為圖表檔案"""
    
    def __init__(self, output_dir: str = "charts"):
        """
        初始化圖表萃取器
        
        Args:
            output_dir (str): 圖片輸出目錄，預設為 "charts"
        """
        self.output_dir = output_dir
        self.metadata_list = []
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """確保輸出目錄存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"✅ 創建輸出目錄: {self.output_dir}")
    
    def _generate_filename(self, page_num: int, img_index: int, extension: str = "png") -> str:
        """
        生成圖片檔案名稱
        
        Args:
            page_num (int): 頁碼 (從1開始)
            img_index (int): 圖片索引 (從1開始)
            extension (str): 檔案副檔名
            
        Returns:
            str: 檔案名稱，格式：chart_page{page}_img{index}.{extension}
        """
        return f"chart_page{page_num}_img{img_index}.{extension}"
    
    def _get_image_bbox(self, page, img_xref: int) -> List[float]:
        """
        獲取圖片在頁面上的邊界框
        
        Args:
            page: PyMuPDF 頁面物件
            img_xref (int): 圖片的 xref 編號
            
        Returns:
            List[float]: [x1, y1, x2, y2] 邊界框座標
        """
        try:
            img_rects = page.get_image_rects(img_xref)
            if img_rects:
                # 取第一個矩形，通常一個圖片只有一個位置
                rect = img_rects[0]
                return [rect.x0, rect.y0, rect.x1, rect.y1]
            else:
                # 如果無法獲取具體位置，返回頁面邊界
                return [0, 0, page.rect.width, page.rect.height]
        except:
            return [0, 0, page.rect.width, page.rect.height]
    
    def extract_images_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        從 PDF 檔案中萃取所有圖片
        
        Args:
            pdf_path (str): PDF 檔案路徑
            
        Returns:
            Dict: {
                "success": bool,
                "total_images": int,
                "extracted_images": List[Dict],
                "metadata_file": str,
                "error": str (if failed)
            }
        """
        if not os.path.exists(pdf_path):
            return {"success": False, "error": f"PDF 檔案不存在: {pdf_path}"}
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return {"success": False, "error": f"無法開啟 PDF 檔案: {e}"}
        
        extracted_images = []
        total_images = 0
        
        print(f"🔍 開始萃取 PDF 圖片: {os.path.basename(pdf_path)}")
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            if not image_list:
                continue
            
            print(f"📄 頁面 {page_num + 1}: 找到 {len(image_list)} 張圖片")
            
            for img_index, img in enumerate(image_list):
                try:
                    # 獲取圖片資料
                    img_xref = img[0]  # 圖片的 xref 編號
                    pix = fitz.Pixmap(doc, img_xref)
                    
                    # 跳過遮罩圖片 (通常是透明度遮罩)
                    if pix.n - pix.alpha < 4:  # 確保是彩色圖片
                        # 生成檔案名稱
                        filename = self._generate_filename(page_num + 1, img_index + 1)
                        file_path = os.path.join(self.output_dir, filename)
                        
                        # 儲存圖片
                        if pix.alpha:
                            # 如果有 alpha 通道，轉換為 PNG
                            pix.save(file_path)
                        else:
                            # 沒有 alpha 通道，可以轉換為 RGB 再儲存
                            rgb_pix = fitz.Pixmap(fitz.csRGB, pix)
                            rgb_pix.save(file_path)
                            rgb_pix = None
                        
                        # 獲取圖片位置資訊
                        bbox = self._get_image_bbox(page, img_xref)
                        
                        # 記錄 metadata
                        metadata = {
                            "page": page_num + 1,
                            "bbox": bbox,
                            "file_path": file_path,
                            "filename": filename,
                            "width": pix.width,
                            "height": pix.height,
                            "extracted_at": datetime.now().isoformat(),
                            "description": None,  # TODO: 未來整合 LLM API 生成圖片描述
                            "description_vector": None  # TODO: 未來使用 RAG 技術轉換描述為向量
                        }
                        
                        self.metadata_list.append(metadata)
                        extracted_images.append(metadata)
                        total_images += 1
                        
                        print(f"  ✅ 儲存: {filename} ({pix.width}x{pix.height})")
                    
                    pix = None  # 釋放記憶體
                    
                except Exception as e:
                    print(f"  ❌ 萃取圖片失敗 (頁面 {page_num + 1}, 圖片 {img_index + 1}): {e}")
                    continue
        
        doc.close()
        
        # 儲存 metadata
        metadata_file = self._save_metadata(pdf_path)
        
        result = {
            "success": True,
            "total_images": total_images,
            "extracted_images": extracted_images,
            "metadata_file": metadata_file
        }
        
        print(f"🎉 萃取完成! 總共萃取了 {total_images} 張圖片")
        return result
    
    def _save_metadata(self, pdf_path: str) -> str:
        """
        儲存 metadata 到 JSON 檔案
        
        Args:
            pdf_path (str): 原始 PDF 檔案路徑
            
        Returns:
            str: metadata 檔案路徑
        """
        # 生成 metadata 檔案名稱
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        metadata_filename = f"{pdf_basename}_metadata.json"
        metadata_path = os.path.join(self.output_dir, metadata_filename)
        
        # 準備完整的 metadata
        full_metadata = {
            "source_pdf": pdf_path,
            "extraction_time": datetime.now().isoformat(),
            "output_directory": self.output_dir,
            "total_images": len(self.metadata_list),
            "images": self.metadata_list
        }
        
        # 儲存到 JSON 檔案
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(full_metadata, f, ensure_ascii=False, indent=2)
            print(f"💾 Metadata 已儲存: {metadata_path}")
            return metadata_path
        except Exception as e:
            print(f"❌ 儲存 metadata 失敗: {e}")
            return ""
    
    def load_metadata(self, metadata_file: str) -> Dict:
        """
        載入 metadata 檔案
        
        Args:
            metadata_file (str): metadata 檔案路徑
            
        Returns:
            Dict: metadata 資料
        """
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 載入 metadata 失敗: {e}")
            return {}
    
    def get_image_info(self, page: int = None, bbox_filter: List[float] = None) -> List[Dict]:
        """
        根據條件篩選圖片資訊
        
        Args:
            page (int): 指定頁碼 (可選)
            bbox_filter (List[float]): 邊界框篩選 [min_x, min_y, max_x, max_y] (可選)
            
        Returns:
            List[Dict]: 符合條件的圖片資訊列表
        """
        filtered_images = self.metadata_list
        
        if page is not None:
            filtered_images = [img for img in filtered_images if img["page"] == page]
        
        if bbox_filter is not None:
            min_x, min_y, max_x, max_y = bbox_filter
            filtered_images = [
                img for img in filtered_images 
                if (img["bbox"][0] >= min_x and img["bbox"][1] >= min_y and 
                    img["bbox"][2] <= max_x and img["bbox"][3] <= max_y)
            ]
        
        return filtered_images
    
    def clear_metadata(self):
        """清空當前的 metadata 列表"""
        self.metadata_list = []
##################################################################################/*    
    # TODO: 未來功能擴展 - LLM 整合與 RAG 技術
    def generate_image_descriptions(self, llm_api_key: str = None):
        """
        TODO: 未來實作 - 使用 LLM API 為萃取的圖片生成描述
        
        規劃功能：
        1. 遍歷所有已萃取的圖片
        2. 呼叫 ChatGPT API 或其他 LLM 分析圖片內容
        3. 生成圖表類型、內容、關鍵資訊的描述
        4. 更新 metadata 中的 description 欄位
        
        Args:
            llm_api_key (str): LLM API 金鑰
        """
        pass
    
    def vectorize_descriptions(self, embedding_model: str = "sentence-transformers"):
        """
        TODO: 未來實作 - 使用 RAG 技術將圖片描述轉換為向量----------->在看要另存，還是把他跟德育同學做出來的表結合
        
        規劃功能：
        1. 讀取所有圖片的 description 文字
        2. 使用 embedding 模型（如 sentence-transformers）轉換為向量
        3. 將向量儲存到 metadata 的 description_vector 欄位
        4. 建立向量資料庫索引以支援語意搜尋
        
        Args:
            embedding_model (str): 使用的 embedding 模型名稱
        """
        pass
    
    def search_images_by_description(self, query: str, top_k: int = 5):
        """
        TODO: 未來實作 - 基於描述的語意搜尋功能--------------->但這應該套回者要架構的內容即可
        
        規劃功能：
        1. 將查詢文字轉換為向量
        2. 與現有圖片描述向量進行相似度比對
        3. 返回最相關的前 k 張圖片
        
        Args:
            query (str): 搜尋查詢文字
            top_k (int): 返回結果數量
            
        Returns:
            List[Dict]: 相關圖片的 metadata 列表
        """
        pass
###########################################################################*/

# 使用範例和測試函數
def extract_charts_from_pdf(pdf_path: str, output_dir: str = "charts") -> Dict:
    """
    便捷函數：從 PDF 萃取圖表
    
    Args:
        pdf_path (str): PDF 檔案路徑
        output_dir (str): 輸出目錄
        
    Returns:
        Dict: 萃取結果
    """
    extractor = PDFChartExtractor(output_dir)
    return extractor.extract_images_from_pdf(pdf_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_directory = sys.argv[2] if len(sys.argv) > 2 else "charts"
        
        print(f"=== PDF 圖表萃取器 ===")
        print(f"PDF 檔案: {pdf_file}")
        print(f"輸出目錄: {output_directory}")
        
        result = extract_charts_from_pdf(pdf_file, output_directory)
        
        if result["success"]:
            print(f"\n✅ 萃取成功!")
            print(f"總共萃取: {result['total_images']} 張圖片")
            print(f"Metadata 檔案: {result['metadata_file']}")
        else:
            print(f"\n❌ 萃取失敗: {result['error']}")
    else:
        print("使用方法: python pdf_chart_extractor.py <PDF檔案路徑> [輸出目錄]")
        print("範例: python pdf_chart_extractor.py document.pdf charts")