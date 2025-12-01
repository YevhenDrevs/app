import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
import re

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)

class ScraperCollector(BaseCollector):
    """Collector for web scraping specific pages."""
    
    async def collect(self) -> List[Dict[str, Any]]:
        """Scrape articles from a webpage."""
        articles = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Scraper fetch failed for {self.name}: HTTP {response.status}")
                        return []
                    
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Get scraping config
            selectors = self.config.get('selectors', {})
            article_selector = selectors.get('article', 'article')
            title_selector = selectors.get('title', 'h2 a, h3 a, .title a')
            desc_selector = selectors.get('description', 'p, .summary, .excerpt')
            link_selector = selectors.get('link', 'a')
            
            # Find article containers
            article_elements = soup.select(article_selector)[:30]
            
            if not article_elements:
                # Fallback: try common patterns
                article_elements = soup.select('article, .post, .entry, .item')[:30]
            
            for element in article_elements:
                try:
                    # Extract title
                    title_el = element.select_one(title_selector)
                    title = title_el.get_text(strip=True) if title_el else ''
                    
                    # Extract link
                    link_el = element.select_one(link_selector) if link_selector != title_selector else title_el
                    if not link_el:
                        link_el = element.find('a')
                    link = link_el.get('href', '') if link_el else ''
                    
                    # Make absolute URL
                    if link and not link.startswith('http'):
                        from urllib.parse import urljoin
                        link = urljoin(self.url, link)
                    
                    # Extract description
                    desc_el = element.select_one(desc_selector)
                    description = desc_el.get_text(strip=True)[:500] if desc_el else ''
                    
                    if not title or not link:
                        continue
                    
                    article = self.normalize_article({
                        'title': title,
                        'description': description,
                        'content': '',
                        'author': '',
                        'url': link,
                        'published_date': datetime.now(timezone.utc).isoformat()
                    })
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.error(f"Error parsing scraped element from {self.name}: {e}")
                    continue
            
            logger.info(f"Scraped {len(articles)} articles from {self.name}")
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error scraping {self.name}: {e}")
        except Exception as e:
            logger.error(f"Error scraping {self.name}: {e}")
        
        return articles
