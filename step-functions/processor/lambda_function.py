"""
Lambda Processor: 1行処理とLLM API呼び出し（スタブモード）
Step Functions Map Stateから呼び出され、1行分のデータを処理してS3に保存
"""

import os
import json
import logging
import boto3
from pathlib import Path

# LiteLLMのインポート
import litellm

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
s3_client = boto3.client('s3')

# Environment variables
RESULTS_BUCKET = os.getenv('RESULTS_BUCKET', 'askul-sandbox-01-regulation-test-bucket')
LITELLM_API_BASE = os.getenv('LITELLM_API_BASE', 'https://askul-gpt.askul-it.com/v1')
LITELLM_MODEL = os.getenv('LITELLM_MODEL', 'gpt-5-mini')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-xxxxxx')
LITELLM_MODE = os.getenv('LITELLM_MODE', 'stub')  # 'stub' or 'production'

# LiteLLMの設定
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
litellm.num_retries = 2
litellm.request_timeout = 120


def lambda_handler(event, context):
    """
    Lambda Processorのメインハンドラー
    
    Expected event structure from Step Functions Map State:
    {
        "execution_id": "20260204-143025-abc123",
        "row_index": 0,
        "row_data": {
            "変更後_キャッチコピーBtoC": "値",
            "変更後_キャッチコピーBtoB": "値",
            ...
        }
    }
    
    Returns:
    {
        "row_index": 0,
        "status": "success",
        "s3_key": "results/20260204-143025-abc123/0.json"
    }
    """
    try:
        logger.info(f"Lambda Processor started. Row: {event.get('row_index', -1)}")
        
        execution_id = event.get('execution_id')
        row_index = event.get('row_index')
        row_data = event.get('row_data', {})
        
        if execution_id is None or row_index is None:
            raise ValueError("execution_id and row_index are required")
        
        # 商品情報メッセージを構築
        product_message = build_product_message(row_data)
        
        # Step 1: SKILLファイルを読み込み
        skill_content = load_skill_file()
        
        # Step 2: キーワード検索してreferenceファイルを特定
        keywords = extract_keywords_from_product(product_message)
        logger.info(f"Row {row_index}: Extracted keywords: {keywords}")
        
        # Step 3: 該当するreferenceファイルを読み込み
        reference_contents = load_reference_files(keywords)
        logger.info(f"Row {row_index}: Loaded {len(reference_contents)} reference files")
        
        # Step 4: LLM APIにリクエスト（スタブモード）
        result_text = call_llm_api(product_message, skill_content, reference_contents)
        
        # Step 5: 結果を解析して各列の結果に分割
        column_results = parse_result_text(result_text)
        
        # Step 6: 結果をS3に保存
        s3_key = f"results/{execution_id}/{row_index}.json"
        save_result_to_s3(s3_key, row_index, column_results)
        
        logger.info(f"Row {row_index}: Successfully processed and saved to {s3_key}")
        
        return {
            'row_index': row_index,
            'status': 'success',
            's3_key': s3_key
        }
        
    except Exception as e:
        logger.error(f"Processor failed: {str(e)}", exc_info=True)
        
        # エラーの場合もS3に保存（エラーメッセージ）
        try:
            execution_id = event.get('execution_id', 'unknown')
            row_index = event.get('row_index', -1)
            s3_key = f"results/{execution_id}/{row_index}.json"
            
            error_result = {
                'row_index': row_index,
                'error': str(e)
            }
            
            # 全列にエラーメッセージを設定
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
            
            for col in check_columns:
                error_result[f"{col}_チェック結果"] = f"エラー: {str(e)}"
            
            save_result_to_s3(s3_key, row_index, error_result)
            
        except Exception as save_error:
            logger.error(f"Failed to save error to S3: {str(save_error)}")
        
        return {
            'row_index': row_index,
            'status': 'error',
            's3_key': s3_key,
            'error': str(e)
        }


def build_product_message(row_data):
    """
    行データから商品情報メッセージを構築
    
    Args:
        row_data: 行データの辞書
        
    Returns:
        str: 商品情報メッセージ
    """
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
    
    message_parts = []
    for col in check_columns:
        value = row_data.get(col, '').strip()
        if value:
            message_parts.append(f"{col}: {value}")
    
    return "\n".join(message_parts)


def load_skill_file():
    """SKILLファイルを読み込み"""
    skill_path = Path('/opt/python/skills/商品コピーチェック/SKILL.md')
    
    if not skill_path.exists():
        skill_path = Path('skills/商品コピーチェック/SKILL.md')
    
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


def extract_keywords_from_product(product_message):
    """商品情報からキーワードを抽出"""
    keyword_list = [
        'MRSA', 'おなか', 'お腹', 'お通じ', 'くびれ', 'そばかす', 'たるみ', 'だるさ',
        'はきけ', 'むくみ', 'めまい', 'もの忘れ', 'やせる', 'よみがえ', 'わかがえ',
        'アトピー', 'アルツハイマー', 'アレルギー作用', 'アレルギー対策', 'アレルギー症状',
        'アレルゲン', 'アンチエイジング', 'インフルエンザ', 'ウィルス', 'ウイルス',
        'ウエスト', 'エイジングケア', 'カゼ', 'ガンが', 'ケミカルピーリング',
        'コレステロール', 'コロナ', 'ゴキブリ', 'シミ', 'シワ', 'ストレス',
        'タルミ', 'ダイエット', 'デトックス', 'ノロウィルス', 'ノロウイルス',
        'ハエ', 'バストアップ', 'バリア', 'ピロリ菌', 'フリーラジカル', 'ブドウ球菌',
        'ヘルニア', 'ベストプライス', 'ホルモン', 'ホワイトニング', 'ボトックス',
        'メタボ', 'リウマチ', '下痢', '不妊症', '不活化', '不活性化', '不眠',
        '乾燥肌', '予防', '二日酔い', '代謝', '体内浄化', '体力', '体質改善',
        '体重', '体験', '作用', '便秘', '便通', '促進', '信頼', '免疫', '冷え',
        '分泌', '判断力', '動悸', '動脈硬化', '医師', '医療', '医者', '口臭',
        '吐き気', '吹き出もの', '吹き出物', '喘息', '回復', '増強', '増毛',
        '夏ばて', '夏バテ', '大腸菌', '学力', '安全', '安心', '宿便', '対策',
        '底値', '強壮', '心臓', '快便', '患者', '悩み', '感想', '感染', '成長促進',
        '手足', '抑制', '抗がん', '抗アレルギー', '抗ガン', '抗体', '抗糖化',
        '抗老化', '抵抗力', '捻挫', '排尿', '推奨', '推薦', '早割', '更年期',
        '最終価格', '有効成分', '服用', '機能が', '機能の', '機能を', '機能性が',
        '機能性の', '機能性を', '歯周', '歯槽膿漏', '殺菌', '毒素', '治る',
        '治療', '治癒力', '活性化', '活性酸素', '消化不良', '消毒', '漢方',
        '熱中症', '燃焼', '物忘', '生活習慣病', '甲状腺', '疲労', '疲労回復',
        '病', '症', '痛', '痩', '癌', '発毛', '発汗', '白髪予防', '皮膚', '眼',
        '神経', '科医', '立ちくらみ', '筋肉', '精力', '糖尿', '細胞', '美容師',
        '美白', '美肌', '老化', '老廃物', '肉体改造', '肝斑', '肝機能', '肝炎',
        '肝細胞', '肝臓', '肝障害', '育毛', '肺炎', '胃もたれ', '胃腸', '胸やけ',
        '脂肪', '脂肪減少', '脂肪燃焼', '脳', '脳出血', '脳卒中', '脳梗塞',
        '腎臓', '腎障害', '腫瘍', '腱鞘炎', '腸', '膿', '花粉', '若返', '薬',
        '薬剤師', '虫歯', '蚊', '血圧', '血液', '血糖値', '血行', '視力', '解毒',
        '記憶力', '豊胸', '貧血', '関節', '集中力', '難聴', '風邪', '食べるだけ',
        '食中毒', '食事制限', '食欲不振', '食欲増進', '食欲減退', '飲むだけ',
        '養毛', '骨粗', '高血圧', 'Ｏ-157', 'Ｏ157'
    ]
    
    found_keywords = []
    for keyword in keyword_list:
        if keyword in product_message:
            found_keywords.append(keyword)
    
    return found_keywords


def load_reference_files(keywords):
    """キーワードに対応するreferenceファイルを読み込み"""
    reference_contents = {}
    
    for keyword in keywords:
        ref_path = Path(f'/opt/python/skills/商品コピーチェック/references/{keyword}.md')
        
        if not ref_path.exists():
            ref_path = Path(f'skills/商品コピーチェック/references/{keyword}.md')
        
        if ref_path.exists():
            try:
                with open(ref_path, 'r', encoding='utf-8') as f:
                    reference_contents[keyword] = f.read()
            except Exception as e:
                logger.warning(f"Failed to load reference file {keyword}.md: {str(e)}")
        else:
            logger.warning(f"Reference file not found: {keyword}.md")
    
    return reference_contents


def call_llm_api(product_message, skill_content, reference_contents):
    """
    LLM APIを呼び出し（スタブモード）
    
    Returns:
        str: LLMからの応答テキスト（各列ごとの結果をまとめた形式）
    """
    if LITELLM_MODE == 'stub':
        logger.info("=== STUB MODE: LLM API call is mocked ===")
        return generate_stub_response(reference_contents)
    else:
        # Production mode (VPC設定後に有効化)
        return call_llm_api_production(product_message, skill_content, reference_contents)


def generate_stub_response(reference_contents):
    """スタブレスポンスを生成"""
    detected_keywords = list(reference_contents.keys())
    
    # チェック対象列のリスト（SKILL.md 指定の8列）
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
    
    stub_response = ""
    
    for col in check_columns:
        stub_response += f"## {col}\n\n"
        
        if detected_keywords:
            keywords_str = ", ".join(detected_keywords[:3])
            if len(detected_keywords) > 3:
                keywords_str += f" 他{len(detected_keywords) - 3}件"
            
            stub_response += f"**結論**: NG\n\n"
            stub_response += f"検出されたキーワード: {keywords_str}\n\n"
            stub_response += f"（スタブ応答）対象箇所の確認が必要です。\n\n"
        else:
            stub_response += f"**結論**: OK\n\n"
            stub_response += f"（スタブ応答）問題なし\n\n"
    
    return stub_response


def call_llm_api_production(product_message, skill_content, reference_contents):
    """本番環境用のLLM API呼び出し（VPC設定後に使用）"""
    # 実装は既存のlambda2と同じロジック
    raise NotImplementedError("Production mode is not yet implemented. Use stub mode.")


def parse_result_text(result_text):
    """
    LLMの応答テキストを解析して各列の結果に分割
    
    Returns:
        dict: {column_name: result_text} の辞書
    """
    import re
    
    column_results = {}
    
    # 各セクションを抽出（## セクション名）
    sections = re.split(r'##\s+', result_text)
    
    for section in sections:
        if not section.strip():
            continue
        
        lines = section.strip().split('\n', 1)
        if len(lines) < 2:
            continue
        
        column_name = lines[0].strip()
        content = lines[1].strip()
        
        # チェック結果列名を生成
        result_column_name = f"{column_name}_チェック結果"
        column_results[result_column_name] = content
    
    return column_results


def save_result_to_s3(s3_key, row_index, column_results):
    """
    結果をS3に保存
    
    Args:
        s3_key: S3オブジェクトキー (results/{execution_id}/{row_index}.json)
        row_index: 行インデックス
        column_results: 列ごとの結果辞書
    """
    result_data = {
        'row_index': row_index,
        **column_results
    }
    
    s3_client.put_object(
        Bucket=RESULTS_BUCKET,
        Key=s3_key,
        Body=json.dumps(result_data, ensure_ascii=False, indent=2),
        ContentType='application/json'
    )
    
    logger.info(f"Saved result to s3://{RESULTS_BUCKET}/{s3_key}")
