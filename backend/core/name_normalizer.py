"""
Name Normalization Module

Handles matching between Bengali and English names for political figures.
Uses political_entities_config as the single source of truth.
"""

import re
from typing import List, Dict, Set, Tuple

# Import the authoritative POLITICAL_ENTITIES configuration
from political_entities_config import POLITICAL_ENTITIES

def _build_name_mappings():
    """
    Build name mappings dynamically from POLITICAL_ENTITIES config.
    Returns (NAME_MAPPING, REVERSE_MAPPING)
    """
    name_mapping = {}
    
    for party_key, party_data in POLITICAL_ENTITIES.items():
        figures_dict = party_data.get('figures', {})
        for canonical_name, variants in figures_dict.items():
            # Map all variants to the canonical name
            for variant in variants:
                name_mapping[variant] = canonical_name
    
    reverse_mapping = {v: k for k, v in name_mapping.items()}
    return name_mapping, reverse_mapping

# Build mappings on import
NAME_MAPPING, REVERSE_NAME_MAPPING = _build_name_mappings()

def normalize_name(name: str) -> str:
    """
    Normalize a name by removing extra spaces and common titles.
    
    Args:
        name: Name to normalize
    
    Returns:
        Normalized name
    """
    if not name:
        return ""
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name.strip())
    
    # Don't remove titles for canonical names - we want to keep them consistent
    # Only remove if it's not already a canonical name
    canonical_names_with_titles = [
        'Dr. Yunus', 'Dr. Muhammad Yunus', 'Dr Yunus',
        'Lt Gen Jahangir Alam Chowdhury', 
        'CEC AMM Nasir Uddin', 'AMM Nasir Uddin',
        'Army Chief General Waqar Uz Zaman', 'General Waker-uz-Zaman',
        'IGP Baharul Alam', 'Baharul Alam',
        'DMP Commissioner Sajjat Ali', 'Sheikh Md. Sajjat Ali',
        'Barrister Fuad'
    ]
    
    # Don't normalize if it's already a canonical name with title
    if name in canonical_names_with_titles:
        return name
    
    return name.strip()

def get_canonical_name(name: str) -> str:
    """
    Get the canonical (English) version of a name.
    Uses POLITICAL_ENTITIES as the source of truth.
    
    Args:
        name: Name in Bengali or English
    
    Returns:
        Canonical English name
    """
    if not name or not name.strip():
        return ""
        
    normalized = normalize_name(name)
    
    # Direct mapping
    if normalized in NAME_MAPPING:
        return NAME_MAPPING[normalized]
    
    # Reverse mapping  
    if normalized in REVERSE_NAME_MAPPING:
        return normalized
    
    # Try partial matching (case-insensitive)
    normalized_lower = normalized.lower()
    
    # Search through all figures in POLITICAL_ENTITIES
    for party_key, party_data in POLITICAL_ENTITIES.items():
        figures_dict = party_data.get('figures', {})
        for canonical_name, variants in figures_dict.items():
            # Check against canonical name
            if normalized_lower == canonical_name.lower():
                return canonical_name
            
            # Check against all variants
            for variant in variants:
                variant_lower = variant.lower()
                
                # Exact match (case-insensitive)
                if normalized_lower == variant_lower:
                    return canonical_name
                
                # Partial matching for compound names
                if (variant_lower in normalized_lower or normalized_lower in variant_lower):
                    # Only match if it's a significant portion (>60% match)
                    variant_words = set(variant_lower.split())
                    normalized_words = set(normalized_lower.split())
                    
                    if len(variant_words) > 0 and len(normalized_words) > 0:
                        similarity = len(variant_words & normalized_words) / max(len(variant_words), len(normalized_words))
                        
                        if similarity > 0.6:
                            return canonical_name
    
    # Return normalized version if no mapping found
    return normalized

def are_same_person(name1: str, name2: str) -> bool:
    """
    Check if two names refer to the same person.
    
    Args:
        name1: First name
        name2: Second name
    
    Returns:
        True if they refer to the same person
    """
    canonical1 = get_canonical_name(name1)
    canonical2 = get_canonical_name(name2)
    
    return canonical1.lower() == canonical2.lower()

def deduplicate_names(names: List[str]) -> List[str]:
    """
    Remove duplicate names from a list, considering Bengali/English variants.
    
    Args:
        names: List of names that may contain duplicates
    
    Returns:
        Deduplicated list with canonical names
    """
    seen_canonical = set()
    result = []
    
    for name in names:
        canonical = get_canonical_name(name)
        if canonical and canonical.lower() not in seen_canonical:
            seen_canonical.add(canonical.lower())
            result.append(canonical)
    
    return result

def get_party_canonical_figures(party_name: str) -> List[str]:
    """
    Get the canonical list of figures for a political party.
    
    Args:
        party_name: Name of the political party (key in POLITICAL_ENTITIES)
    
    Returns:
        List of canonical figure names
    """
    if party_name not in POLITICAL_ENTITIES:
        return []
    
    party_data = POLITICAL_ENTITIES[party_name]
    figures_dict = party_data.get('figures', {})
    
    # Return canonical names (keys of the figures dict)
    return list(figures_dict.keys())

def get_party_for_figure(figure_name: str) -> str:
    """
    Get party affiliation for a figure.
    
    Args:
        figure_name: Figure name (can be Bengali or English)
    
    Returns:
        Party key or empty string if not found
    """
    canonical = get_canonical_name(figure_name)
    
    for party_key, party_data in POLITICAL_ENTITIES.items():
        figures_dict = party_data.get('figures', {})
        if canonical in figures_dict:
            return party_key
    
    return ""

if __name__ == "__main__":
    # Test the normalization
    print("=" * 80)
    print("NAME NORMALIZATION MODULE TEST")
    print("Using POLITICAL_ENTITIES from political_entities_config.py")
    print("=" * 80)
    
    test_names = [
        'তারেক রহমান', 'Tareq Rahman', 'তারেক', 
        'মির্জা ফখরুল', 'Mirza Fakhrul',
        'ড. ইউনূস', 'ড. মুহাম্মদ ইউনূস', 'Dr. Yunus',
        'নাহিদ ইসলাম', 'Nahid Islam',
        'রাশেদ খান মেনন', 'Rashed Khan Menon',
        'বদিউল আলম মজুমদার', 'Badiul Alam Majumdar',
        'শফিকুর রহমান', 'আবু তাহের', 'রিজওয়ানা হাসান'
    ]
    
    print("\nName Normalization Test:")
    for name in test_names:
        canonical = get_canonical_name(name)
        party = get_party_for_figure(name)
        print(f"  '{name}' -> '{canonical}' [{party}]")
    
    print("\nDeduplication Test:")
    duplicates = ['তারেক রহমান', 'Tareq Rahman', 'মির্জা ফখরুল', 'Mirza Fakhrul Islam Alamgir', 'তারেক রহমান', 'রাশেদ খান মেনন', 'Rashed Khan Menon']
    deduplicated = deduplicate_names(duplicates)
    print(f"  Original ({len(duplicates)}): {duplicates}")
    print(f"  Deduplicated ({len(deduplicated)}): {deduplicated}")
    
    print("\nParty Figures Test:")
    for party in ['BNP', 'Jamaat-e-Islami', 'NCP', 'GOP', 'Interim Government']:
        figures = get_party_canonical_figures(party)
        print(f"  {party}: {len(figures)} figures")
        print(f"    {', '.join(figures[:5])}{'...' if len(figures) > 5 else ''}")
    
    print("\n" + "=" * 80)
    print("Module ready for use!")
    print("=" * 80)
