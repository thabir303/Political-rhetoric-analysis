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


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    total_articles: int = Field(0, description="Total articles in database")


class BulkArticleCreate(BaseModel):
    """Request model for bulk article creation."""
    articles: List[ArticleCreate] = Field(..., description="List of articles to store")


class BulkArticleResponse(BaseModel):
    """Response model for bulk operations."""
    success: bool = Field(..., description="Operation success status")
    inserted_count: int = Field(0, description="Number of articles inserted")
    failed_count: int = Field(0, description="Number of failed insertions")
    article_ids: List[str] = Field(default_factory=list)
