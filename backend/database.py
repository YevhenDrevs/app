import sqlite3
import aiosqlite
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "data" / "news.db"

async def init_db():
    """Initialize the SQLite database with required tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DB_PATH) as db:
        # News articles table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                content TEXT,
                author TEXT,
                url TEXT UNIQUE NOT NULL,
                published_date TEXT,
                source_id INTEGER,
                collected_at TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                category TEXT,
                exported INTEGER DEFAULT 0,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        ''')
        
        # News sources table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                url TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                config TEXT,
                last_fetched TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # AI Summaries table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_ids TEXT NOT NULL,
                summary_text TEXT NOT NULL,
                summary_json TEXT,
                category TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Settings table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Exports table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS exports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articles_count INTEGER NOT NULL,
                export_date TEXT NOT NULL,
                filename TEXT NOT NULL,
                export_type TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        await db.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_articles_hash ON articles(content_hash)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_articles_collected ON articles(collected_at)')
        
        await db.commit()
        
        # Insert default settings if not exist
        default_settings = [
            ('schedule_interval', '60'),
            ('categories', 'AI/ML,Software Development,Cybersecurity,New Technologies'),
            ('max_articles_per_fetch', '50'),
            ('auto_summarize', 'true'),
            ('llm_model', 'gpt-4o-mini')
        ]
        for key, value in default_settings:
            await db.execute(
                'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        await db.commit()
    
    logger.info(f"Database initialized at {DB_PATH}")

def generate_content_hash(title: str, url: str) -> str:
    """Generate a hash for duplicate detection."""
    content = f"{title.lower().strip()}{url.lower().strip()}"
    return hashlib.md5(content.encode()).hexdigest()

# Article operations
async def insert_article(article: Dict[str, Any]) -> Optional[int]:
    """Insert a new article, returns ID if successful, None if duplicate."""
    content_hash = generate_content_hash(article['title'], article['url'])
    
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cursor = await db.execute('''
                INSERT INTO articles (title, description, content, author, url, 
                    published_date, source_id, collected_at, content_hash, category, exported)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.get('title', ''),
                article.get('description', ''),
                article.get('content', ''),
                article.get('author', ''),
                article.get('url', ''),
                article.get('published_date', ''),
                article.get('source_id'),
                datetime.now(timezone.utc).isoformat(),
                content_hash,
                article.get('category', ''),
                0
            ))
            await db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.debug(f"Duplicate article skipped: {article.get('title', '')[:50]}")
            return None

async def get_articles(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None,
    search: Optional[str] = None,
    source_id: Optional[int] = None,
    exported: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """Get articles with optional filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        query = '''
            SELECT a.*, s.name as source_name 
            FROM articles a 
            LEFT JOIN sources s ON a.source_id = s.id
            WHERE 1=1
        '''
        params = []
        
        if category:
            query += ' AND a.category = ?'
            params.append(category)
        if search:
            query += ' AND (a.title LIKE ? OR a.description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        if source_id:
            query += ' AND a.source_id = ?'
            params.append(source_id)
        if exported is not None:
            query += ' AND a.exported = ?'
            params.append(1 if exported else 0)
        
        query += ' ORDER BY a.collected_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_article_count(
    category: Optional[str] = None,
    search: Optional[str] = None,
    source_id: Optional[int] = None
) -> int:
    """Get total article count with filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        query = 'SELECT COUNT(*) FROM articles WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        if search:
            query += ' AND (title LIKE ? OR description LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        if source_id:
            query += ' AND source_id = ?'
            params.append(source_id)
        
        cursor = await db.execute(query, params)
        row = await cursor.fetchone()
        return row[0] if row else 0

async def mark_articles_exported(article_ids: List[int]):
    """Mark articles as exported."""
    async with aiosqlite.connect(DB_PATH) as db:
        placeholders = ','.join('?' * len(article_ids))
        await db.execute(
            f'UPDATE articles SET exported = 1 WHERE id IN ({placeholders})',
            article_ids
        )
        await db.commit()

# Source operations
async def insert_source(source: Dict[str, Any]) -> int:
    """Insert a new source."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO sources (name, type, url, enabled, config, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            source['name'],
            source['type'],
            source['url'],
            source.get('enabled', 1),
            json.dumps(source.get('config', {})),
            datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()
        return cursor.lastrowid

async def get_sources(enabled_only: bool = False) -> List[Dict[str, Any]]:
    """Get all sources."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = 'SELECT * FROM sources'
        if enabled_only:
            query += ' WHERE enabled = 1'
        query += ' ORDER BY name'
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        sources = []
        for row in rows:
            source = dict(row)
            source['config'] = json.loads(source.get('config') or '{}')
            sources.append(source)
        return sources

async def update_source(source_id: int, updates: Dict[str, Any]) -> bool:
    """Update a source."""
    async with aiosqlite.connect(DB_PATH) as db:
        set_clauses = []
        params = []
        for key, value in updates.items():
            if key == 'config':
                value = json.dumps(value)
            set_clauses.append(f'{key} = ?')
            params.append(value)
        params.append(source_id)
        
        await db.execute(
            f'UPDATE sources SET {", ".join(set_clauses)} WHERE id = ?',
            params
        )
        await db.commit()
        return True

async def delete_source(source_id: int) -> bool:
    """Delete a source."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM sources WHERE id = ?', (source_id,))
        await db.commit()
        return True

async def update_source_last_fetched(source_id: int):
    """Update the last_fetched timestamp for a source."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'UPDATE sources SET last_fetched = ? WHERE id = ?',
            (datetime.now(timezone.utc).isoformat(), source_id)
        )
        await db.commit()

# Settings operations
async def get_setting(key: str) -> Optional[str]:
    """Get a setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            'SELECT value FROM settings WHERE key = ?', (key,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_all_settings() -> Dict[str, str]:
    """Get all settings."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT key, value FROM settings')
        rows = await cursor.fetchall()
        return {row[0]: row[1] for row in rows}

async def update_setting(key: str, value: str):
    """Update or insert a setting."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        await db.commit()

# Summary operations
async def insert_summary(summary: Dict[str, Any]) -> int:
    """Insert a new summary."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO summaries (article_ids, summary_text, summary_json, category, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            json.dumps(summary['article_ids']),
            summary['summary_text'],
            json.dumps(summary.get('summary_json', {})),
            summary.get('category', ''),
            datetime.now(timezone.utc).isoformat()
        ))
        await db.commit()
        return cursor.lastrowid

async def get_summaries(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent summaries."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM summaries ORDER BY created_at DESC LIMIT ?', (limit,)
        )
        rows = await cursor.fetchall()
        summaries = []
        for row in rows:
            s = dict(row)
            s['article_ids'] = json.loads(s.get('article_ids') or '[]')
            s['summary_json'] = json.loads(s.get('summary_json') or '{}')
            summaries.append(s)
        return summaries

# Export operations
async def insert_export(export: Dict[str, Any]) -> int:
    """Record an export."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO exports (articles_count, export_date, filename, export_type)
            VALUES (?, ?, ?, ?)
        ''', (
            export['articles_count'],
            datetime.now(timezone.utc).isoformat(),
            export['filename'],
            export['export_type']
        ))
        await db.commit()
        return cursor.lastrowid

async def get_exports(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent exports."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            'SELECT * FROM exports ORDER BY export_date DESC LIMIT ?', (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

# Statistics
async def get_stats() -> Dict[str, Any]:
    """Get database statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        
        cursor = await db.execute('SELECT COUNT(*) FROM articles')
        stats['total_articles'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM articles WHERE exported = 1')
        stats['exported_articles'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM sources WHERE enabled = 1')
        stats['active_sources'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute('SELECT COUNT(*) FROM summaries')
        stats['total_summaries'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            '''SELECT category, COUNT(*) as count FROM articles 
               WHERE category != "" GROUP BY category'''
        )
        rows = await cursor.fetchall()
        stats['by_category'] = {row[0]: row[1] for row in rows}
        
        cursor = await db.execute(
            '''SELECT DATE(collected_at) as date, COUNT(*) as count 
               FROM articles GROUP BY DATE(collected_at) 
               ORDER BY date DESC LIMIT 7'''
        )
        rows = await cursor.fetchall()
        stats['articles_by_day'] = [{"date": row[0], "count": row[1]} for row in rows]
        
        return stats

# Initialize default sources
async def seed_default_sources():
    """Add default RSS sources if none exist."""
    sources = await get_sources()
    if len(sources) > 0:
        return
    
    default_sources = [
        # RSS Feeds
        {"name": "Hacker News", "type": "rss", "url": "https://news.ycombinator.com/rss", "enabled": 1},
        {"name": "TechCrunch", "type": "rss", "url": "https://techcrunch.com/feed/", "enabled": 1},
        {"name": "Wired", "type": "rss", "url": "https://www.wired.com/feed/rss", "enabled": 1},
        {"name": "Ars Technica", "type": "rss", "url": "https://feeds.arstechnica.com/arstechnica/index", "enabled": 1},
        {"name": "MIT Tech Review", "type": "rss", "url": "https://www.technologyreview.com/feed/", "enabled": 1},
        {"name": "The Verge", "type": "rss", "url": "https://www.theverge.com/rss/index.xml", "enabled": 1},
        {"name": "AI News (VentureBeat)", "type": "rss", "url": "https://venturebeat.com/category/ai/feed/", "enabled": 1},
        {"name": "Dev.to", "type": "rss", "url": "https://dev.to/feed", "enabled": 1},
        # Reddit (API type)
        {"name": "r/MachineLearning", "type": "reddit", "url": "https://www.reddit.com/r/MachineLearning", "enabled": 1, "config": {"subreddit": "MachineLearning"}},
        {"name": "r/technology", "type": "reddit", "url": "https://www.reddit.com/r/technology", "enabled": 1, "config": {"subreddit": "technology"}},
        {"name": "r/programming", "type": "reddit", "url": "https://www.reddit.com/r/programming", "enabled": 1, "config": {"subreddit": "programming"}},
    ]
    
    for source in default_sources:
        await insert_source(source)
    
    logger.info(f"Seeded {len(default_sources)} default sources")
