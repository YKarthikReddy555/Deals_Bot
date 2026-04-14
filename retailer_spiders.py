import aiohttp
import asyncio
import re
import json
import logging
import random

logger = logging.getLogger("RetailerSpider")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

async def scrape_flipkart_deals(custom_url=None):
    """Stealthily scrapes high-discount deals from Flipkart (Category Deep Hunting)"""
    url = custom_url if custom_url else "https://www.flipkart.com/offers-store"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': random.choice(['https://www.google.com/', 'https://www.facebook.com/', 'https://twitter.com/'])
    }
    
    deals = []
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=15) as response:
                if response.status != 200:
                    logger.warning(f"⚠️ Flipkart block: Status {response.status}")
                    return []
                
                html = await response.text()
                
                # 🔍 ADVANCED PATTERNS: Look for multiple product link styles
                patterns = [
                    r'href="(/[^"]*/p/[^"]*\?pid=[^"]*)"', # Direct product links
                    r'href="(/[^"]*/p/[^"]*\?cmpid=[^"]*)"', # Campaign links
                    r'href="(/p/[^"]*\?pid=[^"]*)"'          # Short product links
                ]
                
                links = []
                for p in patterns:
                    links.extend(re.findall(p, html))
                
                for link in list(set(links))[:8]: # Take top 8 unique deals
                    full_link = f"https://www.flipkart.com{link}"
                    deals.append({
                        "title": "🔥 Verified Flipkart Loot",
                        "price": "Check Offer",
                        "url": full_link,
                        "store": "Flipkart"
                    })
        logger.info(f"✅ Spider grabbed {len(deals)} items from {url}")
        return deals
    except Exception as e:
        logger.error(f"⚠️ Flipkart Spider failed: {e}")
        return []

async def scrape_ajio_deals():
    """Scrapes trending deals from Ajio's public deal pages"""
    url = "https://www.ajio.com/s/60-to-90-percent-off" # High loot URL
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    
    deals = []
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=15) as response:
                html = await response.text()
                # Ajio is complex, but we can grab links with /p/ which are products
                links = re.findall(r'href="(/p/[^"]*)"', html)
                for link in list(set(links))[:5]:
                    deals.append({
                        "title": "💫 Ajio Premium Loot",
                        "price": "Under ₹999",
                        "url": f"https://www.ajio.com{link}",
                        "store": "Ajio"
                    })
        return deals
    except Exception as e:
        logger.error(f"⚠️ Ajio Spider failed: {e}")
        return []
