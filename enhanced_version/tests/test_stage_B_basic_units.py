#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段B基礎測試：測試LLM描述生成功能
"""

import sys
import os

# 添加模組路徑
sys.path.append('modules/pdf_Cutting_TextReplaceImage')
sys.path.append('modules/pdf_Cutting_TextReplaceImage/enhanced_version/backend')

def test_stage_b():
    print("=== Stage B Test: LLM Description Generation ===")
    
    try:
        from llm_providers_sB import LLMManager, LLMRequest
        from llm_description_generator_v2_sB import LLMDescriptionGeneratorV2, DescriptionRequest
        
        print("OK: Modules loaded successfully")
        
        # 創建Mock LLM描述生成器
        generator = LLMDescriptionGeneratorV2("mock")
        print("OK: Mock LLM generator created")
        
        # 模擬階段A的完美輸出
        test_data = {
            "caption": "Figure 1-1 Chinese Abacus",
            "type": "figure",
            "number": "1-1",
            "context": [
                "Chinese abacus is an ancient calculating tool with long history.",
                "It consists of wooden frame and beads, divided into upper and lower rows.",
                "Can perform arithmetic operations like addition, subtraction, multiplication and division."
            ]
        }
        
        print(f"Input: Testing caption '{test_data['caption']}'")
        print(f"Context: {len(test_data['context'])} paragraphs")
        
        # 建立描述請求
        request = DescriptionRequest(
            caption_text=test_data["caption"],
            caption_type=test_data["type"],
            caption_number=test_data["number"],
            related_context=test_data["context"],
            page_number=2
        )
        
        print("Processing: Generating description...")
        
        # 生成描述
        result = generator.generate_description(request)
        
        # 顯示結果
        print(f"Success: {result.success}")
        if result.success:
            print(f"Generated Description: {result.generated_description[:150]}...")
            print(f"Confidence: {result.confidence_score:.2f}")
            print(f"LLM Provider: {result.llm_provider}")
            print(f"Processing Time: {result.processing_time:.2f} seconds")
            
            print("\n=== Test Result ===")
            print("PASS: Stage B Mock LLM works correctly")
            print("INFO: Can generate descriptions for charts/tables")
            print("NEXT: Can switch to OpenAI or local LLM for real descriptions")
        else:
            print(f"FAIL: {result.error_message}")
        
    except Exception as e:
        print(f"ERROR: Test failed - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_stage_b()