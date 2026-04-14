import aiohttp
import asyncio
import logging

logger = logging.getLogger("StockChecker")

async def is_out_of_stock(url):
    """Checks if a product is out of stock across multiple retailers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return False # Keep as available if we can't check
                
                html = await response.text()
                html_lower = html.lower()
                
                # Retailer-specific keywords
                out_of_stock_indicators = [
                    "currently unavailable",      # Amazon
                    "sold out",                    # Flipkart
                    "out of stock",                # Myntra / Common
                    "this item is out of stock",
                    "not available for purchase",
                    "not in stock"
                ]
                
                # Check for any indicator
                for indicator in out_of_stock_indicators:
                    if indicator in html_lower:
                        logger.info(f"🚨 Out of stock detected for: {url}")
                        return True
                
                return False
    except Exception as e:
        logger.warning(f"⚠️ Could not check stock for {url}: {e}")
        return False
