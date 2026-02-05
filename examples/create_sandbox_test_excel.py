#!/usr/bin/env python3
"""
Sandbox環境テスト用のExcelファイルを作成
小規模データで動作確認用
"""

import pandas as pd
from pathlib import Path

def create_sandbox_test_excel():
    """Sandbox用のテストExcelファイルを作成"""
    
    # テストデータ（10行）
    test_data = {
        '商品コード': [f'TEST-{i:04d}' for i in range(1, 11)],
        '商品名': [
            'テスト商品1',
            'テスト商品2',
            'テスト商品3',
            'テスト商品4',
            'テスト商品5',
            'テスト商品6',
            'テスト商品7',
            'テスト商品8',
            'テスト商品9',
            'テスト商品10'
        ],
        '変更後_キャッチコピーBtoC': [
            'ウイルス予防に効果的',
            '血圧を下げる効果',
            'ダイエットに最適',
            '免疫力アップ',
            '健康的な毎日',
            '疲労回復サポート',
            'アンチエイジング効果',
            'デトックス作用',
            'ストレス解消',
            '安心安全'
        ],
        '変更後_キャッチコピーBtoB': [
            '予防効果が期待できます',
            '血圧管理に',
            '体重管理をサポート',
            '免疫機能を高める',
            '健康維持に',
            '疲労回復を促進',
            'エイジングケアに',
            '体内浄化効果',
            'リラックス効果',
            '信頼の品質'
        ],
        '変更後_仕様スペック': [
            '内容量: 100g',
            '内容量: 200ml',
            '内容量: 30粒',
            '内容量: 60粒',
            '内容量: 500g',
            '内容量: 150ml',
            '内容量: 90粒',
            '内容量: 300g',
            '内容量: 250ml',
            '内容量: 120粒'
        ],
        '変更後_商品説明文': [
            'ウイルス対策に効果的な成分を配合',
            '高血圧が気になる方へ',
            '脂肪燃焼をサポート',
            '免疫細胞を活性化',
            '毎日の健康をサポート',
            '疲労物質を除去',
            '老化を防ぐ成分配合',
            '体内の毒素を排出',
            'ストレスを軽減',
            '安全性テスト済み'
        ],
        '変更後_商品名': [
            'ウイルスガード',
            '血圧サポート',
            'ダイエットサプリ',
            '免疫アップ',
            'ヘルスケア',
            '疲労回復剤',
            'アンチエイジング',
            'デトックス茶',
            'リラックスハーブ',
            '安心サプリ'
        ],
        '変更後_検索用キーワード': [
            'ウイルス 予防 免疫',
            '血圧 高血圧 健康',
            'ダイエット 痩せる 脂肪',
            '免疫 抵抗力 健康',
            '健康 サプリ',
            '疲労 回復 元気',
            'アンチエイジング 若返り',
            'デトックス 解毒',
            'ストレス リラックス',
            '安心 安全 信頼'
        ],
        '変更後_使用上の注意': [
            '医師に相談してください',
            '血圧の薬を服用中の方は注意',
            '食事制限と併用',
            'アレルギー体質の方は注意',
            '1日3回服用',
            '運動と併用が効果的',
            '長期服用で効果',
            '飲むだけで効果',
            '寝る前に服用',
            '推奨用量を守る'
        ],
        '変更後_アスクルおススメポイント': [
            'ウイルス対策の決定版',
            '血圧管理の新常識',
            '食べるだけで痩せる',
            '免疫力が劇的に向上',
            '医者もおススメ',
            '疲れが取れる',
            '若返り効果抜群',
            '体内をキレイに',
            'ストレスゼロ',
            'ベストプライス'
        ]
    }
    
    # DataFrameを作成
    df = pd.DataFrame(test_data)
    
    # ファイルパスを設定
    project_root = Path(__file__).parent.parent
    excel_file = project_root / "examples" / "sandbox_test.xlsx"
    
    # Excelに保存
    df.to_excel(excel_file, index=False, sheet_name='Sheet1')
    
    print(f"✅ Sandbox test Excel file created: {excel_file}")
    print(f"📊 Rows: {len(df)}")
    print(f"📏 Columns: {len(df.columns)}")
    print(f"💾 File size: {excel_file.stat().st_size:,} bytes")
    print()
    print("🔍 Expected violations (stub mode):")
    print("  - Row 0: ウイルス, 予防, 免疫")
    print("  - Row 1: 血圧, 高血圧")
    print("  - Row 2: ダイエット, 痩せる, 脂肪")
    print("  - Row 3: 免疫, 抵抗力")
    print("  - Row 4: (No violations)")
    print("  - Row 5: 疲労, 回復")
    print("  - Row 6: アンチエイジング, 若返り")
    print("  - Row 7: デトックス, 解毒")
    print("  - Row 8: ストレス")
    print("  - Row 9: 安心, 安全, 信頼, ベストプライス")
    print()
    print("📤 Upload to S3:")
    print(f"   aws s3 cp {excel_file} s3://askul-sandbox-01-regulation-test-bucket/input/")
    
    return excel_file

if __name__ == "__main__":
    create_sandbox_test_excel()
