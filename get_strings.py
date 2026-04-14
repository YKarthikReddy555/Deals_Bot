import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

async def main():
    API_ID = os.getenv("API_ID")
    API_HASH = os.getenv("API_HASH")
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not API_ID or not API_HASH:
        print("❌ Error: API_ID or API_HASH missing in .env file!")
        return

    print("--- 🚀 Deals Bot Session Generator ---")
    
    # 1. Generate BOT Session String
    print("\n[1/2] Generating BOT Session String...")
    async with TelegramClient(StringSession(), int(API_ID), API_HASH) as bot:
        await bot.start(bot_token=BOT_TOKEN)
        bot_string = bot.session.save()
        print(f"✅ BOT_SESSION_STRING: \n\n{bot_string}\n")

    # 2. Generate SCRAPER (User Account) Session String
    print("\n[2/2] Generating SCRAPER Session String...")
    print("⚠️ You will need to enter your Phone Number (+91...) and the Code Telegram sends you.")
    async with TelegramClient(StringSession(), int(API_ID), API_HASH) as scraper:
        await scraper.start()
        scraper_string = scraper.session.save()
        print(f"✅ SCRAPER_SESSION_STRING: \n\n{scraper_string}\n")

    print("--- 🎉 Success! ---")
    print("1. Copy BOTH strings above.")
    print("2. Go to Railway -> Variables -> Bulk Import.")
    print("3. Add them like this:")
    print(f"BOT_SESSION_STRING={bot_string}")
    print(f"SCRAPER_SESSION_STRING={scraper_string}")
    print("\nOnce you add these, the bot will start on Railway instantly!")

if __name__ == "__main__":
    asyncio.run(main())
