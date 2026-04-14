import aiohttp
import re
import logging

# Configuration
AMAZON_TAG = "cybertech09e-21"
logger = logging.getLogger("AmazonAffiliate")

def is_amazon(url: str) -> bool:
    """Detection: Checks if URL belongs to Amazon India or is an Amzn short link"""
    url_lower = url.lower()
    return "amazon.in" in url_lower or "amzn" in url_lower

async def expand_url(url):
    """Execution: Resolves shortened links using aiohttp (High speed)"""
    if "dp/" in url or "gp/product/" in url:
        return url
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        async with aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as session:
            # Try HEAD first (faster, less bandwidth)
            try:
                async with session.head(url, allow_redirects=True) as response:
                    if response.status < 400:
                        return str(response.url)
            except:
                pass # Fallback to GET
            
            # Fallback to GET for tricky shorteners
            async with session.get(url, allow_redirects=True) as response:
                return str(response.url)
    except Exception as e:
        error_msg = str(e) if str(e) else type(e).__name__
        logger.error(f"⚠️ Expansion failed for {url}: {error_msg}")
        return url

def extract_asin(url):
    """Extraction: Finds the 10-char ASIN for product identification"""
    pattern = r"/(dp|gp/product)/([A-Z0-9]{10})"
    match = re.search(pattern, url)
    return match.group(2) if match else None

def build_amazon_link(asin):
    """Construction: Builds the clean direct affiliate link with your tag"""
    if not asin: return None
    return f"https://www.amazon.in/dp/{asin}?tag={AMAZON_TAG}&linkCode=ll1"

async def process_amazon_link(url):
    """Main Flow: Expand -> Extract -> Build"""
    full_url = await expand_url(url)
    asin = extract_asin(full_url)
    return build_amazon_link(asin)
