-- 📦 MULTI-TARGET POSTING SUPPORT
-- Add a JSONB column to store multiple message IDs across different channels
ALTER TABLE deals ADD COLUMN IF NOT EXISTS target_posts JSONB DEFAULT '{}'::jsonb;

-- Example format in target_posts:
-- { "@my_deals": 1234, "@loot_master": 5678 }
