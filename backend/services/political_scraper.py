"""
Enhanced Scraping Module with Political Storage Integration

Scrapes articles and directly stores them in party-wise collections.
Supports date-range filtering and keyword-based extraction.
"""

import sys
from datetime import datetime
from typing import List, Dict, Optional
import logging

from backend.core.scraping import (
    ProthomAloScraper,
    JugantorScraper, 
    DailyStarScraper,
    DhakaTribuneScraper
)
from backend.services.political_storage import PoliticalArticleStorage, POLITICAL_STRUCTURE# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PoliticalNewsScraper:
    """
    Enhanced scraper that directly stores articles in party-wise collections.
    """
    
    def __init__(
        self,
        start_date: str = "2024-08-05",
        end_date: str = "2025-09-30",
        storage_directory: str = "./political_chroma_db"
    ):
        """
        Initialize the political news scraper.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            storage_directory: Directory for political article storage
        """
        self.start_date = start_date
        self.end_date = end_date
        
        # Initialize storage
        logger.info("Initializing political article storage...")
        self.storage = PoliticalArticleStorage(persist_directory=storage_directory)
        
        # Initialize scrapers
        logger.info(f"Initializing scrapers for date range: {start_date} to {end_date}")
        self.scrapers = {
            "Prothom Alo": ProthomAloScraper(start_date, end_date),
            "Jugantor": JugantorScraper(start_date, end_date),
            "Daily Star": DailyStarScraper(start_date, end_date),
            "Dhaka Tribune": DhakaTribuneScraper(start_date, end_date)
        }
        
        logger.info(f"Initialized {len(self.scrapers)} newspaper scrapers")
    
    def scrape_newspaper(
        self,
        newspaper_name: str,
        party_id: Optional[str] = None,
        figure_name: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Scrape a specific newspaper and store articles.
        
        Args:
            newspaper_name: Name of the newspaper
            party_id: Optional party filter
            figure_name: Optional figure filter
            
        Returns:
            Statistics dictionary
        """
        if newspaper_name not in self.scrapers:
            logger.error(f"Unknown newspaper: {newspaper_name}")
            return {"error": "Unknown newspaper"}
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scraping {newspaper_name}")
        logger.info(f"Date Range: {self.start_date} to {self.end_date}")
        if party_id:
            logger.info(f"Party Filter: {POLITICAL_STRUCTURE[party_id]['name']}")
        if figure_name:
            logger.info(f"Figure Filter: {figure_name}")
        logger.info(f"{'='*60}\n")
        
        scraper = self.scrapers[newspaper_name]
        
        try:
            # Scrape articles
            articles = scraper.scrape()
            logger.info(f"Scraped {len(articles)} articles from {newspaper_name}")
            
            if not articles:
                logger.warning(f"No articles found for {newspaper_name}")
                return {"scraped": 0, "stored": 0}
            
            # Filter by party/figure if specified
            if party_id or figure_name:
                filtered_articles = []
                for article in articles:
                    detection = self.storage.detect_party_and_figures(
                        article.get("content", ""),
                        article.get("title", "")
                    )
                    
                    if detection:
                        # Check party filter
                        if party_id and detection["party_id"] != party_id:
                            continue
                        
                        # Check figure filter
                        if figure_name:
                            if figure_name not in detection["mentioned_figures"]:
                                continue
                        
                        filtered_articles.append(article)
                
                logger.info(f"Filtered to {len(filtered_articles)} articles")
                articles = filtered_articles
            
            # Store articles
            if articles:
                stats = self.storage.store_articles_bulk(articles, party_id)
                total_stored = sum(s["success"] for s in stats.values())
                logger.info(f"Stored {total_stored} articles from {newspaper_name}")
                return {
                    "scraped": len(articles),
                    "stored": total_stored,
                    "party_stats": stats
                }
            else:
                return {"scraped": 0, "stored": 0}
                
        except Exception as e:
            logger.error(f"Error scraping {newspaper_name}: {str(e)}")
            return {"error": str(e)}
    
    def scrape_all_newspapers(
        self,
        party_id: Optional[str] = None,
        figure_name: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Scrape all newspapers and store articles.
        
        Args:
            party_id: Optional party filter
            figure_name: Optional figure filter
            
        Returns:
            Statistics dictionary for each newspaper
        """
        logger.info("\n" + "="*60)
        logger.info("STARTING COMPREHENSIVE SCRAPING")
        logger.info(f"Date Range: {self.start_date} to {self.end_date}")
        if party_id:
            logger.info(f"Party Filter: {POLITICAL_STRUCTURE[party_id]['name']}")
        if figure_name:
            logger.info(f"Figure Filter: {figure_name}")
        logger.info("="*60 + "\n")
        
        all_stats = {}
        
        for newspaper_name in self.scrapers:
            stats = self.scrape_newspaper(newspaper_name, party_id, figure_name)
            all_stats[newspaper_name] = stats
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("SCRAPING SUMMARY")
        logger.info("="*60)
        
        total_scraped = 0
        total_stored = 0
        
        for newspaper, stats in all_stats.items():
            scraped = stats.get("scraped", 0)
            stored = stats.get("stored", 0)
            total_scraped += scraped
            total_stored += stored
            logger.info(f"{newspaper}: {scraped} scraped, {stored} stored")
        
        logger.info(f"\nTOTAL: {total_scraped} scraped, {total_stored} stored")
        logger.info("="*60 + "\n")
        
        # Print storage statistics
        storage_stats = self.storage.get_all_statistics()
        logger.info("\n=== Political Storage Statistics ===")
        logger.info(f"Total Articles in Database: {storage_stats['total_articles']}")
        for party_id_key, party_stats in storage_stats["parties"].items():
            logger.info(f"\n{party_stats['party_name']}:")
            logger.info(f"  Total Articles: {party_stats['total_articles']}")
            if party_stats.get("figure_article_counts"):
                logger.info(f"  Figure Distribution:")
                for figure, count in party_stats["figure_article_counts"].items():
                    if count > 0:
                        logger.info(f"    - {figure}: {count}")
        logger.info("=" * 36)
        
        return all_stats
    
    def scrape_by_party(self, party_id: str) -> Dict[str, Dict]:
        """
        Scrape all newspapers for a specific party.
        
        Args:
            party_id: Party identifier
            
        Returns:
            Statistics dictionary
        """
        if party_id not in POLITICAL_STRUCTURE:
            logger.error(f"Invalid party_id: {party_id}")
            return {"error": "Invalid party_id"}
        
        logger.info(f"\nScraping for: {POLITICAL_STRUCTURE[party_id]['name']}")
        return self.scrape_all_newspapers(party_id=party_id)
    
    def scrape_by_figure(self, figure_name: str, party_id: Optional[str] = None) -> Dict[str, Dict]:
        """
        Scrape all newspapers for a specific political figure.
        
        Args:
            figure_name: Name of the political figure
            party_id: Optional party to restrict search
            
        Returns:
            Statistics dictionary
        """
        logger.info(f"\nScraping for: {figure_name}")
        return self.scrape_all_newspapers(party_id=party_id, figure_name=figure_name)
    
    def get_storage_statistics(self) -> Dict:
        """Get statistics for all stored articles."""
        return self.storage.get_all_statistics()


def main():
    """Command-line interface for political news scraping."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Scrape political news and store in party-wise collections"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-08-05",
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2025-09-30",
        help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--newspaper",
        type=str,
        choices=["Prothom Alo", "Jugantor", "Daily Star", "Dhaka Tribune", "all"],
        default="all",
        help="Newspaper to scrape"
    )
    parser.add_argument(
        "--party",
        type=str,
        choices=list(POLITICAL_STRUCTURE.keys()),
        help="Filter by political party"
    )
    parser.add_argument(
        "--figure",
        type=str,
        help="Filter by political figure name"
    )
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="./political_chroma_db",
        help="Directory for article storage"
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only show storage statistics"
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = PoliticalNewsScraper(
        start_date=args.start_date,
        end_date=args.end_date,
        storage_directory=args.storage_dir
    )
    
    # Show stats only
    if args.stats_only:
        stats = scraper.get_storage_statistics()
        print("\n=== Political Storage Statistics ===")
        print(f"Total Articles: {stats['total_articles']}")
        print(f"Total Collections: {stats['total_collections']}")
        for party_id, party_stats in stats["parties"].items():
            print(f"\n{party_stats['party_name']}:")
            print(f"  Total Articles: {party_stats['total_articles']}")
            if party_stats.get("figure_article_counts"):
                print(f"  Figure Distribution:")
                for figure, count in party_stats["figure_article_counts"].items():
                    if count > 0:
                        print(f"    - {figure}: {count}")
        return
    
    # Scrape newspapers
    if args.newspaper == "all":
        scraper.scrape_all_newspapers(party_id=args.party, figure_name=args.figure)
    else:
        scraper.scrape_newspaper(args.newspaper, party_id=args.party, figure_name=args.figure)


if __name__ == "__main__":
    main()
