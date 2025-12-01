import feedparser
import aiohttp
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

class RSSCollector(BaseCollector):
    """Collector for RSS feeds."""
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed."""
        articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"RSS fetch failed for {self.name}: HTTP {response.status}")
                        return []
                    
                    content = await response.text()
            
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parse warning for {self.name}: {feed.bozo_exception}")
            
            for entry in feed.entries[:50]:  # Limit to 50 per fetch
                try:
                    # Parse published date
                    pub_date = ''
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
                    
                    # Get content
                    content = ''
                    if hasattr(entry, 'content') and entry.content:
                        content = entry.content[0].get('value', '')
                    elif hasattr(entry, 'summary'):
                        content = entry.summary
                    
                    article = self.normalize_article({
                        'title': getattr(entry, 'title', ''),
                        'description': getattr(entry, 'summary', '')[:500],
                        'content': content,
                        'author': getattr(entry, 'author', ''),
                        'url': getattr(entry, 'link', ''),
                        'published_date': pub_date
                    })
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error parsing RSS entry from {self.name}: {e}")
                    continue
            
            logger.info(f"Collected {len(articles)} articles from {self.name}")
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching RSS {self.name}: {e}")
        except Exception as e:
            logger.error(f"Error collecting from RSS {self.name}: {e}")
        
        return articles
