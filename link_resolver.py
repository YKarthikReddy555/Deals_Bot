import aiohttp
import logging
import re
from urllib.parse import urlparse, parse_qs, unquote

logger = logging.getLogger("LinkResolver")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

RETAILER_DOMAINS = [
    "amazon", "flipkart", "ajio", "myntra", "nykaa", "meesho", 
    "jiomart", "tatacliq", "beardo", "boat-lifestyle", "mamaearth"
]

def is_retailer(url: str) -> bool:
    url_lower = url.lower()
    return any(rd in url_lower for rd in RETAILER_DOMAINS)

def find_store_url(text: str) -> str:
    """Finds a retailer link inside any text or URL"""
    for rd in RETAILER_DOMAINS:
        # Regex to find links. We look for the rightmost http to catch nested URLs
        pattern = rf'https?://[^\s"\'%]*?{rd}[^\s"\'%]*'
        matches = re.findall(pattern, text, re.I)
        if matches:
            # Return the shortest match that contains the domain (usually the deep link)
            # or the one that doesn't contain a redirector name
            for m in sorted(matches, key=len):
                if rd in m.lower():
                    # If this match itself contains another http, recursively clean it
                    if m.count("http") > 1:
                        inner = m[m.rfind("http"):]
                        return inner
                    return m
    return None

async def resolve_destination(url: str, depth=0) -> str:
    if depth > 3: return url
    if not url.startswith("http"): return url
    
    # If it's already a clean store link (and doesn't look like a redirector), return it
    if is_retailer(url) and "click" not in url.lower() and "redirect" not in url.lower():
        return url

    try:
        async with aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session:
            async with session.get(url, allow_redirects=True, timeout=12) as response:
                final_url = unquote(str(response.url))
                
                # 1. Check if the final URL itself is a store link
                store_link = find_store_url(final_url)
                if store_link:
                    return store_link
                
                # 2. Check HTML for store links (JS/Meta redirects)
                html_text = await response.text()
                store_link_in_html = find_store_url(html_text)
                if store_link_in_html:
                    return store_link_in_html
                
                return final_url
    except Exception as e:
        logger.error(f"Resolution error for {url}: {e}")
        return url

if __name__ == "__main__":
    import asyncio
    test_link = "https://ajiio.in/rd0juDt"
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(resolve_destination(test_link))
    print(f"Deep Resolved Result: {res}")
