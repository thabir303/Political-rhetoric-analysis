"""
Quick Scraping Test - Check if newspapers are accessible and scraping works

Run: python scripts/quick_scraping_test.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping import ProthomAloScraper, DailyStarScraper, JugantorScraper, DhakaTribuneScraper

print("=" * 80)
print("NEWSPAPER SCRAPING TEST")
print("=" * 80)

# Test each newspaper scraper
scrapers = [
    ("📰 Prothom Alo (Bangla)", ProthomAloScraper("2024-08-05", "2025-09-30")),
    ("📰 Daily Star (English)", DailyStarScraper("2024-08-05", "2025-09-30")),
    ("📰 Jugantor (Bangla)", JugantorScraper("2024-08-05", "2025-09-30")),
    ("📰 Dhaka Tribune (English)", DhakaTribuneScraper("2024-08-05", "2025-09-30"))
]

total_articles = 0

for name, scraper in scrapers:
    print(f"\n{'-' * 80}")
    print(f"Testing: {name}")
    print('-' * 80)
    
    try:
        print(f"Scraping... (limiting to 2 articles for test)")
        articles = scraper.scrape_articles()
        
        # Limit to 2 for quick test
        articles = articles[:2]
        
        print(f"✓ Success! Found {len(articles)} articles\n")
        
        for i, article in enumerate(articles, 1):
            print(f"  Article {i}:")
            print(f"  ├─ Title: {article.get('title', 'N/A')[:70]}...")
            print(f"  ├─ Date: {article.get('date', 'N/A')}")
            print(f"  ├─ Source: {article.get('source', 'N/A')}")
            print(f"  ├─ Language: {article.get('language', 'N/A')}")
            print(f"  ├─ Parties: {', '.join(article.get('parties', [])) or 'None detected'}")
            print(f"  ├─ People: {', '.join(article.get('people', [])) or 'None detected'}")
            print(f"  └─ Content: {len(article.get('content', ''))} characters")
            print()
        
        total_articles += len(articles)
        
    except Exception as e:
        print(f"✗ Error: {str(e)}\n")
        continue

print("=" * 80)
print(f"SUMMARY: Successfully scraped {total_articles} articles across all newspapers")
print("=" * 80)
