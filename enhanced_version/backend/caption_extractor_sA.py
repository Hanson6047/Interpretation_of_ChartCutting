"""
Caption 和內文關鍵字檢索器 - 階段 A 實作

本模組負責從 Digital PDF 中：
1. 識別圖表說明文字 (Caption)
2. 搜尋內文中提及圖表的關鍵段落
3. 建立 Caption 與相關內文段落的對應關係
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
from collections import defaultdict

from dto import CaptionInfo, ContextInfo, CaptionContextPair


# =============================================================================
# Caption 識別模式
# =============================================================================

class CaptionPatterns:
    """Caption 識別的正則表達式模式"""
    
    # 中文 Caption 模式
    CHINESE_PATTERNS = [
        # 圖 X.Y、表 X.Y 格式
        r'(?:圖|表|圖表)[\s]*(\d+)(?:\.(\d+))?[\s]*[：:：]\s*(.+?)(?=\n|$)',
        r'(?:圖|表|圖表)[\s]*(\d+)(?:[.-](\d+))?[\s]*[：:：]\s*(.+?)(?=\n|$)',
        
        # Figure X、Table X 格式
        r'(?:Figure|Table|Fig\.|Tab\.)[\s]*(\d+)(?:\.(\d+))?[\s]*[：:：]?\s*(.+?)(?=\n|$)',
        
        # 圖片 X、表格 X 格式
        r'(?:圖片|表格|圖像)[\s]*(\d+)(?:[.-](\d+))?[\s]*[：:：]\s*(.+?)(?=\n|$)',
        
        # 更靈活的格式：圖/表 + 數字 (沒有冒號)
        r'(?:圖|表)[\s]*(\d+)(?:[.-](\d+))?[\s]+(.+?)(?=(?:\n|$|圖|表|\d))',
    ]
    
    # 英文 Caption 模式
    ENGLISH_PATTERNS = [
        r'(?:Figure|Table|Fig\.|Tab\.)[\s]*(\d+)(?:\.(\d+))?[\s]*[：:：.]?\s*(.+?)(?=\n|$)',
        r'(?:FIGURE|TABLE|FIG\.|TAB\.)[\s]*(\d+)(?:\.(\d+))?[\s]*[：:：.]?\s*(.+?)(?=\n|$)',
    ]
    
    # 內文引用模式
    REFERENCE_PATTERNS = [
        # 中文引用
        r'(?:如|見|參見|參考|詳見)[\s]*(?:圖|表|圖表)[\s]*(\d+)(?:[.-](\d+))?',
        r'(?:圖|表|圖表)[\s]*(\d+)(?:[.-](\d+))?[\s]*(?:所示|顯示|中|內)',
        r'(?:上|下)[\s]*(?:圖|表)[\s]*(\d+)(?:[.-](\d+))?',
        
        # 英文引用
        r'(?:see|refer to|as shown in|in)[\s]*(?:Figure|Table|Fig\.|Tab\.)[\s]*(\d+)(?:\.(\d+))?',
        r'(?:Figure|Table|Fig\.|Tab\.)[\s]*(\d+)(?:\.(\d+))?[\s]*(?:shows|displays|illustrates)',
    ]


# =============================================================================
# 資料結構
# =============================================================================

@dataclass
class TextBlock:
    """文字區塊"""
    text: str
    page_number: int
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    font_size: float = 0.0
    font_name: str = ""
    is_bold: bool = False


@dataclass
class CaptionCandidate:
    """Caption 候選項"""
    text: str
    page_number: int
    position: Tuple[float, float, float, float]
    caption_type: str  # "figure", "table", "chart"
    number: str  # "1", "2.1", etc.
    confidence: float = 0.0
    font_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReferenceMatch:
    """內文引用匹配結果"""
    text: str
    page_number: int
    reference_type: str
    reference_number: str
    surrounding_context: str
    position: Tuple[float, float, float, float]
    confidence: float = 0.0


# =============================================================================
# Caption 擷取器
# =============================================================================

class CaptionExtractor:
    """Caption 和內文引用擷取器"""
    
    def __init__(self, 
                 context_window: int = 200,
                 min_caption_length: int = 5,
                 confidence_threshold: float = 0.3):
        self.context_window = context_window
        self.min_caption_length = min_caption_length
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # 編譯正則表達式以提高效能
        self._compile_patterns()
    
    def _compile_patterns(self):
        """編譯所有正則表達式模式"""
        self.caption_patterns = []
        self.reference_patterns = []
        
        # 編譯 Caption 模式
        for pattern in CaptionPatterns.CHINESE_PATTERNS + CaptionPatterns.ENGLISH_PATTERNS:
            try:
                self.caption_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
            except re.error as e:
                self.logger.warning(f"無效的 Caption 模式: {pattern}, 錯誤: {e}")
        
        # 編譯引用模式
        for pattern in CaptionPatterns.REFERENCE_PATTERNS:
            try:
                self.reference_patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
            except re.error as e:
                self.logger.warning(f"無效的引用模式: {pattern}, 錯誤: {e}")
    
    def extract_text_blocks(self, pdf_path: str) -> List[TextBlock]:
        """從 PDF 中提取文字區塊，保留格式資訊"""
        text_blocks = []
        
        try:
            pdf_doc = fitz.open(pdf_path)
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc.load_page(page_num)
                
                # 獲取文字區塊，包含字體資訊
                blocks = page.get_text("dict")
                
                for block in blocks.get("blocks", []):
                    if "lines" not in block:  # 跳過圖像區塊
                        continue
                    
                    block_text = ""
                    bbox = block["bbox"]
                    font_info = {}
                    
                    # 提取行文字
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                            # 記錄字體資訊
                            if not font_info:
                                font_info = {
                                    "font": span.get("font", ""),
                                    "size": span.get("size", 0),
                                    "flags": span.get("flags", 0)
                                }
                        block_text += line_text + "\n"
                    
                    if block_text.strip():
                        text_blocks.append(TextBlock(
                            text=block_text.strip(),
                            page_number=page_num + 1,
                            bbox=tuple(bbox),
                            font_size=font_info.get("size", 0),
                            font_name=font_info.get("font", ""),
                            is_bold=bool(font_info.get("flags", 0) & 2**4)  # Bold flag
                        ))
            
            pdf_doc.close()
            
        except Exception as e:
            self.logger.error(f"提取文字區塊時發生錯誤: {e}")
            raise
        
        return text_blocks
    
    def identify_captions(self, text_blocks: List[TextBlock]) -> List[CaptionCandidate]:
        """識別 Caption 候選項"""
        caption_candidates = []
        
        for block in text_blocks:
            # 對每個文字區塊應用 Caption 模式
            for pattern in self.caption_patterns:
                matches = pattern.finditer(block.text)
                
                for match in matches:
                    # 提取匹配結果
                    groups = match.groups()
                    if len(groups) >= 3:
                        number1 = groups[0] if groups[0] else ""
                        number2 = groups[1] if groups[1] else ""
                        caption_text = groups[2] if groups[2] else ""
                        
                        # 組合編號
                        number = f"{number1}.{number2}" if number2 else number1
                        
                        # 跳過太短的 Caption
                        if len(caption_text.strip()) < self.min_caption_length:
                            continue
                        
                        # 判斷 Caption 類型
                        caption_type = self._determine_caption_type(match.group(0))
                        
                        # 計算信心度
                        confidence = self._calculate_caption_confidence(block, match.group(0))
                        
                        caption_candidates.append(CaptionCandidate(
                            text=caption_text.strip(),
                            page_number=block.page_number,
                            position=block.bbox,
                            caption_type=caption_type,
                            number=number,
                            confidence=confidence,
                            font_info={
                                "font_name": block.font_name,
                                "font_size": block.font_size,
                                "is_bold": block.is_bold
                            }
                        ))
        
        # 去重和排序
        caption_candidates = self._deduplicate_captions(caption_candidates)
        caption_candidates.sort(key=lambda x: (x.page_number, x.number))
        
        return caption_candidates
    
    def find_references(self, text_blocks: List[TextBlock], 
                       captions: List[CaptionCandidate]) -> List[ReferenceMatch]:
        """在內文中尋找對 Caption 的引用"""
        references = []
        
        # 建立 Caption 編號索引
        caption_numbers = {f"{cap.caption_type}_{cap.number}" for cap in captions}
        caption_numbers.update({cap.number for cap in captions})
        
        for block in text_blocks:
            # 對每個文字區塊應用引用模式
            for pattern in self.reference_patterns:
                matches = pattern.finditer(block.text)
                
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 1:
                        number1 = groups[0] if groups[0] else ""
                        number2 = groups[1] if len(groups) > 1 and groups[1] else ""
                        
                        # 組合編號
                        ref_number = f"{number1}.{number2}" if number2 else number1
                        
                        # 檢查是否有對應的 Caption
                        if ref_number in caption_numbers or any(ref_number in num for num in caption_numbers):
                            # 擷取上下文
                            context = self._extract_context(block.text, match.start(), match.end())
                            
                            # 判斷引用類型
                            ref_type = self._determine_reference_type(match.group(0))
                            
                            # 計算信心度
                            confidence = self._calculate_reference_confidence(match.group(0), context)
                            
                            references.append(ReferenceMatch(
                                text=match.group(0),
                                page_number=block.page_number,
                                reference_type=ref_type,
                                reference_number=ref_number,
                                surrounding_context=context,
                                position=block.bbox,
                                confidence=confidence
                            ))
        
        return references
    
    def pair_captions_with_contexts(self, 
                                  captions: List[CaptionCandidate],
                                  references: List[ReferenceMatch]) -> List[CaptionContextPair]:
        """將 Caption 與內文引用配對"""
        pairs = []
        
        # 按 Caption 分組引用
        caption_refs = defaultdict(list)
        
        for ref in references:
            # 尋找匹配的 Caption
            matching_captions = [
                cap for cap in captions 
                if self._is_matching_caption(cap, ref)
            ]
            
            for caption in matching_captions:
                caption_refs[id(caption)].append(ref)
        
        # 建立配對結果
        for caption in captions:
            caption_id = id(caption)
            matched_refs = caption_refs.get(caption_id, [])
            
            # 轉換為 DTO 格式
            caption_info = CaptionInfo(
                text=caption.text,
                page_number=caption.page_number,
                position=caption.position,
                caption_type=caption.caption_type,
                number=caption.number,
                confidence=caption.confidence
            )
            
            context_infos = []
            for ref in matched_refs:
                context_infos.append(ContextInfo(
                    text=ref.text,
                    page_number=ref.page_number,
                    reference_type=ref.reference_type,
                    reference_number=ref.reference_number,
                    surrounding_text=ref.surrounding_context,
                    confidence=ref.confidence
                ))
            
            # 計算配對信心度
            pairing_confidence = self._calculate_pairing_confidence(caption, matched_refs)
            
            # 生成合併文字
            combined_text = self._generate_combined_text(caption_info, context_infos)
            
            pairs.append(CaptionContextPair(
                caption=caption_info,
                contexts=context_infos,
                combined_text=combined_text,
                pairing_confidence=pairing_confidence
            ))
        
        return pairs
    
    # =============================================================================
    # 輔助方法
    # =============================================================================
    
    def _determine_caption_type(self, caption_text: str) -> str:
        """判斷 Caption 類型"""
        caption_lower = caption_text.lower()
        
        if any(word in caption_lower for word in ['圖', 'figure', 'fig.', '圖片', '圖像']):
            return "figure"
        elif any(word in caption_lower for word in ['表', 'table', 'tab.', '表格']):
            return "table"
        elif any(word in caption_lower for word in ['chart', '圖表']):
            return "chart"
        else:
            return "figure"  # 預設為圖片
    
    def _calculate_caption_confidence(self, block: TextBlock, match_text: str) -> float:
        """計算 Caption 的信心度"""
        confidence = 0.5  # 基礎信心度
        
        # 字體大小因子
        if block.font_size > 12:
            confidence += 0.1
        elif block.font_size < 8:
            confidence -= 0.1
        
        # 粗體因子
        if block.is_bold:
            confidence += 0.2
        
        # 文字長度因子
        text_length = len(match_text.strip())
        if 10 < text_length < 100:
            confidence += 0.1
        elif text_length > 200:
            confidence -= 0.1
        
        # 位置因子（簡化版本）
        # 可以根據實際需求擴展
        
        return min(1.0, max(0.0, confidence))
    
    def _determine_reference_type(self, ref_text: str) -> str:
        """判斷引用類型"""
        ref_lower = ref_text.lower()
        
        if any(word in ref_lower for word in ['圖', 'figure', 'fig.']):
            return "figure"
        elif any(word in ref_lower for word in ['表', 'table', 'tab.']):
            return "table"
        else:
            return "general"
    
    def _calculate_reference_confidence(self, ref_text: str, context: str) -> float:
        """計算引用的信心度"""
        confidence = 0.5  # 基礎信心度
        
        # 上下文長度因子
        if 50 < len(context) < 300:
            confidence += 0.2
        
        # 引用類型明確性
        if any(word in ref_text.lower() for word in ['如圖', '見圖', 'see figure']):
            confidence += 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _extract_context(self, text: str, start_pos: int, end_pos: int) -> str:
        """擷取指定位置周圍的上下文"""
        context_start = max(0, start_pos - self.context_window // 2)
        context_end = min(len(text), end_pos + self.context_window // 2)
        
        return text[context_start:context_end].strip()
    
    def _is_matching_caption(self, caption: CaptionCandidate, reference: ReferenceMatch) -> bool:
        """檢查 Caption 和引用是否匹配"""
        # 簡單的編號匹配
        if caption.number == reference.reference_number:
            return True
        
        # 類型匹配檢查
        if caption.caption_type == reference.reference_type:
            # 更寬鬆的編號匹配
            if caption.number in reference.reference_number or reference.reference_number in caption.number:
                return True
        
        return False
    
    def _calculate_pairing_confidence(self, caption: CaptionCandidate, 
                                    references: List[ReferenceMatch]) -> float:
        """計算配對的信心度"""
        if not references:
            return 0.3  # 沒有引用的低信心度
        
        # 基於引用數量和質量
        base_confidence = min(0.8, 0.4 + len(references) * 0.1)
        
        # 基於引用的平均信心度
        avg_ref_confidence = sum(ref.confidence for ref in references) / len(references)
        
        # 結合 Caption 自身信心度
        combined_confidence = (base_confidence + avg_ref_confidence + caption.confidence) / 3
        
        return min(1.0, max(0.0, combined_confidence))
    
    def _generate_combined_text(self, caption: CaptionInfo, contexts: List[ContextInfo]) -> str:
        """生成合併的文字，供 LLM 處理"""
        combined_parts = []
        
        # Caption 部分
        combined_parts.append(f"圖表說明：{caption.text}")
        
        # 內文引用部分
        if contexts:
            combined_parts.append("相關內文：")
            for i, context in enumerate(contexts, 1):
                combined_parts.append(f"{i}. {context.surrounding_text}")
        
        return "\n\n".join(combined_parts)
    
    def _deduplicate_captions(self, captions: List[CaptionCandidate]) -> List[CaptionCandidate]:
        """去除重複的 Caption"""
        seen = set()
        deduplicated = []
        
        for caption in captions:
            key = (caption.page_number, caption.number, caption.text[:50])  # 使用前50字符避免完全相同
            if key not in seen:
                seen.add(key)
                deduplicated.append(caption)
        
        return deduplicated


# =============================================================================
# 主要處理介面
# =============================================================================

class PDFCaptionContextProcessor:
    """PDF Caption 和上下文處理器 - 階段 A 的主要介面"""
    
    def __init__(self, 
                 context_window: int = 200,
                 min_caption_length: int = 5,
                 confidence_threshold: float = 0.3):
        self.extractor = CaptionExtractor(
            context_window=context_window,
            min_caption_length=min_caption_length,
            confidence_threshold=confidence_threshold
        )
        self.logger = logging.getLogger(__name__)
    
    def process_pdf(self, pdf_path: str) -> List[CaptionContextPair]:
        """處理單個 PDF 檔案，回傳 Caption-Context 配對結果"""
        try:
            self.logger.info(f"開始處理 PDF: {pdf_path}")
            
            # 步驟 1: 提取文字區塊
            text_blocks = self.extractor.extract_text_blocks(pdf_path)
            self.logger.info(f"提取到 {len(text_blocks)} 個文字區塊")
            
            # 步驟 2: 識別 Caption
            captions = self.extractor.identify_captions(text_blocks)
            self.logger.info(f"識別到 {len(captions)} 個 Caption 候選項")
            
            # 步驟 3: 尋找內文引用
            references = self.extractor.find_references(text_blocks, captions)
            self.logger.info(f"找到 {len(references)} 個內文引用")
            
            # 步驟 4: 配對 Caption 與引用
            pairs = self.extractor.pair_captions_with_contexts(captions, references)
            
            # 過濾低信心度結果
            filtered_pairs = [
                pair for pair in pairs 
                if pair.pairing_confidence >= self.extractor.confidence_threshold
            ]
            
            self.logger.info(f"生成 {len(filtered_pairs)} 個高品質配對結果")
            
            return filtered_pairs
            
        except Exception as e:
            self.logger.error(f"處理 PDF 時發生錯誤: {e}")
            raise
    
    def get_processing_stats(self, pairs: List[CaptionContextPair]) -> Dict[str, Any]:
        """取得處理統計資訊"""
        if not pairs:
            return {"total_pairs": 0}
        
        stats = {
            "total_pairs": len(pairs),
            "types_distribution": {},
            "pages_covered": set(),
            "confidence_stats": {
                "min": min(pair.pairing_confidence for pair in pairs),
                "max": max(pair.pairing_confidence for pair in pairs),
                "avg": sum(pair.pairing_confidence for pair in pairs) / len(pairs)
            }
        }
        
        # 統計類型分布
        type_counts = defaultdict(int)
        for pair in pairs:
            type_counts[pair.caption.caption_type] += 1
            stats["pages_covered"].add(pair.caption.page_number)
        
        stats["types_distribution"] = dict(type_counts)
        stats["pages_covered"] = list(stats["pages_covered"])
        
        return stats