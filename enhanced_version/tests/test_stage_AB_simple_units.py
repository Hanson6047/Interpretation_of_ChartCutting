#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段A+B簡化整合測試
"""

import sys
import os
import json
from datetime import datetime

# 導入階段A和B的模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from modules.pdf_Cutting_TextReplaceImage.enhanced_version.backend.caption_extractor_sA import PDFCaptionContextProcessor
from llm_description_generator_v2_sB import LLMDescriptionGeneratorV2, DescriptionRequest

def main():
    print("=== 階段A+B整合測試 ===")
    
    # 步驟1：階段A - Caption識別
    print("\n步驟1：執行階段A - Caption識別")
    processor = PDFCaptionContextProcessor()
    pdf_file = "../../../ignore_file/test_pdf_data/sys_check_digital/計概第一章.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"錯誤: 測試檔案不存在 {pdf_file}")
        return
    
    caption_pairs = processor.process_pdf(pdf_file)
    print(f"完成：找到 {len(caption_pairs)} 個Caption")
    
    # 步驟2：階段B - 描述生成
    print("\n步驟2：執行階段B - 描述生成")
    generator = LLMDescriptionGeneratorV2("mock")  # 使用模擬提供者
    
    # 選擇前3個高信心度Caption進行測試
    test_pairs = [
        pair for pair in stage_a_result.caption_pairs 
        if pair.caption_info.confidence > 0.5
    ][:3]
    
    print(f"選擇 {len(test_pairs)} 個Caption進行描述生成")
    
    results = []
    for i, pair in enumerate(test_pairs, 1):
        caption = pair.caption_info
        context = pair.context_info
        
        # 準備請求
        related_context = []
        if context and context.related_paragraphs:
            related_context = [para[:100] for para in context.related_paragraphs[:2]]
        
        request = DescriptionRequest(
            caption_text=caption.title,
            caption_type=caption.caption_type,
            caption_number=caption.number,
            related_context=related_context,
            page_number=caption.page
        )
        
        print(f"\n處理 {i}/{len(test_pairs)}: {caption.caption_type} {caption.number}")
        result = generator.generate_description(request)
        results.append(result)
        
        if result.success:
            print(f"成功 - 信心度: {result.confidence_score:.2f}")
            print(f"描述: {result.generated_description[:80]}...")
        else:
            print(f"失敗: {result.error_message}")
    
    # 步驟3：結果統計
    print("\n步驟3：結果統計")
    successful = [r for r in results if r.success]
    print(f"階段A成功率: {len([p for p in stage_a_result.caption_pairs if p.caption_info.confidence > 0.5])}/{len(stage_a_result.caption_pairs)}")
    print(f"階段B成功率: {len(successful)}/{len(results)}")
    print(f"整體流程: 階段A → 階段B → 準備進入階段C")
    
    # 保存測試結果
    save_test_results(stage_a_result, results)
    
    print("\n=== 整合測試完成 ===")
    print("階段A+B基礎功能已驗證，可以進入階段C開發")

def save_test_results(stage_a_result, stage_b_results):
    """保存測試結果"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stage_ab_test_results_{timestamp}.json"
    
    data = {
        "test_time": timestamp,
        "stage_a_captions": len(stage_a_result.caption_pairs),
        "stage_b_processed": len(stage_b_results),
        "stage_b_successful": len([r for r in stage_b_results if r.success]),
        "sample_results": [
            {
                "caption": r.original_caption,
                "description": r.generated_description,
                "confidence": r.confidence_score,
                "provider": r.llm_provider
            }
            for r in stage_b_results if r.success
        ]
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"測試結果已保存: {filename}")

if __name__ == "__main__":
    main()