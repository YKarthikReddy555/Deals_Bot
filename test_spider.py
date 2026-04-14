import asyncio
import aiohttp
import re
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestSpider")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
]

async def test_scrape_flipkart_deals(custom_url=None):
    url = custom_url if custom_url else "https://www.flipkart.com/offers-store"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    logger.info(f"Targeting URL: {url}")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=15) as response:
            logger.info(f"Status: {response.status}")
            html = await response.text()
            
            # Simple check for product links
            patterns = [
                r'href="(/[^"]*/p/[^"]*\?pid=[^"]*)"',
                r'href="(/p/[^"]*\?pid=[^"]*)"'
            ]
            
            links = []
            for p in patterns:
                links.extend(re.findall(p, html))
            
            logger.info(f"Fround {len(links)} raw links total.")
            unique_links = list(set(links))
            logger.info(f"Found {len(unique_links)} unique product links.")
            
            for link in unique_links[:5]:
                logger.info(f"Sample Link: https://www.flipkart.com{link}")

async def test_scrape_amazon_deals(custom_url=None):
    url = custom_url if custom_url else "https://www.amazon.in/gp/goldbox"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    }
    logger.info(f"Targeting Amazon URL: {url}")
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=15) as response:
            logger.info(f"Amazon Status: {response.status}")
            html = await response.text()
            links = re.findall(r'href="(/[^"]*/dp/[^"/?]*)', html)
            logger.info(f"Found {len(links)} Amazon product links.")

async def main():
    # Test Laptop category on Flipkart
    flip_url = "https://www.flipkart.com/search?q=laptop"
    await test_scrape_flipkart_deals(flip_url)
    
    # Test Laptop category on Amazon
    amz_url = "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=laptop"
    await test_scrape_amazon_deals(amz_url)

if __name__ == "__main__":
    asyncio.run(main())
