from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """Base class for all news collectors."""
    
    def __init__(self, source: Dict[str, Any]):
        self.source = source
        self.source_id = source.get('id')
        self.name = source.get('name', 'Unknown')
        self.url = source.get('url', '')
        self.config = source.get('config', {})
    
    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect news articles from the source.
        
        Returns:
            List of article dictionaries with keys:
            - title: str
            - description: str
            - content: str
            - author: str
            - url: str
            - published_date: str (ISO format)
            - source_id: int
        """
        pass
    
    def normalize_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize article data to standard format."""
        return {
            'title': str(article.get('title', '')).strip(),
            'description': str(article.get('description', '')).strip()[:1000],
            'content': str(article.get('content', '')).strip()[:10000],
            'author': str(article.get('author', '')).strip()[:200],
            'url': str(article.get('url', '')).strip(),
            'published_date': str(article.get('published_date', '')),
            'source_id': self.source_id,
            'category': article.get('category', '')
        }
