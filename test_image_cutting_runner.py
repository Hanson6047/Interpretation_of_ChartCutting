#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 圖表自動切割測試執行腳本
生成 test_ImageCut_result 資料夾並將切割結果存放其中
"""

import os
import sys
from pathlib import Path

# 確保當前目錄在模組路徑中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pdf_chart_extractor import extract_charts_from_pdf


def run_image_cutting_test():
    """執行圖片切割測試，生成test_ImageCut_result資料夾"""
    
    # 設定輸出資料夾名稱
    output_dir = "test_ImageCut_result"
    
    # 創建輸出目錄
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ 已創建輸出目錄: {output_dir}")
    else:
        print(f"📁 輸出目錄已存在: {output_dir}")
    
    # 使用相對於項目根目錄的路徑
    project_root = os.path.join(current_dir, "..", "..")
    
    # 尋找可用的PDF檔案進行測試
    test_pdf_paths = []
    base_paths = [
        os.path.join(project_root, "pdfFiles", "計概第一章.pdf"),
        os.path.join(project_root, "pdfFiles", "計概第二章.pdf"), 
        os.path.join(project_root, "pdfFiles", "計算機概論(一) - HackMD.pdf")
    ]
    
    # 添加存在的基本PDF檔案
    for path in base_paths:
        if os.path.exists(path):
            test_pdf_paths.append(path)
    
    # 添加其他可能的PDF檔案
    pdf_dirs = [
        os.path.join(project_root, "pdfFiles", "multi_data", "sys_check_digital"),
        os.path.join(project_root, "pdfFiles", "multi_data", "sys_check_scanned")
    ]
    
    for pdf_dir in pdf_dirs:
        if os.path.exists(pdf_dir):
            pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
            for pdf_file in pdf_files[:2]:  # 只取前2個檔案避免太多
                test_pdf_paths.append(os.path.join(pdf_dir, pdf_file))
    
    print("🔍 開始PDF圖表切割測試...")
    print(f"📁 輸出目錄: {output_dir}")
    print(f"📄 準備處理 {len(test_pdf_paths)} 個PDF檔案")
    print("-" * 50)
    
    total_processed = 0
    total_images_extracted = 0
    
    for i, pdf_path in enumerate(test_pdf_paths, 1):
        if not os.path.exists(pdf_path):
            print(f"⚠️  檔案不存在，跳過: {pdf_path}")
            continue
            
        print(f"\n[{i}/{len(test_pdf_paths)}] 處理檔案: {os.path.basename(pdf_path)}")
        
        # 為每個PDF創建子目錄
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_output_dir = os.path.join(output_dir, pdf_basename)
        
        try:
            result = extract_charts_from_pdf(pdf_path, pdf_output_dir)
            
            if result["success"]:
                total_processed += 1
                total_images_extracted += result["total_images"]
                print(f"✅ 成功提取 {result['total_images']} 張圖片")
                print(f"📁 圖片儲存於: {pdf_output_dir}")
                print(f"📋 Metadata: {result['metadata_file']}")
            else:
                print(f"❌ 處理失敗: {result['error']}")
                
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎉 測試完成!")
    print(f"📊 統計結果:")
    print(f"   - 成功處理PDF檔案: {total_processed}")
    print(f"   - 總共提取圖片: {total_images_extracted}")
    print(f"   - 結果儲存於: {output_dir}/")
    print("=" * 50)
    
    return {
        "processed_files": total_processed,
        "total_images": total_images_extracted,
        "output_directory": output_dir
    }


def get_all_available_pdfs():
    """取得所有可用的PDF檔案清單"""
    project_root = os.path.join(current_dir, "..", "..")
    
    all_pdfs = []
    pdf_locations = [
        (os.path.join(project_root, "pdfFiles"), "pdfFiles/"),
        (os.path.join(project_root, "pdfFiles", "multi_data", "sys_check_digital"), "pdfFiles/multi_data/sys_check_digital/"),
        (os.path.join(project_root, "pdfFiles", "multi_data", "sys_check_scanned"), "pdfFiles/multi_data/sys_check_scanned/")
    ]
    
    for location_path, display_location in pdf_locations:
        if os.path.exists(location_path):
            pdf_files = [f for f in os.listdir(location_path) if f.lower().endswith('.pdf')]
            for pdf_file in pdf_files:
                full_path = os.path.join(location_path, pdf_file)
                file_size = os.path.getsize(full_path) / (1024*1024)  # MB
                all_pdfs.append({
                    'full_path': full_path,
                    'filename': pdf_file,
                    'display_location': display_location,
                    'size_mb': file_size
                })
    
    return all_pdfs


def list_available_pdfs():
    """列出可用的PDF檔案"""
    print("📄 可用的PDF檔案:")
    
    all_pdfs = get_all_available_pdfs()
    current_location = ""
    
    for i, pdf_info in enumerate(all_pdfs, 1):
        if current_location != pdf_info['display_location']:
            current_location = pdf_info['display_location']
            print(f"\n📁 {current_location}")
        
        print(f"   {i:2d}. {pdf_info['filename']} ({pdf_info['size_mb']:.1f} MB)")


def interactive_select_pdfs():
    """互動式選擇PDF檔案"""
    all_pdfs = get_all_available_pdfs()
    
    if not all_pdfs:
        print("❌ 未找到任何PDF檔案!")
        return []
    
    print("📄 可用的PDF檔案:")
    print("=" * 60)
    current_location = ""
    
    for i, pdf_info in enumerate(all_pdfs, 1):
        if current_location != pdf_info['display_location']:
            current_location = pdf_info['display_location']
            print(f"\n📁 {current_location}")
        
        print(f"   {i:2d}. {pdf_info['filename']} ({pdf_info['size_mb']:.1f} MB)")
    
    print("\n" + "=" * 60)
    print("選擇模式:")
    print("  - 輸入數字選擇單一檔案 (例如: 1)")
    print("  - 輸入數字範圍選擇多個檔案 (例如: 1-3)")  
    print("  - 輸入逗號分隔的數字選擇多個檔案 (例如: 1,3,5)")
    print("  - 輸入 'all' 選擇所有檔案")
    print("  - 按 Enter 取消")
    
    while True:
        try:
            choice = input("\n請選擇要處理的PDF檔案: ").strip()
            
            if not choice:
                print("❌ 已取消選擇")
                return []
            
            if choice.lower() == 'all':
                return [pdf['full_path'] for pdf in all_pdfs]
            
            selected_indices = []
            
            # 處理逗號分隔的選擇
            if ',' in choice:
                parts = choice.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        # 處理範圍 (例如: 1-3)
                        start, end = map(int, part.split('-'))
                        selected_indices.extend(range(start, end + 1))
                    else:
                        selected_indices.append(int(part))
            elif '-' in choice:
                # 處理範圍 (例如: 1-3)
                start, end = map(int, choice.split('-'))
                selected_indices = list(range(start, end + 1))
            else:
                # 單一選擇
                selected_indices = [int(choice)]
            
            # 驗證選擇的索引
            valid_indices = []
            for idx in selected_indices:
                if 1 <= idx <= len(all_pdfs):
                    valid_indices.append(idx)
                else:
                    print(f"⚠️  無效的選擇: {idx} (範圍: 1-{len(all_pdfs)})")
            
            if valid_indices:
                selected_pdfs = [all_pdfs[i-1]['full_path'] for i in valid_indices]
                
                print(f"\n✅ 已選擇 {len(selected_pdfs)} 個檔案:")
                for i, idx in enumerate(valid_indices, 1):
                    pdf_info = all_pdfs[idx-1]
                    print(f"   {i}. {pdf_info['filename']}")
                
                confirm = input("\n確認處理這些檔案? (y/N): ").strip().lower()
                if confirm == 'y':
                    return selected_pdfs
                else:
                    print("❌ 已取消選擇")
                    return []
            else:
                print("❌ 沒有有效的選擇")
                continue
                
        except (ValueError, IndexError) as e:
            print(f"❌ 輸入格式錯誤: {e}")
            print("請使用正確的格式 (例如: 1, 1-3, 1,3,5, 或 all)")
            continue


def run_selected_files_test(selected_files):
    """執行選定檔案的圖片切割測試"""
    
    # 設定輸出資料夾名稱
    output_dir = "test_ImageCut_result"
    
    # 創建輸出目錄
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ 已創建輸出目錄: {output_dir}")
    else:
        print(f"📁 輸出目錄已存在: {output_dir}")
    
    print("🔍 開始PDF圖表切割測試...")
    print(f"📁 輸出目錄: {output_dir}")
    print(f"📄 準備處理 {len(selected_files)} 個PDF檔案")
    print("-" * 50)
    
    total_processed = 0
    total_images_extracted = 0
    
    for i, pdf_path in enumerate(selected_files, 1):
        if not os.path.exists(pdf_path):
            print(f"⚠️  檔案不存在，跳過: {pdf_path}")
            continue
            
        print(f"\n[{i}/{len(selected_files)}] 處理檔案: {os.path.basename(pdf_path)}")
        
        # 為每個PDF創建子目錄
        pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_output_dir = os.path.join(output_dir, pdf_basename)
        
        try:
            result = extract_charts_from_pdf(pdf_path, pdf_output_dir)
            
            if result["success"]:
                total_processed += 1
                total_images_extracted += result["total_images"]
                print(f"✅ 成功提取 {result['total_images']} 張圖片")
                print(f"📁 圖片儲存於: {pdf_output_dir}")
                print(f"📋 Metadata: {result['metadata_file']}")
            else:
                print(f"❌ 處理失敗: {result['error']}")
                
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎉 測試完成!")
    print(f"📊 統計結果:")
    print(f"   - 成功處理PDF檔案: {total_processed}")
    print(f"   - 總共提取圖片: {total_images_extracted}")
    print(f"   - 結果儲存於: {output_dir}/")
    print("=" * 50)
    
    return {
        "processed_files": total_processed,
        "total_images": total_images_extracted,
        "output_directory": output_dir
    }


if __name__ == "__main__":
    print("=== PDF 圖表自動切割測試工具 ===")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_available_pdfs()
        elif sys.argv[1] == "--select":
            selected_files = interactive_select_pdfs()
            if selected_files:
                run_selected_files_test(selected_files)
        elif sys.argv[1] == "--all":
            run_image_cutting_test()
        elif sys.argv[1] == "--help":
            print("使用方法:")
            print("  python test_image_cutting_runner.py           # 互動式選擇檔案")
            print("  python test_image_cutting_runner.py --select  # 互動式選擇檔案")
            print("  python test_image_cutting_runner.py --all     # 處理所有檔案")
            print("  python test_image_cutting_runner.py --list    # 列出可用PDF檔案")
            print("  python test_image_cutting_runner.py --help    # 顯示說明")
            print("  python test_image_cutting_runner.py <PDF路徑> [輸出目錄]  # 處理指定檔案")
        else:
            # 處理指定的PDF檔案
            pdf_file = sys.argv[1]
            output_dir = sys.argv[2] if len(sys.argv) > 2 else "test_ImageCut_result"
            
            # 支援相對路徑
            if not os.path.isabs(pdf_file):
                project_root = os.path.join(current_dir, "..", "..")
                pdf_file = os.path.join(project_root, pdf_file)
            
            if os.path.exists(pdf_file):
                print(f"處理單一檔案: {pdf_file}")
                
                # 確保輸出目錄存在
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                # 為PDF創建子目錄
                pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
                pdf_output_dir = os.path.join(output_dir, pdf_basename)
                
                result = extract_charts_from_pdf(pdf_file, pdf_output_dir)
                if result["success"]:
                    print(f"✅ 成功提取 {result['total_images']} 張圖片到 {pdf_output_dir}")
                    print(f"📋 Metadata: {result['metadata_file']}")
                else:
                    print(f"❌ 處理失敗: {result['error']}")
            else:
                print(f"❌ 檔案不存在: {pdf_file}")
    else:
        # 預設模式：互動式選擇檔案
        print("\n💡 預設使用互動式選擇模式")
        print("如果要處理所有檔案，請使用: python test_image_cutting_runner.py --all")
        print()
        
        selected_files = interactive_select_pdfs()
        if selected_files:
            run_selected_files_test(selected_files)