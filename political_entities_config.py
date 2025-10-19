"""
Political Entities Configuration

Defines known political parties and their key figures for Bangladesh.
Used by LLM for accurate entity detection.
"""

POLITICAL_ENTITIES = {
    "BNP": {
        "full_name": "Bangladesh Nationalist Party",
        "names": [
            "BNP", "Bangladesh Nationalist Party",
            "বিএনপি", "বাংলাদেশ জাতীয়তাবাদী দল"
        ],
        "figures": {
            "Tareq Rahman": ["তারেক রহমান", "Tareq Rahman", "Tarique Rahman"],
            "Mirza Fakhrul Islam Alamgir": ["মির্জা ফখরুল", "Mirza Fakhrul", "মির্জা ফখরুল ইসলাম আলমগীর"],
            "Salauddin Ahmed": ["সালাউদ্দিন আহমেদ", "Salauddin Ahmed"]
        }
    },
    "Jamaat-e-Islami": {
        "full_name": "Jamaat-e-Islami Bangladesh",
        "names": [
            "Jamaat-e-Islami", "Jamaat", "JI",  # Added "JI" for backward compatibility
            "জামায়াত", "জামায়াতে ইসলামী"
        ],
        "figures": {
            "Shafiqur Rahman": ["শফিকুর রহমান", "Shafiqur Rahman"],
            "Abu Taher": ["আবু তাহের", "Abu Taher"],
            "Golam Parwar": ["গোলাম পারওয়ার", "Golam Parwar"]
        }
    },
    "NCP": {
        "full_name": "National Citizens Party",
        "names": [
            "National Citizens Party", "NCP",
            "জাতীয় নাগরিক পার্টি"
        ],
        "figures": {
            "Nahid Islam": ["নাহিদ ইসলাম", "Nahid Islam"],
            "Sarjis Alam": ["সরজিস আলম", "Sarjis Alam"],
            "Hasnat Abdullah": ["হাসনাত আবদুল্লাহ", "Hasnat Abdullah"],
            "Nasiruddin Patwari": ["নাসিরউদ্দিন পাটোয়ারী", "Nasiruddin Patwari"],
            "Akhtar Hossain": ["আখতার হোসেন", "Akhtar Hossain"],
            "Tasnim Jara": ["তাসনিম জারা", "Tasnim Jara"]
        }
    },
    "AB Party": {
        "full_name": "Amar Bangladesh Party",
        "names": [
            "AB Party", "Amar Bangladesh Party",
            "আমার বাংলাদেশ পার্টি"
        ],
        "figures": {
            "Barrister Fuad": ["ব্যারিস্টার ফুয়াদ", "Barrister Fuad"],
            "Mostafa Amir Faisal": ["মোস্তফা আমীর ফয়সাল", "Mostafa Amir Faisal"]
        }
    },
    "GOP": {
        "full_name": "Gono Odhikar Parishad",
        "names": [
            "Gono Odhikar Parishad", "GOP",
            "গণ অধিকার পরিষদ"
        ],
        "figures": {
            "Nurul Haque Nur": ["নুরুল হক নূর", "Nurul Haque Nur"],
            "Rashed Khan Menon": ["রাশেদ খান মেনন", "Rashed Khan Menon"]
        }
    },
    "Gono Songhati": {
        "full_name": "Gono Songhati Andolon",
        "names": [
            "Gono Songhati Andolon", "Gono Songhati",
            "গণসংহতি আন্দোলন"
        ],
        "figures": {
            "Zonayed Saki": ["জোনায়েদ সাকী", "Zonayed Saki"]
        }
    },
    "Interim Government": {
        "full_name": "Interim Government of Bangladesh",
        "names": [
            "Interim Government", "Advisory Council",
            "অন্তর্বর্তী সরকার", "উপদেষ্টা পরিষদ"
        ],
        "figures": {
            "Dr. Muhammad Yunus": ["ড. মুহাম্মদ ইউনূস", "Dr. Muhammad Yunus", "ড. ইউনূস", "Dr. Yunus"],
            "Shafiqul Alam": ["শফিকুল আলম", "Shafiqul Alam"],
            "Mahfuz Alam": ["মাহফুজ আলম", "Mahfuz Alam"],
            "Asif Nazrul": ["আসিফ নজরুল", "Asif Nazrul"],
            "Rizwana Hasan": ["রিজওয়ানা হাসান", "Rizwana Hasan"],
            "Lt Gen Jahangir Alam Chowdhury": ["Lt Gen জাহাঙ্গীর আলম চৌধুরী", "Lt Gen Jahangir Alam Chowdhury"],
            "Ali Riaz": ["আলী রীয়াজ", "Ali Riaz"],
            "Badiul Alam Majumdar": ["বদিউল আলম মজুমদার", "Badiul Alam Majumdar"],
            "AMM Nasir Uddin": ["এ এম এম নাসির উদ্দিন", "AMM Nasir Uddin"],
            "General Waker-uz-Zaman": ["General ওয়াকার উজ জামান", "General Waker-uz-Zaman"],
            "Baharul Alam": ["বাহারুল আলম", "Baharul Alam"],
            "Sheikh Md. Sajjat Ali": ["শেখ মো. সাজ্জাত আলী", "Sheikh Md. Sajjat Ali"],
            "Mahfuz Anam": ["মাহফুজ আনাম", "Mahfuz Anam"],
            "Mahmudur Rahman": ["মাহমুদুর রহমান", "Mahmudur Rahman"]
        }
    },
    "Awami League": {
        "full_name": "Bangladesh Awami League",
        "names": [
            "Awami League", "AL",
            "আওয়ামী লীগ", "বাংলাদেশ আওয়ামী লীগ"
        ],
        "figures": {
            "Sheikh Hasina": ["শেখ হাসিনা", "Sheikh Hasina"],
            "Obaidul Quader": ["ওবায়দুল কাদের", "Obaidul Quader"],
            "ASM Firoz": ["আ স ম ফিরোজ", "ASM Firoz"]
        }
    },
    "Jatiya Party": {
        "full_name": "Jatiya Party (Ershad)",
        "names": [
            "Jatiya Party", "JP",
            "জাতীয় পার্টি"
        ],
        "figures": {
            "Ershad": ["এরশাদ", "Ershad", "হুসেইন মুহাম্মদ এরশাদ"],
            "Raushan Ershad": ["রওশন এরশাদ", "Raushan Ershad"],
            "GM Quader": ["জিএম কাদের", "GM Quader"]
        }
    }
}

# Generate LLM-friendly lists for prompts
def get_party_list_for_prompt(language='bangla'):
    """Get formatted party list for LLM prompt."""
    if language == 'bangla':
        return ', '.join([
            entity['names'][-1] if len(entity['names']) > 2 else entity['names'][0]
            for entity in POLITICAL_ENTITIES.values()
        ])
    else:
        return ', '.join([
            entity['full_name'] 
            for entity in POLITICAL_ENTITIES.values()
        ])

def get_figures_list_for_prompt(language='bangla'):
    """Get formatted figures list for LLM prompt."""
    all_figures = []
    for entity in POLITICAL_ENTITIES.values():
        figures_dict = entity.get('figures', {})
        if language == 'bangla':
            # Get first Bangla alias for each figure
            for canonical_name, aliases in figures_dict.items():
                bangla_name = next((a for a in aliases if any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in a)), aliases[0])
                all_figures.append(bangla_name)
        else:
            # Use canonical English names
            all_figures.extend(list(figures_dict.keys())[:5])  # Limit to 5 per party
    
    return ', '.join(all_figures[:30])  # Limit total

def normalize_party_name(detected_name: str) -> str:
    """
    Normalize detected party name to standard format.
    
    Args:
        detected_name: Party name as detected by LLM
        
    Returns:
        Standardized party key (e.g., "BNP", "Jamaat-e-Islami")
    """
    detected_lower = detected_name.lower().strip()
    
    for key, entity in POLITICAL_ENTITIES.items():
        # Check against all known names
        for name in entity['names']:
            if detected_lower == name.lower() or detected_lower in name.lower() or name.lower() in detected_lower:
                return key
    
    # Return as-is if no match found
    return detected_name

def normalize_figure_name(detected_name: str) -> tuple:
    """
    Normalize detected figure name to canonical English name and find their party.
    
    Args:
        detected_name: Figure name as detected by LLM (can be Bangla or English)
        
    Returns:
        Tuple of (canonical_english_name, party_key) or (detected_name, None)
    """
    detected_lower = detected_name.lower().strip()
    
    for party_key, entity in POLITICAL_ENTITIES.items():
        figures_dict = entity.get('figures', {})
        for canonical_name, aliases in figures_dict.items():
            # Check if detected name matches any alias
            for alias in aliases:
                if detected_lower == alias.lower() or detected_lower in alias.lower() or alias.lower() in detected_lower:
                    return (canonical_name, party_key)  # Always return canonical English name
    
    return (detected_name, None)

def get_party_for_figure(figure_name: str) -> str:
    """Get party affiliation for a figure."""
    _, party = normalize_figure_name(figure_name)
    return party
