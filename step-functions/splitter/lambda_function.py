"""
Lambda Splitter: Excel分割処理
S3からExcelファイルを読み取り、行データの配列に変換してStep Functionsに渡す
"""

import os
import io
import json
import logging
import boto3
import pandas as pd
from datetime import datetime
from urllib.parse import unquote_plus
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
s3_client = boto3.client('s3')

# Environment variables
RESULTS_BUCKET = os.getenv('RESULTS_BUCKET', 'askul-sandbox-01-regulation-test-bucket')


def lambda_handler(event, context):
    """
    Lambda Splitterのメインハンドラー
    
    EventBridge経由のS3イベント構造（推奨）:
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
        "bucket": "bucket-name",
        "input_key": "input/file.xlsx"
    }
    
    Returns:
    {
        "execution_id": "20260204-143025-abc123",
        "input_bucket": "bucket-name",
        "input_key": "input/file.xlsx",
        "output_bucket": "bucket-name",
        "output_key": "output/file_checked.xlsx",
        "total_rows": 130,
        "rows": [
            {
                "row_index": 0,
                "変更後_キャッチコピーBtoC": "値",
                ...
            },
            ...
        ]
    }
    """
    try:
        logger.info(f"Lambda Splitter started. Event: {json.dumps(event)}")
        
        # S3イベント形式の場合（EventBridge経由またはS3直接トリガー）
        if 'Records' in event and len(event['Records']) > 0 and event['Records'][0].get('eventSource') == 'aws:s3':
            logger.info("Triggered by S3 event (EventBridge or S3 direct trigger)")
            
            # S3イベントからファイル名を取得
            s3_event = event['Records'][0]['s3']
            bucket = s3_event['bucket']['name']
            input_key = s3_event['object']['key']
            
            # URLデコード（S3キーに日本語や特殊文字が含まれる場合）
            input_key = unquote_plus(input_key)
            
            logger.info(f"S3 object: s3://{bucket}/{input_key}")
            
            # input/直下のファイルかチェック
            if not input_key.startswith('input/'):
                logger.warning(f"File {input_key} is not in input/ directory. Skipping.")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'File not in input/ directory, skipped'})
                }
        
        # テストイベントの場合
        else:
            logger.info("Triggered by test event")
            bucket = event.get('bucket', RESULTS_BUCKET)
            input_key = event.get('input_key')
            
            if not input_key:
                raise ValueError("input_key is required in event")
        
        # execution_idを生成
        execution_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
        logger.info(f"Execution ID: {execution_id}")
        
        # ファイル名を取得
        filename = input_key.split('/')[-1]
        base_filename = filename.rsplit('.', 1)[0]  # 拡張子を除去
        
        # 出力ファイル名を生成（必ず.xlsx）
        output_key = f"output/result_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{base_filename}.xlsx"
        
        # S3からExcelファイルをダウンロード
        logger.info(f"Downloading {input_key} from S3")
        excel_bytes = download_from_s3(bucket, input_key)
        
        # Excelファイルを解析して行データの配列に変換
        rows_data = parse_excel_to_rows(excel_bytes)
        total_rows = len(rows_data)
        
        logger.info(f"Parsed Excel: {total_rows} rows")
        
        # 各行データをS3に保存し、S3キーのリストを作成
        logger.info(f"Saving {total_rows} rows to S3...")
        s3_keys = save_rows_to_s3(bucket, execution_id, rows_data)
        
        logger.info(f"Saved {len(s3_keys)} rows to S3")
        
        # Step Functionsに渡すデータを構築（S3キーのリストのみ）
        result = {
            'execution_id': execution_id,
            'input_bucket': bucket,
            'input_key': input_key,
            'output_bucket': bucket,
            'output_key': output_key,
            'total_rows': total_rows,
            's3_row_keys': s3_keys  # S3キーのリスト（各要素は{"row_index": 0, "s3_key": "..."} の形式）
        }
        
        logger.info(f"Splitter completed: {total_rows} rows prepared for processing")
        
        return result
        
    except Exception as e:
        logger.error(f"Splitter failed: {str(e)}", exc_info=True)
        raise


def download_from_s3(bucket, key):
    """
    S3からファイルをダウンロード
    
    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
        
    Returns:
        bytes: ファイルの内容
    """
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    except Exception as e:
        logger.error(f"Failed to download s3://{bucket}/{key}: {str(e)}")
        raise


def parse_excel_to_rows(excel_bytes):
    """
    Excelファイルを解析して行データの配列に変換
    
    Args:
        excel_bytes: Excelファイルのバイトデータ
        
    Returns:
        list: 行データの配列
        [
            {
                "row_index": 0,
                "変更後_キャッチコピーBtoC": "値",
                "変更後_キャッチコピーBtoB": "値",
                ...
            },
            ...
        ]
    """
    try:
        # pandasでExcelを読み込み
        df = pd.read_excel(io.BytesIO(excel_bytes), engine='openpyxl')
        
        # チェック対象の列名（8列）
        check_columns = [
            '変更後_キャッチコピーBtoC',
            '変更後_キャッチコピーBtoB',
            '変更後_仕様スペック',
            '変更後_商品説明文',
            '変更後_商品名',
            '変更後_検索用キーワード',
            '変更後_使用上の注意',
            '変更後_アスクルおススメポイント'
        ]
        
        # 行データの配列を構築
        rows_data = []
        
        for idx, row in df.iterrows():
            row_data = {
                'row_index': int(idx)
            }
            
            # 各列のデータを追加
            for col in check_columns:
                if col in df.columns:
                    value = row[col]
                    # NaN値を空文字列に変換
                    if pd.isna(value):
                        value = ''
                    else:
                        value = str(value).strip()
                    row_data[col] = value
                else:
                    row_data[col] = ''
            
            rows_data.append(row_data)
        
        return rows_data
        
    except Exception as e:
        logger.error(f"Failed to parse Excel: {str(e)}")
        raise


def save_rows_to_s3(bucket, execution_id, rows_data):
    """
    各行データをS3に個別に保存し、S3キーのリストを返す
    
    Args:
        bucket: S3バケット名
        execution_id: 実行ID
        rows_data: 行データの配列
        
    Returns:
        list: S3キーの配列
        [
            {"row_index": 0, "s3_key": "results/execution_id/rows/row_0.json"},
            {"row_index": 1, "s3_key": "results/execution_id/rows/row_1.json"},
            ...
        ]
    """
    try:
        s3_keys = []
        
        for row_data in rows_data:
            row_index = row_data['row_index']
            s3_key = f"results/{execution_id}/rows/row_{row_index}.json"
            
            # 行データをJSONとしてS3に保存
            s3_client.put_object(
                Bucket=bucket,
                Key=s3_key,
                Body=json.dumps(row_data, ensure_ascii=False),
                ContentType='application/json'
            )
            
            s3_keys.append({
                'row_index': row_index,
                's3_key': s3_key,
                'bucket': bucket
            })
        
        return s3_keys
        
    except Exception as e:
        logger.error(f"Failed to save rows to S3: {str(e)}")
        raise

