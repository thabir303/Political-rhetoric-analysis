"""
Utility script to run the newspaper scraper and save articles to the database.

This script provides a command-line interface for scraping articles from
Bangladeshi newspapers and storing them in the vector database.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping import (
    scrape_all_newspapers,
    save_articles_to_vector_db,
    ProthomAloScraper,
    JugantorScraper,
    DailyStarScraper,
    DhakaTribuneScraper
)


def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(
        description='Scrape articles from Bangladeshi newspapers'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default='2024-08-05',
        help='Start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default='2025-09-30',
        help='End date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--source',
        type=str,
        choices=['all', 'prothomalo', 'jugantor', 'dailystar', 'dhakatribune'],
        default='all',
        help='Newspaper source to scrape'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Automatically save to database'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Save results to JSON file'
    )
    
    parser.add_argument(
        '--max-articles',
        type=int,
        default=200,
        help='Maximum articles to scrape per source'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Bangladeshi Newspaper Scraper")
    print("=" * 80)
    print(f"Date range: {args.start_date} to {args.end_date}")
    print(f"Source: {args.source}")
    print("=" * 80)
    
    # Scrape based on source selection
    articles = []
    
    if args.source == 'all':
        articles = scrape_all_newspapers(args.start_date, args.end_date)
    else:
        # Map source name to scraper class
        scrapers = {
            'prothomalo': ProthomAloScraper,
            'jugantor': JugantorScraper,
            'dailystar': DailyStarScraper,
            'dhakatribune': DhakaTribuneScraper
        }
        
        scraper_class = scrapers[args.source]
        scraper = scraper_class(args.start_date, args.end_date)
        articles = scraper.scrape_articles()
    
    print(f"\n✅ Scraped {len(articles)} articles")
    
    # Display summary
    if articles:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        # Group by source
        by_source = {}
        by_mention = {}
        
        for article in articles:
            source = article['source']
            by_source[source] = by_source.get(source, 0) + 1
            
            for mention in article['mentions']:
                by_mention[mention] = by_mention.get(mention, 0) + 1
        
        print("\nArticles by source:")
        for source, count in sorted(by_source.items()):
            print(f"  - {source}: {count}")
        
        print("\nTop mentioned entities:")
        sorted_mentions = sorted(by_mention.items(), key=lambda x: x[1], reverse=True)
        for entity, count in sorted_mentions[:10]:
            print(f"  - {entity}: {count}")
        
        # Show sample articles
        print("\n" + "=" * 80)
        print("SAMPLE ARTICLES")
        print("=" * 80)
        for i, article in enumerate(articles[:5], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']} | Date: {article['date']}")
            print(f"   Mentions: {', '.join(article['mentions'])}")
            print(f"   URL: {article['url']}")
            print(f"   Content preview: {article['content'][:150]}...")
    
    # Save to JSON if requested
    if args.output and articles:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Saved articles to {output_path}")
    
    # Save to database if requested
    if args.save and articles:
        print("\n" + "=" * 80)
        print("Saving to vector database...")
        save_articles_to_vector_db(articles)
        print("✅ Articles saved to database successfully!")
    elif articles and not args.save:
        print("\n" + "=" * 80)
        save_choice = input("Save articles to vector database? (y/n): ")
        if save_choice.lower() == 'y':
            save_articles_to_vector_db(articles)
            print("✅ Articles saved to database successfully!")
    
    print("\n" + "=" * 80)
    print("Scraping complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
