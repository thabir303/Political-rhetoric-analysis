"""
Debug script to check what's stored in the database
"""
import sys
sys.path.insert(0, '/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase

print("=" * 100)
print("DATABASE INSPECTION - Check Party/Figure Storage")
print("=" * 100)

# Initialize database
db = VectorDatabase(collection_name="political_articles")

print(f"\n📊 Total articles in database: {db.collection.count()}")

# Get last 20 articles (to see the newly scraped ones)
print("\n🔍 Inspecting last 20 articles...")
print("=" * 100)

all_results = db.collection.get(
    limit=20,
    include=["metadatas", "documents"]
)

if not all_results or not all_results.get("metadatas"):
    print("❌ No articles found in database!")
else:
    for i, (doc_id, metadata) in enumerate(zip(
        all_results.get("ids", []),
        all_results.get("metadatas", [])
    ), 1):
        print(f"\n📄 Article {i}: {doc_id}")
        print(f"   Title: {metadata.get('title', 'N/A')[:80]}...")
        print(f"   Date: {metadata.get('date', 'N/A')}")
        print(f"   Source: {metadata.get('source', 'N/A')}")
        
        # Check parties field
        parties_str = metadata.get('parties', '')
        if parties_str:
            parties = [p.strip() for p in parties_str.split(',') if p.strip()]
            print(f"   🏛️  Parties (stored): '{parties_str}'")
            print(f"   🏛️  Parties (parsed): {parties}")
        else:
            print(f"   ⚠️  No parties stored!")
        
        # Check people field
        people_str = metadata.get('people', '')
        if people_str:
            people = [p.strip() for p in people_str.split(',') if p.strip()]
            print(f"   👤 People (stored): '{people_str}'")
            print(f"   👤 People (parsed): {people}")
        else:
            print(f"   ⚠️  No people stored!")
        
        # Check people_affiliations
        affiliations_str = metadata.get('people_affiliations', '')
        if affiliations_str:
            print(f"   🔗 Affiliations: {affiliations_str}")
        
        print("   " + "-" * 96)

# Now query for specific parties
print("\n" + "=" * 100)
print("🔍 QUERY TEST: Articles for BNP")
print("=" * 100)

# Try to filter by BNP
all_results = db.collection.get(include=["metadatas", "documents"])
bnp_count = 0
ncp_count = 0
jamaat_count = 0

for metadata in all_results.get("metadatas", []):
    parties_str = metadata.get("parties", "")
    if "BNP" in parties_str:
        bnp_count += 1
    if "NCP" in parties_str:
        ncp_count += 1
    if "Jamaat" in parties_str or "Jamaat-e-Islami" in parties_str:
        jamaat_count += 1

print(f"\n📊 Party Distribution:")
print(f"   BNP: {bnp_count} articles")
print(f"   NCP: {ncp_count} articles")
print(f"   Jamaat-e-Islami: {jamaat_count} articles")

# Show some BNP articles
print("\n🔍 Sample BNP Articles (first 5):")
bnp_articles = []
for doc_id, metadata in zip(all_results.get("ids", []), all_results.get("metadatas", [])):
    parties_str = metadata.get("parties", "")
    if "BNP" in parties_str:
        bnp_articles.append((doc_id, metadata))
        if len(bnp_articles) >= 5:
            break

for i, (doc_id, metadata) in enumerate(bnp_articles, 1):
    print(f"\n{i}. {metadata.get('title', 'N/A')[:80]}...")
    print(f"   Date: {metadata.get('date', 'N/A')}")
    print(f"   Parties: {metadata.get('parties', 'N/A')}")
    print(f"   People: {metadata.get('people', 'N/A')}")

print("\n" + "=" * 100)
print("✅ Inspection complete")
print("=" * 100)
