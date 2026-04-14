import os
import sys
import asyncio
import re
import logging
import aiohttp
import random
import json
from datetime import datetime, timedelta
from urllib.parse import quote
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Local Imports
from image_engine import ImageEngine
from supabase_client import db
from retailer_spiders import scrape_flipkart_deals, scrape_ajio_deals
from amazon_affiliate import process_amazon_link, is_amazon
from category_map import CATEGORY_CONFIG, detect_category

# Load Environment Variables
load_dotenv()
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")

# Initialize Clients
SESSION_DIR = os.getenv("SESSION_DIR", ".")
if not os.path.exists(SESSION_DIR): os.makedirs(SESSION_DIR)

# Use StringSession if available (Best for Railway/Heroku)
BOT_SESSION_STR = os.getenv("BOT_SESSION_STRING")
if BOT_SESSION_STR:
    client = TelegramClient(StringSession(BOT_SESSION_STR), API_ID, API_HASH)
else:
    client = TelegramClient(os.path.join(SESSION_DIR, 'bot_session'), API_ID, API_HASH)

image_engine = ImageEngine()

# Force UTF-8 for Windows Console
class SafeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        return msg.encode('ascii', 'ignore').decode('ascii')

file_handler = logging.FileHandler("bot.log", encoding='utf-8', errors='replace')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(SafeFormatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(level=logging.INFO, handlers=[file_handler, console_handler])
logger = logging.getLogger("DealsBot")

# ===== BOT COMMANDS =====

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handles /start and Referral logic"""
    user_id = event.sender_id
    username = event.sender.username or "User"
    parts = event.message.text.split()
    referrer_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
    
    existing_user = db.get_user(user_id)
    if not existing_user:
        db.create_user(user_id, username, referred_by=referrer_id)
        welcome_text = "Welcome to the Deals Bot! 🚀\n\nInvite friends using your link to earn rewards!\n"
    else:
        welcome_text = "Welcome back! ⚡\n"
    
    me = await client.get_me()
    ref_link = f"https://t.me/{me.username}?start={user_id}"
    await event.respond(f"{welcome_text}\n👉 Your Referral Link: {ref_link}")

# ===== UTILITIES =====

def get_deal_fingerprint(title, price):
    """Creates a unique string for Name + Price to detect visual duplicates"""
    clean_title = re.sub(r'[^\w\s]', '', title).lower().replace(' ', '-')[:40]
    return f"{clean_title}-{price.replace('₹', '').replace(',', '').strip() or '0'}"

def extract_mrp_and_price(text):
    """
    AI PRICE PARSER: Extracts both MRP and Deal Price.
    Returns: (mrp, deal_price)
    """
    # Find all prices: ₹123, Rs. 123
    prices = re.findall(r'(?:₹|RS\.?\s?|@|MRP:?\s?|PRICE:?\s?)(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    clean_prices = [float(p.replace(',', '')) for p in prices]
    
    if not clean_prices: return None, None
    
    # Logic: Usually the HIGHER price is MRP, LOWER is Deal
    if len(clean_prices) >= 2:
        mrp = max(clean_prices)
        deal_price = min(clean_prices)
        return mrp, deal_price
    
    return None, clean_prices[0]

def extract_price(text):
    """Fallback price detection"""
    m, d = extract_mrp_and_price(text)
    return f"₹{d}" if d else "Best Deal"

async def get_ai_badges(uid, price):
    """Checks for All-Time Lows (last 30 days)"""
    badges = []
    hist_low = db.get_historical_low(uid, days=30)
    
    if hist_low and float(price) <= float(hist_low):
        badges.append("✅ **All-Time Low (30 Days)**")
    
    return " ".join(badges)

def extract_unique_id(url):
    if not url: return str(random.randint(100000, 999999))
    match = re.search(r'/([A-Z0-9]{10})(?:[/?]|$)', url)
    if match: return match.group(1)
    match = re.search(r'p/(itm[a-z0-9]+)', url, re.I)
    if match: return match.group(1)
    return str(hash(url))[:10]

async def convert_to_earnkaro(url, scraper):
    bot_handle = os.getenv("EARNKARO_BOT", "@ekconverter9bot")
    ek_id = os.getenv("EARNKARO_ID", "5079830")
    try:
        async with scraper.conversation(bot_handle, timeout=30) as conv:
            await conv.send_message(url)
            response = await conv.get_response()
            if "not locate" in response.text.lower():
                logger.warning(f"❌ EarnKaro: Retailer Not Supported ({url})")
                return None
            new_urls = re.findall(r'(https?://\S+)', response.text)
            if new_urls: return new_urls[0]
            logger.warning(f"⚠️ EarnKaro: No link in response for {url}")
    except asyncio.TimeoutError:
        logger.warning(f"⏰ EarnKaro: Timeout (Bot too slow) for {url}")
    except Exception as e:
        logger.warning(f"⚠️ EarnKaro Error: {str(e) or type(e).__name__} for {url}")
    return None

async def get_affiliate_link(url, scraper):
    """Converts to affiliate or returns None (No original link fallback)"""
    if is_amazon(url): return await process_amazon_link(url)
    return await convert_to_earnkaro(url, scraper)

def extract_links(text):
    # 🧩 STRICT AFFILIATE ONLY: Clean the label (take last line only for the button)
    labeled_links = []
    labels = re.findall(r'(.*?)(https?://\S+)', text, re.DOTALL)
    for label, url in labels:
        # Take the last non-empty line as the label (e.g. "Buy Now")
        lines = [l.strip() for l in label.split('\n') if l.strip()]
        btn_text = lines[-1] if lines else "Buy Now"
        clean_label = re.sub(r'[^\w\s]', '', btn_text).strip()
        labeled_links.append({"label": clean_label if clean_label else "Buy Now", "url": url.strip(' )]*.,\"\'')})
    return labeled_links

def generate_caption(deals):
    """
    PRO STYLE CAPTION ENGINE (Inspired by Osm Dhruva)
    - Direct Inline Links
    - Category Awareness
    - Professional Icons
    """
    if not deals: return ""

    # Detect primary category for the header
    cat_id = detect_category(deals[0]['title'])
    cat_name = CATEGORY_CONFIG.get(cat_id, {}).get('name', 'Mega Loot') if cat_id else 'Mega Loot'
    cat_emoji = CATEGORY_CONFIG.get(cat_id, {}).get('emoji', '🔥') if cat_id else '🔥'
    
    header = f"💥 {cat_name} | Best Deals 💥\n\n"
    body = []

    for deal in deals:
        d_cat_id = detect_category(deal['title'])
        d_emoji = CATEGORY_CONFIG.get(d_cat_id, {}).get('emoji', cat_emoji) if d_cat_id else cat_emoji
        
        # Format: Icon Title Price
        # Format: 👉 Link
        body.append(f"{d_emoji} **{deal['title']}** - **{deal['price']}**")
        for link in deal.get('aff_links', []):
            body.append(f"[🛒 Buy Now]({link['url']})")
        body.append("") # Spacer between items

    footer = f"\n⚡ *Hurry! Price may change anytime.*"
    return header + "\n".join(body) + footer

async def convert_and_clone_text(text, scraper, uid=None):
    """
    CLONE & CONVERT ENGINE:
    - Finds all URLs in text
    - Converts them to affiliate in parallel
    - Injects AI Smart Badges (Loot, All-Time Low)
    - Replaces in original text with [🛒 Buy Now](link)
    """
    # 🧩 SURGICAL URL DETECTION: Exclude trailing punctuation and markdown symbols
    urls = sorted(list(set(re.findall(r'(https?://[^\s\)\}\]\*\'\",]+)', text))), key=len, reverse=True)
    if not urls: return text, []

    # Resolve and convert all in parallel
    tasks = [get_affiliate_link(url.strip(' )]*.,\"\''), scraper) for url in urls]
    aff_links = await asyncio.gather(*tasks)
    
    mapping = {orig: aff for orig, aff in zip(urls, aff_links) if aff}
    
    # Check for All-or-Nothing safety
    if len(mapping) < len(urls):
        logger.warning(f"⚠️ Conversion incomplete: {len(mapping)}/{len(urls)} converted.")
        return None, [] # Abort if any conversion fails for quality

    # AI ANALYSIS: MRP & DISCOUNTS
    mrp, deal_p = extract_mrp_and_price(text)
    header_alert = ""
    if mrp and deal_p:
        discount_pct = int((1 - (deal_p / mrp)) * 100)
        if discount_pct >= 60:
            header_alert = f"🚨 **MEGA LOOT ALERT: {discount_pct}% OFF!** 🚨\n\n"
    
    # AI ANALYSIS: HISTORICAL LOW
    badge_line = ""
    if uid and deal_p:
        badge_line = await get_ai_badges(uid, deal_p)
        if badge_line: badge_line = f"\n{badge_line}\n"

    new_text = text
    # 1. SURGICAL PASS 1: Update existing markdown links [label](url)
    for orig, aff in mapping.items():
        # Replaces [label](orig) with [label](aff) - preserves original button style
        pattern = rf'\[(.*?)\]\({re.escape(orig)}\)' 
        new_text = re.sub(pattern, rf'[\1]({aff})', new_text)
    
    # 2. SURGICAL PASS 2: Convert remaining RAW URLs to buttons
    for orig, aff in mapping.items():
        # Match 'orig' only if NOT preceded by '(' to avoid double-processing markdown
        pattern = rf'(?<!\(){re.escape(orig)}'
        new_text = re.sub(pattern, f"[🛒 Buy Now]({aff})", new_text)
    
    final_text = f"{header_alert}{new_text}{badge_line}"
    return final_text, list(mapping.values())

async def resolve_destination(url):
    if not url or "t.me" in url: return url
    try:
        async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
            async with session.head(url, allow_redirects=True, timeout=5) as resp:
                return str(resp.url)
    except: return url

async def is_out_of_stock(url):
    return False # Placeholder - Expand with retailer specific scrapers

def get_target_channels(settings):
    raw = settings.get('channel_id', CHANNEL_ID)
    if not raw: return [CHANNEL_ID]
    return [c.strip() for c in re.split(r'[\n,]+', str(raw)) if c.strip()]

async def search_source_for_niche(sources, keywords):
    niche_deals = []
    for channel in sources:
        channel = channel.strip().replace("@", "")
        if not channel: continue
        try:
            for kw in keywords[:2]:
                async for message in client.iter_messages(channel, search=kw, limit=10):
                    if not message.text: continue
                    links = extract_links(message.text)
                    if not links: continue
                    niche_deals.append({
                        "title": message.text.split('\n')[0][:50].strip(' *_-'),
                        "price": extract_price(message.text),
                        "url": links[0]['url']
                    })
                    if len(niche_deals) >= 5: break
                if len(niche_deals) >= 5: break
        except: pass
    return niche_deals

# ===== MAIN LOOPS =====

async def process_single_message(message, scraper, target_channels):
    """Processes a single incoming message in real-time"""
    if not message.text or not is_good_deal(message.text): return
    
    # 🕵️ Random Jitter to look human and avoid rate limits
    await asyncio.sleep(random.uniform(0.5, 2.0))
    
    try:
        # 🧠 MULTI-PRODUCT PARSER
        labeled_links = extract_links(message.text)
        if not labeled_links: return
        
        # 🧠 AI-POWERED ANALYSIS
        real_primary = await resolve_destination(labeled_links[0]['url'])
        uid = extract_unique_id(real_primary)
        
        # 🛡️ CLONE & CONVERT MODE (WITH AI)
        new_text, aff_list = await convert_and_clone_text(message.text, scraper, uid=uid)
        if not new_text: return # Safety abort
        
        # Determine primary metadata
        title = message.text.split('\n')[0][:60].strip(' *_-')
        mrp, deal_p = extract_mrp_and_price(message.text)
        current_price = f"₹{deal_p}" if deal_p else extract_price(message.text)
        fingerprint = get_deal_fingerprint(title, current_price)
        discount_pct = int((1 - (deal_p / mrp)) * 100) if mrp and deal_p else None

        if db.is_duplicate_by_id(uid) or db.is_duplicate_by_fingerprint(fingerprint):
            logger.info(f"🚫 Duplicate filtered: {title}")
            return

        # 📤 BROADCAST
        caption = new_text
        primary_orig_url = labeled_links[0]['url']
        primary_aff_url = aff_list[0] if aff_list else primary_orig_url
        
        # 🖼️ SMART IMAGE DETECTION
        img = None
        img_path = f"static/uploads/{uid}.jpg"
        if message.photo:
            img = await scraper.download_media(message.photo, file=img_path)
        elif message.media:
            web = getattr(message.media, 'webpage', None)
            if web and getattr(web, 'photo', None):
                img = await scraper.download_media(web.photo, file=img_path)
            elif getattr(message.media, 'document', None) and 'image' in (message.media.document.mime_type or ''):
                img = await scraper.download_media(message.media.document, file=img_path)
        
        if not img:
            img = image_engine.generate_banner(title, current_price)
        
        if img: 
            img = image_engine.apply_watermark(img)
            web_img_path = "/" + img.replace("\\", "/")
        else:
            web_img_path = None
        
        posts_map = {}
        for target in target_channels:
            try:
                if img: sent = await client.send_file(target, img, caption=caption, parse_mode='markdown')
                else: sent = await client.send_message(target, caption, parse_mode='markdown', hide_link_preview=True)
                posts_map[str(target)] = sent.id
            except: pass
        
        cat_id = detect_category(title)
        db.add_deal(title, current_price, primary_orig_url, primary_aff_url, web_img_path, uid, target_posts=posts_map, category=cat_id, fingerprint=fingerprint, mrp=mrp, discount_pct=discount_pct)
        
        logger.info(f"⚡ [AI CLONE] Posted deal with {discount_pct}% discount.")
    except Exception as e:
        logger.error(f"⚠️ Message processing error: {e}")

def is_good_deal(text):
    text = text.lower()
    loot_keywords = ["₹", "rs", "off", "deal", "loot", "%", "mrp", "price", "only", "@"]
    return any(kw in text for kw in loot_keywords)

async def monitor_stock_loop():
    logger.info("🛡️ Stock Monitoring Service started.")
    while True:
        try:
            deals = db.get_active_deals(hours=24)
            for d in deals:
                if await is_out_of_stock(d['original_link']):
                    posts = d.get('target_posts', {})
                    for chat_id, msg_id in posts.items():
                        try:
                            msg = await client.get_messages(chat_id, ids=msg_id)
                            if msg: await client.edit_message(chat_id, msg_id, text=f"❌ **[SOLD OUT]**\n~~{msg.text}~~")
                        except: pass
                    db.mark_as_sold_out(d['id'])
                await asyncio.sleep(5)
        except: pass
        await asyncio.sleep(2 * 3600)

async def spider_hunt_loop():
    logger.info("🕷️ Spider Intelligence Service started.")
    last_active_cats = None
    while True:
        try:
            settings = db.get_settings()
            active_cats = settings.get('active_categories', [])
            if isinstance(active_cats, str): active_cats = json.loads(active_cats)
            
            if last_active_cats is not None and last_active_cats == active_cats:
                await asyncio.sleep(60)
                continue
            
            last_active_cats = active_cats
            sources = settings.get('source_channels', 'osmdhruva,realearnkaro,DiscountAIDeals').split(',')
            target_channels = get_target_channels(settings)
            
            for cat_id in active_cats:
                if cat_id in CATEGORY_CONFIG:
                    logger.info(f"🕸️ Spider Hunting for Niche: {CATEGORY_CONFIG[cat_id]['name']}")
                    deals = await search_source_for_niche(sources, CATEGORY_CONFIG[cat_id]['keywords'])
                    for deal in deals:
                        real = await resolve_destination(deal['url'])
                        uid = extract_unique_id(real)
                        if db.is_duplicate_by_id(uid): continue
                        
                        aff = await get_affiliate_link(deal['url'], client)
                        if not aff: continue
                        
                        caption = generate_caption([{"title": deal['title'], "price": deal['price'], "aff_links": [{"label": "Buy Now", "url": aff}]}])
                        img = image_engine.generate_banner(deal['title'], deal['price'])
                        img = image_engine.apply_watermark(img)
                        
                        posts_map = {}
                        for target in target_channels:
                            try:
                                sent = await client.send_file(target, img, caption=caption, parse_mode='markdown')
                                posts_map[str(target)] = sent.id
                            except: pass
                        if img and os.path.exists(img): os.remove(img)
                        db.add_deal(deal['title'], deal['price'], deal['url'], aff, "Spider", uid, target_posts=posts_map)
                        await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"⚠️ Spider loop error: {e}")
        await asyncio.sleep(600)

async def broadcast_service():
    logger.info("📣 Broadcast Hub Service started.")
    while True:
        try:
            res = db.client.table("broadcast_queue").select("*").eq("status", "pending").limit(1).execute()
            if res.data:
                broadcast = res.data[0]
                db.client.table("broadcast_queue").update({"status": "sending"}).eq("id", broadcast['id']).execute()
                users_res = db.client.table("users").select("telegram_id").execute()
                all_users = [u['telegram_id'] for u in users_res.data]
                count = 0
                for user_id in all_users:
                    try:
                        await client.send_message(user_id, broadcast['message'], parse_mode='markdown')
                        count += 1
                        await asyncio.sleep(0.1)
                    except: pass
                db.client.table("broadcast_queue").update({"status": "completed", "completed_at": "now()"}).eq("id", broadcast['id']).execute()
                logger.info(f"✅ Broadcast complete! Sent to {count} members.")
        except Exception as e:
            logger.error(f"⚠️ Broadcast service error: {e}")
        await asyncio.sleep(30)

async def manual_post_service():
    logger.info("🛠️ Manual Post Engine started.")
    while True:
        try:
            res = db.client.table("manual_post_queue").select("*").eq("status", "pending").limit(1).execute()
            if res.data:
                deal = res.data[0]
                db.client.table("manual_post_queue").update({"status": "processing"}).eq("id", deal['id']).execute()
                
                deal_url = deal['url'].strip()
                caption = f"🔥 **{deal['title']}**\n\n💰 Price: {deal['price']}\n\n[🛒 Buy Now]({deal_url})\n\n⚡ *Hurry! Limited stock available.*"
                img = image_engine.generate_banner(deal['title'], deal['price'])
                img = image_engine.apply_watermark(img)
                
                posts_map = {}
                target_channels = get_target_channels(db.get_settings())
                for target in target_channels:
                    try:
                        sent = await client.send_file(target, img, caption=caption, parse_mode='markdown')
                        posts_map[str(target)] = sent.id
                    except: pass
                if img and os.path.exists(img): os.remove(img)
                db.add_deal(deal['title'], deal['price'], deal['url'], deal['url'], "Manual", f"MAN_{deal['id'][:8]}", target_posts=posts_map)
                db.client.table("manual_post_queue").update({"status": "completed"}).eq("id", deal['id']).execute()
        except Exception as e:
            logger.error(f"⚠️ Manual tool error: {e}")
        await asyncio.sleep(10)

async def main():
    # 🚀 Initialize both clients
    SCRAPER_SESSION_STR = os.getenv("SCRAPER_SESSION_STRING")
    scraper_session = StringSession(SCRAPER_SESSION_STR) if SCRAPER_SESSION_STR else os.path.join(SESSION_DIR, 'scraper_session')
    
    async with TelegramClient(scraper_session, API_ID, API_HASH) as scraper, \
               client:
        
        await client.start(bot_token=BOT_TOKEN)
        settings = db.get_settings()
        source_channels = settings.get('source_channels', 'osmdhruva,realearnkaro,DiscountAIDeals,iamprasadtech,ttsdeals,CLICKDEALS123').split(',')
        target_channels = get_target_channels(settings)
        
        # 🚀 REAL-TIME LISTENER: Listen for new messages in source channels
        @scraper.on(events.NewMessage(chats=[c.strip() for c in source_channels if c.strip()]))
        async def handler(event):
            await process_single_message(event.message, scraper, target_channels)

        logger.info("✅ All systems connected. Real-time monitoring active 24/7.")
        
        # Run secondary services in background
        asyncio.create_task(monitor_stock_loop())
        asyncio.create_task(spider_hunt_loop())
        asyncio.create_task(broadcast_service())
        asyncio.create_task(manual_post_service())
        
        try:
            # Keep alive
            await scraper.run_until_disconnected()
        finally:
            logger.info("🛑 Shutting down gracefully...")
            await client.disconnect()

@client.on(events.Raw(types.UpdateMessageReactions))
async def handle_reactions(update):
    """AUTOMATED VIRAL PINNING: Pins deal if it hits 15+ 🔥 reactions"""
    try:
        # Check if it's a reaction update on a tracked channel
        target_chat = os.getenv("CHANNEL_ID", "@your_channel")
        peer_id = getattr(update.peer, 'channel_id', None)
        if not peer_id: return
        
        # We only care about high reactions
        total_fire = 0
        for r in update.reactions:
            emoji = getattr(r.reaction, 'emoticon', '')
            if emoji == "🔥":
                total_fire = r.count
                break
        
        if total_fire >= 15:
            # Avoid pinning multiple times with a simple cache
            if not hasattr(client, '_recently_pinned'): client._recently_pinned = set()
            if update.msg_id in client._recently_pinned: return

            await client.pin_message(update.peer, update.msg_id, notify=True)
            client._recently_pinned.add(update.msg_id)
            logger.info(f"🔥 [VIRAL] Pinned message {update.msg_id} due to {total_fire} reactions!")
    except Exception as e:
        logger.debug(f"Reaction handler error (ignore if minor): {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass