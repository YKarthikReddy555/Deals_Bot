# 🧠 Category Knowledge Map
# Contains search patterns, emojis, and deep-hunt URLs for active sourcing

CATEGORY_CONFIG = {
    "laptops": {
        "name": "Laptops & PCs",
        "emoji": "💻",
        "keywords": ["laptop", "macbook", "ryzen", "intel core", "i3", "i5", "i7", "chromebook", "gaming pc", "asus", "rog", "strix", "msi", "predator", "vivobook", "ideapad", "thinkpad", "pavilion", "zenbook"],
        "amazon_url": "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=laptop",
        "flipkart_url": "https://www.flipkart.com/search?q=laptop&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off&p%5B%5D=facets.serviceability%5B%5D%3Dtrue&p%5B%5D=facets.filter_standard%5B%5D%3D1"
    },
    "mobiles": {
        "name": "Mobiles & Tablets",
        "emoji": "📱",
        "keywords": ["iphone", "samsung s2", "oneplus", "realme", "redmi", "xiaomi", "mobile", "smartphone", "ipad", "tablet", "pixel 7", "pixel 8", "nothing phone", "moto g", "poko", "poco", "infinix", "oppo", "vivo", "lava", "tecno"],
        "amazon_url": "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=mobile",
        "flipkart_url": "https://www.flipkart.com/search?q=mobile&otracker=search&p%5B%5D=facets.serviceability%5B%5D%3Dtrue"
    },
    "fashion": {
        "name": "Fashion & Shoes",
        "emoji": "👔",
        "keywords": ["t-shirt", "shirt", "jeans", "shoes", "sneakers", "nike", "puma", "adidas", "watch", "handbag", "crocs", "skechers", "woodland", "levis", "wrangler", "jack & jones", "van heusen"],
        "amazon_url": "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=fashion",
        "flipkart_url": "https://www.flipkart.com/search?q=fashion&p%5B%5D=facets.serviceability%5B%5D%3Dtrue"
    },
    "smartwatches": {
        "name": "Smartwatches",
        "emoji": "⌚",
        "keywords": ["smartwatch", "fitness band", "apple watch", "galaxy watch", "noise", "boat watch", "amazfit", "fire-boltt", "fossil", "garmin", "fitbit", "honor band", "pebble"],
        "amazon_url": "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=smartwatch",
        "flipkart_url": "https://www.flipkart.com/search?q=smartwatch&p%5B%5D=facets.serviceability%5B%5D%3Dtrue"
    },
    "appliances": {
        "name": "Home Appliances",
        "emoji": "📺",
        "keywords": ["refrigerator", "washing machine", "smart tv", "microwave", "air conditioner", "ac", "purifier"],
        "amazon_url": "https://www.amazon.in/gp/goldbox?ref_=nav_cs_gb&search_query=appliances",
        "flipkart_url": "https://www.flipkart.com/search?q=appliances&p%5B%5D=facets.serviceability%5B%5D%3Dtrue"
    }
}

def detect_category(text):
    """Simple keyword matching to detect product category"""
    text = text.lower()
    for cat_id, config in CATEGORY_CONFIG.items():
        if any(kw in text for kw in config['keywords']):
            return cat_id
    return None
