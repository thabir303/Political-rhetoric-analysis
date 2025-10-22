#!/usr/bin/env python3
"""Check all recently scraped articles (article_17611* prefix)"""

import sys
sys.path.append('backend')

from core.vector_db import VectorDatabase

# Initialize database
db = VectorDatabase()

# Get the political_articles collection
collection = db.client.get_collection(
    name="political_articles",
    embedding_function=db.embedding_function
)

# Get all documents
all_docs = collection.get()

# Filter for recent articles
recent_articles = []
for i, doc_id in enumerate(all_docs['ids']):
    if doc_id.startswith('article_17611'):
        metadata = all_docs['metadatas'][i]
        recent_articles.append({
            'id': doc_id,
            'title': metadata.get('title', 'N/A')[:50],
            'date': metadata.get('date', 'N/A'),
            'parties': metadata.get('parties', ''),
            'people': metadata.get('people', ''),
            'has_people': bool(metadata.get('people', '').strip())
        })

# Sort by ID
recent_articles.sort(key=lambda x: x['id'])

print(f"\n📊 Total recent articles: {len(recent_articles)}")
print(f"✅ Articles with people data: {sum(1 for a in recent_articles if a['has_people'])}")
print(f"⚠️  Articles without people data: {sum(1 for a in recent_articles if not a['has_people'])}")

print("\n" + "="*80)
print("ARTICLES WITHOUT PEOPLE DATA:")
print("="*80)
for article in recent_articles:
    if not article['has_people']:
        print(f"\nID: {article['id']}")
        print(f"  Title: {article['title']}...")
        print(f"  Date: {article['date']}")
        print(f"  Parties: {article['parties']}")

print("\n" + "="*80)
print("ARTICLES WITH PEOPLE DATA:")
print("="*80)
for article in recent_articles:
    if article['has_people']:
        print(f"\nID: {article['id']}")
        print(f"  Title: {article['title']}...")
        print(f"  People: {article['people']}")
        print(f"  Parties: {article['parties']}")
