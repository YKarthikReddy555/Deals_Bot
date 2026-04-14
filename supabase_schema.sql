-- Run this in the Supabase SQL Editor to initialize your permanent backend

-- 1. Users table (for growth and referrals)
CREATE TABLE IF NOT EXISTS public.users (
    telegram_id BIGINT PRIMARY KEY,
    username TEXT,
    referred_by BIGINT REFERENCES public.users(telegram_id),
    growth_points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Deals history
CREATE TABLE IF NOT EXISTS public.deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    price TEXT,
    original_link TEXT,
    affiliate_link TEXT,
    banner_path TEXT,
    unique_id TEXT UNIQUE, -- 🚀 Digital fingerprint for deduplication
    msg_id BIGINT,         -- 🚀 Telegram message ID for editing
    chat_id TEXT,          -- 🚀 Target channel/chat ID
    is_available BOOLEAN DEFAULT TRUE, -- 📦 Stock status
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Bot Settings (Centralized management)
CREATE TABLE IF NOT EXISTS public.bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Insert default source channels if not exists
INSERT INTO public.bot_settings (key, value) VALUES 
('source_channels', 'LootDealsIndia,AmazonLooters'),
('channel_id', '@your_channel'),
('growth_message', '🚀 Join our deals channel and invite friends to win rewards!')
ON CONFLICT (key) DO NOTHING;

-- 4. RPC for Growth Points (Referral tracking)
CREATE OR REPLACE FUNCTION increment_growth_points(t_id BIGINT)
RETURNS void AS $$
BEGIN
    UPDATE public.users 
    SET growth_points = growth_points + 1
    WHERE telegram_id = t_id;
END;
$$ LANGUAGE plpgsql;
