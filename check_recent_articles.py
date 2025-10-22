"""
Check most recent articles to see if people field is being stored
"""
import sys
sys.path.insert(0, '/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase
from datetime import datetime

print("=" * 100)
print("CHECKING MOST RECENT ARTICLES")
print("=" * 100)

db = VectorDatabase(collection_name="political_articles")

# Get all articles
all_results = db.collection.get(include=["metadatas"])

# Find articles with IDs starting with article_1761137 (today's timestamp prefix)
# article_1761137158 means it was created around that timestamp
today_prefix = "article_17611"  # Today's articles will have this prefix
recent_articles = []

for doc_id, metadata in zip(all_results.get("ids", []), all_results.get("metadatas", [])):
    if doc_id.startswith(today_prefix):
        recent_articles.append((doc_id, metadata))

print(f"\n📊 Found {len(recent_articles)} recently scraped articles (with ID prefix '{today_prefix}')")
print("=" * 100)

print(f"\n📊 Found {len(recent_articles)} recently scraped articles (with ID prefix '{today_prefix}')")
print("=" * 100)

if recent_articles:
    print("\n🔍 Inspecting recently scraped articles:")
    for i, (doc_id, metadata) in enumerate(recent_articles[:20], 1):
        print(f"\n{i}. ID: {doc_id}")
        print(f"   Title: {metadata.get('title', 'N/A')[:80]}...")
        print(f"   Date: {metadata.get('date', 'N/A')}")
        
        parties = metadata.get('parties', '')
        people = metadata.get('people', '')
        people_aff = metadata.get('people_affiliations', '')
        
        print(f"   🏛️  Parties: '{parties}'")
        print(f"   👤 People: '{people}'")
        print(f"   🔗 Affiliations: '{people_aff}'")
        
        if not people:
            print(f"   ⚠️  People field is empty")
        else:
            print(f"   ✅ People field has data")
        
        print("   " + "-" * 96)
else:
    print(f"\n❌ No recently scraped articles found")
    print("   Articles might be using a different ID format")

print("\n" + "=" * 100)
