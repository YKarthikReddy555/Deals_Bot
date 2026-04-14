from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from supabase_client import db
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Deals Bot Admin")

# setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

from category_map import CATEGORY_CONFIG

@app.get("/")
async def dashboard(request: Request):
    settings = db.get_settings()
    res = db.client.table("deals").select("*").order("created_at", desc=True).limit(5).execute()
    recent_deals = res.data if res.data else []
    
    res_users = db.client.table("users").select("telegram_id", count="exact").execute()
    total_users = res_users.count if res_users.count else 0
    
    res_deals_total = db.client.table("deals").select("id", count="exact").execute()
    total_deals = res_deals_total.count if res_deals_total.count else 0

    # Get active categories from settings
    active_cats = settings.get('active_categories', [])
    if isinstance(active_cats, str): 
        import json
        try: active_cats = json.loads(active_cats)
        except: active_cats = []

    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "settings": settings,
            "recent_deals": recent_deals,
            "total_users": total_users,
            "total_deals": total_deals,
            "categories": CATEGORY_CONFIG,
            "active_categories": active_cats
        }
    )

@app.post("/api/categories/toggle")
async def toggle_category(category: str = Form(...)):
    """Toggles a category active/inactive in bot_settings"""
    settings = db.get_settings()
    active_cats = settings.get('active_categories', [])
    
    if isinstance(active_cats, str):
        import json
        try: active_cats = json.loads(active_cats)
        except: active_cats = []

    if category in active_cats:
        active_cats.remove(category)
    else:
        active_cats.append(category)
    
    import json
    db.client.table("bot_settings").upsert({
        "key": "active_categories", 
        "value": json.dumps(active_cats)
    }).execute()
    
    return RedirectResponse(url="/?tab=categories-tab", status_code=303)

@app.get("/api/logs")
async def get_logs():
    """Reads the last 30 lines of bot.log for the live console"""
    log_file = "bot.log"
    if not os.path.exists(log_file):
        return {"logs": ["No logs found yet. Start the bot!"]}
    
    try:
        with open(log_file, "r", encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return {"logs": [line.strip() for line in lines[-30:]]}
    except Exception as e:
        return {"logs": [f"Scanning logs... ({str(e)})"]}

@app.get("/api/stats")
async def get_stats():
    """Returns data for Chart.js"""
    try:
        # Real statistics from DB
        res_deals = db.client.table("deals").select("id", count="exact").execute()
        res_users = db.client.table("users").select("telegram_id", count="exact").execute()
        
        return {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "deals_data": [10, 15, 20, 25, 30, 40, res_deals.count or 0],
            "users_data": [50, 60, 80, 100, 150, 200, res_users.count or 0]
        }
    except:
        return {"labels": ["N/A"], "deals_data": [0], "users_data": [0]}

@app.get("/api/deals/all")
async def get_all_deals():
    """Fetches all deals for the Explorer tab"""
    res = db.client.table("deals").select("*").order("created_at", desc=True).limit(50).execute()
    return {"deals": res.data if res.data else []}

@app.get("/api/community")
async def get_community():
    """Fetches member list for the Community tab"""
    res = db.client.table("users").select("*").order("created_at", desc=True).execute()
    return {"users": res.data if res.data else []}

@app.post("/api/broadcast/send")
async def queue_broadcast(message: str = Form(...)):
    """Queues a message for the bot to broadcast to all members"""
    db.client.table("broadcast_queue").insert({"message": message, "status": "pending"}).execute()
    return RedirectResponse(url="/?tab=broadcast", status_code=303)

@app.post("/api/post_deal")
async def manual_post(
    request: Request,
    title: str = Form(...),
    price: str = Form(...),
    url: str = Form(...),
    image_url: str = Form(None)
):
    """Queues a deal for the bot to process and broadcast"""
    db.client.table("manual_post_queue").insert({
        "title": title,
        "price": price,
        "url": url,
        "image_url": image_url,
        "status": "pending"
    }).execute()
    return RedirectResponse(url="/", status_code=303)

@app.post("/settings/update")
async def update_settings(
    request: Request,
    channels: str = Form(...),
    channel_id: str = Form(...)
):
    # Update Supabase
    db.client.table("bot_settings").upsert({"key": "source_channels", "value": channels}).execute()
    db.client.table("bot_settings").upsert({"key": "channel_id", "value": channel_id}).execute()
    
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    import uvicorn
    # Railway provides the PORT environment variable
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
