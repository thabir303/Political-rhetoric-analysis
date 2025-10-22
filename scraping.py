"""
Web scraping module for Bangladeshi newspapers.

Scrapes articles from Prothom Alo, Jugantor, Daily Star, and Dhaka Tribune
that mention specific political figures and parties between specified dates.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import time
import logging
from urllib.parse import urljoin, urlparse
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Political figures and parties to track
# Canonical English names only for categorization test comparison
POLITICAL_ENTITIES = {
    "BNP": ["Tareq Rahman", "Mirza Fakhrul", "Salahuddin Ahmed"],
    "JI": ["Shafiqur Rahman", "Abu Taher", "Golam Parwar"],
    "NCP": ["Nahid Islam", "Sarjis Alam", "Hasnat Abdullah", "Nasiruddin Patwary", "Akhter Hossain", "Tasnim Zara"],
    "AB Party": ["Barrister Fuad"],
    "GOP": ["Nurul Haque", "Rashed"],
    "Gono Songhati": ["Jonayed Saki"],
    "Interim Government": [
        "Dr Yunus", "Shafiqul Alam", "Mahfuz Alam", "Asif Nazrul", "Rizwana Hasan",
        "Lt Gen Jahangir Alam Chowdhury", "Ali Riaz", "Badiul Alam Majumder", 
        "AMM Nasir Uddin", "General Waqar Uz Zaman", "IGP Baharul Alam", 
        "DMP Commissioner Sajjat Ali", "Mahfuz Anam", "Mahmudur Rahman"
    ]
}

# Full search list with Bangla variants for article detection
ALL_POLITICAL_FIGURES = {
    "BNP": ["Tareq Rahman", "Mirza Fakhrul", "Salahuddin Ahmed", "তারেক রহমান", "মির্জা ফখরুল", "সালাউদ্দিন আহমেদ"],
    "JI": ["Shafiqur Rahman", "Abu Taher", "Golam Parwar", "শফিকুর রহমান", "আবু তাহের", "গোলাম পারওয়ার"],
    "NCP": ["Nahid Islam", "Sarjis Alam", "Hasnat Abdullah", "Nasiruddin Patwary", "Akhter Hossain", 
            "Tasnim Zara", "নাহিদ ইসলাম", "সরজিস আলম", "হাসনাত আবদুল্লাহ", "নাসিরউদ্দিন পাটোয়ারী"],
    "AB Party": ["Barrister Fuad", "ব্যারিস্টার ফুয়াদ"],
    "GOP": ["Nurul Haque", "Rashed", "নুরুল হক", "রাশেদ"],
    "Gono Songhati": ["Jonayed Saki", "জোনায়েদ সাকী"],
    "Interim Government": [
        "Dr. Yunus", "Dr Yunus", "Shafiqul Alam", "Mahfuz Alam", "Asif Nazrul", "Rizwana Hasan",
        "Lt Gen Jahangir Alam Chowdhury", "Ali Riaz", "Badiul Alam Majumder", 
        "AMM Nasir Uddin", "General Waqar Uz Zaman", "IGP Baharul Alam", 
        "DMP Commissioner Sajjat Ali", "Mahfuz Anam", "Mahmudur Rahman",
        "ড. ইউনূস", "ড ইউনূস", "শফিকুল আলম", "মাহফুজ আলম", "আসিফ নজরুল", "রিজওয়ানা হাসান",
        "জাহাঙ্গীর আলম চৌধুরী", "বদিউল আলম মজুমদার", "ওয়াকার উজ জামান", 
        "বেনজীর আহমেদ", "মাহফুজ আনাম", "মাহমুদুর রহমান"
    ]
}

# Flatten all entities for easier searching
ALL_ENTITIES = []
for party, members in ALL_POLITICAL_FIGURES.items():
    ALL_ENTITIES.extend(members)


class NewspaperScraper:
    """Base class for newspaper scrapers."""
    
    def __init__(self, start_date: str = "2024-08-05", end_date: str = "2025-09-30"):
        """
        Initialize scraper with date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Note: For Prothom Alo, the API returns a mix of recent and older articles.
              Date filtering is applied after fetching to ensure we get relevant content.
        """
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        logger.info(f"Initialized scraper for date range: {start_date} to {end_date}")
    
    def check_mentions(self, text: str) -> List[str]:
        """
        Check if text mentions any political entities.
        
        Args:
            text: Text to search
            
        Returns:
            List of mentioned parties
        """
        if not text:
            return []
        
        text_lower = text.lower()
        mentions = []
        
        for entity in ALL_ENTITIES:
            # Case-insensitive search for both English and Bangla
            if entity.lower() in text_lower:
                # Find which party this entity belongs to
                for party, members in ALL_POLITICAL_FIGURES.items():
                    if entity in members:
                        if party not in mentions:
                            mentions.append(party)
                        break
        
        return mentions
    
    def is_within_date_range(self, article_date: datetime) -> bool:
        """Check if article date is within specified range."""
        return self.start_date <= article_date <= self.end_date
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make HTTP request with retries.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response object or None
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
        return None


class ProthomAloScraper(NewspaperScraper):
    """Scraper for Prothom Alo (Bangla) - Politics and Opinion only."""
    
    BASE_URL = "https://www.prothomalo.com"
    API_URL = "https://www.prothomalo.com/api/v1"
    
    def scrape_articles(self) -> List[Dict]:
        """
        Scrape articles from Prothom Alo using their API.
        
        Returns:
            List of article dictionaries
        """
        logger.info("Starting Prothom Alo scraping...")
        articles = []
        
        # Use the API endpoint for stories
        # The API returns JSON with article data
        api_endpoints = [
            f"{self.API_URL}/collections/politics",
            f"{self.API_URL}/stories?section=politics&limit=100",
        ]
        
        for api_url in api_endpoints:
            logger.info(f"Fetching from API: {api_url}")
            
            response = self.make_request(api_url)
            if not response:
                continue
            
            try:
                data = response.json()
                
                # Handle different response structures
                stories = []
                if 'stories' in data:
                    stories = data['stories']
                elif 'items' in data:
                    # Collection endpoint returns items
                    items = data.get('items', [])
                    for item in items:
                        if item.get('type') == 'story':
                            stories.append(item.get('story', {}))
                
                logger.info(f"Found {len(stories)} stories from API")
                
                for story_data in stories:  # Process all articles from API
                    article_data = self.parse_story_from_api(story_data)
                    
                    if article_data:
                        articles.append(article_data)
                        logger.info(f"Parsed: {article_data['title'][:50]}...")
                    
                    time.sleep(0.2)  # Be respectful
                    
            except Exception as e:
                logger.error(f"Error parsing API response from {api_url}: {e}")
                continue
        
        logger.info(f"Prothom Alo: Scraped {len(articles)} articles")
        return articles
    
    def parse_story_from_api(self, story_data: Dict) -> Optional[Dict]:
        """
        Parse story data from Prothom Alo API response.
        
        Args:
            story_data: Story dictionary from API
            
        Returns:
            Article data dictionary or None
        """
        try:
            # Extract basic info
            title = story_data.get('headline', '')
            if not title:
                return None
            
            # Get URL
            url = story_data.get('url', '')
            if not url:
                slug = story_data.get('slug', '')
                if slug:
                    url = f"{self.BASE_URL}/{slug}"
                else:
                    return None
            
            # Parse date
            published_at = story_data.get('published-at') or story_data.get('first-published-at')
            if not published_at:
                return None
            
            # Convert timestamp (milliseconds) to datetime
            article_date = datetime.fromtimestamp(published_at / 1000)
            
            # Check date range
            if not self.is_within_date_range(article_date):
                logger.debug(f"Article date {article_date} outside range")
                return None
            
            # Get content - fetch the full article
            logger.info(f"Fetching full content for: {title[:50]}...")
            content = self.fetch_article_content(url)
            
            if not content or len(content) < 100:
                # Try to use excerpt as fallback
                metadata = story_data.get('metadata', {})
                excerpt = metadata.get('excerpt', '') or story_data.get('subheadline', '')
                if len(excerpt) > 100:
                    content = excerpt
                else:
                    logger.warning(f"Insufficient content for {url}")
                    return None
            
            # Check for political mentions
            combined_text = f"{title} {content}"
            mentions = self.check_mentions(combined_text)
            
            if not mentions:
                logger.debug(f"No political mentions in {url}")
                return None
            
            # Extract category
            sections = story_data.get('sections', [])
            category = sections[0].get('display-name', 'general') if sections else 'general'
            
            return {
                'title': title,
                'date': article_date.strftime('%Y-%m-%d'),
                'content': content,
                'url': url,
                'mentions': mentions,
                'source': 'Prothom Alo',
                'language': 'Bangla',
                'category': category
            }
            
        except Exception as e:
            logger.error(f"Error parsing story data: {e}")
            return None
    
    def fetch_article_content(self, url: str) -> str:
        """
        Fetch full article content from article URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article content as string
        """
        response = self.make_request(url)
        if not response:
            return ""
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find content in common locations
            content_parts = []
            
            # Look for paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Skip very short paragraphs
                    content_parts.append(text)
            
            return ' '.join(content_parts)  # No limit on paragraphs
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return ""


class JugantorScraper(NewspaperScraper):
    """Scraper for Jugantor (Bangla) - Politics only using archive system."""
    
    BASE_URL = "https://www.jugantor.com"
    ARCHIVE_BASE_URL = "https://www.jugantor.com/archive"
    
    def scrape_articles(self) -> List[Dict]:
        """
        Scrape articles from Jugantor archive for politics category.
        
        Returns:
            List of article dictionaries
        """
        logger.info("Starting Jugantor archive scraping (Politics only)...")
        logger.info(f"Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        
        all_articles = []
        
        # Generate list of dates to scrape
        current_date = self.start_date
        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Scraping articles for date: {date_str}")
            
            articles = self.scrape_articles_for_date(date_str)
            all_articles.extend(articles)
            
            # Add delay between dates
            time.sleep(2)
            
            # Move to next date
            current_date += timedelta(days=1)
        
        logger.info(f"Jugantor: Scraped {len(all_articles)} total articles")
        return all_articles
    
    def get_archive_url(self, date: str, page: int = None) -> str:
        """
        Generate archive URL for a specific date and page.
        
        Args:
            date: Date in YYYY-MM-DD format
            page: Page number (None or 1 for first page)
            
        Returns:
            Archive URL string
        """
        date_from = f"{date}+00%3A00"
        date_to = f"{date}+23%3A55"
        
        if page is None or page == 1:
            # First page has no page parameter
            return f"{self.ARCHIVE_BASE_URL}?search=yes&headline=&dateFrom={date_from}&dateTo={date_to}&newsType="
        else:
            # Subsequent pages have page parameter
            return f"{self.ARCHIVE_BASE_URL}?search=yes&headline=&dateFrom={date_from}&dateTo={date_to}&newsType=&page={page}"
    
    def extract_article_links(self, archive_url: str) -> List[str]:
        """
        Extract article links from archive page, filtering for politics only.
        
        Args:
            archive_url: Archive page URL
            
        Returns:
            List of article URLs
        """
        response = self.make_request(archive_url)
        if not response:
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            article_links = []
            
            # Based on archive structure, articles are in .media.positionRelative divs
            article_containers = soup.find_all('div', class_='media positionRelative')
            
            for container in article_containers:
                # Find the linkOverlay link
                link_elem = container.find('a', class_='linkOverlay')
                if link_elem and link_elem.get('href'):
                    href = link_elem.get('href')
                    full_url = urljoin(self.BASE_URL, href)
                    
                    # Filter for politics articles only
                    if '/politics/' in full_url and full_url not in article_links:
                        article_links.append(full_url)
            
            # If no links found with specific structure, try alternative selectors
            if not article_links:
                selectors = [
                    '.linkOverlay',
                    'h4 a',
                    '.title10 a',
                    'a[href*="/politics/"]'
                ]
                
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.BASE_URL, href)
                            # Filter for politics URLs only
                            if '/politics/' in full_url and full_url not in article_links:
                                article_links.append(full_url)
            
            return article_links
            
        except Exception as e:
            logger.error(f"Error extracting article links from {archive_url}: {e}")
            return []
    
    def scrape_articles_for_date(self, date: str) -> List[Dict]:
        """
        Scrape all politics articles for a specific date across all pages.
        
        Args:
            date: Date in YYYY-MM-DD format
            
        Returns:
            List of article dictionaries
        """
        all_articles = []
        page = 1
        max_pages = 100  # Increased page limit for more comprehensive scraping
        
        while page <= max_pages:
            logger.info(f"  Processing page {page} for {date}")
            
            # Get archive URL for this page
            archive_url = self.get_archive_url(date, page)
            
            # Extract article links from this page (politics only)
            article_links = self.extract_article_links(archive_url)
            
            if not article_links:
                logger.info(f"    No politics articles found on page {page} for {date}")
                break
            
            logger.info(f"    Found {len(article_links)} politics articles on page {page}")
            
            # Extract content from each article
            for i, article_url in enumerate(article_links):
                logger.info(f"      Scraping article {i+1}/{len(article_links)}: {article_url}")
                
                article_data = self.scrape_article(article_url, date)
                if article_data:
                    all_articles.append(article_data)
                
                # Add delay to be respectful to the server
                time.sleep(1)
            
            # Move to next page
            page += 1
            
            # Add delay between pages
            time.sleep(2)
        
        logger.info(f"  Total politics articles scraped for {date}: {len(all_articles)}")
        return all_articles
    
    def clean_content(self, content: str) -> str:
        """
        Clean the content by removing unwanted parts.
        
        Args:
            content: Raw content string
            
        Returns:
            Cleaned content string
        """
        if not content:
            return content
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'ফলো করুন.*?যুগান্তর মেসেঞ্জার',  # Social media buttons
            r'যুগান্তর প্রতিবেদন.*?পিএম',  # Reporter info and timestamp
            r'আরও পড়ুন.*?সম্পর্কিত খবর',  # "Read more" and related news
            r'সর্বশেষ.*?সব খবর',  # Navigation elements
            r'প্রকাশ:.*?পিএম',  # Publication timestamps
            r'সম্পর্কিত খবর.*',  # Related news sections
            r'যুগান্তর.*?হোয়াটসঅ্যাপ.*?মেসেঞ্জার',  # Social media links
        ]
        
        # Apply all patterns
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        # Remove everything from "মেসেঞ্জার" at start if present
        if "মেসেঞ্জার" in content[:200]:  # Only check first 200 chars
            start_pos = content.find("মেসেঞ্জার")
            if start_pos != -1:
                content = content[start_pos + len("মেসেঞ্জার"):]
        
        # Remove everything from "সম্পর্কিত খবর" onwards
        if "সম্পর্কিত খবর" in content:
            end_pos = content.find("সম্পর্কিত খবর")
            if end_pos != -1:
                content = content[:end_pos]
        
        # Remove extra whitespace and newlines
        content = re.sub(r'\n+', '\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
    
    def scrape_article(self, url: str, date: str) -> Optional[Dict]:
        """
        Scrape individual article from Jugantor.
        
        Args:
            url: Article URL
            date: Date string in YYYY-MM-DD format
            
        Returns:
            Article data dictionary or None
        """
        response = self.make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1', class_='article-title') or soup.find('h1') or soup.find('h2', class_=re.compile(r'title|headline'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Extract content - try multiple approaches
            content_parts = []
            
            # Try article/story div first
            content_selectors = [
                '.article-content',
                '.content',
                '.article-body',
                '.story-content',
                '.article-text',
                '.news-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content_parts = [p.get_text(strip=True) for p in content_elem.find_all('p') if len(p.get_text(strip=True)) > 20]
                    break
            
            # Fallback: get all paragraphs
            if not content_parts:
                main_content = soup.find('main') or soup.find('body')
                if main_content:
                    # Remove navigation, ads, etc.
                    for elem in main_content.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                        elem.decompose()
                    
                    paragraphs = main_content.find_all(['p', 'div'])
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 30:
                            content_parts.append(text)
            
            content = '\n\n'.join(content_parts)
            
            # Clean the content
            content = self.clean_content(content)
            
            if not content or len(content) < 100:
                logger.warning(f"Insufficient content for {url}")
                return None
            
            # Check mentions
            combined_text = f"{title} {content}"
            mentions = self.check_mentions(combined_text)
            
            if not mentions:
                logger.debug(f"No political mentions in {url}")
                return None
            
            # Extract author
            author = ""
            author_selectors = ['.author', '.byline', '.writer', '.reporter']
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break
            
            # Extract category
            category = "politics"  # Default to politics since we're filtering for it
            category_elem = soup.find('a', class_=re.compile(r'category'))
            if category_elem:
                category = category_elem.get_text(strip=True)
            
            return {
                'title': title,
                'date': date,
                'content': content,
                'url': url,
                'mentions': mentions,
                'source': 'Jugantor',
                'language': 'Bangla',
                'category': category,
                'author': author if author else None
            }
            
        except Exception as e:
            logger.error(f"Error scraping Jugantor article {url}: {e}")
            return None


class DailyStarScraper(NewspaperScraper):
    """Scraper for The Daily Star (English) - Politics and Opinion only."""
    
    BASE_URL = "https://www.thedailystar.net"
    
    def scrape_articles(self) -> List[Dict]:
        """
        Scrape articles from The Daily Star.
        
        Returns:
            List of article dictionaries
        """
        logger.info("Starting Daily Star scraping...")
        articles = []
        
        # Multiple politics-related URLs as requested
        category_urls = [
            f"{self.BASE_URL}/news/bangladesh/politics",
            f"{self.BASE_URL}/opinion/views/politics",
            f"{self.BASE_URL}/tags/bangladesh-politics"
        ]
        
        for category_url in category_urls:
            logger.info(f"Scraping URL: {category_url}")
            
            response = self.make_request(category_url)
            if not response:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            article_links = soup.find_all('a', href=re.compile(r'/.+/\d+'))
            
            for link in article_links:  # Remove 50-article limit per page
                article_url = urljoin(self.BASE_URL, link.get('href'))
                article_data = self.scrape_article(article_url)
                
                if article_data:
                    articles.append(article_data)
                    logger.info(f"Scraped: {article_data['title'][:50]}...")
                
                time.sleep(0.5)
        
        logger.info(f"Daily Star: Scraped {len(articles)} articles")
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """
        Scrape individual article from Daily Star.
        
        Args:
            url: Article URL
            
        Returns:
            Article data dictionary or None
        """
        response = self.make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|publish'))
            date_str = date_elem.get('datetime', '') if date_elem else ""
            
            article_date = None
            if date_str:
                try:
                    article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            if not article_date or not self.is_within_date_range(article_date):
                return None
            
            # Extract content
            content_divs = soup.find_all(['p'], class_=re.compile(r'content|body|text'))
            if not content_divs:
                content_divs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in content_divs])
            
            # Check mentions
            combined_text = f"{title} {content}"
            mentions = self.check_mentions(combined_text)
            
            if not mentions:
                return None
            
            # Extract author
            author_elem = soup.find('span', class_=re.compile(r'author'))
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            category_elem = soup.find('a', class_=re.compile(r'category'))
            category = category_elem.get_text(strip=True) if category_elem else "general"
            
            return {
                'title': title,
                'date': article_date.strftime('%Y-%m-%d'),
                'content': content,
                'url': url,
                'mentions': mentions,
                'source': 'Daily Star',
                'language': 'English',
                'category': category,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Error scraping Daily Star article {url}: {e}")
            return None


class DhakaTribuneScraper(NewspaperScraper):
    """Scraper for Dhaka Tribune (English) - Politics only."""
    
    BASE_URL = "https://www.dhakatribune.com"
    
    def scrape_articles(self) -> List[Dict]:
        """
        Scrape articles from Dhaka Tribune.
        
        Returns:
            List of article dictionaries
        """
        logger.info("Starting Dhaka Tribune scraping...")
        articles = []
        
        # Only politics URL as requested
        categories = ["bangladesh/politics"]
        
        for category in categories:
            category_url = f"{self.BASE_URL}/{category}"
            logger.info(f"Scraping category: {category_url}")
            
            response = self.make_request(category_url)
            if not response:
                continue
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links - Dhaka Tribune uses /bangladesh/politics/ID/slug pattern
            seen_urls = set()
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                
                # Skip invalid URLs
                if href.startswith('http://'):
                    continue
                    
                # Match article patterns
                if '/bangladesh/politics/' in href and len(href) > 40:
                    if href.startswith('https://'):
                        article_url = href
                    elif href.startswith('//'):
                        article_url = 'https:' + href
                    elif href.startswith('/'):
                        article_url = f"{self.BASE_URL}{href}"
                    else:
                        continue
                    
                    if article_url in seen_urls:
                        continue
                    seen_urls.add(article_url)
                    
                    article_data = self.scrape_article(article_url)
                    
                    if article_data:
                        articles.append(article_data)
                        logger.info(f"Parsed: {article_data['title'][:50]}...")
                    
                    time.sleep(0.3)
                    
                    # Removed 50-article limit per category
        
        logger.info(f"Dhaka Tribune: Scraped {len(articles)} articles")
        return articles
    
    def scrape_article(self, url: str) -> Optional[Dict]:
        """
        Scrape individual article from Dhaka Tribune.
        
        Args:
            url: Article URL
            
        Returns:
            Article data dictionary or None
        """
        response = self.make_request(url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_=re.compile(r'date|time'))
            date_str = date_elem.get('datetime', '') if date_elem else ""
            
            article_date = None
            if date_str:
                try:
                    article_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            if not article_date or not self.is_within_date_range(article_date):
                return None
            
            # Extract content
            content_divs = soup.find_all(['p'], class_=re.compile(r'content|paragraph'))
            if not content_divs:
                content_divs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in content_divs])
            
            # Check mentions
            combined_text = f"{title} {content}"
            mentions = self.check_mentions(combined_text)
            
            if not mentions:
                return None
            
            # Extract author
            author_elem = soup.find('a', class_=re.compile(r'author')) or soup.find('span', class_=re.compile(r'author'))
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            category_elem = soup.find('a', class_=re.compile(r'category'))
            category = category_elem.get_text(strip=True) if category_elem else "general"
            
            return {
                'title': title,
                'date': article_date.strftime('%Y-%m-%d'),
                'content': content,
                'url': url,
                'mentions': mentions,
                'source': 'Dhaka Tribune',
                'language': 'English',
                'category': category,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Error scraping Dhaka Tribune article {url}: {e}")
            return None


def scrape_all_newspapers(start_date: str = "2024-08-05", end_date: str = "2025-09-30") -> List[Dict]:
    """
    Scrape articles from all newspapers.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        List of all scraped articles
    """
    all_articles = []
    
    # Initialize scrapers
    scrapers = [
        ProthomAloScraper(start_date, end_date),
        JugantorScraper(start_date, end_date),
        DailyStarScraper(start_date, end_date),
        DhakaTribuneScraper(start_date, end_date)
    ]
    
    # Scrape from each source
    for scraper in scrapers:
        try:
            articles = scraper.scrape_articles()
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Error with {scraper.__class__.__name__}: {e}")
    
    logger.info(f"Total articles scraped: {len(all_articles)}")
    return all_articles


def save_articles_to_vector_db(articles: List[Dict]):
    """
    Save scraped articles to the vector database.
    
    Args:
        articles: List of article dictionaries
    """
    from database import vector_store
    
    logger.info(f"Saving {len(articles)} articles to vector database...")
    
    for article in articles:
        try:
            # Prepare metadata
            metadata = {
                'date': article['date'],
                'category': article.get('category', 'general'),
                'persons': ', '.join(article['mentions']),
                'source': article['source'],
                'title': article['title'],
                'language': article.get('language', 'Unknown'),
                'url': article['url']
            }
            
            if 'author' in article and article['author']:
                metadata['author'] = article['author']
            
            # Add to vector database
            vector_store.add_article(
                content=article['content'],
                metadata=metadata
            )
            
            logger.info(f"Saved: {article['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving article to database: {e}")
    
    logger.info("Finished saving articles to database")


if __name__ == "__main__":
    # Example usage
    print("Starting newspaper scraping...")
    print("=" * 80)
    
    # Scrape articles
    articles = scrape_all_newspapers()
    
    print(f"\nScraped {len(articles)} articles total")
    print("\nSample articles:")
    for i, article in enumerate(articles[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']} | Date: {article['date']}")
        print(f"   Mentions: {', '.join(article['mentions'])}")
        print(f"   URL: {article['url']}")
    
    # Save to database
    if articles:
        print("\n" + "=" * 80)
        save_choice = input("Save articles to vector database? (y/n): ")
        if save_choice.lower() == 'y':
            save_articles_to_vector_db(articles)
            print("Articles saved successfully!")
    
    print("\nScraping complete!")
