"""
Clear all articles from the database
"""
import sys
sys.path.insert(0, '/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase

print("="*80)
print("DATABASE RESET - Clearing All Articles")
print("="*80)

db = VectorDatabase(collection_name="political_articles")

# Get current count
current_count = db.collection.count()
print(f"\n📊 Current articles in database: {current_count}")

if current_count == 0:
    print("\n✅ Database is already empty!")
    sys.exit(0)

# Confirm
print(f"\n⚠️  WARNING: This will delete ALL {current_count} articles!")
print("   This action CANNOT be undone!")

response = input("\nType 'DELETE' to confirm: ")

if response.strip() != "DELETE":
    print("\n❌ Cancelled. No changes made.")
    sys.exit(0)

# Reset collection
print("\n🗑️  Deleting collection...")
db.reset_collection()

# Verify
new_count = db.collection.count()
print(f"\n✅ Database cleared successfully!")
print(f"   Articles before: {current_count}")
print(f"   Articles after: {new_count}")
print("\n" + "="*80)
print("You can now scrape new articles with the fixed categorization!")
print("="*80)
