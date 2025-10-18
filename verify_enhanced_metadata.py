#!/usr/bin/env python3
"""
Verify Enhanced Metadata in Database

Checks if LLM analysis fields are properly stored in ChromaDB.
"""

import sys
sys.path.append('/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase

def verify_enhanced_metadata():
    """Check if enhanced LLM fields are in database."""
    
    print("=" * 80)
    print("🔍 Verifying Enhanced Metadata in Database")
    print("=" * 80)
    
    # Initialize database
    db = VectorDatabase(collection_name="political_articles")
    
    # Get a few articles
    results = db.collection.get(
        limit=5,
        include=["metadatas", "documents"]
    )
    
    if not results or not results['metadatas']:
        print("\n❌ No articles found in database!")
        print("   Run scraping first: POST /api/v1/scraping/newspapers")
        return
    
    print(f"\n✅ Found {len(results['metadatas'])} articles\n")
    
    # Check what fields are present
    all_fields = set()
    enhanced_fields = {
        'summary', 'keywords', 'topics', 
        'has_election_impact', 'election_impact_description', 'election_impact_parties',
        'political_party', 'political_figures'
    }
    
    for metadata in results['metadatas']:
        all_fields.update(metadata.keys())
    
    print("📊 Metadata Fields Found:")
    print("-" * 80)
    for field in sorted(all_fields):
        is_enhanced = '✨' if field in enhanced_fields else '  '
        print(f"  {is_enhanced} {field}")
    
    print("\n")
    print("🎯 Enhanced LLM Fields Status:")
    print("-" * 80)
    
    for field in enhanced_fields:
        if field in all_fields:
            # Count how many articles have this field
            count = sum(1 for m in results['metadatas'] if m.get(field))
            print(f"  ✅ {field:35s} - Found in {count}/{len(results['metadatas'])} articles")
        else:
            print(f"  ❌ {field:35s} - NOT FOUND")
    
    print("\n")
    print("📝 Sample Article Details:")
    print("=" * 80)
    
    # Show first article with details
    if results['metadatas']:
        metadata = results['metadatas'][0]
        document = results['documents'][0] if results['documents'] else ""
        
        print(f"\n🔹 Title: {metadata.get('title', 'N/A')}")
        print(f"🔹 Date: {metadata.get('date', 'N/A')}")
        print(f"🔹 Source: {metadata.get('source', 'N/A')}")
        
        print(f"\n📄 Summary:")
        print(f"   {metadata.get('summary', '❌ No summary found')[:200]}...")
        
        print(f"\n🏷️  Topics:")
        print(f"   {metadata.get('topics', '❌ No topics found')}")
        
        print(f"\n🔑 Keywords:")
        print(f"   {metadata.get('keywords', '❌ No keywords found')[:150]}...")
        
        print(f"\n🗳️  Election Impact:")
        has_impact = metadata.get('has_election_impact', 'false')
        print(f"   Has Impact: {has_impact}")
        if has_impact == 'True' or has_impact == 'true':
            print(f"   Description: {metadata.get('election_impact_description', 'N/A')[:200]}...")
            print(f"   Affected Parties: {metadata.get('election_impact_parties', 'N/A')}")
        
        print(f"\n👤 Political Entities:")
        print(f"   Party: {metadata.get('political_party', 'N/A')}")
        print(f"   Figures: {metadata.get('political_figures', 'N/A')}")
    
    print("\n" + "=" * 80)
    
    # Check if we need to reprocess
    has_enhanced = any(field in all_fields for field in enhanced_fields)
    
    if not has_enhanced:
        print("\n⚠️  WARNING: No enhanced LLM fields found!")
        print("\n💡 Solutions:")
        print("   1. Make sure backend server is running with updated code")
        print("   2. Run new scraping to generate enhanced metadata:")
        print("      POST /api/v1/scraping/newspapers")
        print("   3. Or reprocess existing articles:")
        print("      python3 reprocess_articles.py")
    else:
        print("\n✅ Enhanced metadata is working!")
        print("   Your frontend should now display:")
        print("   - Article summaries")
        print("   - Clickable keywords")
        print("   - Topic tags")
        print("   - Election impact badges")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        verify_enhanced_metadata()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
