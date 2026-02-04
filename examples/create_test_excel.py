#!/usr/bin/env python3
"""
CSVからExcelファイルを作成するスクリプト
S3アップロード用のテストデータを準備
"""

import pandas as pd
import sys
from pathlib import Path

def create_excel_from_csv():
    """CSVをExcelに変換"""
    # パスの設定
    project_root = Path(__file__).parent.parent
    csv_file = project_root / "examples" / "sample.csv"
    excel_file = project_root / "examples" / "sample.xlsx"
    
    print(f"Reading CSV: {csv_file}")
    
    # CSVを読み込み
    df = pd.read_csv(csv_file)
    
    print(f"Found {len(df)} rows")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Excelに保存
    df.to_excel(excel_file, index=False, sheet_name='Sheet1')
    
    print(f"✅ Excel file created: {excel_file}")
    print(f"File size: {excel_file.stat().st_size} bytes")
    
    return excel_file

if __name__ == "__main__":
    excel_file = create_excel_from_csv()
    print(f"\nNext steps:")
    print(f"1. Upload to S3:")
    print(f"   aws s3 cp {excel_file} s3://askul-sandbox-01-regulation-test-bucket/input/sample.xlsx")
    print(f"2. Or use AWS Console to upload to: input/sample.xlsx")
