import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

class LLMService:
    """Service for AI-powered summarization and categorization."""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY', '')
        self.model = 'gpt-4o-mini'
        self.provider = 'openai'
    
    async def categorize_article(self, article: Dict[str, Any]) -> str:
        """Categorize a single article into predefined categories."""
        if not self.api_key:
            logger.warning("No LLM API key configured")
            return ""
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"categorize_{article.get('id', 'unknown')}",
                system_message="""You are a tech news categorizer. Categorize the given article into ONE of these categories:
- AI/ML
- Software Development
- Cybersecurity
- New Technologies
- Other

Respond with ONLY the category name, nothing else."""
            ).with_model(self.provider, self.model)
            
            text = f"Title: {article.get('title', '')}\nDescription: {article.get('description', '')}"
            message = UserMessage(text=text)
            response = await chat.send_message(message)
            
            category = response.strip()
            valid_categories = ['AI/ML', 'Software Development', 'Cybersecurity', 'New Technologies', 'Other']
            
            return category if category in valid_categories else 'Other'
            
        except Exception as e:
            logger.error(f"Error categorizing article: {e}")
            return ""
    
    async def summarize_articles(
        self,
        articles: List[Dict[str, Any]],
        category: Optional[str] = None,
        output_format: str = "markdown"
    ) -> Dict[str, Any]:
        """Generate a summary of multiple articles."""
        if not self.api_key:
            return {"error": "No LLM API key configured"}
        
        if not articles:
            return {"error": "No articles to summarize"}
        
        try:
            # Prepare article data
            articles_text = ""
            for i, article in enumerate(articles[:20], 1):  # Limit to 20
                articles_text += f"\n---\n{i}. **{article.get('title', '')}**\n"
                articles_text += f"Source: {article.get('source_name', 'Unknown')}\n"
                articles_text += f"Description: {article.get('description', '')}\n"
            
            format_instruction = ""
            if output_format == "json":
                format_instruction = """Output your response as valid JSON with this structure:
{
  "summary": "Overall summary paragraph",
  "key_trends": ["trend1", "trend2", ...],
  "top_stories": [
    {"title": "...", "significance": "...", "index": 1},
    ...
  ],
  "categories": {
    "AI/ML": ["headline1", ...],
    "Software Development": [...],
    ...
  }
}"""
            else:
                format_instruction = """Format your response as clean markdown with:
## Summary
A brief overview paragraph

## Key Trends
- Trend 1
- Trend 2

## Top Stories
1. **Story Title** - Brief significance

## By Category
### AI/ML
- Headlines...
### Software Development
- Headlines...
(etc for relevant categories)"""
            
            system_message = f"""You are a tech news analyst. Analyze the following tech news articles and provide an insightful summary.

Filter and focus on these topics:
- AI/ML advancements
- Software development trends
- Cybersecurity news
- New technologies and research breakthroughs

Ignore irrelevant or low-quality content.

{format_instruction}"""
            
            if category:
                system_message += f"\n\nFocus specifically on articles related to: {category}"
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"summary_{datetime.now(timezone.utc).isoformat()}",
                system_message=system_message
            ).with_model(self.provider, self.model)
            
            message = UserMessage(text=f"Here are the articles to analyze:\n{articles_text}")
            response = await chat.send_message(message)
            
            result = {
                "summary_text": response,
                "article_count": len(articles),
                "category": category,
                "format": output_format,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Try to parse JSON if that was the format
            if output_format == "json":
                try:
                    # Extract JSON from response (may be wrapped in markdown code block)
                    json_str = response
                    if "```json" in response:
                        json_str = response.split("```json")[1].split("```")[0]
                    elif "```" in response:
                        json_str = response.split("```")[1].split("```")[0]
                    
                    result["summary_json"] = json.loads(json_str)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"Error summarizing articles: {e}")
            return {"error": str(e)}
    
    async def generate_notebooklm_prompt(self, articles: List[Dict[str, Any]]) -> str:
        """Generate a filtering prompt for NotebookLM."""
        prompt = """# Tech News Analysis Instructions

Please analyze the uploaded news content with the following criteria:

## Focus Areas
1. **AI/ML** - Artificial Intelligence, Machine Learning, Deep Learning, LLMs, Neural Networks
2. **Software Development** - Programming, DevOps, Frameworks, Tools, Best Practices
3. **Cybersecurity** - Security threats, vulnerabilities, privacy, data protection
4. **New Technologies** - Research breakthroughs, emerging tech, innovations

## Analysis Tasks
1. Categorize each article into the focus areas above
2. Identify key trends across the articles
3. Highlight the most significant developments
4. Note any potential implications or predictions
5. Flag any duplicate or low-quality content

## Output Format
Provide a structured summary with:
- Executive Summary (2-3 sentences)
- Key Trends (bullet points)
- Top Stories by Category
- Potential Implications
- Recommended Deep Dives

---

"""
        return prompt
