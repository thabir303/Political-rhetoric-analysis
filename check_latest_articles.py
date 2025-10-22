"""
Check the LATEST 16 articles that were just stored
"""
import sys
sys.path.insert(0, '/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase

db = VectorDatabase(collection_name="political_articles")

print("="*80)
print("CHECKING LATEST 16 STORED ARTICLES")
print("="*80)
print(f"\n📊 Total articles in DB: {db.collection.count()}")

# Get last 16 articles (sorted by ID - latest ones)
all_results = db.collection.get(include=["metadatas"])
all_ids = all_results.get("ids", [])
all_metadatas = all_results.get("metadatas", [])

# Get articles with timestamp-based IDs (latest ones)
timestamped_articles = []
for i, (doc_id, metadata) in enumerate(zip(all_ids, all_metadatas)):
    if doc_id.startswith("article_1760"):  # Today's timestamp
        timestamped_articles.append({
            'id': doc_id,
            'metadata': metadata,
            'index': i
        })

# Sort by ID (descending - latest first)
timestamped_articles.sort(key=lambda x: x['id'], reverse=True)

print(f"\n🆕 Found {len(timestamped_articles)} articles from latest scraping")
print(f"Showing first 16:\n")

for i, article in enumerate(timestamped_articles[:16], 1):
    metadata = article['metadata']
    
    print(f"\n{'='*80}")
    print(f"Article {i}: {article['id']}")
    print(f"{'='*80}")
    print(f"📰 Title: {metadata.get('title', 'N/A')[:80]}")
    print(f"📅 Date: {metadata.get('date', 'N/A')}")
    print(f"📌 Source: {metadata.get('source', 'N/A')}")
    
    parties = metadata.get('parties', '')
    people = metadata.get('people', '')
    affiliations = metadata.get('people_affiliations', '{}')
    
    print(f"\n🏛️  Parties: '{parties}'")
    if not parties:
        print(f"   ❌ EMPTY - No parties stored!")
    else:
        print(f"   ✅ Has parties: {parties.split(',')}")
    
    print(f"\n👤 People: '{people}'")
    if not people:
        print(f"   ❌ EMPTY - No people stored!")
    else:
        print(f"   ✅ Has people: {people.split(',')}")
    
    print(f"\n🔗 Affiliations: {affiliations}")
    if affiliations == '{}' or not affiliations:
        print(f"   ❌ EMPTY - No affiliations!")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

articles_with_parties = sum(1 for a in timestamped_articles[:16] if a['metadata'].get('parties'))
articles_with_people = sum(1 for a in timestamped_articles[:16] if a['metadata'].get('people'))

print(f"\nOut of {min(16, len(timestamped_articles))} latest articles:")
print(f"✅ With Parties: {articles_with_parties} ({articles_with_parties/min(16, len(timestamped_articles))*100:.0f}%)")
print(f"❌ With People: {articles_with_people} ({articles_with_people/min(16, len(timestamped_articles))*100:.0f}%)")

if articles_with_people == 0:
    print(f"\n🔴 CRITICAL: NO PEOPLE DATA IN LATEST ARTICLES!")
    print(f"   This means the fix is NOT being applied during scraping!")
