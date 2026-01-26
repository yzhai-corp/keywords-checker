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
app = Flask(__name__)
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

# Initialize Skill Manager
SKILLS_DIR = Path(__file__).parent / "skills"
skill_manager = SkillManager(SKILLS_DIR)
skill_manager.load_all_skills()


def build_product_message(row):
    """
    Build a product message from Excel row data
    
    Args:
        row: Pandas Series containing product data
        
    Returns:
        String containing formatted product information
    """
    message_parts = []
    
    for column, value in row.items():
        if pd.notna(value) and value != '':
            message_parts.append(f"{column}: {value}")
    
    return "\n".join(message_parts)


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
            df = pd.read_excel(file)
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        if df.empty:
            return jsonify({'error': 'Excel file is empty'}), 400
        
        # Build system prompt once
        system_prompt = skill_manager.build_system_prompt(skill_name)
        
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
                product_message = build_product_message(row)
                
                # Skip empty rows
                if not product_message or product_message.strip() == '':
                    logger.warning(f"行 {idx + 1} はスキップ（空行）")
                    results.append("(空行)")
                    conclusions.append("SKIPPED")
                    continue
                
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
                logger.error(f"行 {idx + 1} でエラー: {str(e)}", exc_info=True)
                results.append(f"エラー: {str(e)}")
                conclusions.append("ERROR")
        
        logger.info(f"✅ 処理完了: {total_rows}行")
        
        # Add results to dataframe
        df['チェック結果'] = results
        df['結論'] = conclusions
        
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


if __name__ == '__main__':
    # Log loaded skills
    logger.info("Loaded skills:")
    for skill in skill_manager.list_skills():
        logger.info(f"  - {skill['name']}: {skill['description']}")
    
    # Run server
    logger.info("Starting Flask server on http://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
