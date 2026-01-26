"""ArXiv paper fetcher for AI research."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
import arxiv

from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("arxiv_fetcher")


class ArxivFetcher:
    """Fetches recent AI research papers from ArXiv."""

    CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "stat.ML"]

    def __init__(self):
        """Initialize ArXiv fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours * 2)  # Papers are less frequent
        self.max_papers = 20

    async def fetch_all(self) -> List[Article]:
        """Fetch recent AI papers from ArXiv.

        Returns:
            List of Article objects
        """
        logger.info("fetching_arxiv", categories=self.CATEGORIES)

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
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for paper in results:
                try:
                    # Check publication date
                    published_at = paper.published
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)

                    if published_at < cutoff_time:
                        continue

                    # Format authors
                    authors = ", ".join([author.name for author in paper.authors[:3]])
                    if len(paper.authors) > 3:
                        authors += " et al."

                    # Build rich content
                    content_parts = [
                        f"**Abstract:** {paper.summary[:800]}",
                        f"\n**Authors:** {authors}",
                        f"**Categories:** {', '.join(paper.categories[:5])}",
                    ]

                    # Add comment if available (often contains page count, etc.)
                    if paper.comment:
                        content_parts.append(f"**Note:** {paper.comment[:200]}")

                    content = "\n".join(content_parts)

                    article = Article(
                        title=paper.title.strip().replace("\n", " "),
                        url=paper.pdf_url,
                        source="ArXiv",
                        published_at=published_at,
                        content=content,
                        tags=["ArXiv", "Research"] + paper.categories[:3],
                    )
                    articles.append(article)

                except Exception as e:
                    logger.debug("arxiv_paper_error", error=str(e))
                    continue

            logger.info("arxiv_total", count=len(articles))
            return articles

        except Exception as e:
            logger.error("arxiv_fetch_error", error=str(e))
            return []
