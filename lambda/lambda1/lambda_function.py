"""
Lambda 1: Excel Processing and Orchestration
S3からExcelファイルを読み取り、行ごとにLambda2を呼び出し、結果を統合してS3にアップロード
"""

import os
import io
import json
import logging
import boto3
import pandas as pd
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Border, Alignment

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
BUCKET_NAME = os.getenv('BUCKET_NAME', 'askul-sandbox-01-regulation-test-bucket')
LAMBDA2_FUNCTION_NAME = os.getenv('LAMBDA2_FUNCTION_NAME', 'keywords-checker-lambda2')


def lambda_handler(event, context):
    """
    Lambda1のメインハンドラー
    
    S3トリガーとテストイベントの両方に対応
    
    S3トリガーイベント構造:
    {
        "Records": [{
            "eventSource": "aws:s3",
            "s3": {
                "bucket": {"name": "bucket-name"},
                "object": {"key": "input/file.xlsx"}
            }
        }]
    }
    
    テストイベント構造:
    {
        "input_file": "input/sample.xlsx",
        "output_file": "output/result.xlsx"
    }
    """
    try:
        logger.info(f"Lambda1 started. Event: {json.dumps(event)}")
        
        # S3トリガーイベントの場合
        if 'Records' in event and len(event['Records']) > 0 and event['Records'][0].get('eventSource') == 'aws:s3':
            logger.info("Triggered by S3 event")
            
            # S3イベントからファイル名を取得
            s3_event = event['Records'][0]['s3']
            bucket = s3_event['bucket']['name']
            input_file = s3_event['object']['key']
            
            # URLデコード（S3キーに日本語や特殊文字が含まれる場合）
            from urllib.parse import unquote_plus
            input_file = unquote_plus(input_file)
            
            logger.info(f"S3 object key: {input_file}")
            
            # input/直下のファイルかチェック（オプション：サブディレクトリを除外したい場合）
            # 現在はinput/配下のすべてのファイルを処理
            if not input_file.startswith('input/'):
                logger.warning(f"File {input_file} is not in input/ directory. Skipping.")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'File not in input/ directory, skipped'})
                }
            
            # ファイル名を取得（パスの最後の部分）
            filename = input_file.split('/')[-1]
            
            # 空のファイル名チェック
            if not filename:
                logger.error(f"Invalid file path: {input_file}")
                raise ValueError(f"Invalid file path: {input_file}")
            
            # 拡張子を.xlsxに変更（.xlsmファイルでも.xlsxで保存）
            base_filename = filename.rsplit('.', 1)[0]  # 拡張子を除去
            
            # output_fileを自動生成（必ず.xlsx）
            output_file = f"output/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{base_filename}.xlsx"
            
            logger.info(f"S3 trigger: {input_file} → {output_file}")
            logger.info(f"Bucket: {bucket}, Filename: {filename}")
            
            # バケット名を上書き（S3イベントから取得したものを使用）
            bucket_name = bucket
            
        # テストイベントの場合
        else:
            logger.info("Triggered by test event")
            
            input_file = event.get('input_file')
            output_file = event.get('output_file', f"output/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            if not input_file:
                raise ValueError("input_file is required in event")
            
            bucket_name = BUCKET_NAME
        
        # Step 1: S3からExcelファイルをダウンロード
        logger.info(f"Downloading {input_file} from S3 bucket {bucket_name}")
        excel_bytes = download_from_s3(bucket_name, input_file)
        
        # Step 2: Excelファイルを解析
        df, header_row, header_styles = parse_excel(excel_bytes)
        logger.info(f"Parsed Excel with {len(df)} rows, header at row {header_row}")
        
        # Step 3: 各行を処理してLambda2を呼び出し
        results = []
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            logger.info(f"Processing row {idx + 1}/{total_rows}")
            
            # 商品情報とチェック対象データを構築
            product_message, has_check_data = build_product_message(row)
            
            if not has_check_data:
                logger.info(f"Row {idx + 1}: No check data found")
                results.append("チェックデータが存在しません（商品名以外の列にデータがありません）")
                continue
            
            if not product_message.strip():
                logger.info(f"Row {idx + 1}: Empty row")
                results.append("(空行)")
                continue
            
            # Lambda2を呼び出し
            try:
                result_text = invoke_lambda2(idx, product_message)
                results.append(result_text)
                logger.info(f"Row {idx + 1}: Successfully processed")
            except Exception as e:
                error_message = f"エラー: {str(e)}"
                logger.error(f"Row {idx + 1}: {error_message}", exc_info=True)
                results.append(error_message)
        
        # Step 4: 結果をExcelに統合
        logger.info("Combining results into Excel")
        output_excel_bytes = combine_results_to_excel(df, results, header_row, header_styles)
        
        # Step 5: S3にアップロード
        logger.info(f"Uploading result to S3: {output_file}")
        upload_to_s3(bucket_name, output_file, output_excel_bytes)
        
        logger.info("Lambda1 completed successfully")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'output_file': output_file,
                'processed_rows': total_rows
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda1 failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def download_from_s3(bucket, key):
    """S3からファイルをダウンロード"""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()


def upload_to_s3(bucket, key, data):
    """S3にファイルをアップロード"""
    s3_client.put_object(Bucket=bucket, Key=key, Body=data)


def parse_excel(excel_bytes):
    """
    Excelファイルを解析してDataFrameとヘッダー情報を取得
    
    Returns:
        Tuple: (df, header_row, header_styles)
    """
    # ヘッダー行を自動検出（0-5行目をスキャン）
    header_row = None
    df = None
    
    for row_num in range(6):
        try:
            temp_df = pd.read_excel(
                io.BytesIO(excel_bytes),
                sheet_name='NGコピーリスト　要注意表現チェックリスト',
                header=row_num
            )
            temp_df.columns = temp_df.columns.str.strip()
            
            if '*商品名' in temp_df.columns:
                header_row = row_num
                df = temp_df
                logger.info(f"Header found at row {row_num}")
                logger.info(f"Columns: {list(df.columns)}")
                break
        except Exception as e:
            logger.debug(f"Failed to parse with header={row_num}: {str(e)}")
            continue
    
    if df is None:
        raise ValueError("「*商品名」列が見つかりません。シート名とヘッダー行を確認してください。")
    
    # openpyxlでスタイル情報を取得
    header_styles = {}
    try:
        wb = load_workbook(io.BytesIO(excel_bytes))
        ws = wb['NGコピーリスト　要注意表現チェックリスト']
        
        # ヘッダー行周辺のスタイルを保存（1-10行目）
        for row_idx in range(1, 11):
            header_styles[row_idx] = {}
            for col_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                header_styles[row_idx][col_idx] = {
                    'font': cell.font.copy() if cell.font else None,
                    'fill': cell.fill.copy() if cell.fill else None,
                    'border': cell.border.copy() if cell.border else None,
                    'alignment': cell.alignment.copy() if cell.alignment else None
                }
    except Exception as e:
        logger.warning(f"Failed to load styles: {str(e)}")
        header_styles = {}
    
    return df, header_row, header_styles


def build_product_message(row):
    """
    行データから商品情報メッセージを構築
    
    Returns:
        Tuple: (product_message, has_check_data)
    """
    product_info_columns = [
        '*商品名',
        '*管理カテゴリー大大',
        '*管理カテゴリー大',
        '*管理カテゴリー中',
        '*管理カテゴリー小',
        '*許認可大大分類',
        '*許認可大分類'
    ]
    
    check_columns = [
        '変更後_キャッチコピーBtoB',
        '変更後_商品の特徴BtoB',
        '変更後_短いキャッチコピーBtoB',
        '変更後_MDおすすめコメントBtoB',
        '変更後_キャッチコピーBtoC',
        '変更後_商品の特徴BtoC',
        '変更後_MDおすすめコメントBtoC',
        '変更後_短いキャッチコピーBtoC'
    ]
    
    message_parts = []
    has_check_data = False
    
    # 商品情報を追加
    for column in product_info_columns:
        if column in row and pd.notna(row[column]) and row[column] != '':
            message_parts.append(f"{column}: {row[column]}")
    
    # チェック対象列を追加
    for column in check_columns:
        if column in row and pd.notna(row[column]) and row[column] != '':
            message_parts.append(f"{column}: {row[column]}")
            has_check_data = True
    
    return "\n".join(message_parts), has_check_data


def invoke_lambda2(row_index, product_message):
    """
    Lambda2を呼び出してチェック結果を取得
    
    Args:
        row_index: 行番号（ログ用）
        product_message: チェック対象の商品情報
        
    Returns:
        str: Lambda2からの結果テキスト
    """
    payload = {
        'row_index': row_index,
        'product_message': product_message
    }
    
    response = lambda_client.invoke(
        FunctionName=LAMBDA2_FUNCTION_NAME,
        InvocationType='RequestResponse',  # 同期呼び出し
        Payload=json.dumps(payload)
    )
    
    response_payload = json.loads(response['Payload'].read())
    
    if response_payload.get('statusCode') != 200:
        raise Exception(f"Lambda2 returned error: {response_payload.get('body')}")
    
    body = json.loads(response_payload['body'])
    return body.get('result_text', '')


def parse_item_results(result_text):
    """
    LLM結果から各項目の結果を抽出
    """
    check_columns = [
        '変更後_キャッチコピーBtoB',
        '変更後_商品の特徴BtoB',
        '変更後_短いキャッチコピーBtoB',
        '変更後_MDおすすめコメントBtoB',
        '変更後_キャッチコピーBtoC',
        '変更後_商品の特徴BtoC',
        '変更後_MDおすすめコメントBtoC',
        '変更後_短いキャッチコピーBtoC'
    ]
    
    results = {}
    
    # テキストベースのパース
    lines = result_text.split('\n')
    current_item = None
    current_lines = []
    
    for line in lines:
        # 項目名を検出
        found_item = None
        for col in check_columns:
            if col in line:
                found_item = col
                break
        
        if found_item:
            # 前の項目を保存
            if current_item and current_lines:
                item_text = '\n'.join(current_lines)
                conclusion = extract_item_conclusion(item_text)
                results[current_item] = (conclusion, item_text)
            
            # 新しい項目開始
            current_item = found_item
            current_lines = [line]
        elif current_item:
            current_lines.append(line)
    
    # 最後の項目を保存
    if current_item and current_lines:
        item_text = '\n'.join(current_lines)
        conclusion = extract_item_conclusion(item_text)
        results[current_item] = (conclusion, item_text)
    
    # 見つからなかった項目は空で埋める
    for col in check_columns:
        if col not in results:
            results[col] = ('', '')
    
    return results


def extract_item_conclusion(item_text):
    """項目テキストから結論を抽出"""
    if not item_text or item_text.strip() == '':
        return ''
    
    if 'NG' in item_text:
        return 'NG'
    elif 'OK' in item_text:
        return 'OK'
    elif '対象キーワード存在しない' in item_text:
        return '対象キーワード存在しない'
    elif '空' in item_text or '(空)' in item_text:
        return '(空)'
    
    return ''


def combine_results_to_excel(df, results, header_row, header_styles):
    """
    結果をExcelに統合
    
    Args:
        df: 元のDataFrame
        results: Lambda2からの結果リスト
        header_row: ヘッダー行番号
        header_styles: ヘッダーのスタイル情報
        
    Returns:
        bytes: Excelファイルのバイト列
    """
    check_columns = [
        '変更後_キャッチコピーBtoB',
        '変更後_商品の特徴BtoB',
        '変更後_短いキャッチコピーBtoB',
        '変更後_MDおすすめコメントBtoB',
        '変更後_キャッチコピーBtoC',
        '変更後_商品の特徴BtoC',
        '変更後_MDおすすめコメントBtoC',
        '変更後_短いキャッチコピーBtoC'
    ]
    
    # 各項目のチェック結果を格納する辞書
    check_results = {col: [''] * len(df) for col in check_columns}
    
    # resultsから各項目の結果を抽出
    for idx, result_text in enumerate(results):
        if result_text and result_text not in ['(空行)', 'チェックデータが存在しません（商品名以外の列にデータがありません）'] and not result_text.startswith('エラー:'):
            # 各項目の結果をパース
            item_results = parse_item_results(result_text)
            
            for col in check_columns:
                if col in item_results:
                    conclusion, detail = item_results[col]
                    # 結論と詳細を結合
                    if conclusion or detail:
                        result_content = f"結論: {conclusion}\n\n{detail}" if conclusion else detail
                        check_results[col][idx] = result_content
    
    # 新しい列順を構築：各チェック対象列の直後にチェック結果列を挿入
    all_columns = list(df.columns)
    new_df_dict = {}
    
    for col in all_columns:
        # 元の列を追加
        new_df_dict[col] = df[col]
        # チェック対象列の場合、直後にチェック結果列を追加
        if col in check_columns:
            result_col_name = f'{col}_チェック結果'
            new_df_dict[result_col_name] = check_results[col]
    
    # 新しいDataFrameを作成
    df = pd.DataFrame(new_df_dict)
    
    # Create Excel file in memory with styling
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='チェック結果')
        
        # ワークシートを取得してスタイルを適用
        workbook = writer.book
        worksheet = writer.sheets['チェック結果']
        
        # オレンジ色の背景色を定義（チェック結果列用）
        orange_fill = PatternFill(start_color='FFA500', end_color='FFA500', fill_type='solid')
        
        # 元のヘッダー行のスタイルを適用（header_row + 1がExcelの実際の行番号）
        if header_styles:
            actual_header_rows = list(range(1, header_row + 2))  # 1行目からヘッダー行まで
            
            for excel_row_idx in actual_header_rows:
                if excel_row_idx in header_styles:
                    for col_idx in range(1, len(df.columns) + 1):
                        # 元の列のスタイルがある場合は適用
                        if col_idx in header_styles[excel_row_idx]:
                            cell = worksheet.cell(row=excel_row_idx, column=col_idx)
                            style_info = header_styles[excel_row_idx][col_idx]
                            
                            if style_info['font']:
                                cell.font = style_info['font']
                            if style_info['fill']:
                                cell.fill = style_info['fill']
                            if style_info['border']:
                                cell.border = style_info['border']
                            if style_info['alignment']:
                                cell.alignment = style_info['alignment']
        
        # ヘッダー行のチェック結果列にオレンジ色背景を適用
        header_excel_row = header_row + 1  # pandasは0-indexed, Excelは1-indexed
        for col_idx, col_name in enumerate(df.columns, start=1):
            if '_チェック結果' in col_name:
                cell = worksheet.cell(row=header_excel_row, column=col_idx)
                cell.fill = orange_fill
                # 元のフォントと配置を維持（あれば）
                if header_styles and header_excel_row in header_styles and 1 in header_styles[header_excel_row]:
                    base_style = header_styles[header_excel_row][1]
                    if base_style['font']:
                        cell.font = base_style['font']
                    if base_style['alignment']:
                        cell.alignment = base_style['alignment']
    
    output.seek(0)
    return output.getvalue()