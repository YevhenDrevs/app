import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

EXPORT_DIR = Path(__file__).parent.parent / "data" / "exports"

class ExportService:
    """Service for exporting articles to various formats."""
    
    def __init__(self):
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    def export_jsonl(self, articles: List[Dict[str, Any]], filename: str = None) -> str:
        """Export articles to JSONL format."""
        if not filename:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"news_export_{timestamp}.jsonl"
        
        filepath = EXPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for article in articles:
                # Clean article for export
                export_article = {
                    "title": article.get('title', ''),
                    "description": article.get('description', ''),
                    "content": article.get('content', ''),
                    "author": article.get('author', ''),
                    "url": article.get('url', ''),
                    "published_date": article.get('published_date', ''),
                    "source": article.get('source_name', ''),
                    "category": article.get('category', ''),
                    "collected_at": article.get('collected_at', '')
                }
                f.write(json.dumps(export_article, ensure_ascii=False) + '\n')
        
        logger.info(f"Exported {len(articles)} articles to {filepath}")
        return str(filepath)
    
    def export_notebooklm_format(self, articles: List[Dict[str, Any]], include_prompt: bool = True) -> str:
        """Export articles in a format suitable for Google NotebookLM.
        
        NotebookLM accepts:
        - Google Docs
        - PDFs
        - Text files
        - Web URLs
        - YouTube URLs
        
        This generates a clean text file that can be uploaded.
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"notebooklm_export_{timestamp}.txt"
        filepath = EXPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header and instructions
            if include_prompt:
                f.write("""# Tech News Collection for Analysis

This document contains curated tech news articles for analysis.

## Analysis Instructions
Please analyze these articles focusing on:
- AI/ML developments
- Software development trends  
- Cybersecurity news
- New technologies and breakthroughs

Provide insights on key trends, significant developments, and potential implications.

---

""")
            
            # Group by category
            categorized = {}
            for article in articles:
                cat = article.get('category', 'Uncategorized') or 'Uncategorized'
                if cat not in categorized:
                    categorized[cat] = []
                categorized[cat].append(article)
            
            # Write articles by category
            for category, cat_articles in categorized.items():
                f.write(f"\n## {category}\n\n")
                
                for i, article in enumerate(cat_articles, 1):
                    f.write(f"### {i}. {article.get('title', 'Untitled')}\n\n")
                    
                    if article.get('source_name'):
                        f.write(f"**Source:** {article['source_name']}\n")
                    if article.get('published_date'):
                        f.write(f"**Date:** {article['published_date'][:10]}\n")
                    if article.get('url'):
                        f.write(f"**URL:** {article['url']}\n")
                    
                    f.write("\n")
                    
                    if article.get('description'):
                        f.write(f"{article['description']}\n\n")
                    
                    if article.get('content') and len(article['content']) > len(article.get('description', '')):
                        # Include full content if substantially different from description
                        f.write(f"{article['content'][:2000]}\n\n")
                    
                    f.write("---\n\n")
        
        logger.info(f"Exported {len(articles)} articles for NotebookLM to {filepath}")
        return str(filepath)
    
    def export_urls_list(self, articles: List[Dict[str, Any]]) -> str:
        """Export just the URLs for NotebookLM web source import."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"urls_export_{timestamp}.txt"
        filepath = EXPORT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Article URLs for NotebookLM Import\n\n")
            f.write("# You can add these URLs directly to NotebookLM as web sources\n\n")
            
            for article in articles:
                url = article.get('url', '')
                if url and url.startswith('http'):
                    title = article.get('title', 'Untitled')[:80]
                    f.write(f"# {title}\n{url}\n\n")
        
        logger.info(f"Exported {len(articles)} URLs to {filepath}")
        return str(filepath)
    
    def get_exports(self) -> List[Dict[str, Any]]:
        """List all export files."""
        exports = []
        for filepath in EXPORT_DIR.glob('*.*'):
            stat = filepath.stat()
            exports.append({
                "filename": filepath.name,
                "path": str(filepath),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                "type": filepath.suffix[1:] if filepath.suffix else "unknown"
            })
        
        exports.sort(key=lambda x: x['created'], reverse=True)
        return exports
    
    def read_export(self, filename: str) -> str:
        """Read contents of an export file."""
        filepath = EXPORT_DIR / filename
        if not filepath.exists():
            return ""
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def delete_export(self, filename: str) -> bool:
        """Delete an export file."""
        filepath = EXPORT_DIR / filename
        if filepath.exists():
            filepath.unlink()
            return True
        return False
