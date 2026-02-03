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

# LiteLLMのリトライ設定（エラー時のリトライ回数を制限）
litellm.num_retries = 2  # デフォルト3回から2回に減らす
litellm.request_timeout = 120  # タイムアウトを120秒に設定

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
        Tuple: (product_message, has_check_data)
        - product_message: String containing formatted product information
        - has_check_data: Boolean indicating if there's data to check (other than product info)
    """
    # 商品情報項目
    product_info_columns = [
        '*商品名',
        '*管理カテゴリー大大',
        '*管理カテゴリー大',
        '*管理カテゴリー中',
        '*管理カテゴリー小',
        '*許認可大大分類',
        '*許認可大分類'
    ]
    
    # チェック対象列（8項目）
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


def parse_item_results(result_text):
    """
    Parse LLM result to extract individual item results
    
    Args:
        result_text: Text result from LLM containing all 8 items
        
    Returns:
        Dictionary mapping column names to (conclusion, detail_text) tuples
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
    
    # Try to parse as JSON first
    try:
        import json
        # LLMがJSON形式で返した場合
        json_result = json.loads(result_text)
        for col in check_columns:
            if col in json_result:
                item_data = json_result[col]
                conclusion = item_data.get('結論', 'UNKNOWN')
                detail = json.dumps(item_data, ensure_ascii=False, indent=2)
                results[col] = (conclusion, detail)
            else:
                results[col] = ('', '')
        return results
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Fallback: テキストベースのパース
    # 各項目を「##」などのマーカーで分割
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
    """
    Extract conclusion from a single item's result text
    
    Args:
        item_text: Result text for a single item
        
    Returns:
        "OK" or "NG" or "対象キーワード存在しない" or ""
    """
    if not item_text or item_text.strip() == '':
        return ''
    
    # 結論パターンを探す
    if 'NG' in item_text:
        return 'NG'
    elif 'OK' in item_text:
        return 'OK'
    elif '対象キーワード存在しない' in item_text:
        return '対象キーワード存在しない'
    
    return ''


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
        # ヘッダー行を自動検出（最大5行まで試す）
        df = None
        header_row = None
        original_workbook = None
        original_worksheet = None
        
        try:
            # 元のワークブックを開いてスタイル情報を保存
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Border, Alignment
            
            file.seek(0)
            original_workbook = openpyxl.load_workbook(file)
            original_worksheet = original_workbook['NGコピーリスト　要注意表現チェックリスト']
            
            # ヘッダー行のスタイル情報を保存（最大10行まで）
            header_styles = {}
            for row_idx in range(1, 11):  # 1-10行目
                header_styles[row_idx] = {}
                for col_idx in range(1, original_worksheet.max_column + 1):
                    cell = original_worksheet.cell(row=row_idx, column=col_idx)
                    header_styles[row_idx][col_idx] = {
                        'font': cell.font.copy() if cell.font else None,
                        'fill': cell.fill.copy() if cell.fill else None,
                        'border': cell.border.copy() if cell.border else None,
                        'alignment': cell.alignment.copy() if cell.alignment else None,
                    }
            
            file.seek(0)
            
            for header_idx in range(6):  # 0～5行目を試す
                try:
                    temp_df = pd.read_excel(file, sheet_name='NGコピーリスト　要注意表現チェックリスト', header=header_idx, dtype=str)
                    
                    # ファイルポインタをリセット（次の読み込みのため）
                    file.seek(0)
                    
                    # 列名を正規化
                    temp_df.columns = temp_df.columns.str.strip()
                    
                    # *商品名列が存在するかチェック
                    if '*商品名' in temp_df.columns:
                        df = temp_df
                        header_row = header_idx
                        logger.info(f"✅ ヘッダー行を検出: {header_idx}行目（0-indexed）")
                        logger.info(f"読み込まれた列名: {list(df.columns[:15])}")  # 最初の15列を表示
                        break
                except Exception as e:
                    file.seek(0)
                    continue
            
            if df is None:
                # ヘッダー行が見つからなかった場合、デフォルト（0行目）で読み込んでエラー表示
                df = pd.read_excel(file, sheet_name='NGコピーリスト　要注意表現チェックリスト', dtype=str)
                df.columns = df.columns.str.strip()
                
                available_cols = ', '.join([f'"{col}"' for col in df.columns[:10]])
                return jsonify({
                    'error': f'「*商品名」列が見つかりません。\n'
                             f'0～5行目のヘッダーを確認しましたが、「*商品名」列が見つかりませんでした。\n'
                             f'検出された列（1行目）: {available_cols}...\n\n'
                             f'Excelファイルの構造を確認してください：\n'
                             f'1. シート名が「NGコピーリスト　要注意表現チェックリスト」であること\n'
                             f'2. ヘッダー行に「*商品名」列が含まれていること'
                }), 400
                
        except ValueError as e:
            # シートが存在しない場合
            if 'Worksheet' in str(e) or 'NGコピーリスト' in str(e):
                return jsonify({'error': 'シート「NGコピーリスト　要注意表現チェックリスト」が見つかりません。Excelファイルに「NGコピーリスト　要注意表現チェックリスト」という名前のシートが存在することを確認してください。'}), 400
            raise
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        if df.empty:
            return jsonify({'error': 'Excel file is empty'}), 400
        
        # 必須列のチェック（既にヘッダー検出時にチェック済みだが念のため）
        required_columns = ['*商品名']
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
                
                # キーワード検出用：チェック対象8項目のテキストのみを抽出
                check_text_parts = []
                for column in check_columns:
                    if column in row and pd.notna(row[column]) and row[column] != '':
                        check_text_parts.append(row[column])
                
                check_text_for_keywords = '\n'.join(check_text_parts)
                
                # チェック対象テキストからキーワードを検出
                detected_keywords = skill_manager.detect_keywords(skill_name, check_text_for_keywords)
                
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
        
        # チェック対象8項目のリスト
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
            
            # openpyxlのスタイル設定をインポート
            from openpyxl.styles import PatternFill
            
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
            
            # オレンジ色の背景色を定義（チェック結果列用）
            orange_fill = PatternFill(start_color='FFA500', end_color='FFA500', fill_type='solid')
            
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
    
    # デバッグモード（環境変数で制御、本番環境ではFalseにする）
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # use_reloader=Falseにするとファイル変更時の自動再起動を無効化
    app.run(host='0.0.0.0', port=5001, debug=debug_mode, use_reloader=False)
