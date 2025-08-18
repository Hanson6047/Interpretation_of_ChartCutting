"""
Caption 擷取器單元測試

測試 CaptionExtractor 和相關功能的正確性
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from caption_extractor import (
    CaptionExtractor, CaptionPatterns, TextBlock, CaptionCandidate,
    ReferenceMatch, PDFCaptionContextProcessor
)
from dto import CaptionInfo, ContextInfo, CaptionContextPair


class TestCaptionPatterns(unittest.TestCase):
    """測試 Caption 模式識別"""
    
    def setUp(self):
        self.extractor = CaptionExtractor()
    
    def test_chinese_caption_patterns(self):
        """測試中文 Caption 模式"""
        test_cases = [
            ("圖 1：這是測試圖片", ("1", None, "這是測試圖片")),
            ("表 2.1：統計資料表", ("2", "1", "統計資料表")),
            ("圖表 3.2：流程圖說明", ("3", "2", "流程圖說明")),
            ("圖片 4 顯示結果", ("4", None, "顯示結果")),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                pattern = self.extractor.caption_patterns[0]  # 第一個中文模式
                match = pattern.search(text)
                if match and expected:
                    groups = match.groups()
                    self.assertEqual(groups[0], expected[0])  # 主編號
                    self.assertEqual(groups[1], expected[1])  # 子編號
                    self.assertEqual(groups[2], expected[2])  # 文字內容
    
    def test_english_caption_patterns(self):
        """測試英文 Caption 模式"""
        test_cases = [
            ("Figure 1: Test image", ("1", None, "Test image")),
            ("Table 2.1: Statistical data", ("2", "1", "Statistical data")),
            ("Fig. 3.2 Flow chart", ("3", "2", "Flow chart")),
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                # 測試英文模式
                found = False
                for pattern in self.extractor.caption_patterns:
                    match = pattern.search(text)
                    if match and expected:
                        groups = match.groups()
                        if len(groups) >= 3:
                            self.assertEqual(groups[0], expected[0])
                            self.assertEqual(groups[1], expected[1])
                            self.assertEqual(groups[2], expected[2])
                            found = True
                            break
                
                if expected:
                    self.assertTrue(found, f"應該找到匹配: {text}")
    
    def test_reference_patterns(self):
        """測試內文引用模式"""
        test_cases = [
            ("如圖 1 所示", "1"),
            ("參見表 2.1", "2.1"),
            ("見圖表 3", "3"),
            ("as shown in Figure 4", "4"),
            ("see Table 2.1", "2.1"),
        ]
        
        for text, expected_number in test_cases:
            with self.subTest(text=text):
                found = False
                for pattern in self.extractor.reference_patterns:
                    match = pattern.search(text)
                    if match:
                        groups = match.groups()
                        number = f"{groups[0]}.{groups[1]}" if len(groups) > 1 and groups[1] else groups[0]
                        if number == expected_number:
                            found = True
                            break
                
                self.assertTrue(found, f"應該找到引用: {text} -> {expected_number}")


class TestTextBlock(unittest.TestCase):
    """測試 TextBlock 資料結構"""
    
    def test_text_block_creation(self):
        """測試 TextBlock 建立"""
        block = TextBlock(
            text="測試文字",
            page_number=1,
            bbox=(100, 200, 300, 400),
            font_size=12.0,
            font_name="Arial",
            is_bold=True
        )
        
        self.assertEqual(block.text, "測試文字")
        self.assertEqual(block.page_number, 1)
        self.assertEqual(block.bbox, (100, 200, 300, 400))
        self.assertEqual(block.font_size, 12.0)
        self.assertEqual(block.font_name, "Arial")
        self.assertTrue(block.is_bold)


class TestCaptionExtractor(unittest.TestCase):
    """測試 CaptionExtractor 主要功能"""
    
    def setUp(self):
        self.extractor = CaptionExtractor(
            context_window=100,
            min_caption_length=5,
            confidence_threshold=0.3
        )
    
    def test_determine_caption_type(self):
        """測試 Caption 類型判斷"""
        test_cases = [
            ("圖 1：測試", "figure"),
            ("表 2：統計", "table"),
            ("Figure 3", "figure"),
            ("Table 4", "table"),
            ("圖表 5", "chart"),
        ]
        
        for caption_text, expected_type in test_cases:
            with self.subTest(caption_text=caption_text):
                result = self.extractor._determine_caption_type(caption_text)
                self.assertEqual(result, expected_type)
    
    def test_calculate_caption_confidence(self):
        """測試 Caption 信心度計算"""
        # 建立測試用的 TextBlock
        block = TextBlock(
            text="圖 1：這是測試圖片的說明文字",
            page_number=1,
            bbox=(100, 200, 300, 250),
            font_size=14.0,
            font_name="Arial",
            is_bold=True
        )
        
        match_text = "圖 1：這是測試圖片的說明文字"
        confidence = self.extractor._calculate_caption_confidence(block, match_text)
        
        # 信心度應該在合理範圍內
        self.assertGreater(confidence, 0.5)  # 粗體、合理字體大小應該有較高信心度
        self.assertLessEqual(confidence, 1.0)
    
    def test_extract_context(self):
        """測試上下文擷取"""
        text = "這是一段很長的文字內容，包含了圖 1 的引用，後面還有更多文字內容來測試上下文擷取功能。"
        start_pos = text.find("圖 1")
        end_pos = start_pos + 3
        
        context = self.extractor._extract_context(text, start_pos, end_pos)
        
        # 上下文應該包含引用文字
        self.assertIn("圖 1", context)
        # 上下文長度應該合理
        self.assertLessEqual(len(context), self.extractor.context_window)
    
    def test_is_matching_caption(self):
        """測試 Caption 和引用的匹配"""
        caption = CaptionCandidate(
            text="測試圖片",
            page_number=1,
            position=(100, 200, 300, 250),
            caption_type="figure",
            number="1",
            confidence=0.8
        )
        
        reference = ReferenceMatch(
            text="如圖 1 所示",
            page_number=1,
            reference_type="figure",
            reference_number="1",
            surrounding_context="前面文字 如圖 1 所示 後面文字",
            position=(100, 300, 400, 350),
            confidence=0.7
        )
        
        result = self.extractor._is_matching_caption(caption, reference)
        self.assertTrue(result)
    
    def test_identify_captions_with_mock_blocks(self):
        """使用模擬的文字區塊測試 Caption 識別"""
        # 建立測試用的文字區塊
        test_blocks = [
            TextBlock(
                text="圖 1：測試圖片說明\n這是圖片的詳細描述。",
                page_number=1,
                bbox=(100, 200, 400, 280),
                font_size=12.0,
                font_name="Arial",
                is_bold=True
            ),
            TextBlock(
                text="表 2.1：統計資料表\n包含各種數據的統計表格。",
                page_number=2,
                bbox=(100, 150, 400, 230),
                font_size=11.0,
                font_name="Times",
                is_bold=False
            )
        ]
        
        captions = self.extractor.identify_captions(test_blocks)
        
        # 應該識別出兩個 Caption
        self.assertEqual(len(captions), 2)
        
        # 檢查第一個 Caption
        self.assertEqual(captions[0].number, "1")
        self.assertEqual(captions[0].caption_type, "figure")
        self.assertIn("測試圖片", captions[0].text)
        
        # 檢查第二個 Caption
        self.assertEqual(captions[1].number, "2.1")
        self.assertEqual(captions[1].caption_type, "table")
        self.assertIn("統計資料", captions[1].text)
    
    def test_find_references_with_mock_blocks(self):
        """使用模擬的文字區塊測試引用查找"""
        # 建立測試用的 Caption
        captions = [
            CaptionCandidate(
                text="測試圖片",
                page_number=1,
                position=(100, 200, 300, 250),
                caption_type="figure",
                number="1",
                confidence=0.8
            )
        ]
        
        # 建立測試用的文字區塊
        test_blocks = [
            TextBlock(
                text="根據研究結果，如圖 1 所示，數據呈現明顯趨勢。",
                page_number=1,
                bbox=(100, 300, 400, 350),
                font_size=10.0,
                font_name="Arial",
                is_bold=False
            )
        ]
        
        references = self.extractor.find_references(test_blocks, captions)
        
        # 應該找到一個引用
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].reference_number, "1")
        self.assertEqual(references[0].reference_type, "figure")
        self.assertIn("如圖 1 所示", references[0].text)


class TestPDFCaptionContextProcessor(unittest.TestCase):
    """測試主要處理器"""
    
    def setUp(self):
        self.processor = PDFCaptionContextProcessor()
    
    @patch('caption_extractor.CaptionExtractor.extract_text_blocks')
    @patch('caption_extractor.CaptionExtractor.identify_captions')
    @patch('caption_extractor.CaptionExtractor.find_references')
    @patch('caption_extractor.CaptionExtractor.pair_captions_with_contexts')
    def test_process_pdf(self, mock_pair, mock_find_refs, mock_identify, mock_extract):
        """測試完整的 PDF 處理流程"""
        # 設定模擬回傳值
        mock_extract.return_value = [
            TextBlock("圖 1：測試", 1, (100, 200, 300, 250), 12.0, "Arial", True)
        ]
        
        mock_identify.return_value = [
            CaptionCandidate("測試", 1, (100, 200, 300, 250), "figure", "1", 0.8)
        ]
        
        mock_find_refs.return_value = [
            ReferenceMatch("如圖 1", 1, "figure", "1", "上下文", (100, 300, 400, 350), 0.7)
        ]
        
        mock_pair.return_value = [
            CaptionContextPair(
                caption=CaptionInfo("測試", 1, (100, 200, 300, 250), "figure", "1", 0.8),
                contexts=[ContextInfo("如圖 1", 1, "figure", "1", "上下文", 0.7)],
                combined_text="圖表說明：測試\n\n相關內文：\n1. 上下文",
                pairing_confidence=0.8
            )
        ]
        
        # 執行測試
        result = self.processor.process_pdf("test.pdf")
        
        # 驗證結果
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].caption.number, "1")
        self.assertEqual(result[0].caption.caption_type, "figure")
        self.assertEqual(len(result[0].contexts), 1)
    
    def test_get_processing_stats(self):
        """測試處理統計功能"""
        # 建立測試資料
        pairs = [
            CaptionContextPair(
                caption=CaptionInfo("測試1", 1, (0, 0, 100, 50), "figure", "1", 0.8),
                contexts=[],
                combined_text="測試",
                pairing_confidence=0.8
            ),
            CaptionContextPair(
                caption=CaptionInfo("測試2", 2, (0, 0, 100, 50), "table", "2", 0.6),
                contexts=[],
                combined_text="測試",
                pairing_confidence=0.6
            )
        ]
        
        stats = self.processor.get_processing_stats(pairs)
        
        # 驗證統計結果
        self.assertEqual(stats["total_pairs"], 2)
        self.assertEqual(stats["types_distribution"]["figure"], 1)
        self.assertEqual(stats["types_distribution"]["table"], 1)
        self.assertEqual(stats["confidence_stats"]["min"], 0.6)
        self.assertEqual(stats["confidence_stats"]["max"], 0.8)
        self.assertEqual(stats["confidence_stats"]["avg"], 0.7)
        self.assertEqual(set(stats["pages_covered"]), {1, 2})


class TestIntegration(unittest.TestCase):
    """整合測試"""
    
    def test_complete_workflow_with_sample_text(self):
        """使用樣本文字測試完整工作流程"""
        # 這個測試需要實際的 PDF 檔案，暫時跳過
        # 在實際環境中可以使用測試 PDF 檔案
        pass


def create_test_pdf():
    """建立測試用的 PDF 檔案（輔助函數）"""
    # 這裡可以使用 reportlab 或其他工具建立測試 PDF
    # 暫時留空，實際實作時可以補充
    pass


if __name__ == '__main__':
    # 設定日誌
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 執行測試
    unittest.main(verbosity=2)