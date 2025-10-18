#!/usr/bin/env python3
"""
Database Inspection Tool

Visualize and inspect articles stored in ChromaDB to verify:
1. How articles are saved
2. Political entities extraction
3. Categorization results
4. Enhanced political_entities field
"""

import sys
import json
from datetime import datetime
from collections import Counter
sys.path.append('/home/bs01127/Desktop/RAG-IR')

from backend.core.vector_db import VectorDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.syntax import Syntax

console = Console()

def inspect_database(limit=10, show_details=False):
    """
    Inspect ChromaDB and show how articles are stored.
    """
    console.print("\n[bold cyan]🔍 DATABASE INSPECTION TOOL[/bold cyan]\n")
    
    # Initialize VectorDB
    try:
        db = VectorDatabase(
            persist_directory="./chroma_db",
            collection_name="political_articles"
        )
        console.print(f"✅ Connected to database: [green]{db.collection_name}[/green]")
        console.print(f"📊 Total documents: [yellow]{db.collection.count()}[/yellow]\n")
    except Exception as e:
        console.print(f"[red]❌ Error connecting to database: {e}[/red]")
        return
    
    # Get recent articles
    try:
        results = db.collection.get(
            limit=limit,
            include=['documents', 'metadatas']
        )
    except Exception as e:
        console.print(f"[red]❌ Error fetching articles: {e}[/red]")
        return
    
    if not results['ids']:
        console.print("[yellow]⚠️  No articles found in database[/yellow]")
        return
    
    # Show summary statistics
    show_database_summary(results)
    
    # Show individual articles
    console.print(f"\n[bold cyan]📰 RECENT ARTICLES (Last {len(results['ids'])})[/bold cyan]\n")
    
    for i, (doc_id, doc, meta) in enumerate(zip(results['ids'], results['documents'], results['metadatas']), 1):
        show_article_card(i, doc_id, doc, meta, show_details)
    
    # Show political entities analysis
    show_political_entities_analysis(results['metadatas'])


def show_database_summary(results):
    """Show summary statistics about the database."""
    metadatas = results['metadatas']
    
    # Count statistics
    sources = Counter(m.get('source', 'Unknown') for m in metadatas)
    languages = Counter(m.get('language', 'Unknown') for m in metadatas)
    categories = Counter(m.get('category', 'Unknown') for m in metadatas)
    
    # Extract political entities
    all_parties = []
    all_figures = []
    
    for meta in metadatas:
        # Check for enhanced political_entities field
        if 'political_entities' in meta:
            # Parse JSON if stored as string
            try:
                entities = json.loads(meta['political_entities']) if isinstance(meta['political_entities'], str) else meta['political_entities']
                all_parties.extend(entities.keys())
                for party_data in entities.values():
                    all_figures.extend(party_data.get('figures', []))
            except:
                pass
        
        # Also check primary_parties and mentioned_figures
        if 'primary_parties' in meta:
            parties = meta['primary_parties'].split(', ') if isinstance(meta['primary_parties'], str) else [meta['primary_parties']]
            all_parties.extend(parties)
        
        if 'mentioned_figures' in meta:
            figures = meta['mentioned_figures'].split(', ') if isinstance(meta['mentioned_figures'], str) else [meta['mentioned_figures']]
            all_figures.extend(figures)
    
    party_counts = Counter(all_parties)
    figure_counts = Counter(all_figures)
    
    # Create summary table
    table = Table(title="📊 Database Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="yellow", justify="right")
    table.add_column("Details", style="green")
    
    table.add_row("Total Articles", str(len(metadatas)), "")
    table.add_row("", "", "")
    
    # Sources
    table.add_row("Sources", str(len(sources)), ", ".join(f"{s}({c})" for s, c in sources.most_common(3)))
    
    # Languages
    table.add_row("Languages", str(len(languages)), ", ".join(f"{l}({c})" for l, c in languages.most_common()))
    
    # Categories
    table.add_row("Categories", str(len(categories)), ", ".join(f"{c}({n})" for c, n in categories.most_common(3)))
    
    table.add_row("", "", "")
    
    # Political entities
    table.add_row("Unique Parties", str(len(party_counts)), ", ".join(f"{p}({c})" for p, c in party_counts.most_common(5)))
    table.add_row("Unique Figures", str(len(figure_counts)), ", ".join(f"{f}({c})" for f, c in figure_counts.most_common(5)))
    
    console.print(table)


def show_article_card(index, doc_id, document, metadata, show_details=False):
    """Display an article card with all extracted information."""
    
    # Extract title and content
    parts = document.split('\n\n', 1)
    title = parts[0] if parts else document[:100]
    content = parts[1] if len(parts) > 1 else document
    
    # Create card content
    card_lines = []
    
    # Basic info
    card_lines.append(f"[bold yellow]📰 Article #{index}[/bold yellow]")
    card_lines.append(f"[bold]ID:[/bold] {doc_id}")
    card_lines.append(f"[bold]Title:[/bold] {title[:100]}...")
    card_lines.append("")
    
    # Metadata
    card_lines.append("[bold cyan]📋 Metadata:[/bold cyan]")
    card_lines.append(f"  • Source: [green]{metadata.get('source', 'N/A')}[/green]")
    card_lines.append(f"  • Date: [green]{metadata.get('date', 'N/A')}[/green]")
    card_lines.append(f"  • Language: [green]{metadata.get('language', 'N/A')}[/green]")
    card_lines.append(f"  • Category: [green]{metadata.get('category', 'N/A')}[/green]")
    
    if metadata.get('url'):
        card_lines.append(f"  • URL: [blue]{metadata['url'][:80]}...[/blue]")
    
    card_lines.append("")
    
    # Political entities (Enhanced structure)
    card_lines.append("[bold magenta]🏛️  Political Entities:[/bold magenta]")
    
    # Check for enhanced political_entities field
    if 'political_entities' in metadata:
        try:
            # Parse JSON if stored as string
            entities = json.loads(metadata['political_entities']) if isinstance(metadata['political_entities'], str) else metadata['political_entities']
            
            if entities:
                for party, party_data in entities.items():
                    party_mentioned = party_data.get('party_mentioned', False)
                    figures = party_data.get('figures', [])
                    
                    status = "✅ Party name mentioned" if party_mentioned else "👤 Only figures mentioned"
                    card_lines.append(f"  • [yellow]{party}[/yellow] - {status}")
                    
                    if figures:
                        card_lines.append(f"    Figures: {', '.join(figures)}")
            else:
                card_lines.append("  • [dim]No specific entities (General Politics)[/dim]")
        except Exception as e:
            card_lines.append(f"  • [red]Error parsing entities: {e}[/red]")
    
    # Fallback to primary_parties
    elif 'primary_parties' in metadata:
        parties = metadata['primary_parties']
        card_lines.append(f"  • Parties: [yellow]{parties}[/yellow]")
    
    # Mentioned figures
    if 'mentioned_figures' in metadata and metadata['mentioned_figures']:
        figures = metadata['mentioned_figures']
        card_lines.append(f"  • Figures: [cyan]{figures}[/cyan]")
    
    card_lines.append("")
    
    # Show content preview if details requested
    if show_details:
        card_lines.append("[bold cyan]📄 Content Preview:[/bold cyan]")
        preview = content[:300].replace('\n', ' ')
        card_lines.append(f"  {preview}...")
        card_lines.append("")
    
    # Show raw metadata in JSON format if details requested
    if show_details:
        card_lines.append("[bold cyan]🔍 Raw Metadata (JSON):[/bold cyan]")
        metadata_json = json.dumps(metadata, indent=2, ensure_ascii=False)
        syntax = Syntax(metadata_json, "json", theme="monokai", line_numbers=False)
        console.print(Panel("\n".join(card_lines), border_style="blue", expand=False))
        console.print(syntax)
        console.print("")
    else:
        console.print(Panel("\n".join(card_lines), border_style="blue", expand=False))
        console.print("")


def show_political_entities_analysis(metadatas):
    """Show detailed analysis of political entities across all articles."""
    
    console.print("\n[bold cyan]🏛️  POLITICAL ENTITIES ANALYSIS[/bold cyan]\n")
    
    # Collect all entities
    party_figure_map = {}
    party_article_count = Counter()
    figure_article_count = Counter()
    
    for meta in metadatas:
        if 'political_entities' in meta:
            try:
                entities = json.loads(meta['political_entities']) if isinstance(meta['political_entities'], str) else meta['political_entities']
                
                for party, party_data in entities.items():
                    party_article_count[party] += 1
                    
                    if party not in party_figure_map:
                        party_figure_map[party] = Counter()
                    
                    for figure in party_data.get('figures', []):
                        party_figure_map[party][figure] += 1
                        figure_article_count[figure] += 1
            except:
                pass
    
    # Create party analysis table
    table = Table(title="Parties & Figures Distribution", show_header=True, header_style="bold magenta")
    table.add_column("Party", style="cyan", width=20)
    table.add_column("Articles", justify="right", style="yellow")
    table.add_column("Top Figures", style="green")
    
    for party, count in party_article_count.most_common():
        top_figures = party_figure_map.get(party, Counter()).most_common(3)
        figures_str = ", ".join(f"{fig}({c})" for fig, c in top_figures) if top_figures else "None"
        table.add_row(party, str(count), figures_str)
    
    console.print(table)
    console.print("")
    
    # Top figures overall
    if figure_article_count:
        console.print("[bold cyan]👤 Top Political Figures (Most Mentioned):[/bold cyan]")
        for i, (figure, count) in enumerate(figure_article_count.most_common(10), 1):
            console.print(f"  {i}. [yellow]{figure}[/yellow]: {count} articles")
        console.print("")


def show_sample_query():
    """Show how to query the database for specific parties/figures."""
    
    console.print("\n[bold green]💡 SAMPLE QUERIES[/bold green]\n")
    
    examples = [
        {
            "title": "Get all BNP articles",
            "code": 'db.collection.get(where={"primary_parties": {"$contains": "BNP"}})'
        },
        {
            "title": "Get articles mentioning Tareq Rahman",
            "code": 'db.collection.get(where={"mentioned_figures": {"$contains": "Tareq Rahman"}})'
        },
        {
            "title": "Get articles from specific date",
            "code": 'db.collection.get(where={"date": "2025-10-15"})'
        },
        {
            "title": "Get Jugantor articles",
            "code": 'db.collection.get(where={"source": "Jugantor"})'
        }
    ]
    
    for example in examples:
        console.print(f"[bold cyan]📌 {example['title']}:[/bold cyan]")
        console.print(f"   {example['code']}")
        console.print("")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Inspect ChromaDB articles")
    parser.add_argument("--limit", type=int, default=10, help="Number of articles to show (default: 10)")
    parser.add_argument("--details", action="store_true", help="Show detailed metadata and content")
    parser.add_argument("--all", action="store_true", help="Show all articles")
    
    args = parser.parse_args()
    
    limit = None if args.all else args.limit
    
    inspect_database(limit=limit, show_details=args.details)
    show_sample_query()
