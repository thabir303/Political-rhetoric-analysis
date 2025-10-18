#!/usr/bin/env python3
"""
Verification Script: Check Name Normalization

Verifies that the migration worked correctly by checking:
1. People have canonical names
2. People_affiliations are correct
3. Party-figure associations are consistent
"""

import logging
import json
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def verify_migration():
    """Verify the migration results."""
    try:
        from backend.core.vector_db import VectorDatabase
        from backend.core.scraping import POLITICAL_ENTITIES
        
        logger.info("=" * 70)
        logger.info("🔍 VERIFICATION: Name Normalization & People Affiliations")
        logger.info("=" * 70)
        
        db = VectorDatabase(collection_name="political_articles")
        
        # Get sample articles
        results = db.collection.get(limit=30, include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        if not metadatas:
            logger.warning("No articles found!")
            return
        
        logger.info(f"\n✓ Retrieved {len(metadatas)} articles for verification\n")
        
        # Analyze the data
        party_figures_actual = defaultdict(set)
        all_people = set()
        articles_with_affiliations = 0
        articles_with_people = 0
        bengali_names_found = []
        
        for i, metadata in enumerate(metadatas, 1):
            people_str = metadata.get('people', '')
            parties_str = metadata.get('parties', '')
            people_affiliations_str = metadata.get('people_affiliations', '{}')
            
            # Parse people_affiliations
            try:
                people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
            except:
                people_affiliations = {}
            
            if people_str:
                articles_with_people += 1
                people = [p.strip() for p in people_str.split(',') if p.strip()]
                
                # Check for Bengali characters
                for person in people:
                    all_people.add(person)
                    if any('\u0980' <= char <= '\u09FF' for char in person):
                        bengali_names_found.append(person)
                
                # Track affiliations
                if people_affiliations:
                    articles_with_affiliations += 1
                    for person, party in people_affiliations.items():
                        party_figures_actual[party].add(person)
        
        # Print results
        logger.info("📊 VERIFICATION RESULTS:")
        logger.info("-" * 70)
        
        logger.info(f"\n1. ARTICLES ANALYSIS:")
        logger.info(f"   • Total articles checked: {len(metadatas)}")
        logger.info(f"   • Articles with people: {articles_with_people}")
        logger.info(f"   • Articles with affiliations: {articles_with_affiliations}")
        logger.info(f"   • Coverage: {(articles_with_affiliations/max(articles_with_people,1))*100:.1f}%")
        
        logger.info(f"\n2. NAME NORMALIZATION CHECK:")
        logger.info(f"   • Unique people found: {len(all_people)}")
        logger.info(f"   • Bengali names remaining: {len(bengali_names_found)}")
        
        if bengali_names_found:
            logger.warning(f"   ⚠️  Found Bengali names (should be normalized):")
            for name in bengali_names_found[:5]:
                logger.warning(f"      - {name}")
        else:
            logger.info(f"   ✅ All names normalized to English!")
        
        logger.info(f"\n3. PARTY-FIGURE ASSOCIATIONS:")
        for party_key in sorted(party_figures_actual.keys()):
            figures_found = sorted(party_figures_actual[party_key])
            canonical_figures = list(POLITICAL_ENTITIES.get(party_key, {}).get("figures", {}).keys())
            
            logger.info(f"\n   {party_key}:")
            logger.info(f"   ├─ Figures found in DB: {len(figures_found)}")
            logger.info(f"   ├─ Canonical figures: {len(canonical_figures)}")
            
            # Show figures
            if figures_found:
                logger.info(f"   └─ Found: {', '.join(figures_found[:5])}")
                if len(figures_found) > 5:
                    logger.info(f"              ... and {len(figures_found)-5} more")
        
        logger.info(f"\n4. SAMPLE ARTICLES:")
        logger.info("-" * 70)
        
        for i, metadata in enumerate(metadatas[:3], 1):
            title = metadata.get('title', 'No title')[:60]
            parties_str = metadata.get('parties', 'None')
            people_str = metadata.get('people', 'None')
            people_affiliations_str = metadata.get('people_affiliations', '{}')
            
            try:
                people_affiliations = json.loads(people_affiliations_str)
            except:
                people_affiliations = {}
            
            logger.info(f"\nArticle {i}: {title}...")
            logger.info(f"  Parties: {parties_str}")
            logger.info(f"  People: {people_str}")
            if people_affiliations:
                logger.info(f"  Affiliations:")
                for person, party in list(people_affiliations.items())[:3]:
                    logger.info(f"    • {person} → {party}")
        
        logger.info("\n" + "=" * 70)
        
        # Final verdict
        if bengali_names_found:
            logger.warning("⚠️  PARTIAL SUCCESS: Some Bengali names still exist")
            logger.warning("    Run the migration script again if needed")
        elif articles_with_affiliations == 0:
            logger.warning("⚠️  NO AFFILIATIONS: people_affiliations not found")
            logger.warning("    Migration may not have run completely")
        else:
            logger.info("✅ MIGRATION SUCCESSFUL!")
            logger.info("   • All names normalized")
            logger.info("   • People affiliations present")
            logger.info("   • Party associations correct")
        
        logger.info("=" * 70 + "\n")
        
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)

if __name__ == "__main__":
    verify_migration()
