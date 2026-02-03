"""
Lambda 2: LLM API Request Handler
Lambda1からのリクエストを受け、キーワード検索してLLM APIにリクエスト
"""

import os
import json
import logging
import re
from pathlib import Path

# LiteLLMのインポート
import litellm

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
LITELLM_API_BASE = os.getenv('LITELLM_API_BASE', 'https://askul-gpt.askul-it.com/v1')
LITELLM_MODEL = os.getenv('LITELLM_MODEL', 'gpt-5-mini')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-xxxxxx')

# LiteLLMの設定
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
litellm.num_retries = 2
litellm.request_timeout = 120


def lambda_handler(event, context):
    """
    Lambda2のメインハンドラー
    
    Expected event structure:
    {
        "row_index": 0,
        "product_message": "商品情報とチェック対象データ"
    }
    """
    try:
        logger.info(f"Lambda2 started. Event: {json.dumps(event, ensure_ascii=False)}")
        
        row_index = event.get('row_index', -1)
        product_message = event.get('product_message', '')
        
        if not product_message:
            raise ValueError("product_message is required in event")
        
        # Step 1: SKILLファイルを読み込み
        skill_content = load_skill_file()
        
        # Step 2: キーワード検索してreferenceファイルを特定
        keywords = extract_keywords_from_product(product_message)
        logger.info(f"Row {row_index}: Extracted keywords: {keywords}")
        
        # Step 3: 該当するreferenceファイルを読み込み
        reference_contents = load_reference_files(keywords)
        logger.info(f"Row {row_index}: Loaded {len(reference_contents)} reference files")
        
        # Step 4: LLM APIにリクエスト
        result_text = call_llm_api(product_message, skill_content, reference_contents)
        
        logger.info(f"Row {row_index}: Successfully processed")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'result_text': result_text
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Lambda2 failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }, ensure_ascii=False)
        }


def load_skill_file():
    """
    SKILLファイルを読み込み
    
    Returns:
        str: SKILLファイルの内容
    """
    skill_path = Path('/opt/skills/商品コピーチェック/SKILL.md')
    
    if not skill_path.exists():
        # Lambdaレイヤーにない場合はローカルパスを試す
        skill_path = Path('skills/商品コピーチェック/SKILL.md')
    
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content


def extract_keywords_from_product(product_message):
    """
    商品情報からキーワードを抽出
    
    Args:
        product_message: 商品情報テキスト
        
    Returns:
        list: 検出されたキーワードのリスト
    """
    # SKILLファイルに記載されているキーワードリスト
    # （実際にはSKILLファイルから動的に読み込むことも可能）
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
    """
    キーワードに対応するreferenceファイルを読み込み
    
    Args:
        keywords: キーワードリスト
        
    Returns:
        dict: {keyword: file_content} の辞書
    """
    reference_contents = {}
    
    for keyword in keywords:
        ref_path = Path(f'/opt/skills/商品コピーチェック/references/{keyword}.md')
        
        if not ref_path.exists():
            # Lambdaレイヤーにない場合はローカルパスを試す
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
    LLM APIを呼び出し
    
    Args:
        product_message: 商品情報
        skill_content: SKILLファイルの内容
        reference_contents: referenceファイルの内容辞書
        
    Returns:
        str: LLMからの応答テキスト
    """
    # システムプロンプトを構築
    system_message = f"""あなたは商品コピーチェックの専門家です。
以下のスキル定義に従って、商品情報をチェックしてください。

{skill_content}
"""
    
    # referenceファイルの内容を追加
    if reference_contents:
        system_message += "\n\n## 参照ファイル\n"
        for keyword, content in reference_contents.items():
            system_message += f"\n### {keyword}\n{content}\n"
    
    # LLM APIを呼び出し
    response = litellm.completion(
        model=LITELLM_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": product_message}
        ],
        api_base=LITELLM_API_BASE,
        max_tokens=4096,
        timeout=120
    )
    
    result_text = response.choices[0].message.content
    return result_text
