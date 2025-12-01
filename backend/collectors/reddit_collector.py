import aiohttp
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
import os

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

class RedditCollector(BaseCollector):
    """Collector for Reddit subreddits using JSON API."""
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Fetch posts from Reddit subreddit."""
        articles = []
        subreddit = self.config.get('subreddit', '')
        
        if not subreddit:
            # Extract from URL
            parts = self.url.split('/r/')
            if len(parts) > 1:
                subreddit = parts[1].split('/')[0]
        
        if not subreddit:
            logger.error(f"No subreddit configured for {self.name}")
            return []
        
        try:
            # Use Reddit's JSON API (no auth required for public data)
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
            
            headers = {
                'User-Agent': 'TechNewsMonitor/1.0 (Educational Project)'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Reddit fetch failed for r/{subreddit}: HTTP {response.status}")
                        return []
                    
                    data = await response.json()
            
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                try:
                    post_data = post.get('data', {})
                    
                    # Skip stickied posts
                    if post_data.get('stickied'):
                        continue
                    
                    # Parse timestamp
                    created_utc = post_data.get('created_utc', 0)
                    pub_date = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat() if created_utc else ''
                    
                    article = self.normalize_article({
                        'title': post_data.get('title', ''),
                        'description': post_data.get('selftext', '')[:500] or f"Score: {post_data.get('score', 0)} | Comments: {post_data.get('num_comments', 0)}",
                        'content': post_data.get('selftext', ''),
                        'author': post_data.get('author', ''),
                        'url': post_data.get('url', '') or f"https://reddit.com{post_data.get('permalink', '')}",
                        'published_date': pub_date
                    })
                    
                    if article['title'] and article['url']:
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error parsing Reddit post from r/{subreddit}: {e}")
                    continue
            
            logger.info(f"Collected {len(articles)} posts from r/{subreddit}")
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching Reddit r/{subreddit}: {e}")
        except Exception as e:
            logger.error(f"Error collecting from Reddit r/{subreddit}: {e}")
        
        return articles
