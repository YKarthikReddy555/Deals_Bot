import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class DBManager:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            self.client = None
            print("⚠️ Supabase credentials missing. Run locally with caution.")
        else:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_settings(self):
        if not self.client: return {}
        res = self.client.table("bot_settings").select("*").execute()
        return {item['key']: item['value'] for item in res.data}

    def is_duplicate_by_id(self, unique_id, window_mins=5):
        if not self.client or not unique_id: return False
        time_threshold = (datetime.utcnow() - timedelta(minutes=window_mins)).isoformat()
        res = self.client.table("deals").select("id")\
            .eq("unique_id", unique_id)\
            .gt("created_at", time_threshold)\
            .limit(1).execute()
        return len(res.data) > 0

    def is_duplicate_by_fingerprint(self, fingerprint, window_mins=5):
        if not self.client or not fingerprint: return False
        time_threshold = (datetime.utcnow() - timedelta(minutes=window_mins)).isoformat()
        res = self.client.table("deals").select("id")\
            .eq("fingerprint", fingerprint)\
            .gt("created_at", time_threshold)\
            .limit(1).execute()
        return len(res.data) > 0

    def add_deal(self, title, price, original_link, aff_link, banner_path=None, unique_id=None, msg_id=None, chat_id=None, target_posts=None, category=None, fingerprint=None, mrp=None, discount_pct=None):
        if not self.client: return
        data = {
            "title": title,
            "price": price,
            "original_link": original_link,
            "affiliate_link": aff_link,
            "banner_path": banner_path,
            "unique_id": unique_id,
            "msg_id": msg_id,
            "chat_id": chat_id,
            "target_posts": target_posts or {},
            "category": category,
            "fingerprint": fingerprint,
            "is_available": True,
            "mrp": mrp,
            "discount_pct": discount_pct
        }
        try:
            self.client.table("deals").insert(data).execute()
        except Exception as e:
            # 🛡️ ELITE STABILITY: Silently catch and log to prevent bot crash
            print(f"⚠️ DB Insert skipped (likely race condition duplicate): {e}")
            # We don't try twice here to keep the code clean and fast. 
            # The logic in ultimate_bot.py handles the primary duplicate check.

    def get_historical_low(self, unique_id, days=30):
        if not self.client or not unique_id: return None
        try:
            # We call the custom RPC function we defined in SQL
            res = self.client.rpc("get_historical_low", {"u_id": unique_id, "days_back": days}).execute()
            return res.data
        except: return None

    def get_active_deals(self, hours=24):
        """Fetches available deals from the last X hours for stock checking"""
        if not self.client: return []
        time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        try:
            res = self.client.table("deals")\
                .select("*")\
                .eq("is_available", True)\
                .gt("created_at", time_threshold)\
                .execute()
            return res.data
        except Exception as e:
            if "is_available" in str(e):
                # 🛡️ Silently wait for Supabase Cache to sync
                return []
            print(f"⚠️ Stock check DB error: {e}")
            return []

    def mark_as_sold_out(self, deal_id):
        if not self.client: return
        self.client.table("deals").update({"is_available": False}).eq("id", deal_id).execute()

    def get_user(self, telegram_id):
        if not self.client: return None
        res = self.client.table("users").select("*").eq("telegram_id", telegram_id).execute()
        return res.data[0] if res.data else None

    def create_user(self, telegram_id, username, referred_by=None):
        if not self.client: return
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "referred_by": referred_by
        }
        self.client.table("users").upsert(data).execute()
        
        # If it's a referral, add points to the referrer
        if referred_by:
            self.client.rpc("increment_growth_points", {"t_id": referred_by}).execute()

db = DBManager()
