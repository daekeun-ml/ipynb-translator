"""
Text processing utilities for Jupyter Notebook translation
"""
import re
import logging
from typing import List, Dict, Any
from .config import Config

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles text processing and validation logic for Jupyter notebooks"""
    
    @staticmethod
    def should_skip_translation(text: str) -> bool:
        """Determine if text should be skipped from translation"""
        if not text or not text.strip():
            return True
        
        text = text.strip()
        
        # Check against skip patterns
        for pattern in Config.SKIP_PATTERNS:
            if re.match(pattern, text):
                return True
        
        # Skip very short text that's likely not translatable
        if len(text) <= 2 and not any(c.isalpha() for c in text):
            return True
        
        # Skip if it's only code (no natural language)
        if TextProcessor.is_only_code(text):
            return True
        
        return False
    
    @staticmethod
    def is_only_code(text: str) -> bool:
        """Check if text contains only code without natural language"""
        # Remove code blocks and inline code
        text_without_code = re.sub(r'```[\s\S]*?```', '', text)
        text_without_code = re.sub(r'`[^`]+`', '', text_without_code)
        
        # Remove common code patterns
        text_without_code = re.sub(r'[{}()\[\];,.]', ' ', text_without_code)
        text_without_code = re.sub(r'\b\d+\b', ' ', text_without_code)
        text_without_code = re.sub(r'[=+\-*/<>!&|]', ' ', text_without_code)
        
        # Check if there are meaningful words left
        words = text_without_code.split()
        meaningful_words = [w for w in words if len(w) > 2 and not w.isupper()]
        
        return len(meaningful_words) < 2
    
    @staticmethod
    def has_translatable_content(markdown_text: str) -> bool:
        """Check if markdown text has translatable content"""
        if not markdown_text or not markdown_text.strip():
            return False
        
        # Remove code blocks
        text_without_code_blocks = re.sub(r'```[\s\S]*?```', '', markdown_text)
        
        # Remove inline code
        text_without_inline_code = re.sub(r'`[^`]+`', '', text_without_code_blocks)
        
        # Remove markdown formatting
        text_clean = re.sub(r'[#*_\[\]()!-]', ' ', text_without_inline_code)
        
        # Check if there's meaningful text left
        words = text_clean.split()
        meaningful_words = [w for w in words if len(w) > 2 and re.search(r'[a-zA-Z가-힣]', w)]
        
        return len(meaningful_words) >= 2
    
    @staticmethod
    def has_translatable_comments(code_text: str) -> bool:
        """Check if code has translatable comments or docstrings"""
        if not code_text or not code_text.strip():
            return False
        
        comments = TextProcessor.extract_code_comments(code_text)
        
        for comment in comments:
            content = comment['content'].strip()
            if content and not TextProcessor.should_skip_translation(content):
                return True
        
        return False
    
    @staticmethod
    def clean_translation_response(response: str) -> str:
        """Clean up translation response by removing unwanted prefixes/suffixes"""
        unwanted_prefixes = [
            "Here are the translations:",
            "Here is the translation:",
            "Translated texts:",
            "Translated text:",
            "Translations:",
            "Translation:",
            "번역:",
            "번역 결과:",
            "다음은 번역입니다:",
            "翻译:",
            "翻訳:",
            "Traductions:",
            "Übersetzungen:",
            "Traducciones:",
            "The translations are:",
            "Translation results:"
        ]
        
        unwanted_suffixes = [
            "End of translations.",
            "Translation complete.",
            "번역 완료.",
            "翻译完成。",
            "翻訳完了。"
        ]
        
        cleaned = response.strip()
        
        # Remove prefixes
        for prefix in unwanted_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                logger.debug(f"🧹 Removed prefix: '{prefix}'")
                break
        
        # Remove suffixes
        for suffix in unwanted_suffixes:
            if cleaned.lower().endswith(suffix.lower()):
                cleaned = cleaned[:-len(suffix)].strip()
                logger.debug(f"🧹 Removed suffix: '{suffix}'")
                break
        
        return cleaned
    
    @staticmethod
    def parse_batch_response(response: str, expected_count: int) -> List[str]:
        """Parse batch translation response for markdown cells"""
        cleaned_response = TextProcessor.clean_translation_response(response)
        parts = cleaned_response.split("---CELL_SEPARATOR---")
        
        # Clean each part
        cleaned_parts = [part.strip() for part in parts]
        
        return cleaned_parts
    
    @staticmethod
    def extract_code_comments(code_text: str) -> List[Dict[str, Any]]:
        """Extract only # comments from code for translation"""
        comments = []
        lines = code_text.split('\n')
        
        for i, line in enumerate(lines):
            # Handle single line comments only
            if '#' in line:
                comment_idx = line.find('#')
                # Make sure it's not inside a string
                before_comment = line[:comment_idx]
                if before_comment.count('"') % 2 == 0 and before_comment.count("'") % 2 == 0:
                    comment_content = line[comment_idx+1:].strip()
                    if comment_content and not comment_content.startswith('#'):  # Skip shebang
                        comments.append({
                            'type': 'comment',
                            'line': i,
                            'content': comment_content,
                            'original_line': line
                        })
        
        return comments
    
    @staticmethod
    def replace_code_comments(code_text: str, translated_comments: List[str]) -> str:
        """Replace # comments in code with translated versions"""
        comments = TextProcessor.extract_code_comments(code_text)
        
        if len(comments) != len(translated_comments):
            logger.warning(f"Comment count mismatch: {len(comments)} vs {len(translated_comments)}")
            return code_text
        
        lines = code_text.split('\n')
        result_lines = lines.copy()
        
        # Sort comments by line number in reverse order to avoid index shifting
        comment_translation_pairs = list(zip(comments, translated_comments))
        comment_translation_pairs.sort(key=lambda x: x[0]['line'], reverse=True)
        
        # Replace comments with translations
        for comment, translation in comment_translation_pairs:
            line_idx = comment['line']
            original_line = comment['original_line']
            comment_idx = original_line.find('#')
            new_line = original_line[:comment_idx+1] + ' ' + translation
            result_lines[line_idx] = new_line
        
        return '\n'.join(result_lines)
