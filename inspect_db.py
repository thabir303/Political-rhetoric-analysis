#!/usr/bin/env python3
"""
Database Visualization Script

This script queries the ChromaDB database and displays stored articles
with their political categorization and metadata for inspection.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import chromadb
from chromadb.config import Settings

def inspect_database():
    """
    Inspect the ChromaDB database and display stored articles.
    """
    print("🔍 Database Inspection Tool")
    print("=" * 50)

    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=os.path.join(os.getcwd(), "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get the political_articles collection
        collection = client.get_collection("political_articles")

        # Get total count
        total_count = collection.count()
        print(f"📊 Total articles in database: {total_count}")

        if total_count == 0:
            print("❌ No articles found in database")
            return

        # Query all articles (limit to last 50 for display)
        results = collection.get(
            limit=50,
            include=["documents", "metadatas"]
        )

        articles = results.get("metadatas", [])
        documents = results.get("documents", [])
        ids = results.get("ids", [])

        print(f"\n📋 Displaying last {len(articles)} articles:")
        print("=" * 80)

        for i, (article_id, metadata, document) in enumerate(zip(ids, articles, documents)):
            print(f"\n📰 Article {i+1} (ID: {article_id})")
            print("-" * 40)

            # Basic info
            title = metadata.get('title', 'No title')
            date = metadata.get('date', 'No date')
            source = metadata.get('source', 'Unknown source')
            category = metadata.get('category', 'Unknown category')

            print(f"📅 Date: {date}")
            print(f"📰 Source: {source}")
            print(f"🏷️  Category: {category}")
            print(f"📖 Title: {title}")

            # Political categorization
            parties = metadata.get('parties', '')
            people = metadata.get('people', '')
            keywords = metadata.get('keywords', '')
            themes = metadata.get('themes', '')
            
            # New political entity fields
            political_entities = metadata.get('political_entities', '')
            mentioned_figures = metadata.get('mentioned_figures', '')
            primary_parties = metadata.get('primary_parties', '')

            if parties:
                print(f"🏛️  Parties: {parties}")
            if people:
                print(f"👥 People: {people}")
            if political_entities:
                print(f"🔗 Political Entities: {political_entities[:100]}...")
            if mentioned_figures:
                print(f"👤 Mentioned Figures: {mentioned_figures}")
            if primary_parties:
                print(f"🏛️  Primary Parties: {primary_parties}")
            if keywords:
                print(f"🔑 Keywords: {keywords[:100]}...")
            if themes:
                print(f"📋 Themes: {themes}")

            # LLM analysis fields (if present)
            llm_summary = metadata.get('llm_summary', '')
            llm_stance = metadata.get('llm_stance', '')
            llm_figure = metadata.get('llm_figure', '')
            llm_party = metadata.get('llm_party', '')

            if llm_summary:
                print(f"🤖 LLM Summary: {llm_summary[:100]}...")
            if llm_stance:
                print(f"📊 LLM Stance: {llm_stance[:100]}...")
            if llm_figure:
                print(f"👤 LLM Figure: {llm_figure}")
            if llm_party:
                print(f"🏛️  LLM Party: {llm_party}")

            # Content preview
            content_preview = document[:200] + "..." if len(document) > 200 else document
            print(f"📝 Content Preview: {content_preview}")

            print()

        # Summary statistics
        print("📈 Summary Statistics:")
        print("-" * 30)

        # Count by source
        sources = {}
        categories = {}
        parties_count = {}
        people_count = {}

        for metadata in articles:
            source = metadata.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1

            category = metadata.get('category', 'Unknown')
            categories[category] = categories.get(category, 0) + 1

            # Count parties
            parties_str = metadata.get('parties', '')
            if parties_str:
                for party in parties_str.split(', '):
                    party = party.strip()
                    if party:
                        parties_count[party] = parties_count.get(party, 0) + 1

            # Count people
            people_str = metadata.get('people', '')
            if people_str:
                for person in people_str.split(', '):
                    person = person.strip()
                    if person:
                        people_count[person] = people_count.get(person, 0) + 1

        print("By Source:")
        for source, count in sources.items():
            print(f"  {source}: {count}")

        print("\nBy Category:")
        for category, count in categories.items():
            print(f"  {category}: {count}")

        print("\nTop Parties:")
        sorted_parties = sorted(parties_count.items(), key=lambda x: x[1], reverse=True)
        for party, count in sorted_parties[:10]:
            print(f"  {party}: {count}")

        print("\nTop People:")
        sorted_people = sorted(people_count.items(), key=lambda x: x[1], reverse=True)
        for person, count in sorted_people[:10]:
            print(f"  {person}: {count}")

    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()

def query_by_party(party_name: str):
    """
    Query articles by specific party.
    """
    print(f"🔍 Querying articles for party: {party_name}")
    print("=" * 50)

    try:
        client = chromadb.PersistentClient(
            path=os.path.join(os.getcwd(), "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )

        collection = client.get_collection("political_articles")

        # Get all articles and filter manually (ChromaDB string filtering is limited)
        results = collection.get(
            include=["documents", "metadatas"]
        )
        
        # Filter results manually
        filtered_articles = []
        filtered_docs = []
        filtered_ids = []
        
        all_metadatas = results.get("metadatas", [])
        all_documents = results.get("documents", [])
        all_ids = results.get("ids", [])
        
        for i, meta in enumerate(all_metadatas):
            parties_str = meta.get('parties', '')
            primary_parties = meta.get('primary_parties', '')
            
            # Check if party name appears in either field
            if party_name.upper() in parties_str.upper() or party_name.upper() in primary_parties.upper():
                filtered_articles.append(meta)
                filtered_docs.append(all_documents[i])
                filtered_ids.append(all_ids[i])
                
                if len(filtered_articles) >= 20:  # Limit to 20
                    break
        
        articles = filtered_articles
        documents = filtered_docs
        ids = filtered_ids

        
        articles = filtered_articles
        documents = filtered_docs
        ids = filtered_ids

        print(f"📊 Found {len(articles)} articles mentioning '{party_name}':")
        print()

        for i, (article_id, metadata, document) in enumerate(zip(ids, articles, documents)):
            title = metadata.get('title', 'No title')
            date = metadata.get('date', 'No date')
            source = metadata.get('source', 'Unknown')

            print(f"{i+1}. [{date}] {title}")
            print(f"   Source: {source}")
            print(f"   Parties: {metadata.get('parties', 'N/A')}")
            print(f"   People: {metadata.get('people', 'N/A')}")
            print()

    except Exception as e:
        print(f"❌ Error querying by party: {e}")

def main():
    """
    Main function to run the database inspection.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--party" and len(sys.argv) > 2:
            query_by_party(sys.argv[2])
        else:
            print("Usage:")
            print("  python inspect_db.py              # Inspect all articles")
            print("  python inspect_db.py --party BNP  # Query articles for specific party")
    else:
        inspect_database()

if __name__ == "__main__":
    main()