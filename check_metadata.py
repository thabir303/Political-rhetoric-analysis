#!/usr/bin/env python3
"""
Check what metadata is actually stored in the database
"""
import sys
sys.path.insert(0, '.')

from backend.core.vector_db import VectorDatabase
import json

def check_metadata():
    """Check actual metadata in database"""
    print("\n🔍 CHECKING DATABASE METADATA\n")
    
    db = VectorDatabase(collection_name="political_articles")
    
    # Get first 5 articles
    results = db.collection.get(limit=5, include=['metadatas', 'documents'])
    
    print(f"Total articles: {db.collection.count()}\n")
    print("="*80)
    
    for i, (doc_id, metadata, document) in enumerate(zip(results['ids'], results['metadatas'], results['documents'])):
        print(f"\nArticle {i+1} (ID: {doc_id[:50]}...)")
        print("-"*80)
        
        # Check key metadata fields
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Date: {metadata.get('date', 'N/A')}")
        print(f"Source: {metadata.get('source', 'N/A')}")
        
        # Check parties field
        parties = metadata.get('parties', '')
        print(f"\nPARTIES field: '{parties}'")
        print(f"  Type: {type(parties)}")
        print(f"  Value: {repr(parties)}")
        
        # Check people field  
        people = metadata.get('people', '')
        print(f"\nPEOPLE field: '{people}'")
        print(f"  Type: {type(people)}")
        print(f"  Value: {repr(people)}")
        
        # Check all metadata keys
        print(f"\nAll metadata keys: {list(metadata.keys())}")
        
        # Show document preview
        print(f"\nDocument preview (first 200 chars):")
        print(f"  {document[:200]}...")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    check_metadata()
