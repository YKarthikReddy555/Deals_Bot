-- 📸 MANUAL POST QUEUE
CREATE TABLE IF NOT EXISTS manual_post_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    price TEXT NOT NULL,
    url TEXT NOT NULL,
    image_url TEXT, -- Optional, bot generates banner if empty
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
