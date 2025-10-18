"""
Enhanced Web Scraping with LLM Analysis

Scrapes articles and automatically generates:
1. Summary
2. Top Keywords
3. Topics Covered
4. Political Parties & Figures Detection
5. 2026 Bangladesh Election Impact Analysis
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

from backend.core.llm_generation import LLMGenerator
from political_entities_config import (
    get_party_list_for_prompt,
    get_figures_list_for_prompt,
    normalize_party_name,
    normalize_figure_name,
    POLITICAL_ENTITIES
)

logger = logging.getLogger(__name__)


class EnhancedArticleAnalyzer:
    """Analyzes articles using LLM during scraping."""
    
    def __init__(self):
        """Initialize the LLM analyzer."""
        self.llm = LLMGenerator()
        logger.info("Enhanced Article Analyzer initialized with Gemini LLM")
    
    def detect_language(self, text: str) -> str:
        """
        Detect if text is Bangla or English.
        
        Args:
            text: Article content
            
        Returns:
            'bangla' or 'english'
        """
        # Check first 200 chars for Bangla Unicode range (U+0980 to U+09FF)
        is_bangla = any('\u0980' <= char <= '\u09FF' for char in text[:200])
        return 'bangla' if is_bangla else 'english'
    
    def analyze_article(
        self, 
        article_content: str,
        article_title: str,
        article_date: str,
        political_party: Optional[str] = None,
        political_figure: Optional[str] = None
    ) -> Dict:
        """
        Complete analysis of article using LLM.
        
        Generates:
        1. Summary (3-4 sentences)
        2. Top Keywords (5-10 keywords)
        3. Topics Covered (3-5 topics)
        4. 2026 Election Impact Analysis
        
        Args:
            article_content: Full article text
            article_title: Article headline
            article_date: Publication date
            political_party: Associated party (if any)
            political_figure: Associated figure (if any)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Detect language
            language = self.detect_language(article_content)
            
            # Build comprehensive analysis prompt
            if language == 'bangla':
                prompt = self._build_bangla_analysis_prompt(
                    article_content, article_title, article_date,
                    political_party, political_figure
                )
            else:
                prompt = self._build_english_analysis_prompt(
                    article_content, article_title, article_date,
                    political_party, political_figure
                )
            
            logger.info(f"Analyzing article: {article_title[:50]}... (Language: {language})")
            
            # Get LLM analysis
            start_time = time.time()
            analysis_text = self.llm._call_llm(prompt)
            processing_time = time.time() - start_time
            
            logger.info(f"Analysis completed in {processing_time:.2f} seconds")
            
            # Parse the structured response
            parsed_analysis = self._parse_analysis_response(analysis_text, language)
            
            # Add metadata
            parsed_analysis['processing_time'] = processing_time
            parsed_analysis['analyzed_at'] = datetime.now().isoformat()
            parsed_analysis['language'] = language
            
            return parsed_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze article: {e}")
            return self._get_fallback_analysis(language)
    
    def _build_bangla_analysis_prompt(
        self,
        content: str,
        title: str,
        date: str,
        party: Optional[str],
        figure: Optional[str]
    ) -> str:
        """Build Bangla analysis prompt with known entities."""
        
        # Get known parties and figures
        known_parties = get_party_list_for_prompt('bangla')
        known_figures = get_figures_list_for_prompt('bangla')
        
        context = f"শিরোনাম: {title}\nতারিখ: {date}\n"
        context += f"\n[পরিচিত রাজনৈতিক দল: {known_parties}]\n"
        context += f"[পরিচিত রাজনৈতিক ব্যক্তিত্ব: {known_figures}]\n"
        
        prompt = f"""নিচের বাংলাদেশী রাজনৈতিক আর্টিকেলটি বিশ্লেষণ করুন এবং নিম্নলিখিত তথ্য প্রদান করুন:

{context}

আর্টিকেল:
{content}

অনুগ্রহ করে নিম্নলিখিত ফরম্যাটে উত্তর দিন (শুধুমাত্র বাংলায়):

1. SUMMARY:
[৩-৪টি সংক্ষিপ্ত বাক্যে আর্টিকেলের সারসংক্ষেপ লিখুন]

2. KEYWORDS:
[৫-১০টি গুরুত্বপূর্ণ কীওয়ার্ড, কমা দিয়ে আলাদা করুন]

3. TOPICS:
[৩-৫টি প্রধান বিষয়, কমা দিয়ে আলাদা করুন]

4. POLITICAL_PARTIES:
[আর্টিকেলে উল্লেখিত সকল রাজনৈতিক দল/সংগঠনের নাম। উপরে দেওয়া পরিচিত দলের তালিকা থেকে খুঁজে বের করুন এবং EXACT নাম ব্যবহার করুন। উদাহরণ: বিএনপি, আওয়ামী লীগ, জামায়াতে ইসলামী, অন্তর্বর্তী সরকার ইত্যাদি। কমা দিয়ে আলাদা করুন। যদি কোনো দল উল্লেখ না থাকে তাহলে "None" লিখুন।

⚠️ IMPORTANT: পরিচিত দলের তালিকায় থাকা নাম ব্যবহার করুন। নতুন নাম তৈরি করবেন না।]

5. POLITICAL_FIGURES:
[আর্টিকেলে উল্লেখিত সকল রাজনৈতিক ব্যক্তিত্ব/নেতাদের নাম। উপরে দেওয়া পরিচিত ব্যক্তিত্বের তালিকা থেকে খুঁজে বের করুন এবং EXACT নাম ব্যবহার করুন। উদাহরণ: তারেক রহমান, মির্জা ফখরুল, ড. মুহাম্মদ ইউনূস ইত্যাদি। কমা দিয়ে আলাদা করুন। যদি কেউ উল্লেখ না থাকে তাহলে "None" লিখুন।

⚠️ IMPORTANT: পরিচিত ব্যক্তিত্বের তালিকায় থাকা নাম ব্যবহার করুন। নতুন নাম তৈরি করবেন না।]

6. ELECTION_2026_IMPACT:
[বাংলাদেশের ২০২৬ সালের নির্বাচনে এই আর্টিকেল/বক্তব্যের সম্ভাব্য প্রভাব কী হতে পারে? যদি কোনো প্রভাব থাকে তাহলে ২-৩ বাক্যে ব্যাখ্যা করুন। যদি সরাসরি কোনো প্রভাব না থাকে তাহলে "কোনো সরাসরি প্রভাব নেই" লিখুন]

উত্তর:"""
        
        return prompt
    
    def _build_english_analysis_prompt(
        self,
        content: str,
        title: str,
        date: str,
        party: Optional[str],
        figure: Optional[str]
    ) -> str:
        """Build English analysis prompt with known entities."""
        
        # Get known parties and figures
        known_parties = get_party_list_for_prompt('english')
        known_figures = get_figures_list_for_prompt('english')
        
        context = f"Title: {title}\nDate: {date}\n"
        context += f"\n[Known Political Parties: {known_parties}]\n"
        context += f"[Known Political Figures: {known_figures}]\n"
        
        prompt = f"""Analyze the following Bangladeshi political article and provide the following information:

{context}

Article:
{content}

Please respond in the following format (in English):

1. SUMMARY:
[Provide a 3-4 sentence summary of the article]

2. KEYWORDS:
[List 5-10 important keywords, separated by commas]

3. TOPICS:
[List 3-5 main topics covered, separated by commas]

4. POLITICAL_PARTIES:
[List all political parties/organizations mentioned in the article. Find them from the Known Political Parties list above and use EXACT names. Examples: BNP, Awami League, Jamaat-e-Islami, Interim Government, etc. Separate by commas. If no parties are mentioned, write "None".

⚠️ IMPORTANT: Use names from the Known Political Parties list only. Do not create new names.]

5. POLITICAL_FIGURES:
[List all political figures/leaders mentioned in the article. Find them from the Known Political Figures list above and use EXACT names. Examples: Tareq Rahman, Mirza Fakhrul, Dr. Muhammad Yunus, etc. Separate by commas. If no figures are mentioned, write "None".

⚠️ IMPORTANT: Use names from the Known Political Figures list only. Do not create new names.]

6. ELECTION_2026_IMPACT:
[What is the potential impact of this article/speech on Bangladesh's 2026 election? If there is an impact, explain in 2-3 sentences. If there is no direct impact, write "No direct impact"]

Response:"""
        
        return prompt
    
    def _parse_analysis_response(self, response: str, language: str) -> Dict:
        """
        Parse structured LLM response into dictionary.
        
        Args:
            response: Raw LLM response
            language: 'bangla' or 'english'
            
        Returns:
            Parsed analysis dictionary
        """
        result = {
            'summary': '',
            'keywords': [],
            'topics': [],
            'political_parties': [],
            'political_figures': [],
            'election_2026_impact': '',
            'has_election_impact': False
        }
        
        try:
            # Split response into sections
            lines = response.strip().split('\n')
            current_section = None
            section_content = []
            
            for line in lines:
                line = line.strip()
                
                # Check for section headers
                if 'SUMMARY' in line.upper() or 'সারসংক্ষেপ' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'summary'
                    section_content = []
                elif 'KEYWORDS' in line.upper() or 'কীওয়ার্ড' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'keywords'
                    section_content = []
                elif 'TOPICS' in line.upper() or 'বিষয়' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'topics'
                    section_content = []
                elif 'POLITICAL_PARTIES' in line.upper() or 'রাজনৈতিক দল' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'political_parties'
                    section_content = []
                elif 'POLITICAL_FIGURES' in line.upper() or 'রাজনৈতিক ব্যক্তিত্ব' in line or 'নেতা' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'political_figures'
                    section_content = []
                elif 'ELECTION' in line.upper() or 'নির্বাচন' in line or 'IMPACT' in line.upper() or 'প্রভাব' in line:
                    if current_section and section_content:
                        self._process_section(result, current_section, section_content)
                    current_section = 'election_impact'
                    section_content = []
                elif line and not line.startswith(('1.', '2.', '3.', '4.', '-', '*')):
                    # Content line
                    section_content.append(line)
            
            # Process last section
            if current_section and section_content:
                self._process_section(result, current_section, section_content)
            
            # Determine if has election impact
            impact_text = result['election_2026_impact'].lower()
            no_impact_indicators = ['no direct impact', 'কোনো সরাসরি প্রভাব নেই', 'no impact', 'নেই']
            result['has_election_impact'] = not any(indicator in impact_text for indicator in no_impact_indicators)
            
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
        
        return result
    
    def _process_section(self, result: Dict, section: str, content: List[str]):
        """Process a section of the analysis."""
        
        text = ' '.join(content).strip()
        
        if section == 'summary':
            result['summary'] = text
        elif section == 'keywords':
            # Split by commas and clean
            keywords = [kw.strip() for kw in text.split(',') if kw.strip()]
            result['keywords'] = keywords
        elif section == 'topics':
            # Split by commas and clean
            topics = [topic.strip() for topic in text.split(',') if topic.strip()]
            result['topics'] = topics
        elif section == 'political_parties':
            # Split by commas, clean, and normalize to standard names
            raw_parties = [p.strip() for p in text.split(',') if p.strip() and p.strip().lower() != 'none']
            normalized_parties = []
            for party in raw_parties:
                normalized = normalize_party_name(party)
                if normalized and normalized not in normalized_parties:
                    normalized_parties.append(normalized)
            result['political_parties'] = normalized_parties
            
        elif section == 'political_figures':
            # Split by commas, clean, and normalize with party detection
            raw_figures = [f.strip() for f in text.split(',') if f.strip() and f.strip().lower() != 'none']
            normalized_figures = []
            figure_to_party = {}
            
            for figure in raw_figures:
                normalized, party = normalize_figure_name(figure)
                if normalized and normalized not in normalized_figures:
                    normalized_figures.append(normalized)
                    if party:
                        figure_to_party[normalized] = party
            
            result['political_figures'] = normalized_figures
            result['figure_to_party_mapping'] = figure_to_party  # For storage routing
        elif section == 'election_impact':
            result['election_2026_impact'] = text
    
    def _get_fallback_analysis(self, language: str) -> Dict:
        """Return fallback analysis if LLM fails."""
        
        if language == 'bangla':
            return {
                'summary': 'বিশ্লেষণ ব্যর্থ হয়েছে',
                'keywords': ['রাজনীতি', 'বাংলাদেশ'],
                'topics': ['রাজনৈতিক খবর'],
                'political_parties': [],
                'political_figures': [],
                'election_2026_impact': 'বিশ্লেষণ করা সম্ভব হয়নি',
                'has_election_impact': False,
                'language': language
            }
        else:
            return {
                'summary': 'Analysis failed',
                'keywords': ['politics', 'bangladesh'],
                'topics': ['political news'],
                'political_parties': [],
                'political_figures': [],
                'election_2026_impact': 'Could not analyze',
                'has_election_impact': False,
                'language': language
            }


# Singleton instance
_analyzer = None

def get_article_analyzer() -> EnhancedArticleAnalyzer:
    """Get or create the article analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = EnhancedArticleAnalyzer()
    return _analyzer
