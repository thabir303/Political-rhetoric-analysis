"""
Name Normalization Module

Handles matching between Bengali and English names for political figures.
"""

import re
from typing import List, Dict, Set

# Name mapping for political figures (All variants -> Canonical English name)
# Based on POLITICAL_ENTITIES in scraping.py - the key in figures dict is the canonical name
NAME_MAPPING = {
    # ===================== BNP =====================
    # Tareq Rahman variants
    'তারেক রহমান': 'Tareq Rahman',
    'তারেক': 'Tareq Rahman',
    'তারিক রহমান': 'Tareq Rahman',
    'বিএনপি ভারপ্রাপ্ত চেয়ারম্যান তারেক': 'Tareq Rahman',
    'বিএনপি ভারপ্রাপ্ত চেয়ারম্যান': 'Tareq Rahman',
    'BNP Acting Chairman': 'Tareq Rahman',
    'BNP leader Tarique': 'Tareq Rahman',
    'Tarique Rahman': 'Tareq Rahman',
    'Tarek Rahman': 'Tareq Rahman',
    
    # Mirza Fakhrul variants
    'মির্জা ফখরুল': 'Mirza Fakhrul',
    'মির্জা ফখরুল ইসলাম আলমগীর': 'Mirza Fakhrul',
    'ফখরুল': 'Mirza Fakhrul',
    'Mirza Fakhrul Islam Alamgir': 'Mirza Fakhrul',
    'BNP Secretary General Fakhrul': 'Mirza Fakhrul',
    'Mr Fakhrul Islam Alamgir': 'Mirza Fakhrul',
    
    # Salahuddin Ahmed variants
    'সালাহউদ্দিন আহমেদ': 'Salahuddin Ahmed',
    'সালাউদ্দিন আহমেদ': 'Salahuddin Ahmed',
    'সালাহউদ্দিন': 'Salahuddin Ahmed',
    'বিএনপি নেতা সালাহউদ্দিন': 'Salahuddin Ahmed',
    'Salah Uddin Ahmed': 'Salahuddin Ahmed',
    'Salahuddin Ahmad': 'Salahuddin Ahmed',
    'BNP leader Salahuddin': 'Salahuddin Ahmed',
    
    # ===================== JI (Jamaat-e-Islami) =====================
    # Shafiqur Rahman variants
    'শফিকুর রহমান': 'Shafiqur Rahman',
    'জামায়াত আমীর শফিকুর রহমান': 'Shafiqur Rahman',
    'Dr Shafiqur Rahman': 'Shafiqur Rahman',
    'Ameer Shafiqur Rahman': 'Shafiqur Rahman',
    
    # Abu Taher variants
    'আবু তাহের': 'Abu Taher',
    'মাওলানা তাহের': 'Abu Taher',
    'মাও. তাহের': 'Abu Taher',
    'Syed Abdullah Muhammad Taher': 'Abu Taher',
    'Maulana Abu Taher': 'Abu Taher',
    
    # Golam Parwar variants
    'গোলাম পারওয়ার': 'Golam Parwar',
    'মিয়া গোলাম পারওয়ার': 'Golam Parwar',
    'জামায়াত নেতা পারওয়ার': 'Golam Parwar',
    'Mia Golam Parwar': 'Golam Parwar',
    'Mia Ghulam Parwar': 'Golam Parwar',
    
    # ===================== NCP (National Citizens Party) =====================
    # Nahid Islam variants
    'নাহিদ ইসলাম': 'Nahid Islam',
    'মো. নাহিদ ইসলাম': 'Nahid Islam',
    'Md Nahid Islam': 'Nahid Islam',
    'Convener Nahid Islam': 'Nahid Islam',
    'Student Leader Nahid': 'Nahid Islam',
    
    # Sarjis Alam variants
    'সরজিস আলম': 'Sarjis Alam',
    'সারজিস আলম': 'Sarjis Alam',
    'Sarjis Alom': 'Sarjis Alam',
    'Chief Coordinator Sarjis': 'Sarjis Alam',
    
    # Hasnat Abdullah variants
    'হাসনাত আবদুল্লাহ': 'Hasnat Abdullah',
    'নাগরিক পার্টির হাসনাত আবদুল্লাহ': 'Hasnat Abdullah',
    'Hasnath Abdullah': 'Hasnat Abdullah',
    
    # Nasiruddin Patwary variants
    'নাসিরউদ্দিন পাটোয়ারী': 'Nasiruddin Patwary',
    'নাসিরউদ্দিন পাটওয়ারী': 'Nasiruddin Patwary',
    'Nasir Uddin Patwary': 'Nasiruddin Patwary',
    
    # Akhter Hossain variants
    'আখতার হোসেন': 'Akhter Hossain',
    'Akhtar Hossain': 'Akhter Hossain',
    'Akhtar Hossen': 'Akhter Hossain',
    
    # Tasnim Zara variants
    'তাসনিম জারা': 'Tasnim Zara',
    'Tasnim Jara': 'Tasnim Zara',
    
    # ===================== AB Party =====================
    # Barrister Fuad variants
    'ব্যারিস্টার ফুয়াদ': 'Barrister Fuad',
    'ফুয়াদ': 'Barrister Fuad',
    'এবি পার্টির ফুয়াদ': 'Barrister Fuad',
    'Barrister Asaduzzaman Fuad': 'Barrister Fuad',
    'Asaduzzaman Fuad': 'Barrister Fuad',
    
    # ===================== GOP (Gono Odhikar Parishad) =====================
    # Nurul Haque variants
    'নুরুল হক': 'Nurul Haque',
    'নুরুল হক নুর': 'Nurul Haque',
    'নূর': 'Nurul Haque',
    'গণ অধিকার পরিষদের নুর': 'Nurul Haque',
    'Nurul Haque Nur': 'Nurul Haque',
    'Nur Chowdhury': 'Nurul Haque',
    
    # Rashed variants
    'রাশেদ': 'Rashed',
    'রাশেদ খান': 'Rashed',
    'Rashed Khan': 'Rashed',
    
    # ===================== Gono Songhati =====================
    # Jonayed Saki variants
    'জোনায়েদ সাকী': 'Jonayed Saki',
    'জনায়েদ সাকি': 'Jonayed Saki',
    'গণসংহতি নেতা সাকি': 'Jonayed Saki',
    'Zonayed Saki': 'Jonayed Saki',
    
    # ===================== Interim Government =====================
    # Dr Yunus variants
    'ড. ইউনূস': 'Dr Yunus',
    'ড ইউনূস': 'Dr Yunus',
    'ড. ইউনুস': 'Dr Yunus',
    'মুহাম্মদ ইউনূস': 'Dr Yunus',
    'ড. মুহাম্মদ ইউনূস': 'Dr Yunus',
    'ডক্টর মুহাম্মদ ইউনূস': 'Dr Yunus',
    'Dr Muhammad Yunus': 'Dr Yunus',
    'Prof. Muhammad Yunus': 'Dr Yunus',
    'Dr M. Yunus': 'Dr Yunus',
    'Chief Adviser Yunus': 'Dr Yunus',
    'Professor Yunus': 'Dr Yunus',
    'Dr. Yunus': 'Dr Yunus',
    
    # Shafiqul Alam variants
    'শফিকুল আলম': 'Shafiqul Alam',
    'ড. শফিকুল আলম': 'Shafiqul Alam',
    
    # Mahfuz Alam variants
    'মাহফুজ আলম': 'Mahfuz Alam',
    
    # Asif Nazrul variants
    'আসিফ নজরুল': 'Asif Nazrul',
    'Dr Asif Nazrul': 'Asif Nazrul',
    'Professor Asif Nazrul': 'Asif Nazrul',
    
    # Rizwana Hasan variants
    'রিজওয়ানা হাসান': 'Rizwana Hasan',
    'এডভোকেট রিজওয়ানা হাসান': 'Rizwana Hasan',
    
    # Lt Gen Jahangir Alam Chowdhury variants
    'জাহাঙ্গীর আলম চৌধুরী': 'Lt Gen Jahangir Alam Chowdhury',
    'লেফটেন্যান্ট জেনারেল জাহাঙ্গীর': 'Lt Gen Jahangir Alam Chowdhury',
    'লেফটেন্যান্ট জেনারেল জাহাঙ্গীর আলম চৌধুরী': 'Lt Gen Jahangir Alam Chowdhury',
    'Lt. Gen. Jahangir Alam Chowdhury': 'Lt Gen Jahangir Alam Chowdhury',
    
    # Ali Riaz variants
    'আলী রিয়াজ': 'Ali Riaz',
    'Dr Ali Riaz': 'Ali Riaz',
    'Professor Ali Riaz': 'Ali Riaz',
    
    # Badiul Alam Majumder variants
    'বদিউল আলম মজুমদার': 'Badiul Alam Majumder',
    'Dr Badiul Alam Majumder': 'Badiul Alam Majumder',
    
    # CEC AMM Nasir Uddin variants
    'নাসির উদ্দিন': 'CEC AMM Nasir Uddin',
    'এএমএম নাসির উদ্দিন': 'CEC AMM Nasir Uddin',
    'AMM Nasir Uddin': 'CEC AMM Nasir Uddin',
    'Nasir Uddin': 'CEC AMM Nasir Uddin',
    
    # Army Chief General Waqar Uz Zaman variants
    'ওয়াকার উজ জামান': 'Army Chief General Waqar Uz Zaman',
    'জেনারেল ওয়াকার': 'Army Chief General Waqar Uz Zaman',
    'জেনারেল ওয়াকার উজ জামান': 'Army Chief General Waqar Uz Zaman',
    'General Waqar Uz Zaman': 'Army Chief General Waqar Uz Zaman',
    'Army Chief Waqar': 'Army Chief General Waqar Uz Zaman',
    
    # IGP Baharul Alam variants
    'বাহারুল আলম': 'IGP Baharul Alam',
    'Baharul Alam': 'IGP Baharul Alam',
    
    # DMP Commissioner Sajjat Ali variants
    'সাজ্জাত আলী': 'DMP Commissioner Sajjat Ali',
    'Sajjat Ali': 'DMP Commissioner Sajjat Ali',
    
    # Mahfuz Anam variants
    'মাহফুজ আনাম': 'Mahfuz Anam',
    'Editor Mahfuz Anam': 'Mahfuz Anam',
    
    # Mahmudur Rahman variants
    'মাহমুদুর রহমান': 'Mahmudur Rahman',
    'Editor Mahmudur Rahman': 'Mahmudur Rahman'
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