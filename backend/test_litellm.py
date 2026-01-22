#!/usr/bin/env python3
"""
Simple test script for LiteLLM API integration
Tests the basic API connectivity before running the full app
"""

import os
import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure LiteLLM
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', 'sk-xxxxxx')
LITELLM_API_BASE = os.getenv('LITELLM_API_BASE', 'https://askul-gpt.askul-it.com/v1')
LITELLM_MODEL = os.getenv('LITELLM_MODEL', 'gpt-5-mini')

print("=" * 60)
print("LiteLLM API Connection Test")
print("=" * 60)
print(f"API Base: {LITELLM_API_BASE}")
print(f"Model: {LITELLM_MODEL}")
print(f"API Key: {os.environ['OPENAI_API_KEY'][:20]}...")
print("=" * 60)

try:
    print("\nSending test request...")
    
    response = litellm.completion(
        model=LITELLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "あなたは商品コピーチェッカーです。"
            },
            {
                "role": "user",
                "content": "こんにちは。テストメッセージです。"
            }
        ],
        api_base=LITELLM_API_BASE,
        max_tokens=100
    )
    
    print("\n✅ API Connection Successful!")
    print("=" * 60)
    print("Response:")
    print("-" * 60)
    print(response.choices[0].message.content)
    print("-" * 60)
    print(f"\nUsage:")
    print(f"  Input tokens: {response.usage.prompt_tokens}")
    print(f"  Output tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")
    print("=" * 60)
    print("\n✨ Test completed successfully!")
    
except Exception as e:
    print("\n❌ API Connection Failed!")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("=" * 60)
    print("\nPlease check:")
    print("  1. API Key is correct in .env file")
    print("  2. API Base URL is correct")
    print("  3. Network connectivity")
    print("  4. Model name is correct")

if __name__ == "__main__":
    pass
