from supabase_client import db

def fix():
    correct_channels = "realearnkaro,OsmLooters,LootDealsIndia,AmazonLooters"
    print(f"Cleaning database. Final source channels: {correct_channels}")
    try:
        db.client.table("bot_settings").upsert({"key": "source_channels", "value": correct_channels}).execute()
        print("[OK] Successfully updated database!")
    except Exception as e:
        print(f"[ERROR]: {e}")

if __name__ == "__main__":
    fix()
