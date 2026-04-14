from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from supabase_client import db
import os
from dotenv import load_dotenv

# Load Environment
load_dotenv()

app = FastAPI(title="Cyber Tech Telugu Deals")

# Templates & Static Files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def homepage(request: Request, cat: str = None, q: str = None, page: int = 1):
    """The Public Frontend: Shows all verified deals with pagination (50/page)"""
    page_size = 50
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    # 🔍 Initial query with exact count
    query = db.client.table("deals").select("*", count="exact")
    
    # 🔍 Search & Filter
    if cat:
        query = query.eq("category", cat.lower())
    if q:
        query = query.ilike("title", f"%{q}%")
        
    res = query.order("created_at", desc=True).range(start, end).execute()
    deals = res.data if res.data else []
    total_count = res.count if res.count else 0
    
    # 🧹 Clean up for display
    import re
    for deal in deals:
        deal['title'] = re.sub(r'\*\*|~~|__|\*', '', deal['title'])
        if deal.get('price') and deal['price'] in deal['title']:
            deal['title'] = deal['title'].replace(deal['price'], "").strip(' -|@')

    has_next = total_count > (start + page_size)
    total_pages = (total_count + page_size - 1) // page_size
    
    return templates.TemplateResponse(
        request=request,
        name="website.html",
        context={
            "deals": deals, 
            "active_cat": cat, 
            "search_q": q, 
            "page": int(page or 1),
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": page > 1
        }
    )

if __name__ == "__main__":
    import uvicorn
    # Using port 8080 to keep it separate from the Admin Dashboard at 8000
    print("Cyber Tech Telugu Deals is launching on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
