#!/usr/bin/env python3
"""
Update Name Variants Migration Script

Re-categorizes articles with updated name variants to catch Bengali names
that were previously missed.
"""

import sys
from backend.core.vector_db import VectorDatabase
from backend.core.categorization import ArticleCategorizer
import json

def update_articles_with_new_variants():
    """Update articles with new name variants."""
    
    print("=" * 70)
    print("Re-categorizing Articles with Updated Name Variants")
    print("=" * 70)
    print()
    
    db = VectorDatabase(collection_name="political_articles")
    categorizer = ArticleCategorizer()
    
    # Get all articles
    print("Loading articles from database...")
    results = db.collection.get(include=["metadatas", "documents"])
    all_metadatas = results.get("metadatas", [])
    all_documents = results.get("documents", [])
    all_ids = results.get("ids", [])
    
    print(f"Total articles in database: {len(all_ids)}")
    print()
    
    # Find articles that need updating
    # This includes articles that mention political figures but don't have them categorized
    articles_to_update = []
    
    # Check for common Bengali name patterns that might have been missed
    name_patterns = [
        'সালাহউদ্দিন', 'সালাউদ্দিন',  # Salahuddin variants
        'তারেক', 'ফখরুল',  # Partial BNP names
        'ইউনূস', 'ইউনুস',  # Yunus variants
        'নাহিদ', 'সরজিস', 'হাসনাত',  # NCP members
    ]
    
    for i, (doc_id, metadata, document) in enumerate(zip(all_ids, all_metadatas, all_documents)):
        content = f"{metadata.get('title', '')} {document}"
        
        # Check if any name pattern is mentioned
        needs_update = False
        for pattern in name_patterns:
            if pattern in content:
                # Check if we're missing this person in categorization
                people_str = metadata.get('people', '')
                people_affiliations_str = metadata.get('people_affiliations', '{}')
                
                try:
                    people_affiliations = json.loads(people_affiliations_str) if people_affiliations_str else {}
                except:
                    people_affiliations = {}
                
                # Simple heuristic: if we found a pattern but people field is empty or short
                # it might need re-categorization
                if len(people_str.split(',')) < 2 or len(people_affiliations) < 2:
                    needs_update = True
                    break
        
        if needs_update:
            articles_to_update.append({
                'id': doc_id,
                'metadata': metadata,
                'document': document
            })
    
    print(f"Found {len(articles_to_update)} articles that may need updating")
    print()
    
    if len(articles_to_update) == 0:
        print("No articles need updating. All done!")
        return
    
    # Update each article
    updated_count = 0
    error_count = 0
    
    for i, article_data in enumerate(articles_to_update):
        doc_id = article_data['id']
        metadata = article_data['metadata']
        document = article_data['document']
        
        try:
            # Re-categorize
            cat_result = categorizer.categorize_article({
                'title': metadata.get('title', ''),
                'content': document
            })
            
            # Update metadata with new categorization
            metadata['people'] = ', '.join(cat_result.get('people', []))
            metadata['parties'] = ', '.join(cat_result.get('parties', []))
            metadata['people_affiliations'] = json.dumps(cat_result.get('people_affiliations', {}))
            metadata['categories'] = ', '.join(cat_result.get('categories', []))
            metadata['keywords'] = ', '.join(cat_result.get('keywords', []))
            
            # Update in database
            db.collection.update(
                ids=[doc_id],
                metadatas=[metadata]
            )
            
            updated_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{len(articles_to_update)} articles processed...")
                
        except Exception as e:
            print(f"Error updating article {doc_id}: {e}")
            error_count += 1
            continue
    
    print()
    print("=" * 70)
    print("Update Complete!")
    print("=" * 70)
    print(f"Articles updated: {updated_count}/{len(articles_to_update)}")
    print(f"Errors: {error_count}")
    print()
    
    # Show sample of updated articles
    print("Sample of updated categorization:")
    print("-" * 70)
    
    # Get a few updated articles to show
    sample_results = db.collection.get(
        ids=articles_to_update[:3] if len(articles_to_update) >= 3 else articles_to_update,
        include=["metadatas"]
    )
    
    for i, metadata in enumerate(sample_results.get("metadatas", [])):
        print(f"\nArticle {i + 1}:")
        print(f"Title: {metadata.get('title', 'No title')[:80]}...")
        print(f"People: {metadata.get('people', 'None')}")
        print(f"Parties: {metadata.get('parties', 'None')}")
        
        # Parse people_affiliations
        people_affiliations_str = metadata.get('people_affiliations', '{}')
        try:
            people_affiliations = json.loads(people_affiliations_str)
            if people_affiliations:
                print("People → Party Affiliations:")
                for person, party in people_affiliations.items():
                    print(f"  {person} → {party}")
        except:
            pass
    
    print()
    print("All articles have been re-categorized with updated name variants!")
    print("Bengali names like 'সালাহউদ্দিন' will now be properly detected.")


if __name__ == "__main__":
    update_articles_with_new_variants()
