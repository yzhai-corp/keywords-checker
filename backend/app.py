"""
Flask Backend Server for Keywords Checker
Provides API endpoints for product copy checking with Excel support
"""

import os
import io
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import litellm
import pandas as pd
from skill_manager import SkillManager
from s3_manager import S3Manager
from redis_cache_manager import RedisCacheManager

# Load environment variables
load_dotenv()

# Configure logging
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

log_filename = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("Keywords Checker Backend Server Starting...")
logger.info(f"Log file: {log_filename}")
logger.info("=" * 60)

# Initialize Flask app
app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Serve frontend
@app.route('/')
def serve_frontend():
    """Serve the frontend index.html"""
    return app.send_static_file('index.html')

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure LiteLLM
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', 'sk-xxxxxx')
LITELLM_API_BASE = os.getenv('LITELLM_API_BASE', 'https://askul-gpt.askul-it.com/v1')
LITELLM_MODEL = os.getenv('LITELLM_MODEL', 'gpt-5-mini')

# LiteLLMのリトライ設定（エラー時のリトライ回数を制限）
litellm.num_retries = 2  # デフォルト3回から2回に減らす
litellm.request_timeout = 120  # タイムアウトを120秒に設定

# Initialize Skill Manager
SKILLS_DIR = Path(__file__).parent / "skills"
skill_manager = SkillManager(SKILLS_DIR)
skill_manager.load_all_skills()

# Initialize S3 Manager (optional, only if bucket names are set)
s3_manager = None
if os.getenv('EXCEL_BUCKET_NAME') or os.getenv('S3_BUCKET_NAME'):
    try:
        s3_manager = S3Manager()
        logger.info(f"S3 Manager initialized - Excel: {os.getenv('EXCEL_BUCKET_NAME')}, Skills: {os.getenv('SKILLS_BUCKET_NAME')}")
    except Exception as e:
        logger.warning(f"S3 Manager initialization failed: {e}")

# Initialize Redis Cache Manager
redis_cache = None
if os.getenv('REDIS_HOST'):
    try:
        redis_cache = RedisCacheManager(ttl=86400)  # 24 hour TTL for skills
        logger.info(f"Redis Cache Manager initialized: {os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT', 6379)}")
    except Exception as e:
        logger.warning(f"Redis Cache Manager initialization failed: {e}")


def get_skill_file_with_cache(file_key):
    """
    Get skill file from cache or S3
    
    Args:
        file_key: S3 key for skill file
        
    Returns:
        str: File content or None
    """
    # Try cache first
    if redis_cache:
        cached_content = redis_cache.get_skill_file(file_key)
        if cached_content:
            logger.debug(f"Skill file from cache: {file_key}")
            return cached_content
    
    # Load from S3
    if s3_manager and s3_manager.skills_bucket_name:
        try:
            content = s3_manager.get_skill_file(file_key)
            
            # Store in cache
            if redis_cache and content:
                redis_cache.set_skill_file(file_key, content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading skill file from S3: {e}")
            return None
    
    # Fallback to local file
    local_path = SKILLS_DIR / file_key
    if local_path.exists():
        logger.debug(f"Skill file from local: {file_key}")
        return local_path.read_text(encoding='utf-8')
    
    return None


def build_product_message(row):
    """
    Build a product message from Excel row data
    
    Args:
        row: Pandas Series containing product data
        
    Returns:
        Tuple: (product_message, has_check_data)
        - product_message: String containing formatted product information
        - has_check_data: Boolean indicating if there's data to check (other than product name)
    """
    # チェック対象列（商品名以外）
    check_columns = [
        '*変更前_商品の特徴BtoB',
        '*変更前_MDおすすめコメントBtoB',
        '*変更前_短いキャッチコピーBtoB',
        '*変更前_キャッチコピーBtoC',
        '*変更前_商品の特徴BtoC'
    ]
    
    message_parts = []
    has_check_data = False
    
    # 商品名を最初に追加
    if '*商品名' in row and pd.notna(row['*商品名']) and row['*商品名'] != '':
        message_parts.append(f"商品名: {row['*商品名']}")
    
    # チェック対象列を追加
    for column in check_columns:
        if column in row and pd.notna(row[column]) and row[column] != '':
            message_parts.append(f"{column}: {row[column]}")
            has_check_data = True
    
    return "\n".join(message_parts), has_check_data


def extract_conclusion(result_text):
    """
    Extract OK/NG conclusion from LLM result
    
    Args:
        result_text: Text result from LLM
        
    Returns:
        "OK" or "NG" or "UNKNOWN"
    """
    # Look for conclusion pattern in the result
    lines = result_text.split('\n')
    for line in lines:
        if '結論' in line:
            # Check the next few lines for OK or NG
            idx = lines.index(line)
            for i in range(idx, min(idx + 5, len(lines))):
                if 'NG' in lines[i]:
                    return "NG"
                elif 'OK' in lines[i]:
                    return "OK"
    
    # Fallback: search entire text
    if 'NG' in result_text:
        return "NG"
    elif 'OK' in result_text:
        return "OK"
    
    return "UNKNOWN"


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'skills_loaded': len(skill_manager.skills)
    })


@app.route('/api/skills', methods=['GET'])
def list_skills():
    """List all available skills"""
    return jsonify({
        'skills': skill_manager.list_skills()
    })


@app.route('/api/check', methods=['POST'])
def check_keywords():
    """
    Check a single product for keyword violations
    
    Request JSON:
        {
            "skill_name": "商品コピーチェック",
            "product_info": "商品名: テスト商品\n説明: ..."
        }
        
    Response JSON:
        {
            "result": "チェック結果...",
            "conclusion": "OK" or "NG",
            "usage": {...}
        }
    """
    try:
        data = request.json
        skill_name = data.get('skill_name', '商品コピーチェック')
        product_info = data.get('product_info', '')
        
        if not product_info:
            return jsonify({'error': 'product_info is required'}), 400
        
        # Build system prompt from skill
        system_prompt = skill_manager.build_system_prompt(skill_name)
        
        # Call LiteLLM API
        response = litellm.completion(
            model=LITELLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": product_info
                }
            ],
            api_base=LITELLM_API_BASE,
            max_tokens=4096,
            timeout=120  # 個別API呼び出しのタイムアウト: 120秒
        )
        
        result_text = response.choices[0].message.content
        conclusion = extract_conclusion(result_text)
        
        return jsonify({
            'result': result_text,
            'conclusion': conclusion,
            'usage': {
                'input_tokens': response.usage.prompt_tokens,
                'output_tokens': response.usage.completion_tokens
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-excel', methods=['POST'])
def check_excel():
    """
    Check multiple products from an Excel file
    
    Request:
        - file: Excel file (multipart/form-data)
        - skill_name: Skill name (optional, defaults to '商品コピーチェック')
        
    Response:
        Excel file with check results
    """
    try:
        # Check if file is provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        skill_name = request.form.get('skill_name', '商品コピーチェック')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = ['.xlsx', '.xls', '.xlsm']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'error': f'Unsupported file format: {file_ext}. Allowed formats: .xlsx, .xls, .xlsm'
            }), 400
        
        # Read Excel file - pandas will auto-detect the format
        try:
            # シート「チェック対象」を読み込み（全列を文字列として読み込み、元の型を保持）
            df = pd.read_excel(file, sheet_name='チェック対象', dtype=str)
        except ValueError as e:
            # シートが存在しない場合
            if 'Worksheet' in str(e) or 'チェック対象' in str(e):
                return jsonify({'error': 'シート「チェック対象」が見つかりません。Excelファイルに「チェック対象」という名前のシートが存在することを確認してください。'}), 400
            raise
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        if df.empty:
            return jsonify({'error': 'Excel file is empty'}), 400
        
        # 必須列のチェック
        required_columns = ['*商品名']
        check_columns = [
            '*変更前_商品の特徴BtoB',
            '*変更前_MDおすすめコメントBtoB',
            '*変更前_短いキャッチコピーBtoB',
            '*変更前_キャッチコピーBtoC',
            '*変更前_商品の特徴BtoC'
        ]
        
        # 商品名列の存在チェック
        if '*商品名' not in df.columns:
            return jsonify({'error': '「*商品名」列が見つかりません。シート「チェック対象」に「*商品名」列が必要です。'}), 400
        
        # Process each row
        results = []
        conclusions = []
        total_rows = len(df)
        
        logger.info(f"📊 Excel一括チェック開始: {total_rows}行 (ファイル: {file.filename})")
        
        for idx, row in df.iterrows():
            try:
                # Progress logging
                if (idx + 1) % 100 == 0 or idx == 0:
                    logger.info(f"進捗: {idx + 1}/{total_rows} 行処理中...")
                
                # Build product message from row
                product_message, has_check_data = build_product_message(row)
                
                # Skip empty rows
                if not product_message or product_message.strip() == '':
                    logger.warning(f"行 {idx + 1} はスキップ（空行）")
                    results.append("(空行)")
                    conclusions.append("SKIPPED")
                    continue
                
                # チェックデータが存在しない場合（商品名のみの場合）
                if not has_check_data:
                    logger.warning(f"行 {idx + 1} はチェックデータなし（商品名のみ）")
                    results.append("チェックデータが存在しません（商品名以外の列にデータがありません）")
                    conclusions.append("NO_DATA")
                    continue
                
                # 商品テキストからキーワードを検出
                detected_keywords = skill_manager.detect_keywords(skill_name, product_message)
                
                # 検出されたキーワード（references/*.mdファイル）をログ出力
                if detected_keywords:
                    logger.info(f"行 {idx + 1}: 検出されたキーワード数 = {len(detected_keywords)}")
                    logger.info(f"  → 使用するreferencesファイル: {', '.join(sorted(detected_keywords))}")
                else:
                    logger.info(f"行 {idx + 1}: キーワード検出なし（一般的なチェックのみ実施）")
                
                # 検出されたキーワードに基づいて動的にsystem_promptを構築
                system_prompt = skill_manager.build_dynamic_system_prompt(skill_name, detected_keywords)
                
                # Call LiteLLM API
                response = litellm.completion(
                    model=LITELLM_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": product_message
                        }
                    ],
                    api_base=LITELLM_API_BASE,
                    max_tokens=4096,
                    timeout=120  # 個別API呼び出しのタイムアウト: 120秒
                )
                
                result_text = response.choices[0].message.content
                conclusion = extract_conclusion(result_text)
                
                # Log if conclusion is UNKNOWN
                if conclusion == "UNKNOWN":
                    logger.warning(f"行 {idx + 1} で結論が不明 (UNKNOWN)")
                    logger.debug(f"商品情報: {product_message[:100]}...")
                    logger.debug(f"LLM応答の一部: {result_text[:200]}...")
                
                results.append(result_text)
                conclusions.append(conclusion)
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"行 {idx + 1} でエラー: {error_message}", exc_info=True)
                
                # リトライエラーの場合は特別に記録
                if 'retry' in error_message.lower() or 'timeout' in error_message.lower():
                    logger.warning(f"行 {idx + 1}: LLM APIリトライ/タイムアウトエラー。商品情報: {product_message[:100]}...")
                
                results.append(f"エラー: {error_message}")
                conclusions.append("ERROR")
        
        logger.info(f"✅ 処理完了: {total_rows}行")
        
        # Add results to dataframe (文字列型として明示的に設定)
        df['チェック結果'] = pd.Series(results, dtype=str)
        df['結論'] = pd.Series(conclusions, dtype=str)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='チェック結果')
        
        output.seek(0)
        
        # Send file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='check_result.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-excel-s3', methods=['POST'])
def check_excel_s3():
    """
    Check products from the latest Excel file in S3
    
    Request JSON (optional):
        {
            "skill_name": "商品コピーチェック",
            "file_key": "input/specific_file.xlsx"  # Optional: specify a file
        }
        
    Response JSON:
        {
            "status": "success",
            "input_file": "input/file.xlsx",
            "output_file": "output/file_checked_20260127_123456.xlsx",
            "rows_processed": 100,
            "download_url": "https://..."
        }
    """
    if not s3_manager:
        return jsonify({'error': 'S3 is not configured. Please set S3_BUCKET_NAME environment variable.'}), 503
    
    try:
        data = request.json or {}
        skill_name = data.get('skill_name', '商品コピーチェック')
        specified_file_key = data.get('file_key')
        
        # Get file from S3
        if specified_file_key:
            logger.info(f"Processing specified file: {specified_file_key}")
            file_obj = s3_manager.s3_client.get_object(
                Bucket=s3_manager.bucket_name,
                Key=specified_file_key
            )
            file_stream = file_obj['Body'].read()
            file_key = specified_file_key
        else:
            logger.info("Getting latest Excel file from S3...")
            file_key, file_stream = s3_manager.get_latest_excel_file()
            
            if not file_key:
                return jsonify({'error': 'No Excel files found in S3'}), 404
        
        logger.info(f"Processing file: {file_key}")
        
        # Process Excel file (same logic as check_excel endpoint)
        # Read Excel file
        try:
            df = pd.read_excel(io.BytesIO(file_stream), sheet_name='チェック対象', dtype=str)
        except ValueError as e:
            if 'Worksheet' in str(e) or 'チェック対象' in str(e):
                return jsonify({'error': 'シート「チェック対象」が見つかりません。'}), 400
            raise
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        if df.empty:
            return jsonify({'error': 'Excel file is empty'}), 400
        
        # Check required columns
        if '*商品名' not in df.columns:
            return jsonify({'error': '「*商品名」列が見つかりません。'}), 400
        
        # Process each row (same as check_excel)
        from app import build_product_message, extract_conclusion
        
        results = []
        conclusions = []
        total_rows = len(df)
        
        logger.info(f"📊 S3 Excel一括チェック開始: {total_rows}行 (ファイル: {file_key})")
        
        for idx, row in df.iterrows():
            try:
                if (idx + 1) % 100 == 0 or idx == 0:
                    logger.info(f"進捗: {idx + 1}/{total_rows} 行処理中...")
                
                product_message, has_check_data = build_product_message(row)
                
                if not product_message or product_message.strip() == '':
                    logger.warning(f"行 {idx + 1} はスキップ（空行）")
                    results.append("(空行)")
                    conclusions.append("SKIPPED")
                    continue
                
                if not has_check_data:
                    logger.warning(f"行 {idx + 1} はチェックデータなし（商品名のみ）")
                    results.append("チェックデータが存在しません（商品名以外の列にデータがありません）")
                    conclusions.append("NO_DATA")
                    continue
                
                detected_keywords = skill_manager.detect_keywords(skill_name, product_message)
                
                if detected_keywords:
                    logger.info(f"行 {idx + 1}: 検出されたキーワード数 = {len(detected_keywords)}")
                    logger.info(f"  → 使用するreferencesファイル: {', '.join(sorted(detected_keywords))}")
                else:
                    logger.info(f"行 {idx + 1}: キーワード検出なし（一般的なチェックのみ実施）")
                
                system_prompt = skill_manager.build_dynamic_system_prompt(skill_name, detected_keywords)
                
                response = litellm.completion(
                    model=LITELLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": product_message}
                    ],
                    api_base=LITELLM_API_BASE,
                    max_tokens=4096,
                    timeout=120
                )
                
                result_text = response.choices[0].message.content
                conclusion = extract_conclusion(result_text)
                
                if conclusion == "UNKNOWN":
                    logger.warning(f"行 {idx + 1} で結論が不明 (UNKNOWN)")
                
                results.append(result_text)
                conclusions.append(conclusion)
                
            except Exception as e:
                error_message = str(e)
                logger.error(f"行 {idx + 1} でエラー: {error_message}", exc_info=True)
                results.append(f"エラー: {error_message}")
                conclusions.append("ERROR")
        
        logger.info(f"✅ 処理完了: {total_rows}行")
        
        # Add results to dataframe
        df['チェック結果'] = pd.Series(results, dtype=str)
        df['結論'] = pd.Series(conclusions, dtype=str)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='チェック結果')
        
        output.seek(0)
        file_content = output.getvalue()
        
        # Upload result to S3
        output_key = s3_manager.upload_result_file(file_content, os.path.basename(file_key))
        
        # Generate presigned URL for download
        download_url = s3_manager.get_file_url(output_key, expiration=3600)
        
        return jsonify({
            'status': 'success',
            'input_file': file_key,
            'output_file': output_key,
            'rows_processed': total_rows,
            'download_url': download_url,
            'bucket': s3_manager.bucket_name
        })
        
    except Exception as e:
        logger.error(f"S3処理エラー: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/s3/files', methods=['GET'])
def list_s3_files():
    """
    List all Excel files in S3 input directory
    
    Response JSON:
        {
            "files": [
                {
                    "key": "input/file.xlsx",
                    "filename": "file.xlsx",
                    "size": 12345,
                    "last_modified": "2026-01-27T12:34:56"
                }
            ]
        }
    """
    if not s3_manager:
        return jsonify({'error': 'S3 is not configured'}), 503
    
    try:
        files = s3_manager.list_input_files()
        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"S3ファイルリスト取得エラー: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Log loaded skills
    logger.info("Loaded skills:")
    for skill in skill_manager.list_skills():
        logger.info(f"  - {skill['name']}: {skill['description']}")
    
    # Run server
    logger.info("Starting Flask server on http://0.0.0.0:5001")
    
    # デバッグモード（環境変数で制御、本番環境ではFalseにする）
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # use_reloader=Falseにするとファイル変更時の自動再起動を無効化
    app.run(host='0.0.0.0', port=5001, debug=debug_mode, use_reloader=False)
