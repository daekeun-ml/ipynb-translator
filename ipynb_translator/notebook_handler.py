"""
Jupyter Notebook handler for reading, processing, and writing notebooks
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import nbformat
from .text_utils import TextProcessor

logger = logging.getLogger(__name__)


class NotebookHandler:
    """Handles Jupyter notebook file operations and cell processing"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def load_notebook(self, notebook_path: str) -> nbformat.NotebookNode:
        """Load a Jupyter notebook from file"""
        try:
            notebook_path = Path(notebook_path)
            if not notebook_path.exists():
                raise FileNotFoundError(f"Notebook file not found: {notebook_path}")
            
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)
            
            logger.info(f"✅ Loaded notebook: {notebook_path}")
            logger.info(f"📊 Notebook info: {len(notebook.cells)} cells")
            
            return notebook
            
        except Exception as e:
            logger.error(f"❌ Failed to load notebook {notebook_path}: {str(e)}")
            raise
    
    def save_notebook(self, notebook: nbformat.NotebookNode, output_path: str) -> None:
        """Save a Jupyter notebook to file"""
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                nbformat.write(notebook, f)
            
            logger.info(f"✅ Saved translated notebook: {output_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save notebook {output_path}: {str(e)}")
            raise
    
    def extract_markdown_cells(self, notebook: nbformat.NotebookNode) -> List[Dict[str, Any]]:
        """Extract markdown cells that need translation"""
        markdown_cells = []
        
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'markdown':
                source = cell.source
                if source and self.text_processor.has_translatable_content(source):
                    markdown_cells.append({
                        'index': i,
                        'source': source,
                        'cell': cell
                    })
                    logger.debug(f"📝 Found translatable markdown cell {i}: {source[:50]}...")
                else:
                    logger.debug(f"⏭️ Skipping markdown cell {i}: no translatable content")
        
        logger.info(f"📝 Found {len(markdown_cells)} translatable markdown cells")
        return markdown_cells
    
    def extract_code_cells(self, notebook: nbformat.NotebookNode) -> List[Dict[str, Any]]:
        """Extract code cells that need comment/docstring translation"""
        code_cells = []
        
        for i, cell in enumerate(notebook.cells):
            if cell.cell_type == 'code':
                source = cell.source
                if source and self.text_processor.has_translatable_comments(source):
                    code_cells.append({
                        'index': i,
                        'source': source,
                        'cell': cell
                    })
                    logger.debug(f"💻 Found code cell with translatable comments {i}")
                else:
                    logger.debug(f"⏭️ Skipping code cell {i}: no translatable comments")
        
        logger.info(f"💻 Found {len(code_cells)} code cells with translatable comments")
        return code_cells
    
    def get_notebook_info(self, notebook: nbformat.NotebookNode) -> Dict[str, Any]:
        """Get information about the notebook"""
        cell_counts = {}
        for cell in notebook.cells:
            cell_type = cell.cell_type
            cell_counts[cell_type] = cell_counts.get(cell_type, 0) + 1
        
        markdown_cells = self.extract_markdown_cells(notebook)
        code_cells = self.extract_code_cells(notebook)
        
        info = {
            'total_cells': len(notebook.cells),
            'cell_counts': cell_counts,
            'translatable_markdown_cells': len(markdown_cells),
            'translatable_code_cells': len(code_cells),
            'notebook_format': notebook.nbformat,
            'notebook_format_minor': notebook.nbformat_minor
        }
        
        # Get kernel info if available
        if hasattr(notebook.metadata, 'kernelspec'):
            info['kernel'] = {
                'name': notebook.metadata.kernelspec.get('name', 'unknown'),
                'display_name': notebook.metadata.kernelspec.get('display_name', 'unknown'),
                'language': notebook.metadata.kernelspec.get('language', 'unknown')
            }
        
        return info
    
    def update_markdown_cells(self, notebook: nbformat.NotebookNode, 
                            markdown_cells: List[Dict[str, Any]], 
                            translations: List[str]) -> nbformat.NotebookNode:
        """Update markdown cells with translations"""
        if len(markdown_cells) != len(translations):
            raise ValueError(f"Mismatch between markdown cells ({len(markdown_cells)}) and translations ({len(translations)})")
        
        # Create a copy of the notebook
        translated_notebook = nbformat.v4.new_notebook()
        translated_notebook.metadata = notebook.metadata.copy()
        translated_notebook.cells = []
        
        # Create a mapping of cell indices to translations
        translation_map = {}
        for cell_info, translation in zip(markdown_cells, translations):
            translation_map[cell_info['index']] = translation
        
        # Process all cells
        for i, cell in enumerate(notebook.cells):
            if i in translation_map:
                # This is a markdown cell that was translated
                new_cell = nbformat.v4.new_markdown_cell(source=translation_map[i])
                # Copy metadata if it exists
                if hasattr(cell, 'metadata'):
                    new_cell.metadata = cell.metadata.copy()
                translated_notebook.cells.append(new_cell)
                logger.debug(f"✅ Updated markdown cell {i} with translation")
            else:
                # This is a cell that wasn't translated (code, raw, or non-translatable markdown)
                if cell.cell_type == 'code':
                    # Ensure code cells have required fields
                    new_cell = nbformat.v4.new_code_cell(source=cell.source)
                    if hasattr(cell, 'metadata'):
                        new_cell.metadata = cell.metadata.copy()
                    if hasattr(cell, 'execution_count'):
                        new_cell.execution_count = cell.execution_count
                    # Ensure outputs field exists
                    if not hasattr(new_cell, 'outputs'):
                        new_cell.outputs = []
                    translated_notebook.cells.append(new_cell)
                else:
                    translated_notebook.cells.append(cell)
                logger.debug(f"📋 Copied cell {i} without changes ({cell.cell_type})")
        
        logger.info(f"✅ Updated {len(translations)} markdown cells with translations")
        return translated_notebook
    
    def update_code_cells(self, notebook: nbformat.NotebookNode, 
                         code_cells: List[Dict[str, Any]], 
                         translations: List[str]) -> nbformat.NotebookNode:
        """Update code cells with translated comments/docstrings"""
        if len(code_cells) != len(translations):
            raise ValueError(f"Mismatch between code cells ({len(code_cells)}) and translations ({len(translations)})")
        
        # Create a mapping of cell indices to translations
        translation_map = {}
        for cell_info, translation in zip(code_cells, translations):
            translation_map[cell_info['index']] = translation
        
        # Process all cells
        for i, cell in enumerate(notebook.cells):
            if i in translation_map and cell.cell_type == 'code':
                # This is a code cell that was translated
                cell.source = translation_map[i]
                # Ensure required fields exist
                if not hasattr(cell, 'outputs'):
                    cell.outputs = []
                if not hasattr(cell, 'execution_count'):
                    cell.execution_count = None
                logger.debug(f"✅ Updated code cell {i} with translated comments")
        
        logger.info(f"✅ Updated {len(translations)} code cells with translated comments")
        return notebook
    
    def preview_translations(self, markdown_cells: List[Dict[str, Any]], 
                           translations: List[str], max_length: int = 100) -> str:
        """Generate a preview of translations for user review"""
        if len(markdown_cells) != len(translations):
            return "❌ Translation count mismatch - cannot generate preview"
        
        preview_lines = ["📋 Translation Preview:", "=" * 50]
        
        for i, (cell_info, translation) in enumerate(zip(markdown_cells, translations)):
            original = cell_info['source']
            cell_index = cell_info['index']
            
            # Truncate long texts for preview
            original_preview = original[:max_length] + "..." if len(original) > max_length else original
            translation_preview = translation[:max_length] + "..." if len(translation) > max_length else translation
            
            preview_lines.extend([
                f"\n📝 Cell {cell_index + 1} (Index: {cell_index}):",
                f"🔤 Original: {original_preview}",
                f"🌐 Translation: {translation_preview}",
                "-" * 30
            ])
        
        return "\n".join(preview_lines)
    
    def generate_output_filename(self, input_path: str, target_language: str) -> str:
        """Generate output filename for translated notebook"""
        input_path = Path(input_path)
        stem = input_path.stem
        extension = input_path.suffix
        
        output_filename = f"{stem}_translated_{target_language}{extension}"
        output_path = input_path.parent / output_filename
        
        return str(output_path)
    
    def validate_notebook(self, notebook: nbformat.NotebookNode) -> Tuple[bool, str]:
        """Validate notebook structure and content"""
        try:
            # Check basic structure
            if not hasattr(notebook, 'cells'):
                return False, "Notebook missing 'cells' attribute"
            
            if not isinstance(notebook.cells, list):
                return False, "Notebook 'cells' is not a list"
            
            # Check each cell
            for i, cell in enumerate(notebook.cells):
                if not hasattr(cell, 'cell_type'):
                    return False, f"Cell {i} missing 'cell_type' attribute"
                
                if cell.cell_type not in ['markdown', 'code', 'raw']:
                    return False, f"Cell {i} has invalid cell_type: {cell.cell_type}"
                
                if not hasattr(cell, 'source'):
                    return False, f"Cell {i} missing 'source' attribute"
            
            return True, "Notebook validation passed"
            
        except Exception as e:
            return False, f"Notebook validation error: {str(e)}"
