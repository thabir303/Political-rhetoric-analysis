"""
LLM Generation Module for Political Speech Analysis

Supports multiple LLM providers:
1. OpenAI (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
2. Google Gemini (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
3. Groq API with LLaMA models

Generates:
1. Political speech summaries with context about stances
2. Keywords highlighting important topics and discourse

Supports both English and Bangla content.
"""

import os
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available. Install with: pip install openai")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("groq not available. Install with: pip install groq")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not available. Install with: pip install google-generativeai")

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logger.warning("python-dotenv not available")

# Load environment variables
if DOTENV_AVAILABLE:
    load_dotenv()


class LLMGenerator:
    """
    LLM-based generator for political speech summaries and keywords.
    
    Supports multiple LLM providers:
    - OpenAI (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
    - Google Gemini (gemini-2.0-flash-exp, gemini-1.5-pro, etc.)
    - Groq API with LLaMA models
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        api_key: Optional[str] = None,
        provider: Optional[str] = None
    ):
        """
        Initialize the LLM generator.
        
        Args:
            model: Model name 
                   - OpenAI: gpt-4o, gpt-4o-mini (default), gpt-4-turbo, gpt-3.5-turbo
                   - Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
                   - Groq: llama-3.3-70b-versatile, llama-3.1-8b-instant
            temperature: Sampling temperature (0.0-1.0, lower = more focused)
            max_tokens: Maximum tokens to generate
            api_key: API key (defaults to OPENAI_API_KEY, GEMINI_API_KEY or GROQ_API_KEY env variable)
            provider: LLM provider ("openai", "gemini" or "groq")
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Auto-detect provider if not specified
        if provider is None:
            if model.startswith("gpt") or model.startswith("o1"):
                provider = "openai"
            elif model.startswith("gemini"):
                provider = "gemini"
            elif model.startswith("llama"):
                provider = "groq"
            else:
                # Default to OpenAI for unknown models
                provider = "openai"
        
        self.provider = provider.lower()
        
        # Initialize based on provider
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("openai not installed. Install with: pip install openai")
            
            # Get OpenAI API key
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key not found. Provide via api_key parameter or OPENAI_API_KEY environment variable."
                )
            
            # Initialize OpenAI client
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"LLM Generator initialized with OpenAI model: {model}")
            
        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("google-generativeai not installed. Install with: pip install google-generativeai")
            
            # Get Gemini API key
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Gemini API key not found. Provide via api_key parameter or GEMINI_API_KEY environment variable."
                )
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(model)
            logger.info(f"LLM Generator initialized with Gemini model: {model}")
            
        elif self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError("groq not installed. Install with: pip install groq")
            
            # Get Groq API key
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Groq API key not found. Provide via api_key parameter or GROQ_API_KEY environment variable."
                )
            
            # Initialize Groq client
            self.client = Groq(api_key=self.api_key)
            logger.info(f"LLM Generator initialized with Groq model: {model}")
            
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'gemini' or 'groq'")
    
    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call the LLM API.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for instruction
            temperature: Override default temperature
            max_tokens: Override default max_tokens
        
        Returns:
            Generated text
        """
        try:
            if self.provider == "openai":
                # OpenAI API call
                messages = []
                
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                # Use max_completion_tokens for newer models (gpt-4o, o1, etc.)
                # Use max_tokens for older models (gpt-3.5-turbo, gpt-4-turbo)
                completion_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "top_p": 1
                }
                
                # Check if using newer models that require max_completion_tokens
                if any(model_prefix in self.model for model_prefix in ["gpt-4o", "o1", "gpt-5"]):
                    completion_params["max_completion_tokens"] = max_tokens or self.max_tokens
                else:
                    completion_params["max_tokens"] = max_tokens or self.max_tokens
                
                response = self.client.chat.completions.create(**completion_params)
                
                generated_text = response.choices[0].message.content
                
                # Debug log for empty responses
                if not generated_text or len(generated_text.strip()) == 0:
                    logger.warning(f"⚠️ Empty response from {self.model}")
                    logger.warning(f"Response object: {response}")
                    logger.warning(f"Finish reason: {response.choices[0].finish_reason}")
                    logger.warning(f"Completion params: {completion_params}")
                
                generated_text = generated_text.strip() if generated_text else ""
                logger.info(f"OpenAI response received successfully (length: {len(generated_text)} chars)")
                
            elif self.provider == "gemini":
                # Gemini API call
                # Combine system and user prompts
                full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
                
                generation_config = {
                    "temperature": temperature or self.temperature,
                    "max_output_tokens": max_tokens or self.max_tokens,
                }
                
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Check if response has valid parts
                if not response.candidates:
                    logger.error("Gemini returned no candidates")
                    raise ValueError("Gemini API returned no response candidates")
                
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                
                # Log finish reason for debugging
                logger.info(f"Gemini finish_reason: {finish_reason} ({candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else 'unknown'})")
                
                # finish_reason enum values:
                # FINISH_REASON_UNSPECIFIED = 0
                # STOP = 1 (natural completion - success)
                # MAX_TOKENS = 2 (hit token limit)
                # SAFETY = 3 (blocked by safety filters)
                # RECITATION = 4 (blocked due to recitation)
                # OTHER = 5 (other reason)
                
                if finish_reason == 3:  # SAFETY
                    logger.error("Content was blocked by Gemini safety filters")
                    logger.error(f"Safety ratings: {candidate.safety_ratings}")
                    raise ValueError("Content was blocked by safety filters. Try a different prompt or fewer articles.")
                
                if finish_reason == 2:  # MAX_TOKENS
                    logger.error("Response was truncated/stopped due to MAX_TOKENS or similar issue")
                    logger.error(f"Candidate content: {candidate.content}")
                    # This can also mean the response was blocked for other reasons
                    if not candidate.content or not candidate.content.parts:
                        raise ValueError("Content generation failed. The prompt may be too short or contain problematic content. Try with more articles or different content.")
                
                if not candidate.content or not candidate.content.parts:
                    logger.error(f"No content parts in response. Finish reason: {finish_reason}")
                    logger.error(f"Full candidate: {candidate}")
                    raise ValueError(f"Gemini did not generate content. Finish reason: {finish_reason}. Try with more articles or adjust the prompt.")
                
                generated_text = response.text.strip()
                
            elif self.provider == "groq":
                # Groq API call
                messages = []
                
                if system_prompt:
                    messages.append({
                        "role": "system",
                        "content": system_prompt
                    })
                
                messages.append({
                    "role": "user",
                    "content": prompt
                })
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    top_p=1,
                    stream=False
                )
                
                generated_text = response.choices[0].message.content.strip()
            
            # Validate response is not empty
            if not generated_text or len(generated_text.strip()) == 0:
                error_msg = f"⚠️ Empty response from {self.model}. This model may not be supported or may have issues."
                logger.error(error_msg)
                logger.error(f"Finish reason: {response.choices[0].finish_reason}")
                raise ValueError(f"Empty response from model {self.model}. Please verify the model name is correct and supported by OpenAI.")
            
            # Print complete LLM response to terminal
            print("\n" + "="*80)
            print("🤖 LLM RESPONSE (Complete)")
            print("="*80)
            print("PROVIDER:", self.provider.upper())
            print("MODEL:", self.model)
            print("TEMPERATURE:", temperature or self.temperature)
            print("TOKENS USED:", len(generated_text.split()))
            print("-"*80)
            print("RESPONSE:")
            print(generated_text)
            print("="*80 + "\n")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error calling {self.provider} API: {e}")
            raise
    
    def generate_speech_summary(
        self,
        article_content: str,
        article_title: Optional[str] = None,
        political_figure: Optional[str] = None,
        political_party: Optional[str] = None,
        key_issues: Optional[List[str]] = None,
        language: str = "English"
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Generate a comprehensive summary of a political speech.
        
        Args:
            article_content: The article text containing the speech
            article_title: Article title (optional)
            political_figure: Name of the political figure (optional)
            political_party: Political party affiliation (optional)
            key_issues: List of key issues to focus on (optional)
            language: Content language ('English' or 'Bangla')
        
        Returns:
            Dictionary with 'summary', 'key_points', and 'stance_analysis'
        """
        # Build context
        context_parts = []
        
        if article_title:
            context_parts.append(f"Article Title: {article_title}")
        
        if political_figure:
            context_parts.append(f"Political Figure: {political_figure}")
        
        if political_party:
            context_parts.append(f"Political Party: {political_party}")
        
        if key_issues:
            context_parts.append(f"Key Issues: {', '.join(key_issues)}")
        
        context = "\n".join(context_parts) if context_parts else ""
        
        # Build system prompt based on language
        if language.lower() == "bangla":
            system_prompt = """আপনি বাংলাদেশের রাজনীতি বিশেষজ্ঞ একজন রাজনৈতিক বিশ্লেষক। 
আপনার কাজ হল রাজনৈতিক বক্তৃতা এবং বিবৃতি বিশ্লেষণ করা, এবং মূল পয়েন্ট, রাজনৈতিক অবস্থান, 
এবং আলোচনার প্রেক্ষাপট তুলে ধরে বিস্তৃত সারসংক্ষেপ প্রদান করা।

মনোযোগ দিন:
1. প্রধান যুক্তি এবং মূল পয়েন্টসমূহ
2. গুরুত্বপূর্ণ বিষয়ে রাজনৈতিক অবস্থান (নির্বাচন কমিশন, অন্তর্বর্তী সরকার, গণতন্ত্র ইত্যাদি)
3. ব্যবহৃত ভাষা ও বাগ্মিতা
4. রাজনৈতিক পরিস্থিতিতে প্রভাব
5. নির্দিষ্ট নীতি প্রস্তাব বা দাবিসমূহ

অবশ্যই বাংলায় উত্তর দিন।"""
        else:
            system_prompt = """You are an expert political analyst specializing in Bangladeshi politics. 
Your task is to analyze political speeches and statements, providing comprehensive summaries 
that highlight key points, political stances, and the context of the discourse.

Focus on:
1. Main arguments and key points made
2. Political stance on important issues (Election Commission, Interim Government, Democracy, etc.)
3. Tone and rhetoric used
4. Implications for political landscape
5. Specific policy proposals or demands"""
        
        # Build user prompt
        if language.lower() == "bangla":
            user_prompt = f"""বাংলাদেশের রাজনৈতিক প্রেক্ষাপটে নিম্নলিখিত রাজনৈতিক বক্তৃতা/বিবৃতি বিশ্লেষণ করুন।

{context}

Article Content:
{article_content}

দয়া করে প্রদান করুন:
1. **Summary** (সারসংক্ষেপ): বক্তৃতার মূল বিষয়বস্তু (২-৩ বাক্য)
2. **Key Points** (মূল পয়েন্ট): গুরুত্বপূর্ণ পয়েন্টগুলির তালিকা (৩-৫টি)
3. **Keywords** (মূল শব্দ): রাজনৈতিকভাবে গুরুত্বপূর্ণ শব্দ (৫-৮টি) - শুধুমাত্র বিষয়, ইস্যু, ধারণা (ব্যক্তি/দল/দেশের নাম নয়)
4. **Topics Covered** (আলোচিত বিষয়): প্রধান রাজনৈতিক বিষয়সমূহ (৩-৫টি) - নির্বাচন, সংস্কার, নিরাপত্তা ইত্যাদি
5. **Stance Analysis** (অবস্থান বিশ্লেষণ): প্রধান ইশুতে রাজনৈতিক অবস্থান (২-৩ বাক্য)

IMPORTANT: 
- সম্পূর্ণ উত্তর অবশ্যই বাংলায় দিন
- Keywords এবং Topics এ ব্যক্তি, দল, বা দেশের নাম ব্যবহার করবেন না
- রাজনৈতিক ধারণা, নীতি, এবং ইস্যু focus করুন
- Clear sections ব্যবহার করুন"""
        else:
            user_prompt = f"""Analyze the following political speech/statement in the context of Bangladeshi politics.

{context}

Article Content:
{article_content}

Please provide:
1. **Summary**: A concise summary of the speech (2-3 sentences)
2. **Key Points**: List of main arguments or points made (3-5 bullet points)
3. **Keywords**: Politically significant keywords (5-8 words) - ONLY concepts, issues, policies (NO names of people/parties/countries)
4. **Topics Covered**: Main political topics discussed (3-5 topics) - e.g., elections, reforms, security, democracy
5. **Stance Analysis**: Analysis of the political figure's stance on key issues mentioned (2-3 sentences)

IMPORTANT:
- For Keywords and Topics, focus ONLY on political concepts, policies, and issues
- DO NOT include names of individuals, political parties, or countries
- Focus on themes like: election reform, judicial independence, corruption, democracy, governance, etc.
- Use clear section headers in your response"""
        
        # Call LLM
        try:
            print(f"\n🔍 GENERATING SPEECH SUMMARY for: {political_figure or 'Unknown Figure'}")
            print(f"📰 Article Title: {article_title or 'N/A'}")
            print(f"🏛️ Political Party: {political_party or 'N/A'}")
            print(f"🌐 Language: {language}")
            
            response = self._call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1500
            )
            
            # Parse response
            result = self._parse_speech_summary(response)
            
            # Add metadata
            result['political_figure'] = political_figure
            result['political_party'] = political_party
            result['language'] = language
            
            # Print summary of generated content
            print(f"\n✅ SPEECH SUMMARY GENERATED SUCCESSFULLY")
            print(f"👤 Political Figure: {political_figure or 'Unknown'}")
            print(f"🏛️ Political Party: {political_party or 'Unknown'}")
            print(f"📝 Summary Length: {len(result.get('summary', ''))}")
            print(f"🎯 Key Points Count: {len(result.get('key_points', []))}")
            print(f"📊 Has Stance Analysis: {'Yes' if result.get('stance_analysis') else 'No'}")
            
            logger.info(f"Generated speech summary for {political_figure or 'unknown figure'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating speech summary: {e}")
            return {
                'summary': 'Error generating summary',
                'key_points': [],
                'stance_analysis': 'Error analyzing stance',
                'error': str(e)
            }
    
    def generate_keywords(
        self,
        article_content: str,
        article_title: Optional[str] = None,
        political_context: Optional[str] = None,
        num_keywords: int = 10,
        language: str = "English"
    ) -> Dict[str, Union[List[str], str]]:
        """
        Generate keywords representing political discourse.
        
        Args:
            article_content: The article text
            article_title: Article title (optional)
            political_context: Additional political context (optional)
            num_keywords: Number of keywords to generate
            language: Content language ('English' or 'Bangla')
        
        Returns:
            Dictionary with 'keywords', 'phrases', and 'topics'
        """
        # Build context
        context = f"Article Title: {article_title}\n" if article_title else ""
        if political_context:
            context += f"Political Context: {political_context}\n"
        
        # Build system prompt based on language
        if language.lower() == "bangla":
            system_prompt = """আপনি রাজনৈতিক আলোচনা বিশ্লেষণ এবং NLP এর বিশেষজ্ঞ। 
আপনার কাজ হল রাজনৈতিক নিবন্ধ থেকে সবচেয়ে গুরুত্বপূর্ণ এবং প্রাসঙ্গিক keywords নিষ্কাশন করা, 
বিষয়, অবস্থান, নীতি, এবং রাজনৈতিক বাগ্মিতার উপর মনোযোগ দিয়ে যা আলোচনার বৈশিষ্ট্য নির্ধারণ করে।

অবশ্যই বাংলায় keywords এবং phrases প্রদান করুন।"""
        else:
            system_prompt = """You are an expert in political discourse analysis and NLP. 
Your task is to extract the most important and relevant keywords from political articles, 
focusing on topics, stances, policies, and political rhetoric that characterize the discourse."""
        
        # Build user prompt
        if language.lower() == "bangla":
            user_prompt = f"""বাংলাদেশী রাজনৈতিক প্রসঙ্গে নিম্নলিখিত নিবন্ধ থেকে গুরুত্বপূর্ণ keywords এবং phrases নির্ধারণ করুন।

{context}

Article Content:
{article_content}

দয়া করে প্রদান করুন:
1. **Keywords** ({num_keywords}টি): একক শব্দ keywords (যেমন: নির্বাচন, সংস্কার, গণতন্ত্র)
2. **Key Phrases** (৫টি): গুরুত্বপূর্ণ ২-৩ শব্দের phrases (যেমন: নির্বাচন কমিশন সংস্কার)  
3. **Main Topics** (৩টি): প্রধান বিষয়/থিম

IMPORTANT: অবশ্যই পুরো উত্তর বাংলায় দিন। শুধুমাত্র তালিকা আকারে উত্তর দিন, কোনো ব্যাখ্যা ছাড়া। প্রতিটি item নতুন লাইনে।"""
        else:
            user_prompt = f"""Extract the most important and relevant keywords and phrases from the following political article 
in the context of Bangladeshi politics.

{context}

Article Content:
{article_content}

Please provide:
1. **Keywords** ({num_keywords}): Single-word keywords (e.g., election, reform, democracy)
2. **Key Phrases** (5): Important 2-3 word phrases (e.g., election commission reform)
3. **Main Topics** (3): Main themes or topics discussed

Provide ONLY the lists, no explanations. Each item on a new line."""
        
        # Call LLM
        try:
            print(f"\n🔍 GENERATING KEYWORDS")
            print(f"📰 Article Title: {article_title or 'N/A'}")
            print(f"🎯 Number of Keywords: {num_keywords}")
            print(f"🌐 Language: {language}")
            
            response = self._call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=800
            )
            
            # Parse response
            result = self._parse_keywords(response, num_keywords)
            
            # Add metadata
            result['language'] = language
            
            # Print summary of generated content
            print(f"\n✅ KEYWORDS GENERATED SUCCESSFULLY")
            print(f"🔑 Keywords: {result.get('keywords', [])}")
            print(f"📋 Key Phrases: {result.get('phrases', [])}")
            print(f"📊 Main Topics: {result.get('topics', [])}")
            
            logger.info(f"Generated {len(result['keywords'])} keywords")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating keywords: {e}")
            return {
                'keywords': [],
                'phrases': [],
                'topics': [],
                'error': str(e)
            }
    
    def analyze_article(
        self,
        article: Dict,
        generate_summary: bool = True,
        generate_keywords: bool = True
    ) -> Dict:
        """
        Comprehensive analysis of a political article.
        
        Args:
            article: Article dictionary with 'content', 'title', etc.
            generate_summary: Whether to generate speech summary
            generate_keywords: Whether to generate keywords
        
        Returns:
            Dictionary with analysis results
        """
        result = {
            'article_id': article.get('id'),
            'article_title': article.get('title')
        }
        
        # Extract article information
        content = article.get('content', '')
        title = article.get('title', '')
        language = article.get('language', 'English')
        
        # Get political context
        political_figure = None
        political_party = None
        key_issues = []
        
        if 'people' in article and article['people']:
            political_figure = article['people'][0] if isinstance(article['people'], list) else article['people']
        
        if 'parties' in article and article['parties']:
            political_party = article['parties'][0] if isinstance(article['parties'], list) else article['parties']
        
        if 'themes' in article and article['themes']:
            key_issues = article['themes'] if isinstance(article['themes'], list) else [article['themes']]
        
        # Generate summary
        if generate_summary:
            summary_result = self.generate_speech_summary(
                article_content=content,
                article_title=title,
                political_figure=political_figure,
                political_party=political_party,
                key_issues=key_issues,
                language=language
            )
            result['llm_summary'] = summary_result
        
        # Generate keywords
        if generate_keywords:
            political_context = f"{political_party} - {political_figure}" if political_party and political_figure else None
            
            keywords_result = self.generate_keywords(
                article_content=content,
                article_title=title,
                political_context=political_context,
                language=language
            )
            result['llm_keywords'] = keywords_result
        
        return result
    
    def _parse_speech_summary(self, response: str) -> Dict[str, Union[str, List[str]]]:
        """
        Parse LLM response for speech summary.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Parsed dictionary
        """
        result = {
            'summary': '',
            'key_points': [],
            'keywords': [],
            'topics': [],
            'stance_analysis': '',
            'raw_response': response  # Keep raw response for debugging
        }
        
        # Try to find sections using different patterns
        lines = response.split('\n')
        current_section = None
        summary_buffer = []
        stance_buffer = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Check for section headers (case-insensitive, various formats)
            line_lower = line_stripped.lower()
            
            # Summary section - handle both English and Bangla headers
            if any(marker in line_lower for marker in ['## summary', '**summary**', '1. summary', '1. **summary', 'summary:', 
                                                       '**সারসংক্ষেপ**', 'সারসংক্ষেপ:', '## সারসংক্ষেপ']):
                current_section = 'summary'
                # Try to extract summary from same line
                if ':' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    if len(parts) > 1 and parts[1].strip():
                        summary_buffer.append(parts[1].strip())
                continue
            
            # Key points section - handle both English and Bangla headers
            elif any(marker in line_lower for marker in ['## key point', '**key point', '2. key point', '2. **key', 'key points:',
                                                         '**মূল পয়েন্ট**', 'মূল পয়েন্ট:', '## মূল পয়েন্ট', '২. মূল পয়েন্ট']):
                current_section = 'key_points'
                continue
            
            # Keywords section - NEW
            elif any(marker in line_lower for marker in ['## keyword', '**keyword', '3. keyword', '3. **keyword', 'keywords:',
                                                         '**মূল শব্দ**', 'মূল শব্দ:', '## মূল শব্দ', '৩. মূল শব্দ']):
                current_section = 'keywords'
                continue
            
            # Topics section - NEW  
            elif any(marker in line_lower for marker in ['## topic', '**topic', '4. topic', '4. **topic', 'topics covered:', 'topics:',
                                                         '**আলোচিত বিষয়**', 'আলোচিত বিষয়:', '## আলোচিত বিষয়', '৪. আলোচিত বিষয়']):
                current_section = 'topics'
                continue
            
            # Stance analysis section - handle both English and Bangla headers
            elif any(marker in line_lower for marker in ['## stance', '**stance', '5. stance', '5. **stance', 'stance analysis:',
                                                         '**অবস্থান বিশ্লেষণ**', 'অবস্থান বিশ্লেষণ:', '## অবস্থান বিশ্লেষণ', '৫. অবস্থান বিশ্লেষণ']):
                current_section = 'stance_analysis'
                # Try to extract stance from same line
                if ':' in line_stripped:
                    parts = line_stripped.split(':', 1)
                    if len(parts) > 1 and parts[1].strip():
                        stance_buffer.append(parts[1].strip())
                continue
            
            # Add content to current section
            if current_section == 'summary':
                # Skip if it's just a header line
                if not line_stripped.startswith('#'):
                    summary_buffer.append(line_stripped)
            elif current_section == 'key_points':
                # Remove bullet points (*), numbering, and markdown (including Bangla patterns)
                clean_line = line_stripped.lstrip('•-*#123456789. ')
                # Remove common bullet point markers and numbers
                if clean_line.startswith('* '):
                    clean_line = clean_line[2:]
                elif clean_line.startswith('• '):
                    clean_line = clean_line[2:]
                elif clean_line.startswith('- '):
                    clean_line = clean_line[2:]
                
                clean_line = clean_line.strip('*_')
                
                if clean_line and not clean_line.startswith('**') and not clean_line.startswith('#') and len(clean_line) > 5:
                    result['key_points'].append(clean_line)
                    print(f"DEBUG: Added key point: {clean_line}")
            elif current_section == 'keywords':
                # Parse keywords - can be comma-separated or bullet points
                clean_line = line_stripped.lstrip('•-*#123456789. ').strip('*_')
                if clean_line and not clean_line.startswith('**') and not clean_line.startswith('#'):
                    # Check if comma-separated
                    if ',' in clean_line:
                        keywords = [kw.strip() for kw in clean_line.split(',')]
                        result['keywords'].extend([kw for kw in keywords if kw and len(kw) > 2])
                    elif clean_line and len(clean_line) > 2:
                        result['keywords'].append(clean_line)
            elif current_section == 'topics':
                # Parse topics - can be comma-separated or bullet points
                clean_line = line_stripped.lstrip('•-*#123456789. ').strip('*_')
                if clean_line and not clean_line.startswith('**') and not clean_line.startswith('#'):
                    # Check if comma-separated
                    if ',' in clean_line:
                        topics = [t.strip() for t in clean_line.split(',')]
                        result['topics'].extend([t for t in topics if t and len(t) > 2])
                    elif clean_line and len(clean_line) > 2:
                        result['topics'].append(clean_line)
            elif current_section == 'stance_analysis':
                # Skip if it's just a header line
                if not line_stripped.startswith('#'):
                    stance_buffer.append(line_stripped)
        
        # Join buffered content
        result['summary'] = ' '.join(summary_buffer)
        result['stance_analysis'] = ' '.join(stance_buffer)
        
        # Debug parsing results
        print("DEBUG PARSING RESULTS:")
        print(f"  Summary: {len(result['summary'])} chars")
        print(f"  Key Points: {len(result['key_points'])} items")
        print(f"  Keywords: {len(result['keywords'])} items - {result['keywords']}")
        print(f"  Topics: {len(result['topics'])} items - {result['topics']}")
        print(f"  Stance Analysis: {len(result['stance_analysis'])} chars")
        if result['key_points']:
            print(f"  Key Points List: {result['key_points']}")
        else:
            print("  No key points found. Raw response lines:")
            for i, line in enumerate(response.split('\n')[:10]):
                print(f"    Line {i}: '{line.strip()}')")
        
        # If parsing failed, try to extract something useful from raw response
        if not result['summary'] and not result['key_points']:
            # Use first paragraph as summary
            paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
            if paragraphs:
                result['summary'] = paragraphs[0]
        
        return result
    
    def _parse_keywords(self, response: str, expected_count: int) -> Dict[str, List[str]]:
        """
        Parse LLM response for keywords.
        
        Args:
            response: Raw LLM response
            expected_count: Expected number of keywords
        
        Returns:
            Parsed dictionary
        """
        result = {
            'keywords': [],
            'phrases': [],
            'topics': [],
            'raw_response': response  # Keep raw response for debugging
        }
        
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                continue
            
            # Check for section headers (case-insensitive, various formats)
            line_lower = line_stripped.lower()
            
            # Keywords section - handle both English and Bangla
            if any(marker in line_lower for marker in ['**keywords**', '1. keywords', '1. **keywords', 'keywords:']):
                current_section = 'keywords'
                continue
            
            # Phrases section - handle both English and Bangla  
            elif any(marker in line_lower for marker in ['**key phrase', '**phrase', '2. key phrase', '2. **key', 'key phrases:', 'phrases:']):
                current_section = 'phrases'
                continue
            
            # Topics section - handle both English and Bangla
            elif any(marker in line_lower for marker in ['**main topic', '**topic', '3. main topic', '3. **main', 'main topics:', 'topics:']):
                current_section = 'topics'
                continue
            
            # Skip section headers
            if line_stripped.startswith('**') and line_stripped.endswith('**'):
                continue
            if line_stripped.startswith('#'):
                continue
            
            # Add content to current section
            # Remove bullet points, numbering, and extra formatting
            clean_line = line_stripped.lstrip('•-*#123456789. ').strip('*_')
            
            if clean_line:
                if current_section == 'keywords':
                    result['keywords'].append(clean_line)
                elif current_section == 'phrases':
                    result['phrases'].append(clean_line)
                elif current_section == 'topics':
                    result['topics'].append(clean_line)
        
        # If no keywords found, try to extract from raw response
        if not result['keywords'] and not result['phrases']:
            # Split by commas or newlines and take unique words
            words = []
            for line in response.split('\n'):
                line = line.strip().lstrip('•-*#123456789. ')
                if line and not line.startswith('**') and not line.startswith('#'):
                    words.extend([w.strip() for w in line.split(',') if w.strip()])
            result['keywords'] = words[:expected_count]
        
        # Limit to expected counts
        result['keywords'] = result['keywords'][:expected_count]
        result['phrases'] = result['phrases'][:5]
        result['topics'] = result['topics'][:3]
        
        return result


# Convenience functions
def generate_speech_summary(
    article_content: str,
    article_title: Optional[str] = None,
    political_figure: Optional[str] = None,
    political_party: Optional[str] = None,
    key_issues: Optional[List[str]] = None,
    language: str = "English",
    api_key: Optional[str] = None
) -> Dict[str, Union[str, List[str]]]:
    """
    Convenience function to generate speech summary.
    
    Args:
        article_content: The article text
        article_title: Article title
        political_figure: Political figure name
        political_party: Political party
        key_issues: Key issues list
        language: Content language
        api_key: Groq API key
    
    Returns:
        Summary dictionary
    """
    generator = LLMGenerator(api_key=api_key)
    return generator.generate_speech_summary(
        article_content=article_content,
        article_title=article_title,
        political_figure=political_figure,
        political_party=political_party,
        key_issues=key_issues,
        language=language
    )


def generate_keywords(
    article_content: str,
    article_title: Optional[str] = None,
    political_context: Optional[str] = None,
    num_keywords: int = 10,
    language: str = "English",
    api_key: Optional[str] = None
) -> Dict[str, Union[List[str], str]]:
    """
    Convenience function to generate keywords.
    
    Args:
        article_content: The article text
        article_title: Article title
        political_context: Political context
        num_keywords: Number of keywords
        language: Content language
        api_key: Groq API key
    
    Returns:
        Keywords dictionary
    """
    generator = LLMGenerator(api_key=api_key)
    return generator.generate_keywords(
        article_content=article_content,
        article_title=article_title,
        political_context=political_context,
        num_keywords=num_keywords,
        language=language
    )


def analyze_article(
    article: Dict,
    generate_summary: bool = True,
    generate_keywords: bool = True,
    api_key: Optional[str] = None
) -> Dict:
    """
    Convenience function to analyze an article.
    
    Args:
        article: Article dictionary
        generate_summary: Generate summary flag
        generate_keywords: Generate keywords flag
        api_key: Groq API key
    
    Returns:
        Analysis dictionary
    """
    generator = LLMGenerator(api_key=api_key)
    return generator.analyze_article(
        article=article,
        generate_summary=generate_summary,
        generate_keywords=generate_keywords
    )


if __name__ == "__main__":
    # Example usage
    print("=" * 80)
    print("LLM GENERATION MODULE")
    print("=" * 80)
    
    # Check if API key is available
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("\n❌ Error: GROQ_API_KEY not found in environment variables")
        print("Please set GROQ_API_KEY in .env file")
        exit(1)
    
    print(f"\n✓ API Key found: {api_key[:20]}...")
    
    # Initialize generator
    print("\n[1/3] Initializing LLM Generator...")
    print("-" * 80)
    
    try:
        generator = LLMGenerator(api_key=api_key)
        print(f"✓ Generator initialized with model: {generator.model}")
    except Exception as e:
        print(f"❌ Error initializing generator: {e}")
        exit(1)
    
    # Example article
    print("\n[2/3] Generating Speech Summary...")
    print("-" * 80)
    
    sample_article = {
        'title': 'BNP Demands Comprehensive Election Reforms',
        'content': '''
        BNP acting chairman Tareq Rahman addressed party members in a virtual rally,
        calling for sweeping election reforms. He emphasized that free and fair elections
        are essential for democracy and criticized the current Election Commission structure.
        Rahman proposed a neutral caretaker government system for election oversight and
        demanded the reconstitution of the Election Commission with independent members.
        He also highlighted the importance of voter list verification and transparent
        ballot counting. The BNP leader warned that without credible reforms, any future
        election would lack legitimacy.
        ''',
        'people': ['Tareq Rahman'],
        'parties': ['BNP'],
        'themes': ['Election Commission', 'Democracy', 'Reform'],
        'language': 'English'
    }
    
    try:
        # Generate summary
        summary = generator.generate_speech_summary(
            article_content=sample_article['content'],
            article_title=sample_article['title'],
            political_figure='Tareq Rahman',
            political_party='BNP',
            key_issues=['Election Commission', 'Democracy'],
            language='English'
        )
        
        print(f"✓ Summary generated successfully")
        print(f"\nSummary:")
        print(f"  {summary['summary']}")
        print(f"\nKey Points:")
        for i, point in enumerate(summary['key_points'], 1):
            print(f"  {i}. {point}")
        print(f"\nStance Analysis:")
        print(f"  {summary['stance_analysis']}")
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
    
    # Generate keywords
    print("\n[3/3] Generating Keywords...")
    print("-" * 80)
    
    try:
        keywords_result = generator.generate_keywords(
            article_content=sample_article['content'],
            article_title=sample_article['title'],
            political_context="BNP - Tareq Rahman",
            num_keywords=10,
            language='English'
        )
        
        print(f"✓ Keywords generated successfully")
        print(f"\nKeywords: {', '.join(keywords_result['keywords'][:8])}")
        print(f"\nKey Phrases:")
        for phrase in keywords_result['phrases'][:3]:
            print(f"  - {phrase}")
        print(f"\nMain Topics: {', '.join(keywords_result['topics'])}")
        
    except Exception as e:
        print(f"❌ Error generating keywords: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Module ready for use!")
    print("=" * 80)
