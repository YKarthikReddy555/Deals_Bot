import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

def clean_url(url: str) -> str:
    """Removes tracking query parameters and normalizes the URL"""
    try:
        parsed = urlparse(url)
        # Keep only essential parameters if needed, but for deduplication we usually want none
        # or we want to normalize the path
        clean_path = parsed.path
        if clean_path.endswith('/'):
            clean_path = clean_path[:-1]
            
        return urlunparse((parsed.scheme, parsed.netloc, clean_path, '', '', ''))
    except Exception:
        return url

def extract_unique_id(url: str) -> str:
    """Extracts Amazon ASIN or generates a hash for deduplication"""
    # 1. Look for Amazon ASIN (B0...)
    # Matches /dp/ASIN or /gp/product/ASIN
    asin_match = re.search(r'/(?:dp|gp/product)/([A-Z0-9]{10})', url)
    if asin_match:
        return f"AMZN_{asin_match.group(1)}"
    
    # 2. Look for Flipkart ID
    fsn_match = re.search(r'pid=([A-Z0-9]{16})', url)
    if fsn_match:
        return f"FK_{fsn_match.group(1)}"
        
    # 3. Fallback: Hash the cleaned URL
    cleaned = clean_url(url)
    return hashlib.sha256(cleaned.encode()).hexdigest()
