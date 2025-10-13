"""
Name Normalization Module

Handles matching between Bengali and English names for political figures.
"""

import re
from typing import List, Dict, Set

# Name mapping for political figures (Bengali -> English)
NAME_MAPPING = {
    # BNP
    'তারেক রহমান': 'Tareq Rahman',
    'মির্জা ফখরুল': 'Mirza Fakhrul',
    'মির্জা ফখরুল ইসলাম আলমগীর': 'Mirza Fakhrul',
    'সালাহউদ্দিন আহমেদ': 'Salahuddin Ahmed',
    
    # JI (Jamaat-e-Islami)
    'শফিকুর রহমান': 'Shafiqur Rahman',
    'আবু তাহের': 'Abu Taher',
    'গোলাম পারওয়ার': 'Golam Parwar',
    
    # NCP (National Citizens' Committee)
    'নাহিদ ইসলাম': 'Nahid Islam',
    'সারজিস আলম': 'Sarjis Alam',
    'হাসনাত আবদুল্লাহ': 'Hasnat Abdullah',
    'নাসিরউদ্দিন পাটওয়ারী': 'Nasiruddin Patwary',
    'আখতার হোসেন': 'Akhter Hossain',
    'তাসনিম জারা': 'Tasnim Zara',
    
    # AB Party
    'ব্যারিস্টার ফুয়াদ': 'Barrister Fuad',
    'ফুয়াদ': 'Barrister Fuad',
    
    # GOP (Gono Odhikar Parishad)
    'নুরুল হক': 'Nurul Haque',
    'রাশেদ': 'Rashed',
    'রাশেদ খান মেনন': 'Rashed',
    
    # Gono Songhati
    'জনায়েদ সাকী': 'Jonayed Saki',
    
    # Interim Government - Advisory Board
    'ড. ইউনূস': 'Dr Yunus',
    'মুহাম্মদ ইউনূস': 'Dr Yunus',
    'ডক্টর মুহাম্মদ ইউনূস': 'Dr Yunus',
    'শফিকুল আলম': 'Shafiqul Alam',
    'মাহফুজ আলম': 'Mahfuz Alam',
    'আসিফ নজরুল': 'Asif Nazrul',
    'রিজওয়ানা হাসান': 'Rizwana Hasan',
    'লেফটেন্যান্ট জেনারেল জাহাঙ্গীর আলম চৌধুরী': 'Lt Gen Jahangir Alam Chowdhury',
    'জাহাঙ্গীর আলম চৌধুরী': 'Lt Gen Jahangir Alam Chowdhury',
    
    # Interim Government - Consensus Commission
    'আলী রিয়াজ': 'Ali Riaz',
    'বদিউল আলম মজুমদার': 'Badiul Alam Majumder',
    
    # Interim Government - Election Commission  
    'এএমএম নাসির উদ্দিন': 'CEC AMM Nasir Uddin',
    'নাসির উদ্দিন': 'CEC AMM Nasir Uddin',
    
    # Interim Government - Security Forces
    'জেনারেল ওয়াকার উজ জামান': 'Army Chief General Waqar Uz Zaman',
    'ওয়াকার উজ জামান': 'Army Chief General Waqar Uz Zaman',
    'বাহারুল আলম': 'IGP Baharul Alam',
    'সাজ্জাত আলী': 'DMP Commissioner Sajjat Ali',
    
    # Interim Government - Civil Society
    'মাহফুজ আনাম': 'Mahfuz Anam',
    'মাহমুদুর রহমান': 'Mahmudur Rahman'
}

# Reverse mapping (English -> Bengali)
REVERSE_NAME_MAPPING = {v: k for k, v in NAME_MAPPING.items()}

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
        'Dr Yunus', 'Lt Gen Jahangir Alam Chowdhury', 'CEC AMM Nasir Uddin',
        'Army Chief General Waqar Uz Zaman', 'IGP Baharul Alam', 
        'DMP Commissioner Sajjat Ali', 'Barrister Fuad'
    ]
    
    # Don't normalize if it's already a canonical name with title
    if name in canonical_names_with_titles:
        return name
    
    return name.strip()

def get_canonical_name(name: str) -> str:
    """
    Get the canonical (English) version of a name.
    
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
    for bengali, english in NAME_MAPPING.items():
        bengali_lower = bengali.lower()
        english_lower = english.lower()
        
        # Exact match (case-insensitive)
        if normalized_lower == bengali_lower or normalized_lower == english_lower:
            return english
            
        # Partial matching for compound names
        if (bengali_lower in normalized_lower or normalized_lower in bengali_lower or
            english_lower in normalized_lower or normalized_lower in english_lower):
            # Only match if it's a significant portion (>60% match)
            similarity_bengali = len(set(normalized_lower.split()) & set(bengali_lower.split())) / max(len(normalized_lower.split()), len(bengali_lower.split()))
            similarity_english = len(set(normalized_lower.split()) & set(english_lower.split())) / max(len(normalized_lower.split()), len(english_lower.split()))
            
            if similarity_bengali > 0.6 or similarity_english > 0.6:
                return english
    
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
        if canonical.lower() not in seen_canonical:
            seen_canonical.add(canonical.lower())
            result.append(canonical)
    
    return result

def get_party_canonical_figures(party_name: str) -> List[str]:
    """
    Get the canonical list of figures for a political party.
    
    Args:
        party_name: Name of the political party
    
    Returns:
        List of canonical figure names
    """
    party_figures = {
        'BNP': [
            'Tareq Rahman', 
            'Mirza Fakhrul', 
            'Salahuddin Ahmed'
        ],
        'JI': [
            'Shafiqur Rahman', 
            'Abu Taher', 
            'Golam Parwar'
        ],
        'NCP': [
            'Nahid Islam', 
            'Sarjis Alam', 
            'Hasnat Abdullah', 
            'Nasiruddin Patwary',
            'Akhter Hossain', 
            'Tasnim Zara'
        ],
        'AB Party': [
            'Barrister Fuad'
        ],
        'GOP': [
            'Nurul Haque', 
            'Rashed'
        ],
        'Gono Songhati': [
            'Jonayed Saki'
        ],
        'Interim Government': [
            # Advisory Board
            'Dr Yunus',  # Chief Advisor
            'Shafiqul Alam',  # Press Secretary
            'Mahfuz Alam',  # Info Advisor
            'Asif Nazrul',  # Law Advisor
            'Rizwana Hasan',  # Environment
            'Lt Gen Jahangir Alam Chowdhury',
            # Consensus Commission
            'Ali Riaz',
            'Badiul Alam Majumder',
            # Election Commission
            'CEC AMM Nasir Uddin',
            # Security Forces
            'Army Chief General Waqar Uz Zaman',
            'IGP Baharul Alam',
            'DMP Commissioner Sajjat Ali',
            # Civil Society
            'Mahfuz Anam',
            'Mahmudur Rahman'
        ]
    }
    
    return party_figures.get(party_name, [])

if __name__ == "__main__":
    # Test the normalization
    test_names = [
        'তারেক রহমান', 'Tareq Rahman', 'মির্জা ফখরুল', 'Mirza Fakhrul',
        'ড. ইউনূস', 'Dr Yunus', 'নাহিদ ইসলাম', 'Nahid Islam',
        'রাশেদ', 'Rashed', 'বদিউল আলম মজুমদার', 'Badiul Alam Majumder',
        'শফিকুর রহমান', 'আবু তাহের', 'রিজওয়ানা হাসান'
    ]
    
    print("Name Normalization Test:")
    for name in test_names:
        canonical = get_canonical_name(name)
        print(f"'{name}' -> '{canonical}'")
    
    print("\nDeduplication Test:")
    duplicates = ['তারেক রহমান', 'Tareq Rahman', 'মির্জা ফখরুল', 'Mirza Fakhrul', 'তারেক রহমান', 'রাশেদ', 'Rashed']
    deduplicated = deduplicate_names(duplicates)
    print(f"Original: {duplicates}")
    print(f"Deduplicated: {deduplicated}")
    
    print("\nParty Figures Test:")
    for party in ['BNP', 'JI', 'NCP', 'GOP', 'Interim Government']:
        figures = get_party_canonical_figures(party)
        print(f"{party}: {figures}")