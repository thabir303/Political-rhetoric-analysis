#!/usr/bin/env python3
"""
Fix categorization issues in the database:
1. Normalize all Bangla names to canonical English names
2. Fix incorrect party-figure associations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.vector_db import VectorDatabase
from backend.core.scraping import POLITICAL_ENTITIES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def normalize_name_to_canonical(name: str) -> str:
    """
    Convert any name variant (English/Bangla) to its canonical English name.
    
    Args:
        name: Name to normalize
        
    Returns:
        Canonical English name if found, otherwise original name
    """
    name_stripped = name.strip()
    
    # Search through all parties and figures
    for party_key, party_data in POLITICAL_ENTITIES.items():
        if isinstance(party_data, dict) and "figures" in party_data:
            for canonical_name, variants in party_data["figures"].items():
                if name_stripped == canonical_name or name_stripped in variants:
                    return canonical_name
    
    return name_stripped


def get_correct_party_for_figure(figure_canonical: str) -> str:
    """
    Get the correct party for a given figure.
    
    Args:
        figure_canonical: Canonical English name of the figure
        
    Returns:
        Party key if found, otherwise empty string
    """
    for party_key, party_data in POLITICAL_ENTITIES.items():
        if isinstance(party_data, dict) and "figures" in party_data:
            if figure_canonical in party_data["figures"]:
                return party_key
    
    return ""


def fix_categorization_issues():
    """Main function to fix all categorization issues."""
    
    logger.info("Starting categorization fix...")
    
    # Initialize database
    db = VectorDatabase(collection_name="political_articles")
    
    # Get all articles
    results = db.collection.get(
        include=["documents", "metadatas"]
    )
    
    if not results or not results.get("ids"):
        logger.error("No articles found in database")
        return
    
    ids = results["ids"]
    metadatas = results["metadatas"]
    documents = results["documents"]
    
    logger.info(f"Found {len(ids)} articles to process")
    
    # Track changes
    updates_needed = []
    normalization_count = 0
    party_fix_count = 0
    
    for i, article_id in enumerate(ids):
        metadata = metadatas[i]
        document = documents[i]
        
        people_str = metadata.get("people", "")
        parties_str = metadata.get("parties", "")
        
        if not people_str:
            continue
        
        # Split and normalize names
        people_list = [p.strip() for p in people_str.split(",") if p.strip()]
        normalized_people = []
        correct_parties = set()
        
        for person in people_list:
            canonical_name = normalize_name_to_canonical(person)
            normalized_people.append(canonical_name)
            
            # Get correct party for this figure
            correct_party = get_correct_party_for_figure(canonical_name)
            if correct_party:
                correct_parties.add(correct_party)
            
            # Track if normalization happened
            if canonical_name != person:
                logger.info(f"  Normalizing: '{person}' → '{canonical_name}'")
                normalization_count += 1
        
        # Create updated metadata
        new_people = ", ".join(normalized_people)
        new_parties = ", ".join(sorted(correct_parties)) if correct_parties else parties_str
        
        # Check if update is needed
        needs_update = False
        if new_people != people_str:
            needs_update = True
            logger.info(f"Article {i+1}: People update needed")
            logger.info(f"  Before: {people_str}")
            logger.info(f"  After:  {new_people}")
        
        if new_parties != parties_str:
            needs_update = True
            party_fix_count += 1
            logger.info(f"Article {i+1}: Party update needed")
            logger.info(f"  Before: {parties_str}")
            logger.info(f"  After:  {new_parties}")
        
        if needs_update:
            # Create updated metadata
            updated_metadata = metadata.copy()
            updated_metadata["people"] = new_people
            updated_metadata["parties"] = new_parties
            
            updates_needed.append({
                "id": article_id,
                "metadata": updated_metadata,
                "document": document
            })
    
    # Apply updates
    if updates_needed:
        logger.info(f"\nApplying {len(updates_needed)} updates...")
        
        # Delete old entries and add updated ones
        ids_to_delete = [u["id"] for u in updates_needed]
        db.collection.delete(ids=ids_to_delete)
        
        # Add updated entries
        db.collection.add(
            ids=[u["id"] for u in updates_needed],
            documents=[u["document"] for u in updates_needed],
            metadatas=[u["metadata"] for u in updates_needed]
        )
        
        logger.info("✓ Updates applied successfully")
    else:
        logger.info("✓ No updates needed - all data is correct")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY:")
    logger.info(f"  Total articles processed: {len(ids)}")
    logger.info(f"  Articles updated: {len(updates_needed)}")
    logger.info(f"  Names normalized: {normalization_count}")
    logger.info(f"  Party associations fixed: {party_fix_count}")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        fix_categorization_issues()
    except Exception as e:
        logger.error(f"Error fixing categorization: {e}", exc_info=True)
        sys.exit(1)
