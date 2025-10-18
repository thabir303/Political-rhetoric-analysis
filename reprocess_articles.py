#!/usr/bin/env python3
"""
Reprocess existing articles with enhanced LLM analysis.

This script:
1. Loads existing articles from ChromaDB
2. Analyzes each with EnhancedArticleAnalyzer
3. Updates metadata with: summary, keywords, topics, election_2026_impact
4. Saves back to ChromaDB

Use this to upgrade your existing database to the new enhanced schema.
"""

import sys
import logging
from typing import List, Dict
from datetime import datetime
from enhanced_scraping import get_article_analyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def reprocess_articles():
    """Reprocess all existing articles with LLM analysis."""
    
    logger.info("="*80)
    logger.info("Starting Enhanced Article Reprocessing")
    logger.info("="*80)
    
    # Import vector store
    try:
        from database import vector_store
    except ImportError:
        logger.error("Failed to import vector_store. Make sure database module is available.")
        return
    
    # Initialize analyzer
    logger.info("Initializing LLM analyzer...")
    analyzer = get_article_analyzer()
    
    # Get all existing articles
    logger.info("Loading existing articles from ChromaDB...")
    try:
        collection = vector_store.collection
        results = collection.get(include=["metadatas", "documents"])
        
        if not results or not results['metadatas']:
            logger.warning("No articles found in database!")
            return
        
        total_articles = len(results['metadatas'])
        logger.info(f"Found {total_articles} articles to reprocess")
        
    except Exception as e:
        logger.error(f"Error loading articles: {e}")
        return
    
    # Ask for confirmation
    print(f"\n⚠️  This will reprocess {total_articles} articles with LLM analysis.")
    print(f"⏱️  Estimated time: {total_articles * 5} - {total_articles * 7} seconds (~{(total_articles * 6) // 60} minutes)")
    print(f"💰 Estimated cost: ~${total_articles * 0.0006:.2f}")
    
    response = input("\nProceed with reprocessing? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Reprocessing cancelled by user")
        return
    
    # Process each article
    successful = 0
    failed = 0
    skipped = 0
    start_time = datetime.now()
    
    logger.info("\nStarting reprocessing...")
    logger.info("-"*80)
    
    for idx, (article_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
        try:
            # Check if already processed (has summary field)
            if metadata.get('summary') and metadata.get('keywords') and metadata.get('topics'):
                logger.info(f"[{idx}/{total_articles}] Skipping (already processed): {metadata.get('title', 'Unknown')[:50]}...")
                skipped += 1
                continue
            
            logger.info(f"[{idx}/{total_articles}] Processing: {metadata.get('title', 'Unknown')[:50]}...")
            
            # Get original content (fallback to document if not in metadata)
            content = metadata.get('original_content', document)
            
            if not content or len(content.strip()) < 50:
                logger.warning(f"  ⚠️  Skipping - content too short or empty")
                skipped += 1
                continue
            
            # Perform LLM analysis
            analysis = analyzer.analyze_article(
                article_content=content,
                article_title=metadata.get('title', ''),
                article_date=metadata.get('date', ''),
                political_party=metadata.get('category', ''),
                political_figure=metadata.get('persons', '').split(',')[0].strip() if metadata.get('persons') else None
            )
            
            # Update metadata with analysis
            updated_metadata = metadata.copy()
            updated_metadata['original_content'] = content  # Preserve original
            updated_metadata['summary'] = analysis['summary']
            updated_metadata['keywords'] = ','.join(analysis['keywords'])
            updated_metadata['topics'] = ','.join(analysis['topics'])
            updated_metadata['election_2026_impact'] = analysis['election_2026_impact']
            updated_metadata['has_election_impact'] = analysis['has_election_impact']
            updated_metadata['analyzed_at'] = analysis['analyzed_at']
            updated_metadata['analysis_language'] = analysis['language']
            updated_metadata['processing_time'] = analysis['processing_time']
            
            # Update in ChromaDB
            collection.update(
                ids=[article_id],
                documents=[analysis['summary']],  # Use summary as main document
                metadatas=[updated_metadata]
            )
            
            successful += 1
            logger.info(f"  ✓ Success! Keywords: {len(analysis['keywords'])}, Topics: {len(analysis['topics'])}, "
                       f"Election Impact: {analysis['has_election_impact']}")
            
            # Progress update every 10 articles
            if idx % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time = elapsed / idx
                remaining = (total_articles - idx) * avg_time
                logger.info(f"\n📊 Progress: {idx}/{total_articles} ({(idx/total_articles*100):.1f}%)")
                logger.info(f"   ⏱️  Time elapsed: {elapsed:.0f}s | Estimated remaining: {remaining:.0f}s")
                logger.info(f"   ✓ Success: {successful} | ⚠️ Skipped: {skipped} | ✗ Failed: {failed}\n")
            
        except Exception as e:
            failed += 1
            logger.error(f"  ✗ Error processing article: {e}")
            logger.error(f"    Article ID: {article_id}")
            logger.error(f"    Title: {metadata.get('title', 'Unknown')}")
            continue
    
    # Final summary
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "="*80)
    logger.info("Reprocessing Complete!")
    logger.info("="*80)
    logger.info(f"Total articles: {total_articles}")
    logger.info(f"  ✓ Successfully processed: {successful}")
    logger.info(f"  ⚠️  Skipped (already done/too short): {skipped}")
    logger.info(f"  ✗ Failed: {failed}")
    logger.info(f"\n⏱️  Total time: {total_time:.0f} seconds ({total_time/60:.1f} minutes)")
    logger.info(f"⚡ Average time per article: {total_time/successful:.1f} seconds" if successful > 0 else "N/A")
    logger.info(f"💰 Estimated cost: ~${successful * 0.0006:.4f}")
    logger.info("="*80)
    
    if successful > 0:
        logger.info("\n✅ Your database has been successfully upgraded with enhanced LLM analysis!")
        logger.info("   All articles now have: summary, keywords, topics, and 2026 election impact analysis")
        logger.info("\n🚀 New API endpoints are now available:")
        logger.info("   - GET /api/v1/topics")
        logger.info("   - GET /api/v1/keywords")
        logger.info("   - GET /api/v1/election-impact")


if __name__ == "__main__":
    try:
        reprocess_articles()
    except KeyboardInterrupt:
        logger.info("\n\nReprocessing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
