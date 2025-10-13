"""
Complete RAG-IR Pipeline Demo with Real Scraping + LLM Analysis

This script demonstrates the ENTIRE flow:
1. Scrape newspapers → 2. Categorize → 3. Embed → 4. LLM Analysis → 5. Store in Vector DB

Run: python scripts/live_pipeline_demo.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all modules
from scraping import ProthomAloScraper, DailyStarScraper, JugantorScraper, DhakaTribuneScraper
from categorization import ArticleCategorizer
from embeddings import EmbeddingGenerator
from llm_generation import LLMGenerator
from vector_db import VectorDatabase

print("=" * 100)
print(" " * 30 + "RAG-IR COMPLETE PIPELINE DEMO")
print(" " * 20 + "Newspaper Scraping → LLM Analysis → Vector Storage")
print("=" * 100)

# Configuration
USE_REAL_SCRAPING = True  # Set False to use sample data
MAX_ARTICLES_PER_SOURCE = 3  # Limit for demo
START_DATE = "2024-08-05"
END_DATE = "2025-09-30"

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def print_step(step_num, total_steps, description):
    """Print a step header."""
    print(f"\n{'─' * 100}")
    print(f"  [{step_num}/{total_steps}] {description}")
    print("─" * 100)

def print_article_summary(article, index):
    """Print article summary."""
    print(f"\n  Article #{index + 1}:")
    print(f"  ├─ Title: {article.get('title', 'N/A')[:80]}...")
    print(f"  ├─ Source: {article.get('source', 'N/A')}")
    print(f"  ├─ Date: {article.get('date', 'N/A')}")
    print(f"  ├─ Language: {article.get('language', 'N/A')}")
    print(f"  ├─ Parties: {', '.join(article.get('parties', [])) or 'None detected'}")
    print(f"  ├─ People: {', '.join(article.get('people', [])) or 'None detected'}")
    print(f"  └─ Content: {len(article.get('content', ''))} characters")

def print_categorization_results(article):
    """Print categorization results."""
    print(f"\n  Categorization Results:")
    print(f"  ├─ Themes: {', '.join(article.get('themes', [])) or 'None'}")
    print(f"  ├─ Keywords: {', '.join(article.get('keywords', [])[:5]) or 'None'}")
    print(f"  ├─ Is Speech: {'Yes ✓' if article.get('is_speech') else 'No'}")
    print(f"  └─ Is Stance: {'Yes ✓' if article.get('is_stance') else 'No'}")

def print_llm_results(article):
    """Print LLM analysis results."""
    llm_summary = article.get('llm_summary', {})
    llm_keywords = article.get('llm_keywords', {})
    
    if llm_summary:
        print(f"\n  🎤 LLM Speech Summary:")
        summary_text = llm_summary.get('summary', 'N/A')
        print(f"     {summary_text[:200]}...")
        
        key_points = llm_summary.get('key_points', [])
        if key_points:
            print(f"\n  📋 Key Points:")
            for i, point in enumerate(key_points[:3], 1):
                print(f"     {i}. {point}")
        
        stance = llm_summary.get('stance_analysis', '')
        if stance:
            print(f"\n  🎯 Political Stance:")
            print(f"     {stance[:150]}...")
    
    if llm_keywords:
        keywords = llm_keywords.get('keywords', [])
        topics = llm_keywords.get('topics', [])
        
        if keywords:
            print(f"\n  🏷️  LLM Keywords: {', '.join(keywords[:8])}")
        if topics:
            print(f"  📊 LLM Topics: {', '.join(topics[:5])}")

# ============================================================================
# STEP 1: NEWSPAPER SCRAPING
# ============================================================================

print_step(1, 6, "NEWSPAPER SCRAPING")

all_articles = []

if USE_REAL_SCRAPING:
    print("\n  🌐 Starting real newspaper scraping...")
    print(f"  📅 Date Range: {START_DATE} to {END_DATE}")
    print(f"  📰 Newspapers: Prothom Alo, Daily Star, Jugantor, Dhaka Tribune")
    
    scrapers = [
        ("Prothom Alo", ProthomAloScraper(START_DATE, END_DATE)),
        ("Daily Star", DailyStarScraper(START_DATE, END_DATE)),
        ("Jugantor", JugantorScraper(START_DATE, END_DATE)),
        ("Dhaka Tribune", DhakaTribuneScraper(START_DATE, END_DATE))
    ]
    
    for name, scraper in scrapers:
        print(f"\n  🔍 Scraping {name}...")
        try:
            articles = scraper.scrape_articles()
            # Limit for demo
            articles = articles[:MAX_ARTICLES_PER_SOURCE]
            all_articles.extend(articles)
            print(f"  ✓ Found {len(articles)} articles from {name}")
        except Exception as e:
            print(f"  ✗ Error scraping {name}: {str(e)}")
            continue
else:
    # Use sample data if real scraping disabled
    print("\n  📝 Using sample articles for demo...")
    all_articles = [
        {
            'title': 'BNP Demands Comprehensive Election Reforms',
            'content': '''BNP acting chairman Tareq Rahman addressed party members in a virtual rally,
            calling for sweeping election reforms. He emphasized that free and fair elections
            are essential for democracy and criticized the current Election Commission structure.
            Rahman proposed a neutral caretaker government system for election oversight.
            "We demand immediate reforms to ensure transparent elections," Rahman stated.''',
            'date': '2024-10-05',
            'source': 'Daily Star',
            'url': 'https://example.com/bnp-election-reforms',
            'language': 'English'
        },
        {
            'title': 'Dr. Yunus Outlines Economic Reform Strategy',
            'content': '''Chief Adviser Dr. Muhammad Yunus presented the interim government's economic
            reform agenda, focusing on inflation control and GDP growth acceleration.
            He discussed monetary policy adjustments and structural reforms to attract
            foreign investment. "Our priority is economic stability," Dr. Yunus said.
            The plan includes banking sector reforms and anti-corruption measures.''',
            'date': '2024-10-06',
            'source': 'Dhaka Tribune',
            'url': 'https://example.com/yunus-economic-reforms',
            'language': 'English'
        }
    ]

print(f"\n  ✓ Total articles scraped: {len(all_articles)}")

if not all_articles:
    print("\n  ⚠️  No articles found. Exiting...")
    sys.exit(1)

# Show sample articles
print("\n  📄 Sample scraped articles:")
for i, article in enumerate(all_articles[:2]):
    print_article_summary(article, i)

# ============================================================================
# STEP 2: ARTICLE CATEGORIZATION
# ============================================================================

print_step(2, 6, "ARTICLE CATEGORIZATION & KEYWORD EXTRACTION")

print("\n  🏷️  Initializing categorizer...")
categorizer = ArticleCategorizer()

print("  📊 Processing articles...")
categorized_articles = []

for i, article in enumerate(all_articles):
    print(f"\n  Processing article {i+1}/{len(all_articles)}: {article['title'][:50]}...")
    
    # Categorize article
    categorized = categorizer.categorize_article(article)
    categorized_articles.append(categorized)
    
    print_categorization_results(categorized)

print(f"\n  ✓ Categorized {len(categorized_articles)} articles")

# ============================================================================
# STEP 3: EMBEDDING GENERATION
# ============================================================================

print_step(3, 6, "EMBEDDING GENERATION")

print("\n  🧠 Initializing embedding model (all-MiniLM-L6-v2)...")
try:
    embedder = EmbeddingGenerator(model_name='all-MiniLM-L6-v2')
    print(f"  ✓ Model loaded. Embedding dimension: {embedder.get_embedding_dimension()}")
    
    print("\n  🔢 Generating embeddings for articles...")
    
    # Prepare texts (title + content)
    texts = []
    for article in categorized_articles:
        text = f"{article.get('title', '')}\n\n{article.get('content', '')}"
        texts.append(text)
    
    # Generate embeddings
    embeddings = embedder.generate_embeddings(texts, show_progress=True)
    
    print(f"  ✓ Generated {len(embeddings)} embeddings")
    print(f"  ✓ Shape: {embeddings.shape}")
    
    # Add embeddings to articles
    for i, article in enumerate(categorized_articles):
        article['embedding'] = embeddings[i]
    
except Exception as e:
    print(f"  ⚠️  Error generating embeddings: {str(e)}")
    print("  ⚠️  Continuing without embeddings (ChromaDB will generate them)")
    embeddings = None

# ============================================================================
# STEP 4: LLM ANALYSIS (Speech Summarization & Keyword Extraction)
# ============================================================================

print_step(4, 6, "LLM ANALYSIS (Groq API - LLaMA 3.3 70B)")

print("\n  🤖 Initializing LLM Generator...")
try:
    llm = LLMGenerator(model="llama-3.3-70b-versatile", temperature=0.3)
    print(f"  ✓ LLM initialized: {llm.model}")
    
    print("\n  📝 Processing articles with LLM...")
    
    for i, article in enumerate(categorized_articles):
        print(f"\n  {'-' * 80}")
        print(f"  Processing article {i+1}/{len(categorized_articles)}: {article['title'][:60]}...")
        
        # Check if it's a speech
        is_speech = article.get('is_speech', False)
        
        if is_speech:
            print("  🎤 Detected as speech - generating summary...")
            
            # Find political figure and party
            people = article.get('people', [])
            parties = article.get('parties', [])
            
            political_figure = people[0] if people else "Political Figure"
            political_party = parties[0] if parties else "Political Party"
            
            try:
                # Generate speech summary
                summary_result = llm.generate_speech_summary(
                    article_text=article['content'],
                    political_figure=political_figure,
                    political_party=political_party
                )
                
                article['llm_summary'] = summary_result
                print("  ✓ Speech summary generated")
                
            except Exception as e:
                print(f"  ✗ Error generating summary: {str(e)}")
        else:
            print("  📰 Not detected as speech - skipping speech summary")
        
        # Extract keywords for all articles
        print("  🔍 Extracting keywords with LLM...")
        try:
            keywords_result = llm.extract_keywords(
                article_text=article['content'],
                num_keywords=10,
                num_phrases=5,
                include_topics=True
            )
            
            article['llm_keywords'] = keywords_result
            print("  ✓ Keywords extracted")
            
        except Exception as e:
            print(f"  ✗ Error extracting keywords: {str(e)}")
        
        # Show LLM results
        print_llm_results(article)
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n  ✓ LLM analysis completed for {len(categorized_articles)} articles")
    
except Exception as e:
    print(f"  ⚠️  LLM initialization failed: {str(e)}")
    print("  ⚠️  Continuing without LLM analysis")

# ============================================================================
# STEP 5: VECTOR DATABASE STORAGE
# ============================================================================

print_step(5, 6, "VECTOR DATABASE STORAGE")

print("\n  💾 Initializing ChromaDB...")
db = VectorDatabase(
    persist_directory="./live_demo_chroma_db",
    collection_name="live_demo_articles",
    embedding_model="all-MiniLM-L6-v2"
)

print(f"  ✓ Database initialized")
print(f"  📍 Location: ./live_demo_chroma_db")
print(f"  📦 Collection: live_demo_articles")
print(f"  📊 Current count: {db.collection.count()} documents")

print("\n  💾 Storing articles with embeddings and LLM analysis...")

# Prepare articles for storage
articles_to_store = []
for i, article in enumerate(categorized_articles):
    # Generate unique ID
    article['id'] = f"article_{datetime.now().timestamp()}_{i}"
    articles_to_store.append(article)

# Store in database
result = db.store_embeddings(
    articles=articles_to_store,
    batch_size=10
)

if result.get('success'):
    print(f"  ✓ Successfully stored {result.get('stored', 0)} articles")
    print(f"  ✓ Total documents in database: {db.collection.count()}")
else:
    print(f"  ✗ Storage failed: {result.get('message', 'Unknown error')}")

# ============================================================================
# STEP 6: QUERY DEMONSTRATION
# ============================================================================

print_step(6, 6, "SEMANTIC SEARCH DEMONSTRATION")

print("\n  🔍 Testing semantic search with stored articles...")

test_queries = [
    "election reforms",
    "economic policy",
    "BNP political stance"
]

for query in test_queries:
    print(f"\n  {'─' * 80}")
    print(f"  Query: '{query}'")
    print(f"  {'─' * 80}")
    
    try:
        # Search in vector database
        search_results = db.query_articles(
            query_text=query,
            top_k=3
        )
        
        results = search_results.get('results', [])
        print(f"  ✓ Found {len(results)} relevant articles")
        
        for i, result in enumerate(results[:2], 1):
            metadata = result.get('metadata', {})
            distance = result.get('distance', 0)
            similarity = 1 - distance
            
            print(f"\n  Result #{i} (Similarity: {similarity*100:.1f}%):")
            print(f"  ├─ Title: {metadata.get('title', 'N/A')[:70]}...")
            print(f"  ├─ Date: {metadata.get('date', 'N/A')}")
            print(f"  ├─ Source: {metadata.get('source', 'N/A')}")
            print(f"  ├─ Parties: {', '.join(metadata.get('parties', []))}")
            
            # Show LLM summary if available
            llm_summary = metadata.get('llm_summary')
            if llm_summary:
                print(f"  └─ Summary: {llm_summary[:100]}...")
        
    except Exception as e:
        print(f"  ✗ Search error: {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================

print_section("PIPELINE EXECUTION COMPLETE")

print(f"""
  📊 Summary:
  ├─ Articles Scraped:     {len(all_articles)}
  ├─ Articles Categorized: {len(categorized_articles)}
  ├─ Embeddings Generated: {len(embeddings) if embeddings is not None else 'N/A'}
  ├─ LLM Analyses:         {sum(1 for a in categorized_articles if 'llm_summary' in a or 'llm_keywords' in a)}
  ├─ Articles Stored:      {db.collection.count()}
  └─ Database Location:    ./live_demo_chroma_db

  ✅ Complete pipeline executed successfully!
  
  🔗 Data Flow:
     Newspapers → Scraping → Categorization → Embeddings → LLM Analysis → Vector DB
  
  📝 Next Steps:
     1. Start backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000
     2. Start frontend: cd frontend && npm run dev
     3. Browse articles at: http://localhost:5174
""")

print("=" * 100)
