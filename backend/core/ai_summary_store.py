"""
AI Summary Storage Module

Stores AI-generated summaries, keywords, and topics for political parties and figures.
Uses JSON file for simple persistent storage.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AISummaryStore:
    """
    Store and retrieve AI-generated summaries for parties and figures.
    """
    
    def __init__(self, storage_file: str = "ai_summaries.json"):
        """
        Initialize the AI summary store.
        
        Args:
            storage_file: Path to JSON storage file
        """
        self.storage_file = Path(storage_file)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading AI summaries: {e}")
                return {"parties": {}, "figures": {}}
        return {"parties": {}, "figures": {}}
    
    def _save_data(self):
        """Save data to JSON file."""
        try:
            # Create parent directory if it doesn't exist
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"AI summaries saved to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving AI summaries: {e}")
    
    def save_party_summary(
        self,
        party_name: str,
        keywords: List[str],
        topics: List[str],
        summary: str,
        articles_analyzed: int
    ):
        """
        Save AI summary for a political party.
        
        Args:
            party_name: Name of the party
            keywords: List of keywords
            topics: List of topics
            summary: Summary text
            articles_analyzed: Number of articles analyzed
        """
        if "parties" not in self.data:
            self.data["parties"] = {}
        
        self.data["parties"][party_name] = {
            "keywords": keywords,
            "topics": topics,
            "summary": summary,
            "articles_analyzed": articles_analyzed,
            "last_updated": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
        
        self._save_data()
        logger.info(f"Saved AI summary for party: {party_name}")
    
    def save_figure_summary(
        self,
        figure_name: str,
        keywords: List[str],
        topics: List[str],
        summary: str,
        articles_analyzed: int,
        associated_party: Optional[str] = None
    ):
        """
        Save AI summary for a political figure.
        
        Args:
            figure_name: Name of the figure
            keywords: List of keywords
            topics: List of topics
            summary: Summary text
            articles_analyzed: Number of articles analyzed
            associated_party: Associated party name
        """
        if "figures" not in self.data:
            self.data["figures"] = {}
        
        self.data["figures"][figure_name] = {
            "keywords": keywords,
            "topics": topics,
            "summary": summary,
            "articles_analyzed": articles_analyzed,
            "associated_party": associated_party,
            "last_updated": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
        
        self._save_data()
        logger.info(f"Saved AI summary for figure: {figure_name}")
    
    def get_party_summary(self, party_name: str) -> Optional[Dict[str, Any]]:
        """
        Get AI summary for a party.
        
        Args:
            party_name: Name of the party
            
        Returns:
            Dictionary with summary data or None
        """
        return self.data.get("parties", {}).get(party_name)
    
    def get_figure_summary(self, figure_name: str) -> Optional[Dict[str, Any]]:
        """
        Get AI summary for a figure.
        
        Args:
            figure_name: Name of the figure
            
        Returns:
            Dictionary with summary data or None
        """
        return self.data.get("figures", {}).get(figure_name)
    
    def get_all_parties(self) -> Dict[str, Dict[str, Any]]:
        """Get all party summaries."""
        return self.data.get("parties", {})
    
    def get_all_figures(self) -> Dict[str, Dict[str, Any]]:
        """Get all figure summaries."""
        return self.data.get("figures", {})
    
    def delete_party_summary(self, party_name: str):
        """Delete party summary."""
        if "parties" in self.data and party_name in self.data["parties"]:
            del self.data["parties"][party_name]
            self._save_data()
            logger.info(f"Deleted AI summary for party: {party_name}")
    
    def delete_figure_summary(self, figure_name: str):
        """Delete figure summary."""
        if "figures" in self.data and figure_name in self.data["figures"]:
            del self.data["figures"][figure_name]
            self._save_data()
            logger.info(f"Deleted AI summary for figure: {figure_name}")
    
    def get_summary_age_days(self, entity_name: str, entity_type: str = "party") -> Optional[float]:
        """
        Get age of summary in days.
        
        Args:
            entity_name: Name of party or figure
            entity_type: "party" or "figure"
            
        Returns:
            Age in days or None if not found
        """
        if entity_type == "party":
            summary = self.get_party_summary(entity_name)
        else:
            summary = self.get_figure_summary(entity_name)
        
        if not summary or "timestamp" not in summary:
            return None
        
        age_seconds = datetime.now().timestamp() - summary["timestamp"]
        return age_seconds / 86400  # Convert to days
