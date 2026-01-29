import json
import os
import urllib.request
import boto3

# Lambda function triggered by S3 EventBridge or manual invocation
def lambda_handler(event, context):
    """
    AWS Lambda handler for processing Excel files from S3
    
    Trigger sources:
    1. S3 Event (via EventBridge) - auto-triggered when new file is uploaded
    2. Manual invocation - process latest file on demand
    """
    
    # API endpoint (replace with your actual ALB or API Gateway URL)
    API_ENDPOINT = os.environ.get('API_ENDPOINT', 'http://your-alb-url.amazonaws.com')
    
    # Determine file to process
    file_key = None
    
    # Check if triggered by S3 event
    if 'Records' in event and len(event['Records']) > 0:
        # S3 event from EventBridge
        record = event['Records'][0]
        if 's3' in record:
            file_key = record['s3']['object']['key']
            bucket = record['s3']['bucket']['name']
            print(f"S3 Event detected: File {file_key} uploaded to bucket {bucket}")
    
    # Prepare API request
    api_url = f"{API_ENDPOINT}/api/check-excel-s3"
    
    payload = {
        'skill_name': '商品コピーチェック'
    }
    
    # If specific file from S3 event, include it
    if file_key:
        payload['file_key'] = file_key
    
    # Call the API
    try:
        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"Processing completed successfully")
            print(f"Input file: {result.get('input_file')}")
            print(f"Output file: {result.get('output_file')}")
            print(f"Rows processed: {result.get('rows_processed')}")
            
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
            
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
