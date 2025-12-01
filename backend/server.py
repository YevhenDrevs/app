from fastapi import FastAPI, APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import asyncio

from database import (
    init_db, seed_default_sources, insert_article, get_articles, get_article_count,
    mark_articles_exported, insert_source, get_sources, update_source, delete_source,
    update_source_last_fetched, get_setting, get_all_settings, update_setting,
    insert_summary, get_summaries, insert_export, get_exports as get_db_exports, get_stats
)
from collectors import RSSCollector, RedditCollector, ScraperCollector
from services import LLMService, ExportService, SchedulerService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection (kept for compatibility)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'tech_news_monitor')]

# Initialize services
llm_service = LLMService()
export_service = ExportService()
scheduler_service = SchedulerService()

# Create the main app
app = FastAPI(title="Tech News Monitor", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class SourceCreate(BaseModel):
    name: str
    type: str = "rss"  # rss, reddit, scraper, api
    url: str
    enabled: bool = True
    config: Dict[str, Any] = {}

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]

class SummarizeRequest(BaseModel):
    article_ids: Optional[List[int]] = None
    category: Optional[str] = None
    output_format: str = "markdown"  # markdown or json
    limit: int = 20

class ExportRequest(BaseModel):
    article_ids: Optional[List[int]] = None
    export_type: str = "notebooklm"  # notebooklm, jsonl, urls
    mark_exported: bool = True
    unexported_only: bool = False
    limit: int = 100

class ArticleResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    content: Optional[str]
    author: Optional[str]
    url: str
    published_date: Optional[str]
    source_id: Optional[int]
    source_name: Optional[str]
    collected_at: str
    category: Optional[str]
    exported: bool

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    await init_db()
    await seed_default_sources()
    
    # Set up scheduler callback
    scheduler_service.set_collect_callback(collect_all_sources)
    
    # Start scheduler with saved interval
    interval = await get_setting('schedule_interval')
    if interval:
        scheduler_service.start(int(interval))
    else:
        scheduler_service.start(60)  # Default 60 minutes
    
    logger.info("Tech News Monitor started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    scheduler_service.stop()
    client.close()

# Collection logic
async def collect_from_source(source: Dict[str, Any]) -> int:
    """Collect articles from a single source."""
    source_type = source.get('type', 'rss')
    
    if source_type == 'rss':
        collector = RSSCollector(source)
    elif source_type == 'reddit':
        collector = RedditCollector(source)
    elif source_type == 'scraper':
        collector = ScraperCollector(source)
    else:
        logger.warning(f"Unknown source type: {source_type}")
        return 0
    
    try:
        articles = await collector.collect()
        inserted_count = 0
        
        # Categorize and insert articles
        auto_summarize = await get_setting('auto_summarize')
        
        for article in articles:
            # Auto-categorize if enabled
            if auto_summarize == 'true' and not article.get('category'):
                try:
                    category = await llm_service.categorize_article(article)
                    article['category'] = category
                except Exception as e:
                    logger.error(f"Categorization failed: {e}")
            
            # Insert article
            article_id = await insert_article(article)
            if article_id:
                inserted_count += 1
        
        # Update last fetched timestamp
        await update_source_last_fetched(source['id'])
        
        logger.info(f"Collected {inserted_count} new articles from {source['name']}")
        return inserted_count
        
    except Exception as e:
        logger.error(f"Error collecting from {source.get('name')}: {e}")
        return 0

async def collect_all_sources() -> Dict[str, Any]:
    """Collect from all enabled sources."""
    sources = await get_sources(enabled_only=True)
    total_collected = 0
    results = []
    
    for source in sources:
        count = await collect_from_source(source)
        total_collected += count
        results.append({"source": source['name'], "collected": count})
    
    logger.info(f"Total collected: {total_collected} articles from {len(sources)} sources")
    return {
        "total_collected": total_collected,
        "sources_processed": len(sources),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# API Routes

# Dashboard / Stats
@api_router.get("/")
async def root():
    return {"message": "Tech News Monitor API", "version": "1.0.0"}

@api_router.get("/stats")
async def get_statistics():
    """Get dashboard statistics."""
    stats = await get_stats()
    stats['scheduler_running'] = scheduler_service.is_running()
    stats['next_collection'] = scheduler_service.get_next_run()
    return stats

# Articles
@api_router.get("/articles")
async def list_articles(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    search: Optional[str] = None,
    source_id: Optional[int] = None,
    exported: Optional[bool] = None
):
    """List articles with filters."""
    articles = await get_articles(
        limit=limit,
        offset=offset,
        category=category,
        search=search,
        source_id=source_id,
        exported=exported
    )
    total = await get_article_count(category=category, search=search, source_id=source_id)
    
    return {
        "articles": articles,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@api_router.get("/articles/categories")
async def get_categories():
    """Get list of categories."""
    settings = await get_all_settings()
    categories = settings.get('categories', 'AI/ML,Software Development,Cybersecurity,New Technologies')
    return {"categories": categories.split(',')}

# Sources
@api_router.get("/sources")
async def list_sources():
    """List all news sources."""
    sources = await get_sources()
    return {"sources": sources}

@api_router.post("/sources")
async def create_source(source: SourceCreate):
    """Create a new news source."""
    source_id = await insert_source(source.model_dump())
    return {"id": source_id, "message": "Source created successfully"}

@api_router.put("/sources/{source_id}")
async def update_source_endpoint(source_id: int, source: SourceUpdate):
    """Update a news source."""
    updates = {k: v for k, v in source.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    await update_source(source_id, updates)
    return {"message": "Source updated successfully"}

@api_router.delete("/sources/{source_id}")
async def delete_source_endpoint(source_id: int):
    """Delete a news source."""
    await delete_source(source_id)
    return {"message": "Source deleted successfully"}

@api_router.post("/sources/{source_id}/collect")
async def collect_from_single_source(source_id: int, background_tasks: BackgroundTasks):
    """Trigger collection from a single source."""
    sources = await get_sources()
    source = next((s for s in sources if s['id'] == source_id), None)
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Run collection in background
    background_tasks.add_task(collect_from_source, source)
    
    return {"message": f"Collection started for {source['name']}"}

# Collection
@api_router.post("/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """Trigger collection from all enabled sources."""
    background_tasks.add_task(collect_all_sources)
    return {"message": "Collection started for all sources"}

@api_router.post("/collect/sync")
async def trigger_collection_sync():
    """Trigger synchronous collection from all enabled sources."""
    result = await collect_all_sources()
    return result

# Summaries / AI
@api_router.post("/summarize")
async def summarize_articles(request: SummarizeRequest):
    """Generate AI summary of articles."""
    # Get articles
    if request.article_ids:
        # Get specific articles - would need to add this to database.py
        articles = await get_articles(limit=len(request.article_ids))
        articles = [a for a in articles if a['id'] in request.article_ids]
    else:
        articles = await get_articles(
            limit=request.limit,
            category=request.category
        )
    
    if not articles:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Generate summary
    result = await llm_service.summarize_articles(
        articles=articles,
        category=request.category,
        output_format=request.output_format
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Save summary
    summary_id = await insert_summary({
        "article_ids": [a['id'] for a in articles],
        "summary_text": result.get("summary_text", ""),
        "summary_json": result.get("summary_json", {}),
        "category": request.category
    })
    
    result["summary_id"] = summary_id
    return result

@api_router.get("/summaries")
async def list_summaries(limit: int = Query(50, ge=1, le=200)):
    """List recent summaries."""
    summaries = await get_summaries(limit=limit)
    return {"summaries": summaries}

@api_router.get("/notebooklm/prompt")
async def get_notebooklm_prompt():
    """Get the filtering prompt for NotebookLM."""
    articles = await get_articles(limit=1)
    prompt = await llm_service.generate_notebooklm_prompt(articles)
    return {"prompt": prompt}

# Exports
@api_router.post("/export")
async def export_articles(request: ExportRequest):
    """Export articles for NotebookLM or other uses."""
    # Get articles
    if request.article_ids:
        articles = await get_articles(limit=len(request.article_ids))
        articles = [a for a in articles if a['id'] in request.article_ids]
    else:
        articles = await get_articles(
            limit=request.limit,
            exported=False if request.unexported_only else None
        )
    
    if not articles:
        raise HTTPException(status_code=404, detail="No articles found")
    
    # Export based on type
    if request.export_type == "notebooklm":
        filepath = export_service.export_notebooklm_format(articles)
    elif request.export_type == "jsonl":
        filepath = export_service.export_jsonl(articles)
    elif request.export_type == "urls":
        filepath = export_service.export_urls_list(articles)
    else:
        raise HTTPException(status_code=400, detail="Invalid export type")
    
    # Mark as exported if requested
    if request.mark_exported:
        article_ids = [a['id'] for a in articles]
        await mark_articles_exported(article_ids)
    
    # Record export
    filename = Path(filepath).name
    await insert_export({
        "articles_count": len(articles),
        "filename": filename,
        "export_type": request.export_type
    })
    
    return {
        "message": "Export created successfully",
        "filename": filename,
        "articles_count": len(articles),
        "filepath": filepath
    }

@api_router.get("/exports")
async def list_exports():
    """List all export files."""
    exports = export_service.get_exports()
    db_exports = await get_db_exports()
    return {"files": exports, "history": db_exports}

@api_router.get("/exports/{filename}")
async def download_export(filename: str):
    """Download an export file."""
    content = export_service.read_export(filename)
    if not content:
        raise HTTPException(status_code=404, detail="Export not found")
    
    return PlainTextResponse(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@api_router.delete("/exports/{filename}")
async def delete_export(filename: str):
    """Delete an export file."""
    if export_service.delete_export(filename):
        return {"message": "Export deleted"}
    raise HTTPException(status_code=404, detail="Export not found")

# Settings
@api_router.get("/settings")
async def get_settings():
    """Get all settings."""
    settings = await get_all_settings()
    return {"settings": settings}

@api_router.put("/settings")
async def update_settings(request: SettingsUpdate):
    """Update settings."""
    for key, value in request.settings.items():
        await update_setting(key, value)
    
    # Update scheduler if interval changed
    if 'schedule_interval' in request.settings:
        new_interval = int(request.settings['schedule_interval'])
        if scheduler_service.is_running():
            scheduler_service.update_interval(new_interval)
    
    return {"message": "Settings updated successfully"}

# Scheduler
@api_router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status."""
    return {
        "running": scheduler_service.is_running(),
        "next_run": scheduler_service.get_next_run()
    }

@api_router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler."""
    interval = await get_setting('schedule_interval')
    scheduler_service.start(int(interval) if interval else 60)
    return {"message": "Scheduler started"}

@api_router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler."""
    scheduler_service.stop()
    return {"message": "Scheduler stopped"}

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
