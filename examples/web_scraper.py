"""
Dify Code Node - Web Scraping
Input: url (String)
Output: body_text (String)
"""

import urllib.request
import urllib.error
from html.parser import HTMLParser
from urllib.parse import urlparse
import ssl
import certifi

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']:
            self.skip = True
            
    def handle_endtag(self, tag):
        if tag in ['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']:
            self.skip = False
            
    def handle_data(self, data):
        if not self.skip:
            stripped = data.strip()
            if stripped:
                self.text.append(stripped)
    
    def get_text(self):
        return '\n'.join(self.text)

def scrape_web(url):
    if not url or not isinstance(url, str):
        return {"body_text": "Error: Invalid URL provided"}
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return {"body_text": "Error: Invalid URL format"}
    except Exception:
        return {"body_text": "Error: URL parsing failed"}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)

        # certifiのCAバンドルを使用（推奨）
        context = ssl.create_default_context(cafile=certifi.where())
        
        with urllib.request.urlopen(req, timeout=15, context=context) as response:
            charset = response.headers.get_content_charset()
            if not charset:
                charset = 'utf-8'
            html_content = response.read().decode(charset, errors='ignore')
        
        parser = TextExtractor()
        parser.feed(html_content)
        clean_text = parser.get_text()
        
        if not clean_text:
            return {"body_text": "Warning: No text content found"}
        
        return {"body_text": clean_text}
    
    except urllib.error.URLError as e:
        if hasattr(e, 'code'):
            return {"body_text": f"Error: HTTP {e.code}"}
        else:
            return {"body_text": f"Error: Connection failed - {str(e.reason)}"}
    except Exception as e:
        return {"body_text": f"Error: Unexpected error - {str(e)}"}

def main(url):
    return scrape_web(url)