"""ArXiv paper fetcher for AI research."""

import asyncio
from datetime import datetime, timedelta
from typing import List
import arxiv
from src.models.article import Article
from src.config import settings


class ArxivFetcher:
    """Fetches recent AI research papers from ArXiv."""

    CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV"]

    def __init__(self):
        """Initialize ArXiv fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_papers = 15

    async def fetch_all(self) -> List[Article]:
        """Fetch recent AI papers from ArXiv.

        Returns:
            List of Article objects
        """
        try:
            # Build search query for AI categories
            category_query = " OR ".join([f"cat:{cat}" for cat in self.CATEGORIES])

            # Run arxiv search in thread pool
            loop = asyncio.get_event_loop()
            search = arxiv.Search(
                query=category_query,
                max_results=self.max_papers,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )

            results = await loop.run_in_executor(None, lambda: list(search.results()))

            articles = []
            cutoff_time = datetime.now() - self.max_age

            for paper in results:
                # Check publication date
                published_at = paper.published.replace(tzinfo=None)
                if published_at < cutoff_time:
                    continue

                # Format authors
                authors = ", ".join([author.name for author in paper.authors[:3]])
                if len(paper.authors) > 3:
                    authors += " et al."

                # Build content
                content = f"{paper.summary[:500]}...\n\nAuthors: {authors}"

                article = Article(
                    title=paper.title.strip(),
                    url=paper.pdf_url,
                    source="ArXiv",
                    published_at=published_at,
                    content=content,
                    tags=["ArXiv", "Research"] + paper.categories,
                )
                articles.append(article)

            return articles

        except Exception as e:
            print(f"Error fetching ArXiv papers: {e}")
            return []
