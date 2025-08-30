"""
Core translation engine using AWS Bedrock for Jupyter Notebooks
"""
import logging
from typing import List, Dict, Any
from .config import Config
from .bedrock_client import BedrockClient
from .prompts import PromptGenerator
from .text_utils import TextProcessor

logger = logging.getLogger(__name__)


class NotebookTranslationEngine:
    """Core translation engine using AWS Bedrock for Jupyter Notebooks"""
    
    def __init__(self, model_id: str = Config.DEFAULT_MODEL_ID, enable_polishing: bool = Config.ENABLE_POLISHING):
        self.model_id = model_id
        self.enable_polishing = enable_polishing
        self.bedrock = BedrockClient()
        self.text_processor = TextProcessor()
        self.prompt_generator = PromptGenerator()
        
        logger.info(f"🎨 Translation mode: {'Natural/Polished' if enable_polishing else 'Literal'}")
        logger.info(f"🤖 Using model: {model_id}")
    
    def translate_markdown_cell(self, markdown_text: str, target_language: str) -> str:
        """Translate a single markdown cell"""
        if self.text_processor.should_skip_translation(markdown_text):
            return markdown_text
        
        try:
            prompt = self.prompt_generator.create_markdown_prompt(target_language, self.enable_polishing)
            
            response = self.bedrock.converse(
                modelId=self.model_id,
                system=[{"text": prompt}],
                messages=[{
                    "role": "user",
                    "content": [{"text": markdown_text}]
                }],
                inferenceConfig={
                    "maxTokens": Config.MAX_TOKENS,
                    "temperature": Config.TEMPERATURE
                }
            )
            
            translated_text = response['output']['message']['content'][0]['text'].strip()
            translated_text = self.text_processor.clean_translation_response(translated_text)
            
            # Remove quotes if wrapped
            if (translated_text.startswith('"') and translated_text.endswith('"')) or \
               (translated_text.startswith("'") and translated_text.endswith("'")):
                translated_text = translated_text[1:-1].strip()
            
            logger.debug(f"Translated markdown cell: '{markdown_text[:50]}...' -> '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return markdown_text
    
    def translate_markdown_cells_batch(self, markdown_cells: List[str], target_language: str) -> List[str]:
        """Translate multiple markdown cells in a single API call"""
        if not markdown_cells:
            return []
        
        logger.info(f"🔄 Starting batch translation of {len(markdown_cells)} markdown cells to {target_language}")
        
        # Filter translatable cells
        translatable_cells = []
        skip_indices = []
        
        for i, cell_text in enumerate(markdown_cells):
            if self.text_processor.should_skip_translation(cell_text):
                skip_indices.append(i)
                logger.debug(f"⏭️ Skipping cell {i}: {cell_text[:30]}...")
            else:
                translatable_cells.append(cell_text)
                logger.debug(f"✅ Will translate cell {i}: {cell_text[:30]}...")
        
        if not translatable_cells:
            return markdown_cells
        
        try:
            # Create batch input
            batch_input = "---CELL_SEPARATOR---".join(translatable_cells)
            prompt = self.prompt_generator.create_batch_prompt(target_language, self.enable_polishing)
            
            logger.info(f"🔄 Batch translating {len(translatable_cells)} markdown cells...")
            
            response = self.bedrock.converse(
                modelId=self.model_id,
                system=[{"text": prompt}],
                messages=[{
                    "role": "user",
                    "content": [{"text": batch_input}]
                }],
                inferenceConfig={
                    "maxTokens": Config.MAX_TOKENS,
                    "temperature": Config.TEMPERATURE
                }
            )
            
            translated_batch = response['output']['message']['content'][0]['text'].strip()
            cleaned_parts = self.text_processor.parse_batch_response(translated_batch, len(translatable_cells))
            
            # Reconstruct results with available translations
            results = markdown_cells.copy()
            translatable_idx = 0
            
            for i, cell_text in enumerate(markdown_cells):
                if i not in skip_indices:
                    if translatable_idx < len(cleaned_parts):
                        results[i] = cleaned_parts[translatable_idx]
                        translatable_idx += 1
            
            logger.info(f"✅ Batch translation completed for {len(translatable_cells)} markdown cells")
            return results
            
        except Exception as e:
            logger.error(f"❌ Batch translation error: {str(e)}")
            return self._fallback_individual_translation(markdown_cells, target_language)
    
    def translate_code_comments(self, code_text: str, target_language: str) -> str:
        """Translate comments and docstrings in code while preserving code structure"""
        try:
            # Check if there are any translatable comments
            if not self.text_processor.has_translatable_comments(code_text):
                logger.debug("No translatable comments found in code")
                return code_text
            
            # Use the specific code comment prompt
            prompt = self.prompt_generator.create_code_comment_prompt(target_language, self.enable_polishing)
            
            response = self.bedrock.converse(
                modelId=self.model_id,
                system=[{"text": prompt}],
                messages=[{
                    "role": "user",
                    "content": [{"text": code_text}]
                }],
                inferenceConfig={
                    "maxTokens": Config.MAX_TOKENS,
                    "temperature": Config.TEMPERATURE
                }
            )
            
            translated_code = response['output']['message']['content'][0]['text'].strip()
            translated_code = self.text_processor.clean_translation_response(translated_code)
            
            # Remove quotes if wrapped
            if (translated_code.startswith('```') and translated_code.endswith('```')):
                # Remove code block markers if present
                lines = translated_code.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1].strip() == '```':
                    lines = lines[:-1]
                translated_code = '\n'.join(lines)
            
            logger.debug(f"Translated code comments: {len(code_text)} -> {len(translated_code)} chars")
            return translated_code
            
        except Exception as e:
            logger.error(f"Code comment translation error: {str(e)}")
            return code_text
    
    def translate_code_cells_batch(self, code_cells: List[str], target_language: str) -> List[str]:
        """Translate comments and docstrings in multiple code cells"""
        if not code_cells:
            return []
        
        logger.info(f"🔄 Starting batch translation of {len(code_cells)} code cells to {target_language}")
        
        results = []
        for i, code_text in enumerate(code_cells):
            try:
                translated_code = self.translate_code_comments(code_text, target_language)
                results.append(translated_code)
                logger.debug(f"✅ Translated code cell {i+1}/{len(code_cells)}")
            except Exception as e:
                logger.error(f"❌ Failed to translate code cell {i+1}: {str(e)}")
                results.append(code_text)
        
        logger.info(f"✅ Code cell translation completed: {len(results)} results")
        return results
    
    def _fallback_individual_translation(self, markdown_cells: List[str], target_language: str) -> List[str]:
        """Fallback to individual translation when batch fails"""
        logger.info(f"🔄 Falling back to individual translation for {len(markdown_cells)} cells...")
        results = []
        
        for i, cell_text in enumerate(markdown_cells):
            try:
                translated = self.translate_markdown_cell(cell_text, target_language)
                results.append(translated)
                logger.debug(f"✅ Individual translation {i+1}/{len(markdown_cells)}")
            except Exception as e:
                logger.error(f"❌ Failed to translate cell {i+1}: {str(e)}")
                results.append(cell_text)
        
        logger.info(f"✅ Individual translation fallback completed: {len(results)} results")
        return results
    
    def get_translation_stats(self, original_cells: List[str], translated_cells: List[str]) -> Dict[str, Any]:
        """Generate translation statistics"""
        stats = {
            'total_cells': len(original_cells),
            'translated_cells': 0,
            'skipped_cells': 0,
            'original_chars': 0,
            'translated_chars': 0,
            'avg_original_length': 0,
            'avg_translated_length': 0
        }
        
        for orig, trans in zip(original_cells, translated_cells):
            stats['original_chars'] += len(orig)
            stats['translated_chars'] += len(trans)
            
            if orig != trans:
                stats['translated_cells'] += 1
            else:
                stats['skipped_cells'] += 1
        
        if stats['total_cells'] > 0:
            stats['avg_original_length'] = stats['original_chars'] / stats['total_cells']
            stats['avg_translated_length'] = stats['translated_chars'] / stats['total_cells']
        
        return stats
