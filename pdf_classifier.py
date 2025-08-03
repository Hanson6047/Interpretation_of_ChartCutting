# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import os
import sys
from typing import Dict, List

# 設置控制台編碼支援Unicode
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


def classify_pdf_type(pdf_path: str) -> Dict[str, any]:
    """
    判斷 PDF 檔案是否為數位生成或掃描型
    
    Args:
        pdf_path (str): PDF 檔案路徑
        
    Returns:
        Dict: {
            "type": "digital" 或 "scanned",
            "text_pages": [有文字的頁數],
            "image_pages": [純圖片的頁數]
        }
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"無法開啟 PDF 檔案: {e}")
    
    text_pages = []
    image_pages = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 檢查頁面是否有可提取的文字
        text = page.get_text().strip()
        has_meaningful_text = len(text) > 50  # 超過50個字符視為有意義的文字
        
        # 檢查頁面是否主要由圖片組成
        image_list = page.get_images()
        has_images = len(image_list) > 0
        
        # 檢查圖片是否覆蓋大部分頁面
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        
        large_image_coverage = 0
        for img_index, img in enumerate(image_list):
            try:
                # 獲取圖片在頁面上的位置和大小
                img_rects = page.get_image_rects(img[0])
                for rect in img_rects:
                    img_area = rect.width * rect.height
                    coverage_ratio = img_area / page_area
                    if coverage_ratio > 0.3:  # 圖片覆蓋超過30%的頁面
                        large_image_coverage += coverage_ratio
            except:
                continue
        
        # 判斷頁面類型
        if has_meaningful_text and large_image_coverage < 0.7:
            # 有文字且圖片覆蓋率不高 -> 文字頁面
            text_pages.append(page_num + 1)  # 頁數從1開始
        elif has_images and (large_image_coverage > 0.5 or not has_meaningful_text):
            # 圖片覆蓋率高或無有意義文字 -> 圖片頁面
            image_pages.append(page_num + 1)
        elif has_meaningful_text:
            # 有文字但無明顯圖片 -> 文字頁面
            text_pages.append(page_num + 1)
        else:
            # 預設歸類為圖片頁面
            image_pages.append(page_num + 1)
    
    doc.close()
    
    # 判斷整體 PDF 類型
    total_pages = len(text_pages) + len(image_pages)
    if total_pages == 0:
        pdf_type = "digital"  # 空文件預設為數位
    elif len(text_pages) > len(image_pages):
        pdf_type = "digital"
    else:
        pdf_type = "scanned"
    
    return {
        "type": pdf_type,
        "text_pages": text_pages,
        "image_pages": image_pages
    }


def batch_classify_pdfs(directory_path: str, recursive: bool = True) -> Dict[str, Dict]:
    """
    批量分析目錄中的所有PDF檔案
    
    Args:
        directory_path (str): 目錄路徑
        recursive (bool): 是否遞迴搜尋子目錄
        
    Returns:
        Dict: {檔案路徑: 分析結果}
    """
    import glob
    
    results = {}
    
    # 搜尋PDF檔案
    if recursive:
        pattern = os.path.join(directory_path, "**", "*.pdf")
        pdf_files = glob.glob(pattern, recursive=True)
    else:
        pattern = os.path.join(directory_path, "*.pdf")
        pdf_files = glob.glob(pattern)
    
    print(f"找到 {len(pdf_files)} 個PDF檔案")
    
    for pdf_file in pdf_files:
        try:
            result = classify_pdf_type(pdf_file)
            results[pdf_file] = result
            print(f"✅ {os.path.basename(pdf_file)}: {result['type']}")
        except Exception as e:
            results[pdf_file] = {"error": str(e)}
            print(f"❌ {os.path.basename(pdf_file)}: {e}")
    
    return results


def generate_report(results: Dict[str, Dict], output_file: str = None) -> str:
    """
    生成分析報告
    
    Args:
        results (Dict): batch_classify_pdfs 的結果
        output_file (str): 輸出檔案路徑 (可選)
        
    Returns:
        str: 報告內容
    """
    digital_count = 0
    scanned_count = 0
    error_count = 0
    
    report_lines = ["=== PDF 分類分析報告 ===\n"]
    
    for file_path, result in results.items():
        filename = os.path.basename(file_path)
        
        if "error" in result:
            error_count += 1
            report_lines.append(f"❌ {filename}: 錯誤 - {result['error']}")
        else:
            if result['type'] == 'digital':
                digital_count += 1
                emoji = "📄"
            else:
                scanned_count += 1
                emoji = "🖼️"
            
            total_pages = len(result['text_pages']) + len(result['image_pages'])
            report_lines.append(f"{emoji} {filename}: {result['type']} ({total_pages}頁)")
    
    # 統計摘要
    total_files = len(results)
    report_lines.extend([
        f"\n=== 統計摘要 ===",
        f"總檔案數: {total_files}",
        f"數位PDF: {digital_count}",
        f"掃描PDF: {scanned_count}",
        f"錯誤檔案: {error_count}",
        f"成功率: {((total_files - error_count) / total_files * 100):.1f}%" if total_files > 0 else "0%"
    ])
    
    report_content = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"\n報告已儲存至: {output_file}")
    
    return report_content


# 使用範例
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 批量模式: python pdf_classifier.py <目錄路徑>
        directory = sys.argv[1]
        if os.path.isdir(directory):
            print(f"批量分析目錄: {directory}")
            results = batch_classify_pdfs(directory)
            report = generate_report(results, "pdf_analysis_report.txt")
            print(f"\n{report}")
        else:
            # 單檔模式: python pdf_classifier.py <檔案路徑>
            try:
                result = classify_pdf_type(directory)
                print(f"PDF 類型: {result['type']}")
                print(f"文字頁面: {result['text_pages']}")
                print(f"圖片頁面: {result['image_pages']}")
            except Exception as e:
                print(f"錯誤: {e}")
    else:
        # 預設模式: 分析當前目錄
        print("分析當前目錄的PDF檔案...")
        results = batch_classify_pdfs(".")
        if results:
            report = generate_report(results)
            print(f"\n{report}")
        else:
            print("當前目錄沒有找到PDF檔案")