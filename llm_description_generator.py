#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段B：LLM API 圖表描述生成器
使用 OpenAI API 根據 Caption 和內文生成圖表描述
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import openai
from dotenv import load_dotenv
import time
import json

# 載入環境變數
load_dotenv()

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
    error_message: Optional[str] = None

class LLMDescriptionGenerator:
    """LLM 描述生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.client = None
        self.setup_openai()
        
        # 設定日誌
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # API 使用統計
        self.total_tokens_used = 0
        self.total_requests = 0
        
    def setup_openai(self):
        """設定 OpenAI API"""
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # 設定 OpenAI 客戶端
        openai.api_key = api_key
        openai.api_base = base_url
        
        self.logger.info(f"OpenAI API 設定完成，使用 base_url: {base_url}")
    
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
            
            # 調用 OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的學術文件分析助手，擅長為圖表生成清晰、準確的文字描述。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3,
                top_p=0.9
            )
            
            # 提取回應
            description = response.choices[0].message.content.strip()
            
            # 清理描述文字
            if description.startswith("描述："):
                description = description[3:].strip()
            
            # 計算處理時間
            processing_time = time.time() - start_time
            
            # 更新統計
            token_usage = response.usage
            self.total_tokens_used += token_usage.total_tokens
            self.total_requests += 1
            
            # 簡單的信心度評估
            confidence = self._calculate_confidence(description, request)
            
            self.logger.info(f"描述生成成功，耗時 {processing_time:.2f}s，使用 {token_usage.total_tokens} tokens")
            
            return DescriptionResult(
                original_caption=request.caption_text,
                generated_description=description,
                confidence_score=confidence,
                processing_time=processing_time,
                token_usage=token_usage.__dict__,
                success=True
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
                error_message=error_msg
            )
    
    def _calculate_confidence(self, description: str, request: DescriptionRequest) -> float:
        """計算描述品質的信心度"""
        score = 0.5  # 基礎分數
        
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
                                   delay: float = 1.0) -> List[DescriptionResult]:
        """批次生成描述"""
        results = []
        
        self.logger.info(f"開始批次生成 {len(requests)} 個描述")
        
        for i, request in enumerate(requests, 1):
            try:
                result = self.generate_description(request)
                results.append(result)
                
                # 顯示進度
                if i % 5 == 0 or i == len(requests):
                    success_count = sum(1 for r in results if r.success)
                    self.logger.info(f"進度: {i}/{len(requests)}, 成功率: {success_count}/{i}")
                
                # API 呼叫間隔
                if i < len(requests):
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"處理第 {i} 個請求時發生錯誤：{str(e)}")
                continue
        
        self.logger.info(f"批次處理完成，總計使用 {self.total_tokens_used} tokens")
        return results
    
    def get_usage_statistics(self) -> Dict:
        """獲取使用統計"""
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_request": self.total_tokens_used / max(self.total_requests, 1)
        }
    
    def save_results_to_json(self, results: List[DescriptionResult], 
                           output_path: str) -> None:
        """將結果保存為 JSON 檔案"""
        data = {
            "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
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
    generator = LLMDescriptionGenerator()
    
    # 測試單個描述生成
    test_request = DescriptionRequest(
        caption_text="中國的算盤",
        caption_type="圖",
        caption_number="1-1",
        related_context=["算盤是中國古代重要的計算工具", "圖1-1顯示了傳統算盤的結構"],
        page_number=2
    )
    
    result = generator.generate_description(test_request)
    print(f"生成結果：{result.generated_description}")
    print(f"信心度：{result.confidence_score}")