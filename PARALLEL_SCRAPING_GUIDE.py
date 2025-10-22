"""
Enhanced JugantorScraper with Parallel Processing

Add these imports at the top of scraping.py:
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Then modify JugantorScraper class:

class JugantorScraper(NewspaperScraper):
    """Scraper with parallel processing support."""
    
    def __init__(self, start_date, end_date, max_workers=3, max_article_workers=2):
        super().__init__(start_date, end_date)
        self.max_workers = max_workers
        self.max_article_workers = max_article_workers
        self.lock = threading.Lock()
    
    def scrape_articles_parallel(self) -> List[Dict]:
        """
        Scrape articles using parallel processing.
        
        Returns:
            List of article dictionaries
        """
        logger.info("Starting parallel Jugantor scraping...")
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Max workers: {self.max_workers} dates, {self.max_article_workers} articles")
        
        all_articles = []
        
        # Generate list of dates
        dates = []
        current_date = self.start_date
        while current_date <= self.end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Process dates in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_date = {
                executor.submit(self.scrape_articles_for_date, date): date 
                for date in dates
            }
            
            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    articles = future.result()
                    with self.lock:  # Thread-safe append
                        all_articles.extend(articles)
                    logger.info(f"✓ Completed scraping for {date}: {len(articles)} articles")
                except Exception as e:
                    logger.error(f"Error scraping {date}: {e}")
        
        logger.info(f"Jugantor: Scraped {len(all_articles)} total articles")
        return all_articles
    
    def scrape_articles_for_date_parallel(self, date: str) -> List[Dict]:
        """
        Scrape articles for a specific date with parallel article extraction.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        page = 1
        max_pages = 100
        
        while page <= max_pages:
            logger.info(f"  Processing page {page} for {date}")
            
            archive_url = self.get_archive_url(date, page)
            article_links = self.extract_article_links(archive_url)
            
            if not article_links:
                break
            
            logger.info(f"    Found {len(article_links)} articles on page {page}")
            
            # Extract articles in parallel
            with ThreadPoolExecutor(max_workers=self.max_article_workers) as executor:
                future_to_url = {
                    executor.submit(self.scrape_article, url, date): url 
                    for url in article_links
                }
                
                for future in as_completed(future_to_url):
                    article_url = future_to_url[future]
                    try:
                        article_data = future.result()
                        if article_data:
                            all_articles.append(article_data)
                    except Exception as e:
                        logger.error(f"Error scraping {article_url}: {e}")
            
            page += 1
            time.sleep(2)
        
        return all_articles


# Usage in scraping route:
# Instead of: scraper.scrape_articles()
# Use:        scraper.scrape_articles_parallel()
