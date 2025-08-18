#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段A+B整合測試：Caption識別 + LLM描述生成
"""

import sys
import os
import json
from datetime import datetime

# 導入階段A和B的模組
from caption_extractor import PDFCaptionContextProcessor
from llm_description_generator import LLMDescriptionGenerator, DescriptionRequest

def test_stage_ab_integration():
    """測試階段A+B整合功能"""
    
    print("🔄 開始階段A+B整合測試")
    print("=" * 60)
    
    # 步驟1：使用階段A提取Caption
    print("📋 步驟1：執行階段A - Caption識別")
    processor = PDFCaptionContextProcessor()
    pdf_file = "../../pdfFiles/計概第一章.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"❌ 測試檔案不存在: {pdf_file}")
        return
    
    try:
        # 執行Caption提取
        stage_a_result = processor.process_pdf(pdf_file)
        print(f"✅ 階段A完成，找到 {len(stage_a_result.caption_pairs)} 個Caption")
        
        # 步驟2：準備階段B的輸入
        print("\n📋 步驟2：準備LLM描述生成請求")
        description_requests = []
        
        # 選擇前5個高信心度的Caption進行測試
        high_confidence_pairs = [
            pair for pair in stage_a_result.caption_pairs 
            if pair.caption_info.confidence > 0.5
        ][:5]
        
        for pair in high_confidence_pairs:
            caption = pair.caption_info
            context = pair.context_info
            
            # 準備相關內文
            related_context = []
            if context and context.related_paragraphs:
                related_context = [para[:100] for para in context.related_paragraphs[:3]]
            
            # 建立描述請求
            request = DescriptionRequest(
                caption_text=caption.title,
                caption_type=caption.caption_type,
                caption_number=caption.number,
                related_context=related_context,
                page_number=caption.page
            )
            description_requests.append(request)
        
        print(f"✅ 準備了 {len(description_requests)} 個描述生成請求")
        
        # 步驟3：使用階段B生成描述
        print("\n📋 步驟3：執行階段B - LLM描述生成")
        generator = LLMDescriptionGenerator()
        
        # 生成描述
        description_results = []
        for i, request in enumerate(description_requests, 1):
            print(f"\n🔄 正在處理 {i}/{len(description_requests)}: {request.caption_type} {request.caption_number}")
            
            result = generator.generate_description(request)
            description_results.append(result)
            
            if result.success:
                print(f"✅ 生成成功 (信心度: {result.confidence_score:.2f})")
                print(f"📝 描述: {result.generated_description[:100]}...")
            else:
                print(f"❌ 生成失敗: {result.error_message}")
        
        # 步驟4：整合結果分析
        print("\n📋 步驟4：整合結果分析")
        analyze_integration_results(stage_a_result, description_results)
        
        # 步驟5：保存整合結果
        print("\n📋 步驟5：保存整合結果")
        save_integration_results(stage_a_result, description_results)
        
        print("\n✅ 階段A+B整合測試完成")
        
    except Exception as e:
        print(f"❌ 整合測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()

def analyze_integration_results(stage_a_result, description_results):
    """分析整合結果"""
    
    print("\n📊 整合結果分析")
    print("-" * 40)
    
    # 階段A統計
    total_captions = len(stage_a_result.caption_pairs)
    high_conf_captions = len([p for p in stage_a_result.caption_pairs if p.caption_info.confidence > 0.5])
    
    print(f"階段A統計:")
    print(f"  • 總Caption數: {total_captions}")
    print(f"  • 高信心度(>0.5): {high_conf_captions}")
    print(f"  • 成功率: {high_conf_captions/total_captions*100:.1f}%")
    
    # 階段B統計
    successful_descriptions = [r for r in description_results if r.success]
    total_tokens = sum(r.token_usage.get('total_tokens', 0) for r in successful_descriptions)
    avg_confidence = sum(r.confidence_score for r in successful_descriptions) / len(successful_descriptions) if successful_descriptions else 0
    
    print(f"\n階段B統計:")
    print(f"  • 處理請求數: {len(description_results)}")
    print(f"  • 成功生成數: {len(successful_descriptions)}")
    print(f"  • 成功率: {len(successful_descriptions)/len(description_results)*100:.1f}%")
    print(f"  • 平均信心度: {avg_confidence:.2f}")
    print(f"  • 總Token使用: {total_tokens}")
    
    # 品質評估
    print(f"\n📈 品質評估:")
    for i, result in enumerate(successful_descriptions):
        print(f"  {i+1}. 信心度: {result.confidence_score:.2f}, 描述長度: {len(result.generated_description)}")

def save_integration_results(stage_a_result, description_results):
    """保存整合結果"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"stage_ab_integration_results_{timestamp}.json"
    
    # 準備保存數據
    integration_data = {
        "test_time": timestamp,
        "stage_a_summary": {
            "total_captions": len(stage_a_result.caption_pairs),
            "caption_types": {},
            "average_confidence": 0
        },
        "stage_b_summary": {
            "total_requests": len(description_results),
            "successful_generations": len([r for r in description_results if r.success]),
            "total_tokens_used": sum(r.token_usage.get('total_tokens', 0) for r in description_results),
            "average_confidence": 0
        },
        "integrated_results": []
    }
    
    # 計算階段A統計
    caption_types = {}
    total_conf_a = 0
    for pair in stage_a_result.caption_pairs:
        caption_type = pair.caption_info.caption_type
        caption_types[caption_type] = caption_types.get(caption_type, 0) + 1
        total_conf_a += pair.caption_info.confidence
    
    integration_data["stage_a_summary"]["caption_types"] = caption_types
    integration_data["stage_a_summary"]["average_confidence"] = total_conf_a / len(stage_a_result.caption_pairs)
    
    # 計算階段B統計
    successful_results = [r for r in description_results if r.success]
    if successful_results:
        avg_conf_b = sum(r.confidence_score for r in successful_results) / len(successful_results)
        integration_data["stage_b_summary"]["average_confidence"] = avg_conf_b
    
    # 整合結果詳情
    for i, result in enumerate(description_results):
        integrated_item = {
            "index": i + 1,
            "original_caption": result.original_caption,
            "generated_description": result.generated_description,
            "stage_b_confidence": result.confidence_score,
            "success": result.success,
            "processing_time": result.processing_time,
            "token_usage": result.token_usage
        }
        integration_data["integrated_results"].append(integrated_item)
    
    # 保存檔案
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(integration_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 整合結果已保存到: {output_file}")

if __name__ == "__main__":
    try:
        test_stage_ab_integration()
    except KeyboardInterrupt:
        print("\n⚠️ 測試被使用者中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生未預期錯誤: {str(e)}")
        import traceback
        traceback.print_exc()