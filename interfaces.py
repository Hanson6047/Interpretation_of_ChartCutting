"""
介面定義 - 定義子模組對外提供的服務介面
用於確保子模組與主專案之間的標準化整合

設計原則：
1. 抽象介面定義，不包含具體實作
2. 支援依賴注入和測試
3. 提供清楚的錯誤處理機制
4. 支援非同步操作
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Protocol
from pathlib import Path
import asyncio
from datetime import datetime

from .dto import (
    ProcessingRequest, ProcessingResult, BatchProcessingResult,
    ServiceInfo, HealthCheckResult, CaptionContextPair,
    LoggingConfig, CacheConfig
)


# =============================================================================
# 核心處理介面
# =============================================================================

class IPDFCaptionProcessor(ABC):
    """PDF Caption 處理器的主要介面"""
    
    @abstractmethod
    async def process_single_file(self, request: ProcessingRequest) -> ProcessingResult:
        """處理單一 PDF 檔案
        
        Args:
            request: 處理請求，包含檔案資訊和配置
            
        Returns:
            ProcessingResult: 處理結果
            
        Raises:
            FileNotFoundError: 檔案不存在
            InvalidConfigError: 配置參數無效
            ProcessingError: 處理過程中發生錯誤
        """
        pass
    
    @abstractmethod
    async def process_batch_files(self, 
                                requests: List[ProcessingRequest]) -> BatchProcessingResult:
        """批量處理多個 PDF 檔案
        
        Args:
            requests: 處理請求列表
            
        Returns:
            BatchProcessingResult: 批量處理結果
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> ServiceInfo:
        """取得服務資訊"""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """健康檢查"""
        pass


# =============================================================================
# RAG 整合介面
# =============================================================================

class IRAGIntegrationManager(ABC):
    """RAG 系統整合管理器介面"""
    
    @abstractmethod
    async def integrate_processing_results(self, 
                                         results: List[ProcessingResult]) -> Dict[str, Any]:
        """將處理結果整合到 RAG 系統
        
        Args:
            results: PDF 處理結果列表
            
        Returns:
            Dict[str, Any]: 整合結果統計
            
        Raises:
            IntegrationError: 整合過程中發生錯誤
        """
        pass
    
    @abstractmethod
    async def create_sidecar_index(self, 
                                 caption_pairs: List[CaptionContextPair],
                                 source_file: str) -> str:
        """建立伴生索引
        
        Args:
            caption_pairs: Caption 和內文配對結果
            source_file: 來源檔案路徑
            
        Returns:
            str: 伴生索引檔案路徑
        """
        pass
    
    @abstractmethod
    async def merge_with_main_index(self, 
                                  sidecar_index_path: str,
                                  merge_strategy: str = "append") -> bool:
        """將伴生索引與主索引合併
        
        Args:
            sidecar_index_path: 伴生索引路徑
            merge_strategy: 合併策略 ("append", "replace", "smart_merge")
            
        Returns:
            bool: 合併是否成功
        """
        pass
    
    @abstractmethod
    def get_index_status(self) -> Dict[str, Any]:
        """取得索引狀態資訊"""
        pass


class IVectorStoreManager(ABC):
    """向量資料庫管理器介面"""
    
    @abstractmethod
    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """建立文字向量"""
        pass
    
    @abstractmethod
    async def add_documents(self, 
                          texts: List[str], 
                          metadatas: List[Dict[str, Any]]) -> List[str]:
        """添加文件到向量資料庫"""
        pass
    
    @abstractmethod
    async def search_similar(self, 
                           query: str, 
                           k: int = 5,
                           filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """相似度搜尋"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> int:
        """刪除文件"""
        pass


# =============================================================================
# 快取和儲存介面
# =============================================================================

class ICacheManager(ABC):
    """快取管理器介面"""
    
    @abstractmethod
    async def get_cached_result(self, file_hash: str) -> Optional[ProcessingResult]:
        """取得快取的處理結果"""
        pass
    
    @abstractmethod
    async def cache_result(self, file_hash: str, result: ProcessingResult) -> bool:
        """快取處理結果"""
        pass
    
    @abstractmethod
    async def clear_expired_cache(self) -> int:
        """清理過期快取"""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """取得快取統計資訊"""
        pass


class IFileManager(ABC):
    """檔案管理器介面"""
    
    @abstractmethod
    async def validate_file(self, file_path: str) -> bool:
        """驗證檔案有效性"""
        pass
    
    @abstractmethod
    async def calculate_file_hash(self, file_path: str) -> str:
        """計算檔案雜湊值"""
        pass
    
    @abstractmethod
    async def create_backup(self, file_path: str) -> str:
        """建立檔案備份"""
        pass
    
    @abstractmethod
    async def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """清理暫存檔案"""
        pass


# =============================================================================
# 日誌和監控介面
# =============================================================================

class ILogger(Protocol):
    """日誌記錄器介面（使用 Protocol 而非 ABC）"""
    
    def debug(self, message: str, **kwargs) -> None: ...
    def info(self, message: str, **kwargs) -> None: ...
    def warning(self, message: str, **kwargs) -> None: ...
    def error(self, message: str, **kwargs) -> None: ...
    def critical(self, message: str, **kwargs) -> None: ...


class IMetricsCollector(ABC):
    """指標收集器介面"""
    
    @abstractmethod
    def record_processing_time(self, file_path: str, duration: float) -> None:
        """記錄處理時間"""
        pass
    
    @abstractmethod
    def record_success_count(self, operation: str) -> None:
        """記錄成功次數"""
        pass
    
    @abstractmethod
    def record_error_count(self, operation: str, error_type: str) -> None:
        """記錄錯誤次數"""
        pass
    
    @abstractmethod
    def get_metrics_summary(self) -> Dict[str, Any]:
        """取得指標摘要"""
        pass


# =============================================================================
# 配置管理介面
# =============================================================================

class IConfigManager(ABC):
    """配置管理器介面"""
    
    @abstractmethod
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """載入配置"""
        pass
    
    @abstractmethod
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """取得配置值"""
        pass
    
    @abstractmethod
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """驗證配置，回傳錯誤訊息列表"""
        pass


# =============================================================================
# 主服務介面 - 統合所有功能
# =============================================================================

class IPDFCaptionService(ABC):
    """PDF Caption 處理服務的統一介面
    
    這是子模組對外的主要介面，整合所有功能組件
    """
    
    def __init__(self, 
                 rag_manager: IRAGIntegrationManager,
                 vector_store: IVectorStoreManager,
                 cache_manager: ICacheManager,
                 file_manager: IFileManager,
                 logger: ILogger,
                 metrics: IMetricsCollector,
                 config_manager: IConfigManager):
        """依賴注入建構子"""
        self.rag_manager = rag_manager
        self.vector_store = vector_store
        self.cache_manager = cache_manager
        self.file_manager = file_manager
        self.logger = logger
        self.metrics = metrics
        self.config = config_manager
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化服務"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """關閉服務"""
        pass
    
    @abstractmethod
    async def process_and_integrate(self, 
                                  request: ProcessingRequest,
                                  auto_integrate: bool = True) -> ProcessingResult:
        """處理 PDF 並整合到 RAG 系統
        
        這是最主要的對外介面，整合了處理和 RAG 整合功能
        
        Args:
            request: 處理請求
            auto_integrate: 是否自動整合到 RAG 系統
            
        Returns:
            ProcessingResult: 處理結果（包含整合狀態）
        """
        pass


# =============================================================================
# 例外處理
# =============================================================================

class PDFCaptionError(Exception):
    """PDF Caption 處理相關錯誤的基礎類別"""
    pass


class ProcessingError(PDFCaptionError):
    """處理過程中的錯誤"""
    pass


class IntegrationError(PDFCaptionError):
    """RAG 整合錯誤"""
    pass


class InvalidConfigError(PDFCaptionError):
    """配置無效錯誤"""
    pass


class CacheError(PDFCaptionError):
    """快取操作錯誤"""
    pass


# =============================================================================
# 工廠介面 - 用於建立服務實例
# =============================================================================

class IServiceFactory(ABC):
    """服務工廠介面"""
    
    @abstractmethod
    def create_pdf_caption_service(self,
                                 config_path: Optional[str] = None) -> IPDFCaptionService:
        """建立 PDF Caption 服務實例"""
        pass
    
    @abstractmethod
    def create_rag_integration_manager(self,
                                     rag_helper_instance: Any) -> IRAGIntegrationManager:
        """建立 RAG 整合管理器"""
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """取得預設配置"""
        pass


# =============================================================================
# 實用函式介面
# =============================================================================

async def validate_service_dependencies(service: IPDFCaptionService) -> List[str]:
    """驗證服務依賴項
    
    Returns:
        List[str]: 錯誤訊息列表，空列表表示所有依賴都正常
    """
    errors = []
    
    try:
        # 檢查各個依賴組件
        health_result = await service.rag_manager.get_index_status() if hasattr(service, 'rag_manager') else None
        cache_stats = service.cache_manager.get_cache_stats() if hasattr(service, 'cache_manager') else None
        config_errors = service.config.validate_config() if hasattr(service, 'config') else []
        
        if config_errors:
            errors.extend(config_errors)
            
    except Exception as e:
        errors.append(f"依賴項檢查失敗: {str(e)}")
    
    return errors


def create_processing_request_from_dict(data: Dict[str, Any]) -> ProcessingRequest:
    """從字典建立處理請求的便利函式"""
    from .dto import ProcessingRequest, FileInfo, ProcessingConfig
    
    file_info = FileInfo(**data.get('file_info', {}))
    config = ProcessingConfig(**data.get('config', {}))
    
    return ProcessingRequest(
        file_info=file_info,
        config=config,
        output_directory=data.get('output_directory'),
        cache_enabled=data.get('cache_enabled', True)
    )