#!/usr/bin/env python3
"""
Migration Script: Re-categorize Articles with Name Normalization

This script re-processes all articles in the database to:
1. Normalize Bengali names to canonical English names
2. Add people_affiliations mapping
3. Use the updated POLITICAL_ENTITIES structure
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_categorization():
    """Re-categorize all existing articles with name normalization."""
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.categorization import ArticleCategorizer
        
        logger.info("=" * 60)
        logger.info("Starting Categorization Migration")
        logger.info("=" * 60)
        
        # Initialize database and categorizer
        db = VectorDatabase(collection_name="political_articles")
        categorizer = ArticleCategorizer()
        
        # Get all articles
        logger.info("\n[1/4] Fetching all articles from database...")
        results = db.collection.get(include=["documents", "metadatas"])
        
        all_ids = results.get("ids", [])
        all_documents = results.get("documents", [])
        all_metadatas = results.get("metadatas", [])
        
        total_articles = len(all_ids)
        logger.info(f"✓ Found {total_articles} articles to re-categorize")
        
        if total_articles == 0:
            logger.warning("No articles found in database. Nothing to migrate.")
            return
        
        # Re-categorize each article
        logger.info("\n[2/4] Re-categorizing articles with name normalization...")
        updated_metadatas = []
        success_count = 0
        error_count = 0
        
        for i, (doc_id, document, metadata) in enumerate(zip(all_ids, all_documents, all_metadatas), 1):
            try:
                # Create article dict for categorization
                article = {
                    'title': metadata.get('title', ''),
                    'content': document or '',
                    'date': metadata.get('date', ''),
                    'source': metadata.get('source', '')
                }
                
                # Re-categorize with new logic
                categorization = categorizer.categorize_article(article)
                
                # Update metadata with new categorization
                updated_metadata = metadata.copy()
                
                # Update people (now canonical names)
                if 'people' in categorization:
                    updated_metadata['people'] = ', '.join(categorization['people'])
                
                # Update parties
                if 'parties' in categorization:
                    updated_metadata['parties'] = ', '.join(categorization['parties'])
                
                # Add people_affiliations (NEW!)
                if 'people_affiliations' in categorization:
                    import json
                    updated_metadata['people_affiliations'] = json.dumps(categorization['people_affiliations'])
                
                # Update keywords if needed
                if 'keywords' in categorization:
                    updated_metadata['keywords'] = ', '.join(categorization['keywords'][:20])
                
                updated_metadatas.append(updated_metadata)
                success_count += 1
                
                if i % 10 == 0:
                    logger.info(f"  Progress: {i}/{total_articles} articles processed...")
                
            except Exception as e:
                logger.error(f"  Error re-categorizing article {i} (ID: {doc_id}): {e}")
                updated_metadatas.append(metadata)  # Keep original on error
                error_count += 1
        
        logger.info(f"✓ Re-categorization complete: {success_count} success, {error_count} errors")
        
        # Update the database
        logger.info("\n[3/4] Updating database with new categorizations...")
        try:
            # ChromaDB update requires ids, documents, and metadatas
            db.collection.update(
                ids=all_ids,
                documents=all_documents,
                metadatas=updated_metadatas
            )
            logger.info(f"✓ Database updated successfully!")
        except Exception as e:
            logger.error(f"✗ Failed to update database: {e}")
            raise
        
        # Verify the update
        logger.info("\n[4/4] Verifying migration...")
        verification = db.collection.get(limit=5, include=["metadatas"])
        sample_metadata = verification.get("metadatas", [])
        
        if sample_metadata:
            import json
            first_meta = sample_metadata[0]
            logger.info("\n📋 Sample Article After Migration:")
            logger.info(f"  Title: {first_meta.get('title', 'N/A')}")
            logger.info(f"  Parties: {first_meta.get('parties', 'N/A')}")
            logger.info(f"  People: {first_meta.get('people', 'N/A')}")
            
            people_aff_str = first_meta.get('people_affiliations', '{}')
            try:
                people_aff = json.loads(people_aff_str)
                logger.info(f"  People Affiliations: {people_aff}")
            except:
                logger.info(f"  People Affiliations: (parse error)")
        
        logger.info("\n" + "=" * 60)
        logger.info("Migration Complete! 🎉")
        logger.info("=" * 60)
        logger.info(f"\n📊 Summary:")
        logger.info(f"  Total Articles: {total_articles}")
        logger.info(f"  Successfully Updated: {success_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Success Rate: {(success_count/total_articles)*100:.1f}%")
        logger.info("\n✓ Your /parties endpoint should now show consistent key figures!")
        logger.info("✓ Bengali names are now normalized to canonical English names!")
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        migrate_categorization()
    except KeyboardInterrupt:
        logger.info("\n\nMigration interrupted by user")
    except Exception as e:
        logger.error(f"\n\nMigration failed with error: {e}")
        exit(1)
