"""
Translation prompt templates and generators for Jupyter Notebooks
"""
from typing import List
from .config import Config


class PromptGenerator:
    """Generates translation prompts with consistent rules for Jupyter Notebooks"""
    
    @staticmethod
    def _get_base_rules() -> str:
        """Get base translation rules"""
        return """CRITICAL RULES:
- Keep brand names (AWS, Amazon, Microsoft, Google, Apple, etc.) untranslated
- Keep AWS Services (AWS Lambda, Amazon Bedrock, Amazon S3, etc.) untranslated
- Keep company names, person names, and product names untranslated  
- Keep technical terms that are commonly used in English (API, SDK, CLI, etc.)
- Keep programming language keywords, function names, and variable names untranslated
- Keep library/package names (pandas, numpy, matplotlib, sklearn, etc.) untranslated
- Keep file paths, URLs, and email addresses untranslated
- Keep time expressions, currency amounts, and numbers untranslated
- Preserve formatting markers (bullets, numbers, etc.)

JUPYTER NOTEBOOK SPECIFIC RULES:
- Translate markdown text content naturally
- In code snippets within markdown, translate ONLY comments and docstrings to Korean
- Keep all code syntax, variable names, function names, and keywords unchanged
- Translate explanatory text but preserve technical accuracy
- Maintain code block formatting and syntax highlighting markers

TRANSLATION REQUIREMENTS:
- ALWAYS translate Japanese katakana words (e.g., カタカナ) to the target language
- ALWAYS translate short text fragments, even if they are only 2-5 characters
- Do NOT skip translation of any text based on length or format
"""
    
    @staticmethod
    def _get_polishing_instruction(enable_polishing: bool) -> str:
        """Get polishing instruction based on setting"""
        if not enable_polishing:
            return ""
        
        return """
- Focus on natural, fluent translation rather than literal word-for-word translation
- Adapt expressions and idioms to sound natural in the target language
- Maintain the original meaning while making it sound like native content
- Use appropriate tone and style for the target language and context
- For technical documentation, use clear and precise language"""
    
    @staticmethod
    def _get_korean_terminology_rules() -> str:
        """Get Korean-specific terminology rules"""
        terminology_list = []
        for en, ko in Config.KOREAN_TERMINOLOGY.items():
            terminology_list.append(f'- "{en}" → "{ko}" (consistently use this term)')
        
        return f"""
TERMINOLOGY CONSISTENCY (Korean):
{chr(10).join(terminology_list)}
- Use the SAME translation for the SAME English term throughout the entire notebook

NATURAL KOREAN EXPRESSIONS:
- Use "~하겠습니다" instead of "~할 것입니다" for future intentions
- Use "~해보겠습니다" instead of "~해볼 것입니다" for trying actions
- Use "~살펴보겠습니다" instead of "~살펴볼 것입니다" for examining
- Use "~만들어보겠습니다" instead of "~만들어볼 것입니다" for creating
- Use "~시작하겠습니다" instead of "~시작할 것입니다" for beginning
- Use "~생성하겠습니다" instead of "~생성할 것입니다" for generating
- Examples: "Let's create" → "만들어보겠습니다", "We'll generate" → "생성하겠습니다"

PUNCTUATION RULES (STRICTLY ENFORCE):
- EVERY Korean sentence MUST end with proper punctuation (period ., question mark ?, exclamation mark !)
- ALL sentences ending with Korean verbs MUST have a period:
  * "있습니다" → "있습니다."
  * "합니다" → "합니다."
  * "됩니다" → "됩니다."
  * "습니다" → "습니다."
  * "겠습니다" → "겠습니다."
  * "했습니다" → "했습니다."
  * "입니다" → "입니다."
- NEVER leave Korean sentences without ending punctuation
- Check EVERY sentence ending and add appropriate punctuation
- This is MANDATORY for proper Korean grammar

AVOID LITERAL TRANSLATIONS:
- "In this tutorial, we've successfully:" → "이 튜토리얼에서는 다음을 성공적으로 수행했습니다:" (NOT "우리는 성공적으로:")
- "We have learned:" → "다음을 학습했습니다:" (NOT "우리는 학습했습니다:")
- "We will explore:" → "다음을 살펴보겠습니다:" (NOT "우리는 살펴볼 것입니다:")
- "We can see that:" → "다음을 확인할 수 있습니다:" (NOT "우리는 볼 수 있습니다:")
- "We've built:" → "구축했습니다:" (NOT "우리는 구축했습니다:")
- Avoid overusing "우리는" - use natural Korean sentence structures instead

PERSON NAMES - DO NOT TRANSLATE:
- Keep ALL person names in original English
- Do NOT translate names to Korean phonetic equivalents
- Names should remain exactly as: "Daekeun Kim", "Gil-dong Hong", etc.

CODE COMMENTS AND DOCSTRINGS:
- Translate comments (# This is a comment → # 이것은 주석입니다)
- Translate docstrings (\"\"\"This function does...\"\"\" → \"\"\"이 함수는...을 수행합니다\"\"\")
- Keep code structure and indentation intact"""
    
    @classmethod
    def create_markdown_prompt(cls, target_language: str, enable_polishing: bool = True) -> str:
        """Create prompt for markdown cell translation"""
        target_lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        base_rules = cls._get_base_rules()
        polishing_instruction = cls._get_polishing_instruction(enable_polishing)
        
        terminology_rules = ""
        if target_language == 'ko':
            terminology_rules = cls._get_korean_terminology_rules()
        
        return f"""You are a professional translator specializing in technical documentation and Jupyter notebooks. Translate the following markdown content to {target_lang_name}.

{base_rules}

MARKDOWN SPECIFIC RULES:
- Preserve all markdown formatting (headers, lists, links, code blocks, etc.)
- Translate text content while keeping markdown syntax intact
- For inline code snippets, translate comments and docstrings but keep code unchanged
- For code blocks, translate only comments and docstrings within the code
- Maintain proper markdown structure and readability

FINAL OUTPUT REQUIREMENTS:
- Return ONLY the translated markdown content with NO additional explanations, comments, or metadata
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Do NOT add quotation marks around the result
- ENSURE ALL Korean sentences end with proper punctuation marks (., ?, !)
- Double-check that no Korean sentence is left without ending punctuation{polishing_instruction}{terminology_rules}

Respond with the translated markdown content only:"""
    
    @classmethod
    def create_batch_prompt(cls, target_language: str, enable_polishing: bool = True) -> str:
        """Create optimized batch translation prompt for multiple markdown cells"""
        target_lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        base_rules = cls._get_base_rules()
        polishing_instruction = cls._get_polishing_instruction(enable_polishing)
        
        terminology_rules = ""
        if target_language == 'ko':
            terminology_rules = cls._get_korean_terminology_rules()
        
        return f"""You are a professional translator specializing in technical documentation and Jupyter notebooks. Translate the following markdown cells to {target_lang_name}.

{base_rules}

MARKDOWN SPECIFIC RULES:
- Preserve all markdown formatting (headers, lists, links, code blocks, etc.)
- Translate text content while keeping markdown syntax intact
- For inline code snippets, translate comments and docstrings but keep code unchanged
- For code blocks, translate only comments and docstrings within the code
- Maintain proper markdown structure and readability

BATCH TRANSLATION FORMAT:
- Each markdown cell is separated by "---CELL_SEPARATOR---"
- Return translations in the SAME ORDER, separated by "---CELL_SEPARATOR---"
- Return ONLY the translated markdown cells with NO additional explanations, comments, or metadata
- Do NOT include phrases like "Here is the translation:" or "Translated text:"
- Do NOT add quotation marks around the results
- ENSURE ALL Korean sentences end with proper punctuation marks (., ?, !)
- Double-check that no Korean sentence is left without ending punctuation{polishing_instruction}{terminology_rules}

Input format:
Markdown Cell 1
---CELL_SEPARATOR---
Markdown Cell 2
---CELL_SEPARATOR---
Markdown Cell 3

Expected output format:
Translated Markdown Cell 1
---CELL_SEPARATOR---
Translated Markdown Cell 2
---CELL_SEPARATOR---
Translated Markdown Cell 3

Respond with the translated markdown cells only:"""
    
    @classmethod
    def create_code_comment_prompt(cls, target_language: str, enable_polishing: bool = True) -> str:
        """Create prompt specifically for translating code comments and docstrings"""
        target_lang_name = Config.LANGUAGE_MAP.get(target_language, target_language)
        polishing_instruction = cls._get_polishing_instruction(enable_polishing)
        
        terminology_rules = ""
        if target_language == 'ko':
            terminology_rules = cls._get_korean_terminology_rules()
        
        return f"""You are a professional translator specializing in code documentation. Translate ONLY the comments and docstrings in the following code to {target_lang_name}.

CRITICAL RULES FOR CODE TRANSLATION:
- ONLY translate text inside comments (# comment text) and docstrings (\"\"\"docstring text\"\"\")
- Keep ALL code syntax, keywords, variable names, function names, and library names UNCHANGED
- Preserve exact indentation, spacing, and code structure
- Do NOT translate any code elements, only the natural language text within comments and docstrings
- Keep brand names, technical terms, and proper nouns untranslated
- Maintain the original code formatting and structure exactly

COMMENT TRANSLATION RULES:
- Single line comments: # Original comment → # Translated comment
- Docstrings: \"\"\"Original docstring\"\"\" → \"\"\"Translated docstring\"\"\"
- Multi-line docstrings: preserve the triple quote structure

FINAL OUTPUT REQUIREMENTS:
- Return ONLY the code with translated comments/docstrings
- Do NOT add any explanations, metadata, or additional text
- Do NOT change any code logic, syntax, or structure
- ENSURE ALL Korean sentences in comments/docstrings end with proper punctuation marks (., ?, !)
- Double-check that no Korean sentence is left without ending punctuation{polishing_instruction}{terminology_rules}

Respond with the code containing translated comments and docstrings only:"""
