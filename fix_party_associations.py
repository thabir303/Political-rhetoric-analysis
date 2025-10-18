#!/usr/bin/env python3
"""
Fix Party-Figure Associations in Database

This script cleans up inconsistencies where figures are associated with wrong parties.
It uses the strict POLITICAL_ENTITIES mapping from scraping.py to ensure correct associations.
"""

import sys
import os
from typing import Dict, List, Set
import chromadb
from chromadb.config import Settings
import json

# Import the correct POLITICAL_ENTITIES mapping
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.core.scraping import POLITICAL_ENTITIES


def get_correct_party_for_figure(figure_name: str) -> str:
    """
    Find the correct party for a given figure based on POLITICAL_ENTITIES.
    
    Args:
        figure_name: Name of the political figure
        
    Returns:
        Party name or empty string if not found
    """
    figure_lower = figure_name.lower()
    
    for party, party_data in POLITICAL_ENTITIES.items():
        # Check if figure belongs to this party
        figures_dict = party_data.get("figures", {})
        for canonical_name, variants in figures_dict.items():
            for variant in variants:
                if variant.lower() == figure_lower or figure_lower in variant.lower():
                    return party
    
    return ""


def get_all_party_names(party_key: str) -> Set[str]:
    """Get all name variants for a party."""
    party_data = POLITICAL_ENTITIES.get(party_key, {})
    return set(party_data.get("party_names", []))


def fix_party_figure_associations():
    """
    Fix party-figure associations in the database.
    """
    print("🔧 Fixing Party-Figure Associations")
    print("=" * 60)
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=os.path.join(os.getcwd(), "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection("political_articles")
        
        # Get all articles
        results = collection.get(include=["metadatas"])
        
        all_metadatas = results.get("metadatas", [])
        all_ids = results.get("ids", [])
        
        print(f"📊 Total articles in database: {len(all_metadatas)}")
        print()
        
        fixed_count = 0
        issues_found = {}
        
        for i, (article_id, metadata) in enumerate(zip(all_ids, all_metadatas)):
            # Get current parties and people
            parties_str = metadata.get('parties', '')
            people_str = metadata.get('people', '')
            
            if not people_str:
                continue
            
            # Parse people list
            people_list = [p.strip() for p in people_str.split(',') if p.strip()]
            
            # Check each person and find their correct party
            correct_parties = set()
            person_party_map = {}
            
            for person in people_list:
                correct_party = get_correct_party_for_figure(person)
                if correct_party:
                    correct_parties.add(correct_party)
                    person_party_map[person] = correct_party
            
            # Build the correct parties string
            if correct_parties:
                correct_parties_str = ', '.join(sorted(correct_parties))
                
                # Check if current parties string is different
                current_parties_set = set([p.strip() for p in parties_str.split(',') if p.strip()])
                
                if current_parties_set != correct_parties:
                    # Record the issue
                    if parties_str not in issues_found:
                        issues_found[parties_str] = {
                            'incorrect': parties_str,
                            'correct': correct_parties_str,
                            'people': people_list,
                            'count': 0,
                            'article_ids': []
                        }
                    issues_found[parties_str]['count'] += 1
                    issues_found[parties_str]['article_ids'].append(article_id)
                    
                    fixed_count += 1
                    
                    # Update metadata
                    new_metadata = metadata.copy()
                    new_metadata['parties'] = correct_parties_str
                    
                    # Update in ChromaDB
                    collection.update(
                        ids=[article_id],
                        metadatas=[new_metadata]
                    )
            
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{len(all_metadatas)} articles...")
        
        print()
        print("=" * 60)
        print(f"✅ Fixed {fixed_count} articles with incorrect party associations")
        print()
        
        if issues_found:
            print("📋 Issues Found and Fixed:")
            print("-" * 60)
            for idx, (incorrect, data) in enumerate(issues_found.items(), 1):
                print(f"\n{idx}. Issue:")
                print(f"   ❌ Incorrect: {data['incorrect']}")
                print(f"   ✅ Correct: {data['correct']}")
                print(f"   👥 People: {', '.join(data['people'][:3])}")
                print(f"   📊 Count: {data['count']} articles")
                print(f"   🆔 Sample IDs: {', '.join(data['article_ids'][:3])}")
        else:
            print("✨ No issues found! All party-figure associations are correct.")
        
        print()
        print("=" * 60)
        print("🎉 Database cleanup complete!")
        
        # Print correct mappings for reference
        print()
        print("📚 Correct Party-Figure Mappings:")
        print("-" * 60)
        for party, party_data in POLITICAL_ENTITIES.items():
            figures = party_data.get("figures", {})
            if figures:
                print(f"\n{party}:")
                for canonical_name in figures.keys():
                    print(f"  - {canonical_name}")
        
    except Exception as e:
        print(f"❌ Error fixing associations: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    fix_party_figure_associations()
