#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM提供者抽象層 - 支援多種LLM後端切換
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMRequest:
    """LLM請求"""
    prompt: str
    max_tokens: int = 300
    temperature: float = 0.3
    system_message: Optional[str] = None

@dataclass 
class LLMResponse:
    """LLM回應"""
    content: str
    success: bool
    processing_time: float
    token_usage: Dict[str, int]
    error_message: Optional[str] = None
    provider: str = ""

class LLMProvider(ABC):
    """LLM提供者抽象基類"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成回應"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查是否可用"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名稱"""
        pass

class MockLLMProvider(LLMProvider):
    """模擬LLM提供者 - 用於開發測試"""
    
    def __init__(self):
        super().__init__()
        self.response_templates = {
            '圖': "這是一個圖表，展示了{content}。從圖中可以看出相關的資訊和數據關係，有助於理解{context}的概念。這個圖表在文件中起到了重要的說明作用。",
            '表': "這是一個表格，整理了{content}相關的數據。表格中包含了重要的統計資訊和分類數據，提供了{context}的詳細參考資料。"
        }
    
    @property
    def provider_name(self) -> str:
        return "MockLLM"
    
    def is_available(self) -> bool:
        return True
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成模擬回應"""
        start_time = time.time()
        
        try:
            # 模擬處理時間
            time.sleep(0.1)
            
            # 簡單的模板生成
            content = self._generate_mock_content(request.prompt)
            
            processing_time = time.time() - start_time
            
            return LLMResponse(
                content=content,
                success=True,
                processing_time=processing_time,
                token_usage={"prompt_tokens": len(request.prompt)//4, "completion_tokens": len(content)//4, "total_tokens": (len(request.prompt) + len(content))//4},
                provider=self.provider_name
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                processing_time=time.time() - start_time,
                token_usage={},
                error_message=str(e),
                provider=self.provider_name
            )
    
    def _generate_mock_content(self, prompt: str) -> str:
        """生成模擬內容"""
        # 從prompt中提取關鍵資訊
        if "圖" in prompt:
            chart_type = "圖"
        elif "表" in prompt:
            chart_type = "表"
        else:
            chart_type = "圖"
        
        # 提取可能的內容關鍵字
        content_keywords = self._extract_keywords(prompt)
        context_info = self._extract_context(prompt)
        
        template = self.response_templates[chart_type]
        return template.format(
            content=content_keywords or "相關主題",
            context=context_info or "該領域"
        )
    
    def _extract_keywords(self, prompt: str) -> str:
        """提取關鍵字"""
        # 簡單的關鍵字提取
        lines = prompt.split('\n')
        for line in lines:
            if '原始說明' in line:
                parts = line.split('：')
                if len(parts) > 1:
                    return parts[1].strip()
        return "主要內容"
    
    def _extract_context(self, prompt: str) -> str:
        """提取上下文"""
        if "計算機" in prompt or "電腦" in prompt:
            return "計算機科學"
        elif "數學" in prompt:
            return "數學"
        elif "統計" in prompt:
            return "統計學"
        return "該主題"

class OpenAIProvider(LLMProvider):
    """OpenAI提供者"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """使用OpenAI生成回應"""
        start_time = time.time()
        
        try:
            import openai
            
            # 設定API
            openai.api_key = self.api_key
            openai.api_base = self.base_url
            
            messages = []
            if request.system_message:
                messages.append({"role": "system", "content": request.system_message})
            messages.append({"role": "user", "content": request.prompt})
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            content = response.choices[0].message.content.strip()
            processing_time = time.time() - start_time
            
            return LLMResponse(
                content=content,
                success=True,
                processing_time=processing_time,
                token_usage=response.usage.__dict__,
                provider=self.provider_name
            )
            
        except Exception as e:
            return LLMResponse(
                content="",
                success=False,
                processing_time=time.time() - start_time,
                token_usage={},
                error_message=str(e),
                provider=self.provider_name
            )

class LocalLLMProvider(LLMProvider):
    """本地LLM提供者 - 預留給未來的本地模型"""
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__()
        self.model_path = model_path
        self.model = None
        
    @property
    def provider_name(self) -> str:
        return "LocalLLM"
    
    def is_available(self) -> bool:
        # 預留：檢查本地模型是否可用
        return False
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """使用本地LLM生成回應"""
        start_time = time.time()
        
        # 預留：實作本地LLM調用
        # 這裡可以整合像是 Ollama, llama.cpp, 或其他本地LLM方案
        
        return LLMResponse(
            content="本地LLM尚未實作",
            success=False,
            processing_time=time.time() - start_time,
            token_usage={},
            error_message="本地LLM功能尚未實作",
            provider=self.provider_name
        )

class LLMManager:
    """LLM管理器 - 自動選擇可用的提供者"""
    
    def __init__(self, preferred_provider: str = "auto"):
        self.logger = logging.getLogger(__name__)
        self.providers = {
            "mock": MockLLMProvider(),
            "openai": OpenAIProvider(),
            "local": LocalLLMProvider()
        }
        self.preferred_provider = preferred_provider
        self.current_provider = None
        self._select_provider()
    
    def _select_provider(self):
        """選擇可用的提供者"""
        if self.preferred_provider != "auto" and self.preferred_provider in self.providers:
            provider = self.providers[self.preferred_provider]
            if provider.is_available():
                self.current_provider = provider
                self.logger.info(f"使用指定的LLM提供者: {provider.provider_name}")
                return
        
        # 自動選擇順序: OpenAI -> Local -> Mock
        for provider_name in ["openai", "local", "mock"]:
            provider = self.providers[provider_name]
            if provider.is_available():
                self.current_provider = provider
                self.logger.info(f"自動選擇LLM提供者: {provider.provider_name}")
                return
        
        # 最後fallback到Mock
        self.current_provider = self.providers["mock"]
        self.logger.warning("所有LLM提供者都不可用，使用模擬提供者")
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """生成回應"""
        if not self.current_provider:
            return LLMResponse(
                content="",
                success=False,
                processing_time=0,
                token_usage={},
                error_message="沒有可用的LLM提供者"
            )
        
        return self.current_provider.generate(request)
    
    def switch_provider(self, provider_name: str) -> bool:
        """切換提供者"""
        if provider_name not in self.providers:
            self.logger.error(f"未知的提供者: {provider_name}")
            return False
        
        provider = self.providers[provider_name]
        if not provider.is_available():
            self.logger.error(f"提供者不可用: {provider_name}")
            return False
        
        self.current_provider = provider
        self.logger.info(f"已切換到LLM提供者: {provider.provider_name}")
        return True
    
    def get_current_provider(self) -> str:
        """獲取當前提供者名稱"""
        return self.current_provider.provider_name if self.current_provider else "None"
    
    def list_available_providers(self) -> List[str]:
        """列出可用的提供者"""
        return [name for name, provider in self.providers.items() if provider.is_available()]

# 使用範例
if __name__ == "__main__":
    # 初始化管理器
    llm_manager = LLMManager()
    
    print(f"當前LLM提供者: {llm_manager.get_current_provider()}")
    print(f"可用提供者: {llm_manager.list_available_providers()}")
    
    # 測試生成
    request = LLMRequest(
        prompt="請為圖1-1：中國的算盤生成描述",
        system_message="你是專業的學術文件分析助手"
    )
    
    response = llm_manager.generate(request)
    print(f"\n生成結果 (使用 {response.provider}):")
    print(f"成功: {response.success}")
    print(f"內容: {response.content}")
    print(f"處理時間: {response.processing_time:.2f}s")