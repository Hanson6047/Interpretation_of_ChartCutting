#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段B：LLM描述生成器 v2 - 支援多種LLM後端
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import json
from datetime import datetime

# 導入LLM提供者
from llm_providers_sB import LLMManager, LLMRequest

@dataclass
class DescriptionRequest:
    """描述生成請求"""
    caption_text: str
    caption_type: str  # '圖' 或 '表'
    caption_number: str
    related_context: List[str]
    page_number: int

@dataclass
class DescriptionResult:
    """描述生成結果"""
    original_caption: str
    generated_description: str
    confidence_score: float
    processing_time: float
    token_usage: Dict[str, int]
    success: bool
    llm_provider: str
    error_message: Optional[str] = None

class LLMDescriptionGeneratorV2:
    """LLM描述生成器 v2"""
    
    def __init__(self, preferred_provider: str = "auto"):
        """初始化生成器
        
        Args:
            preferred_provider: 偏好的LLM提供者 ("auto", "mock", "openai", "local")
        """
        self.llm_manager = LLMManager(preferred_provider)
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 統計資訊
        self.total_tokens_used = 0
        self.total_requests = 0
        
        self.logger.info(f"描述生成器初始化完成，使用LLM提供者: {self.llm_manager.get_current_provider()}")
    
    def create_prompt_template(self, request: DescriptionRequest) -> str:
        """建立提示詞模板"""
        
        # 根據圖表類型調整提示詞
        if request.caption_type == '圖':
            type_instruction = "這是一個圖片/圖表。請描述其視覺內容、數據關係或概念說明。"
        else:  # 表
            type_instruction = "這是一個表格。請描述其數據結構、統計內容或資訊整理。"
        
        # 組合相關內文
        context_text = "\n".join(request.related_context) if request.related_context else "無相關內文"
        
        prompt = f"""你是一個專業的學術文件分析助手。請根據以下資訊，為圖表生成一個詳細、準確的文字描述。

【圖表資訊】
- 類型：{request.caption_type}
- 編號：{request.caption_number}
- 原始說明：{request.caption_text}
- 頁碼：第{request.page_number}頁

【相關內文脈絡】
{context_text}

【任務要求】
{type_instruction}

請生成一個 100-200 字的完整描述，包含：
1. 圖表的主要內容或主題
2. 關鍵資訊或數據（如果有）
3. 在文件中的作用或意義
4. 與上下文的關聯性

【回應格式】
請只回傳描述文字，不要包含額外說明。

描述："""

        return prompt
    
    def generate_description(self, request: DescriptionRequest) -> DescriptionResult:
        """生成單個圖表描述"""
        start_time = time.time()
        
        try:
            # 建立提示詞
            prompt = self.create_prompt_template(request)
            
            self.logger.info(f"正在生成描述：{request.caption_type} {request.caption_number}")
            
            # 建立LLM請求
            llm_request = LLMRequest(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
                system_message="你是一個專業的學術文件分析助手，擅長為圖表生成清晰、準確的文字描述。"
            )
            
            # 調用LLM
            llm_response = self.llm_manager.generate(llm_request)
            
            if not llm_response.success:
                raise Exception(llm_response.error_message or "LLM調用失敗")
            
            # 清理描述文字
            description = llm_response.content.strip()
            if description.startswith("描述："):
                description = description[3:].strip()
            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            # 更新統計
            self.total_tokens_used += llm_response.token_usage.get('total_tokens', 0)
            self.total_requests += 1
            
            # 計算信心度
            confidence = self._calculate_confidence(description, request, llm_response.provider)
            
            self.logger.info(f"描述生成成功，耗時 {processing_time:.2f}s，使用 {llm_response.token_usage.get('total_tokens', 0)} tokens")
            
            return DescriptionResult(
                original_caption=request.caption_text,
                generated_description=description,
                confidence_score=confidence,
                processing_time=processing_time,
                token_usage=llm_response.token_usage,
                success=True,
                llm_provider=llm_response.provider
            )
            
        except Exception as e:
            error_msg = f"描述生成失敗：{str(e)}"
            self.logger.error(error_msg)
            
            return DescriptionResult(
                original_caption=request.caption_text,
                generated_description="",
                confidence_score=0.0,
                processing_time=time.time() - start_time,
                token_usage={},
                success=False,
                llm_provider=self.llm_manager.get_current_provider(),
                error_message=error_msg
            )
    
    def _calculate_confidence(self, description: str, request: DescriptionRequest, provider: str) -> float:
        """計算描述品質的信心度"""
        score = 0.3  # 基礎分數
        
        # LLM提供者調整
        if provider == "OpenAI":
            score += 0.3
        elif provider == "LocalLLM":
            score += 0.2
        else:  # MockLLM
            score += 0.1
        
        # 長度檢查
        if 50 <= len(description) <= 300:
            score += 0.2
        
        # 關鍵詞包含檢查
        if request.caption_number in description or request.caption_type in description:
            score += 0.1
        
        # 內容相關性檢查
        if request.related_context:
            for context in request.related_context:
                # 簡單的關鍵詞匹配
                common_words = set(context.split()) & set(description.split())
                if len(common_words) > 2:
                    score += 0.1
                    break
        
        # 完整性檢查
        if "圖" in description or "表" in description or "顯示" in description:
            score += 0.1
        
        return min(score, 1.0)
    
    def batch_generate_descriptions(self, requests: List[DescriptionRequest], 
                                   delay: float = 0.5) -> List[DescriptionResult]:
        """批次生成描述"""
        results = []
        
        self.logger.info(f"開始批次生成 {len(requests)} 個描述，使用 {self.llm_manager.get_current_provider()}")
        
        for i, request in enumerate(requests, 1):
            try:
                result = self.generate_description(request)
                results.append(result)
                
                # 顯示進度
                if i % 5 == 0 or i == len(requests):
                    success_count = sum(1 for r in results if r.success)
                    self.logger.info(f"進度: {i}/{len(requests)}, 成功率: {success_count}/{i}")
                
                # API 呼叫間隔 (Mock LLM不需要間隔)
                if i < len(requests) and self.llm_manager.get_current_provider() != "MockLLM":
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"處理第 {i} 個請求時發生錯誤：{str(e)}")
                continue
        
        self.logger.info(f"批次處理完成，總計使用 {self.total_tokens_used} tokens")
        return results
    
    def switch_llm_provider(self, provider_name: str) -> bool:
        """切換LLM提供者"""
        success = self.llm_manager.switch_provider(provider_name)
        if success:
            self.logger.info(f"已切換到LLM提供者: {provider_name}")
        return success
    
    def get_available_providers(self) -> List[str]:
        """獲取可用的提供者列表"""
        return self.llm_manager.list_available_providers()
    
    def get_current_provider(self) -> str:
        """獲取當前提供者"""
        return self.llm_manager.get_current_provider()
    
    def get_usage_statistics(self) -> Dict:
        """獲取使用統計"""
        return {
            "current_provider": self.get_current_provider(),
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_request": self.total_tokens_used / max(self.total_requests, 1)
        }
    
    def save_results_to_json(self, results: List[DescriptionResult], 
                           output_path: str) -> None:
        """將結果保存為 JSON 檔案"""
        data = {
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "llm_provider": self.get_current_provider(),
            "total_results": len(results),
            "success_count": sum(1 for r in results if r.success),
            "usage_statistics": self.get_usage_statistics(),
            "results": [
                {
                    "original_caption": r.original_caption,
                    "generated_description": r.generated_description,
                    "confidence_score": r.confidence_score,
                    "processing_time": r.processing_time,
                    "token_usage": r.token_usage,
                    "success": r.success,
                    "llm_provider": r.llm_provider,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"結果已保存到 {output_path}")

if __name__ == "__main__":
    # 基本測試
    generator = LLMDescriptionGeneratorV2("mock")  # 使用模擬提供者
    
    print(f"當前LLM提供者: {generator.get_current_provider()}")
    print(f"可用提供者: {generator.get_available_providers()}")
    
    # 測試單個描述生成
    test_request = DescriptionRequest(
        caption_text="中國的算盤",
        caption_type="圖",
        caption_number="1-1",
        related_context=["算盤是中國古代重要的計算工具", "圖1-1顯示了傳統算盤的結構"],
        page_number=2
    )
    
    result = generator.generate_description(test_request)
    print(f"\n生成結果:")
    print(f"成功: {result.success}")
    print(f"提供者: {result.llm_provider}")
    print(f"描述: {result.generated_description}")
    print(f"信心度: {result.confidence_score}")
    print(f"處理時間: {result.processing_time:.2f}s")