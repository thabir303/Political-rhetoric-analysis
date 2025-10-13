"""
Integration Script: Scraping + Categorization

Demonstrates complete workflow:
1. Scrape articles from newspapers
2. Categorize each article
3. Save to vector database
4. Generate analysis report
"""

import argparse
import json
from datetime import datetime
from typing import List, Dict

from scraping import scrape_all_newspapers
from categorization import (
    ArticleCategorizer,
    categorize_scraped_articles,
    analyze_categorization_results,
    save_categorized_articles_to_db
)


def scrape_and_categorize(
    start_date: str,
    end_date: str,
    sources: List[str] = None,
    save_to_db: bool = False,
    output_file: str = None
) -> Dict:
    """
    Complete pipeline: scrape, categorize, and optionally save.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        sources: List of newspaper sources or None for all
        save_to_db: Whether to save to vector database
        output_file: Optional JSON output file path
        
    Returns:
        Dictionary with results and statistics
    """
    print("=" * 80)
    print("SCRAPING AND CATEGORIZATION PIPELINE")
    print("=" * 80)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Sources: {sources if sources else 'All newspapers'}")
    print(f"Save to DB: {save_to_db}")
    print("=" * 80)
    
    # Step 1: Scrape articles
    print("\n[1/4] SCRAPING ARTICLES...")
    print("-" * 80)
    
    articles = scrape_all_newspapers(
        start_date=start_date,
        end_date=end_date,
        sources=sources
    )
    
    print(f"✓ Scraped {len(articles)} articles")
    
    if len(articles) == 0:
        print("\n⚠️  No articles found. Exiting.")
        return {
            'total_articles': 0,
            'message': 'No articles found in the specified date range'
        }
    
    # Step 2: Categorize articles
    print("\n[2/4] CATEGORIZING ARTICLES...")
    print("-" * 80)
    
    categorized_articles = categorize_scraped_articles(articles)
    
    print(f"✓ Categorized {len(categorized_articles)} articles")
    
    # Step 3: Analyze results
    print("\n[3/4] ANALYZING RESULTS...")
    print("-" * 80)
    
    categorization_results = [
        article['categorization'] for article in categorized_articles
    ]
    analysis = analyze_categorization_results(categorization_results)
    
    print(f"✓ Analysis complete")
    print(f"  - Speech articles: {analysis['speech_articles']}")
    print(f"  - Stance articles: {analysis['stance_articles']}")
    print(f"  - Avg categories per article: {analysis['avg_categories_per_article']:.2f}")
    
    # Step 4: Save results
    print("\n[4/4] SAVING RESULTS...")
    print("-" * 80)
    
    if save_to_db:
        try:
            save_categorized_articles_to_db(categorized_articles)
            print(f"✓ Saved to vector database")
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
    
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'articles': categorized_articles,
                    'analysis': analysis,
                    'metadata': {
                        'date_range': f"{start_date} to {end_date}",
                        'total_articles': len(categorized_articles),
                        'timestamp': datetime.now().isoformat()
                    }
                }, f, ensure_ascii=False, indent=2)
            print(f"✓ Saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving to file: {e}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Total articles: {len(categorized_articles)}")
    print(f"Speech articles: {analysis['speech_articles']}")
    print(f"Stance articles: {analysis['stance_articles']}")
    
    print(f"\nTop 5 Parties:")
    for party, count in analysis['top_parties'][:5]:
        print(f"  - {party}: {count} mentions")
    
    print(f"\nTop 5 People:")
    for person, count in analysis['top_people'][:5]:
        print(f"  - {person}: {count} mentions")
    
    print(f"\nTop 10 Keywords:")
    for keyword, count in analysis['top_keywords'][:10]:
        print(f"  - {keyword}: {count} occurrences")
    
    print("=" * 80)
    
    return {
        'total_articles': len(categorized_articles),
        'articles': categorized_articles,
        'analysis': analysis
    }


def print_article_details(article: Dict):
    """Print detailed information about a single article."""
    print("\n" + "=" * 80)
    print(f"ARTICLE: {article['title']}")
    print("=" * 80)
    
    print(f"\nSource: {article.get('source', 'Unknown')}")
    print(f"Date: {article.get('date', 'Unknown')}")
    print(f"URL: {article.get('url', 'N/A')}")
    
    if 'categorization' in article:
        cat = article['categorization']
        
        print(f"\nCategories ({len(cat['categories'])}):")
        for category in cat['categories']:
            print(f"  • {category}")
        
        print(f"\nPolitical Parties ({len(cat['parties'])}):")
        for party in cat['parties']:
            print(f"  • {party}")
        
        print(f"\nPeople Mentioned ({len(cat['people'])}):")
        for person in cat['people']:
            print(f"  • {person}")
        
        print(f"\nKey Information:")
        print(f"  • Speech article: {'Yes' if cat['is_speech'] else 'No'}")
        print(f"  • Stance article: {'Yes' if cat['is_stance'] else 'No'}")
        print(f"  • Keywords: {', '.join(cat['keywords'][:8])}")
        
        if cat['dates']:
            print(f"  • Dates mentioned: {', '.join(cat['dates'])}")
        
        if cat['themes']:
            print(f"\nThemes:")
            for theme, score in sorted(cat['themes'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {theme}: {score} mentions")
    
    print("\nContent Preview:")
    print(article['content'][:300] + "..." if len(article['content']) > 300 else article['content'])
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape and categorize articles from Bangladeshi newspapers"
    )
    
    parser.add_argument(
        '--start-date',
        default='2024-08-05',
        help='Start date (YYYY-MM-DD), default: 2024-08-05'
    )
    
    parser.add_argument(
        '--end-date',
        default='2025-09-30',
        help='End date (YYYY-MM-DD), default: 2025-09-30'
    )
    
    parser.add_argument(
        '--source',
        choices=['prothomalo', 'jugantor', 'dailystar', 'dhakatribune'],
        help='Specific newspaper source (optional, scrapes all by default)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save categorized articles to vector database'
    )
    
    parser.add_argument(
        '--output',
        help='Output JSON file path (optional)'
    )
    
    parser.add_argument(
        '--show-details',
        action='store_true',
        help='Show detailed information for each article'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of articles to display details for (when using --show-details)'
    )
    
    args = parser.parse_args()
    
    # Determine sources
    sources = [args.source] if args.source else None
    
    # Run pipeline
    results = scrape_and_categorize(
        start_date=args.start_date,
        end_date=args.end_date,
        sources=sources,
        save_to_db=args.save,
        output_file=args.output
    )
    
    # Show detailed article information if requested
    if args.show_details and results['total_articles'] > 0:
        articles_to_show = results['articles']
        
        if args.limit:
            articles_to_show = articles_to_show[:args.limit]
            print(f"\n\nShowing details for first {args.limit} articles:")
        else:
            print(f"\n\nShowing details for all {len(articles_to_show)} articles:")
        
        for article in articles_to_show:
            print_article_details(article)


if __name__ == "__main__":
    main()
