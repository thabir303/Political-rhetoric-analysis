"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ArticleMetadata(BaseModel):
    """Metadata for an article."""
    date: Optional[str] = Field(None, description="Publication date of the article")
    category: Optional[str] = Field(None, description="Article category")
    persons: Optional[List[str]] = Field(default_factory=list, description="Persons mentioned in the article")
    source: Optional[str] = Field(None, description="Source URL or identifier")
    author: Optional[str] = Field(None, description="Article author")
    title: Optional[str] = Field(None, description="Article title")


class ArticleCreate(BaseModel):
    """Request model for creating/storing an article."""
    content: str = Field(..., description="Article content/text", min_length=1)
    metadata: ArticleMetadata = Field(default_factory=ArticleMetadata)
    article_id: Optional[str] = Field(None, description="Custom article ID")


class ArticleResponse(BaseModel):
    """Response model for article operations."""
    id: str = Field(..., description="Article ID in the database")
    content: str = Field(..., description="Article content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    distance: Optional[float] = Field(None, description="Similarity distance (for search results)")


class QueryRequest(BaseModel):
    """Request model for querying articles."""
    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=50)
    filter_category: Optional[str] = Field(None, description="Filter by category")
    filter_date: Optional[str] = Field(None, description="Filter by date")
    filter_persons: Optional[List[str]] = Field(None, description="Filter by persons")


class QueryResponse(BaseModel):
    """Response model for query results."""
    query: str = Field(..., description="Original query")
    results: List[ArticleResponse] = Field(default_factory=list)
    total_results: int = Field(0, description="Total number of results")
    processing_time: float = Field(0.0, description="Query processing time in seconds")


class ScrapingRequest(BaseModel):
    """Request model for scraping newspapers."""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format", example="2024-08-05")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format", example="2024-09-05")
    newspapers: Optional[List[str]] = Field(
        default=["ProthomAlo", "Jugantor", "DailyStar", "DhakaTribune"],
        description="List of newspapers to scrape"
    )
    enable_llm_analysis: Optional[bool] = Field(
        default=False,
        description="Enable LLM analysis (speech summaries and keywords). Warning: Very slow due to API rate limits!"
    )


class ScrapingResponse(BaseModel):
    """Response model for scraping operation."""
    status: str = Field(..., description="Status of scraping operation")
    total_articles_scraped: int = Field(0, description="Total articles scraped")
    total_articles_stored: int = Field(0, description="Total articles stored in database")
    articles_by_source: Dict[str, int] = Field(default_factory=dict, description="Articles count by newspaper")
    processing_time: float = Field(0.0, description="Total processing time in seconds")
    message: str = Field("", description="Additional information")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    total_articles: int = Field(0, description="Total articles in database")
    chromadb_path: Optional[str] = Field(None, description="ChromaDB storage path")


class BulkArticleCreate(BaseModel):
    """Request model for bulk article creation."""
    articles: List[ArticleCreate] = Field(..., description="List of articles to store")


class BulkArticleResponse(BaseModel):
    """Response model for bulk operations."""
    success: bool = Field(..., description="Operation success status")
    inserted_count: int = Field(0, description="Number of articles inserted")
    failed_count: int = Field(0, description="Number of failed insertions")
    article_ids: List[str] = Field(default_factory=list)


# Political Figure and Party Models

class PoliticalFigure(BaseModel):
    """Model for a political figure."""
    name: str = Field(..., description="Name of the political figure")
    party: str = Field(..., description="Political party affiliation")
    article_count: int = Field(0, description="Number of articles mentioning this figure")


class PartyResponse(BaseModel):
    """Response model for a political party."""
    name: str = Field(..., description="Name of the political party")
    full_name: Optional[str] = Field(None, description="Full name of the political party")
    figures: List[str] = Field(default_factory=list, description="List of popular figures in the party")
    total_articles: int = Field(0, description="Total articles related to this party")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    ai_keywords: List[str] = Field(default_factory=list, description="AI-generated keywords")
    ai_topics: List[str] = Field(default_factory=list, description="AI-generated topics")
    last_analyzed: Optional[str] = Field(None, description="Last AI analysis timestamp")


class PartiesListResponse(BaseModel):
    """Response model for list of parties."""
    parties: List[PartyResponse] = Field(default_factory=list)
    total_parties: int = Field(0, description="Total number of parties")


class ArticleSummary(BaseModel):
    """Summary of an article with LLM analysis."""
    id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    date: str = Field(..., description="Publication date")
    source: str = Field(..., description="Article source")
    similarity: float = Field(..., description="Similarity score")
    summary: Optional[str] = Field(None, description="LLM-generated summary")
    key_points: List[str] = Field(default_factory=list, description="Key points from the article")
    stance_analysis: Optional[str] = Field(None, description="Political stance analysis")
    keywords: List[str] = Field(default_factory=list, description="Article keywords")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases")
    topics: List[str] = Field(default_factory=list, description="Main topics")
    url: Optional[str] = Field(None, description="Article URL")


class FigureProfileResponse(BaseModel):
    """Response model for a political figure's profile."""
    figure_name: str = Field(..., description="Name of the political figure")
    party_name: str = Field(..., description="Political party")
    total_articles: int = Field(0, description="Total articles found")
    articles: List[ArticleSummary] = Field(default_factory=list, description="List of articles")
    summaries_by_date: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Summaries organized by date for timeline views"
    )
    figures: Optional[List[str]] = Field(None, description="List of figures in the party (for party profiles)")
    ai_summary: Optional[str] = Field(None, description="AI-generated summary")
    ai_keywords: List[str] = Field(default_factory=list, description="AI-generated keywords")
    ai_topics: List[str] = Field(default_factory=list, description="AI-generated topics")
    last_analyzed: Optional[str] = Field(None, description="Last AI analysis timestamp")
    page: Optional[int] = Field(None, description="Current page number")
    items_per_page: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


class PartyFigureQueryRequest(BaseModel):
    """Request model for querying by party/figure with date range."""
    query: Optional[str] = Field("recent statements", description="Search query")
    date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    speeches_only: bool = Field(False, description="Filter for speeches only")
    top_k: int = Field(10, description="Maximum number of results", ge=1, le=50)


# Category-related Models

class CategoryAnalysisRequest(BaseModel):
    """Request model for category analysis."""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)", example="2024-10-01")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)", example="2024-10-31")
    limit: Optional[int] = Field(100, description="Maximum articles to analyze", ge=1, le=1000)
    force_reclassify: bool = Field(False, description="Force re-classification of already classified articles")


class CategoryInfo(BaseModel):
    """Model for category information."""
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    keywords: List[str] = Field(default_factory=list, description="Category keywords")


class CategoryStatsResponse(BaseModel):
    """Response model for category statistics."""
    success: bool = Field(..., description="Operation success status")
    total_articles: int = Field(0, description="Total articles")
    categorized_articles: int = Field(0, description="Number of categorized articles")
    uncategorized_articles: int = Field(0, description="Number of uncategorized articles")
    category_stats: Dict[str, Any] = Field(default_factory=dict, description="Detailed stats per category")
    top_categories: List[Dict[str, Any]] = Field(default_factory=list, description="Top categories by article count")


class CategoryArticlesResponse(BaseModel):
    """Response model for articles by category."""
    success: bool = Field(..., description="Operation success status")
    category: str = Field(..., description="Category name")
    total_articles: int = Field(0, description="Total matching articles")
    returned_articles: int = Field(0, description="Number of articles in this response")
    offset: int = Field(0, description="Pagination offset")
    limit: int = Field(50, description="Pagination limit")
    articles: List[Dict[str, Any]] = Field(default_factory=list, description="List of articles")

