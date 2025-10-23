"""
Period Summary Storage Module

Stores period summaries (date range analysis) for political parties and figures.
Uses JSON file for simple persistent storage.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PeriodSummaryStore:
    """
    Store and retrieve period summaries for parties and figures.
    Each entity can have multiple period summaries for different date ranges.
    """
    
    def __init__(self, storage_file: str = "period_summaries.json"):
        """
        Initialize the period summary store.
        
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
                logger.error(f"Error loading period summaries: {e}")
                return {"parties": {}, "figures": {}}
        return {"parties": {}, "figures": {}}
    
    def _save_data(self):
        """Save data to JSON file."""
        try:
            # Create parent directory if it doesn't exist
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"Period summaries saved to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving period summaries: {e}")
    
    def _generate_key(self, start_date: str, end_date: str) -> str:
        """Generate a unique key for a date range."""
        return f"{start_date}_{end_date}"
    
    def save_period_summary(
        self,
        entity_type: str,  # "party" or "figure"
        entity_name: str,
        start_date: str,
        end_date: str,
        summary: str,
        key_points: List[str],
        keywords: List[str],
        topics: List[str],
        total_articles: int,
        newly_summarized: int,
        already_summarized: int
    ):
        """
        Save period summary for an entity.
        
        Args:
            entity_type: "party" or "figure"
            entity_name: Name of the entity
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            summary: Summary text
            key_points: List of key points
            keywords: List of keywords
            topics: List of topics
            total_articles: Total articles analyzed
            newly_summarized: Newly summarized articles
            already_summarized: Already summarized articles
        """
        # Ensure entity type exists
        if entity_type not in self.data:
            self.data[entity_type] = {}
        
        # Ensure entity exists
        if entity_name not in self.data[entity_type]:
            self.data[entity_type][entity_name] = {}
        
        # Create date range key
        date_key = self._generate_key(start_date, end_date)
        
        # Store period summary
        self.data[entity_type][entity_name][date_key] = {
            "start_date": start_date,
            "end_date": end_date,
            "summary": summary,
            "key_points": key_points,
            "keywords": keywords,
            "topics": topics,
            "statistics": {
                "total_articles": total_articles,
                "newly_summarized": newly_summarized,
                "already_summarized": already_summarized
            },
            "last_updated": datetime.now().isoformat(),
            "timestamp": datetime.now().timestamp()
        }
        
        self._save_data()
        logger.info(f"Saved period summary for {entity_type} '{entity_name}': {start_date} to {end_date}")
    
    def get_period_summary(
        self,
        entity_type: str,
        entity_name: str,
        start_date: str,
        end_date: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get period summary for a specific date range.
        
        Args:
            entity_type: "party" or "figure"
            entity_name: Name of the entity
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with period summary data or None
        """
        date_key = self._generate_key(start_date, end_date)
        return self.data.get(entity_type, {}).get(entity_name, {}).get(date_key)
    
    def get_all_period_summaries(
        self,
        entity_type: str,
        entity_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get all period summaries for an entity.
        
        Args:
            entity_type: "party" or "figure"
            entity_name: Name of the entity
            
        Returns:
            Dictionary of all period summaries keyed by date range
        """
        return self.data.get(entity_type, {}).get(entity_name, {})
    
    def delete_period_summary(
        self,
        entity_type: str,
        entity_name: str,
        start_date: str,
        end_date: str
    ):
        """Delete a specific period summary."""
        date_key = self._generate_key(start_date, end_date)
        if (entity_type in self.data and 
            entity_name in self.data[entity_type] and 
            date_key in self.data[entity_type][entity_name]):
            del self.data[entity_type][entity_name][date_key]
            self._save_data()
            logger.info(f"Deleted period summary for {entity_type} '{entity_name}': {start_date} to {end_date}")
    
    def delete_all_entity_summaries(self, entity_type: str, entity_name: str):
        """Delete all period summaries for an entity."""
        if entity_type in self.data and entity_name in self.data[entity_type]:
            del self.data[entity_type][entity_name]
            self._save_data()
            logger.info(f"Deleted all period summaries for {entity_type}: {entity_name}")
    
    def get_summary_age_days(
        self,
        entity_type: str,
        entity_name: str,
        start_date: str,
        end_date: str
    ) -> Optional[float]:
        """
        Get age of period summary in days.
        
        Args:
            entity_type: "party" or "figure"
            entity_name: Name of the entity
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Age in days or None if not found
        """
        summary = self.get_period_summary(entity_type, entity_name, start_date, end_date)
        
        if not summary or "timestamp" not in summary:
            return None
        
        age_seconds = datetime.now().timestamp() - summary["timestamp"]
        return age_seconds / 86400  # Convert to days
