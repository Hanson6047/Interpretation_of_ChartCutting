"""
Data Transfer Objects (DTO) - 標準化資料結構
用於主專案與子模組之間的資料傳遞，確保低耦合設計

  - 資料傳遞標準化：在主專案與 PDF 處理子模組之間傳遞資料
  - 低耦合設計：確保模組間的介面清晰分離
  
設計原則：
1. 只包含資料，不包含業務邏輯
2. 使用標準 Python 型別，易於序列化/反序列化
3. 提供清楚的文件說明每個欄位的含義


"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime


# =============================================================================
# 輸入 DTO - 主專案傳給子模組的資料
# =============================================================================

@dataclass
class ProcessingConfig:
    """處理配置參數"""
    # Caption 識別參數
    context_window: int = 200  # 上下文窗口大小
    min_caption_length: int = 5  # 最小 caption 長度
    confidence_threshold: float = 0.3  # 配對信心度閾值
    
    # 語言設定
    language: str = "zh-TW"  # 主要語言
    
    # 處理選項
    include_tables: bool = True  # 是否包含表格
    include_figures: bool = True  # 是否包含圖片
    include_charts: bool = True  # 是否包含圖表
    
    # 額外設定
    custom_patterns: Optional[Dict[str, List[str]]] = None  # 自定義識別模式
    

@dataclass
class FileInfo:
    """檔案資訊 - 主專案提供給子模組的檔案基本資料"""
    file_path: str
    file_name: str
    file_size: int
    file_hash: Optional[str] = None  # 檔案雜湊，用於快取檢查


@dataclass
class ProcessingRequest:
    """處理請求 - 完整的處理要求"""
    file_info: FileInfo
    config: ProcessingConfig
    output_directory: Optional[str] = None  # 輸出目錄
    cache_enabled: bool = True  # 是否啟用快取
    

# =============================================================================
# 輸出 DTO - 子模組回傳給主專案的資料  
# =============================================================================

@dataclass
class CaptionInfo:
    """圖表說明文字資訊"""
    text: str  # Caption 完整文字
    page_number: int  # 所在頁數
    position: Tuple[float, float, float, float]  # 位置 (x1, y1, x2, y2)
    caption_type: str  # 類型: "figure", "table", "chart"
    number: str  # 編號: "1", "2.1", etc.
    confidence: float  # 識別信心度 0-1


@dataclass 
class ContextInfo:
    """內文引用資訊"""
    text: str  # 引用句子
    page_number: int  # 所在頁數
    reference_type: str  # 引用類型
    reference_number: str  # 引用編號
    surrounding_text: str  # 周圍上下文
    confidence: float  # 匹配信心度


@dataclass
class CaptionContextPair:
    """Caption 與內文的配對結果"""
    caption: CaptionInfo
    contexts: List[ContextInfo]
    combined_text: str  # 合併的完整文字（供 LLM 處理）
    pairing_confidence: float  # 配對信心度
    

@dataclass
class ProcessingResult:
    """處理結果"""
    # 基本資訊
    success: bool
    file_info: FileInfo
    processing_time: float  # 處理耗時（秒）
    timestamp: datetime
    
    # 處理結果
    caption_pairs: List[CaptionContextPair]
    total_captions: int
    total_contexts: int
    
    # 錯誤資訊
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    # 中繼資料
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BatchProcessingResult:
    """批量處理結果"""
    total_files: int
    successful_files: int
    failed_files: int
    results: Dict[str, ProcessingResult]  # file_path -> result
    overall_processing_time: float
    

# =============================================================================
# 介面 DTO - 定義子模組提供的服務介面
# =============================================================================

@dataclass
class ServiceInfo:
    """子模組服務資訊"""
    service_name: str = "pdf_caption_processor"
    version: str = "1.0.0"
    supported_formats: List[str] = None  # 支援的檔案格式
    capabilities: List[str] = None  # 功能列表
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["pdf"]
        if self.capabilities is None:
            self.capabilities = [
                "caption_extraction",
                "context_matching", 
                "text_pairing",
                "batch_processing"
            ]


@dataclass 
class HealthCheckResult:
    """健康檢查結果"""
    is_healthy: bool
    service_info: ServiceInfo
    dependencies_status: Dict[str, bool]  # 依賴套件狀態
    error_messages: List[str]
    check_timestamp: datetime


# =============================================================================
# 依賴注入 DTO - 外部依賴的抽象接口
# =============================================================================

@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = False
    log_file_path: Optional[str] = None


@dataclass
class CacheConfig:
    """快取配置"""
    enabled: bool = True
    cache_directory: str = "./cache"
    max_cache_size_mb: int = 100
    cache_expiry_days: int = 30


# =============================================================================
# 實用函式 - DTO 轉換和驗證
# =============================================================================

def validate_processing_request(request: ProcessingRequest) -> Tuple[bool, List[str]]:
    """驗證處理請求的有效性
    
    Returns:
        Tuple[bool, List[str]]: (是否有效, 錯誤訊息列表)
    """
    errors = []
    
    # 檢查檔案路徑
    if not request.file_info.file_path:
        errors.append("檔案路徑不能為空")
        
    # 檢查配置參數
    config = request.config
    if config.confidence_threshold < 0 or config.confidence_threshold > 1:
        errors.append("信心度閾值必須在 0-1 之間")
        
    if config.context_window < 50:
        errors.append("上下文窗口不能小於 50")
        
    if config.min_caption_length < 1:
        errors.append("最小 caption 長度不能小於 1")
    
    return len(errors) == 0, errors


def create_error_result(file_info: FileInfo, error_message: str, 
                       processing_time: float = 0.0) -> ProcessingResult:
    """建立錯誤結果的便利函式"""
    return ProcessingResult(
        success=False,
        file_info=file_info,
        processing_time=processing_time,
        timestamp=datetime.now(),
        caption_pairs=[],
        total_captions=0,
        total_contexts=0,
        error_message=error_message
    )


def dto_to_dict(dto_object) -> Dict[str, Any]:
    """將 DTO 物件轉換為字典，便於 JSON 序列化"""
    if hasattr(dto_object, '__dict__'):
        result = {}
        for key, value in dto_object.__dict__.items():
            if hasattr(value, '__dict__'):  # 嵌套的 DTO
                result[key] = dto_to_dict(value)
            elif isinstance(value, list):
                result[key] = [dto_to_dict(item) if hasattr(item, '__dict__') else item 
                              for item in value]
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    return dto_object


def create_default_config() -> ProcessingConfig:
    """建立預設配置的便利函式"""
    return ProcessingConfig(
        context_window=200,
        min_caption_length=5, 
        confidence_threshold=0.3,
        language="zh-TW",
        include_tables=True,
        include_figures=True,
        include_charts=True
    )