#!/usr/bin/env python3

import asyncio
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ipynb_translator.translation_engine import NotebookTranslationEngine
from ipynb_translator.config import Config

# Initialize MCP server
mcp = FastMCP("Jupyter Notebook Translator")

@mcp.tool()
def translate_notebook(
    notebook_path: str = Field(description="Path to the Jupyter notebook file"),
    target_language: str = Field(default="ko", description="Target language code (e.g., 'ko', 'ja', 'en')"),
    output_path: str = Field(default="", description="Output file path (optional)"),
    model_id: str = Field(default="", description="Bedrock model ID (optional)"),
    batch_size: int = Field(default=20, description="Batch size for translation"),
    translate_code_cells: bool = Field(default=False, description="Whether to translate code cell comments"),
    enable_polishing: bool = Field(default=True, description="Enable natural translation polishing")
) -> dict[str, Any]:
    """Translate a Jupyter notebook to the specified language."""
    
    try:
        # Load configuration
        config = Config()
        if model_id:
            config.bedrock_model_id = model_id
        if batch_size != 20:
            config.batch_size = batch_size
        config.translate_code_cells = translate_code_cells
        config.enable_polishing = enable_polishing
        
        # Initialize translator
        translator = NotebookTranslationEngine(config)
        
        # Process input file path
        input_path = Path(notebook_path)
        if not input_path.exists():
            return {"error": f"File not found: {notebook_path}"}
        
        # Set output file path
        if not output_path:
            output_path = str(input_path.parent / f"{input_path.stem}_{target_language}{input_path.suffix}")
        
        # Execute translation
        result = translator.translate_notebook(
            input_path=str(input_path),
            output_path=output_path,
            target_language=target_language
        )
        
        return {
            "success": True,
            "input_file": str(input_path),
            "output_file": output_path,
            "target_language": target_language,
            "translated_cells": result.get("translated_cells", 0),
            "total_cells": result.get("total_cells", 0)
        }
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def translate_from_url(
    url: str = Field(description="URL to the Jupyter notebook"),
    target_language: str = Field(default="ko", description="Target language code"),
    output_path: str = Field(default="", description="Output file path (optional)"),
    keep_original: bool = Field(default=False, description="Keep the original downloaded file"),
    translate_code_cells: bool = Field(default=False, description="Whether to translate code cell comments"),
    enable_polishing: bool = Field(default=True, description="Enable natural translation polishing")
) -> dict[str, Any]:
    """Download and translate a Jupyter notebook from URL."""
    
    try:
        from src.downloader import download_notebook
        
        # Download notebook
        downloaded_path = download_notebook(url)
        
        # Execute translation
        config = Config()
        config.translate_code_cells = translate_code_cells
        config.enable_polishing = enable_polishing
        translator = NotebookTranslationEngine(config)
        
        if not output_path:
            output_path = f"translated_{Path(downloaded_path).name}"
        
        result = translator.translate_notebook(
            input_path=downloaded_path,
            output_path=output_path,
            target_language=target_language
        )
        
        # Clean up original file
        if not keep_original:
            Path(downloaded_path).unlink()
        
        return {
            "success": True,
            "source_url": url,
            "output_file": output_path,
            "target_language": target_language,
            "translated_cells": result.get("translated_cells", 0),
            "total_cells": result.get("total_cells", 0),
            "original_kept": keep_original
        }
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_notebook_info(
    notebook_path: str = Field(description="Path to the Jupyter notebook file")
) -> dict[str, Any]:
    """Get information about a Jupyter notebook."""
    
    try:
        import nbformat
        
        input_path = Path(notebook_path)
        if not input_path.exists():
            return {"error": f"File not found: {notebook_path}"}
        
        # Load notebook
        with open(input_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        
        # Collect cell information
        total_cells = len(nb.cells)
        markdown_cells = sum(1 for cell in nb.cells if cell.cell_type == 'markdown')
        code_cells = sum(1 for cell in nb.cells if cell.cell_type == 'code')
        
        return {
            "file_path": str(input_path),
            "total_cells": total_cells,
            "markdown_cells": markdown_cells,
            "code_cells": code_cells,
            "notebook_format": nb.nbformat,
            "kernel_info": nb.metadata.get('kernelspec', {}).get('display_name', 'Unknown')
        }
        
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def list_supported_languages() -> dict[str, Any]:
    """List all supported languages for translation."""
    
    languages = {
        "ko": "Korean",
        "ja": "Japanese", 
        "zh-CN": "Chinese (Simplified)",
        "zh-TW": "Chinese (Traditional)",
        "en": "English",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
        "hi": "Hindi",
        "th": "Thai",
        "vi": "Vietnamese"
    }
    
    return {"supported_languages": languages}

@mcp.tool()
def list_supported_models() -> dict[str, Any]:
    """List all supported Bedrock models."""
    
    from ipynb_translator.config import Config
    
    # Group models by provider
    models = {}
    for model in Config.SUPPORTED_MODELS:
        if model.startswith("amazon.nova"):
            models.setdefault("amazon_nova", []).append(model)
        elif "anthropic" in model:
            models.setdefault("anthropic_claude", []).append(model)
        elif "meta.llama" in model or "us.meta.llama" in model:
            models.setdefault("meta_llama", []).append(model)
        elif "deepseek" in model:
            models.setdefault("deepseek", []).append(model)
        elif "mistral" in model:
            models.setdefault("mistral", []).append(model)
        elif "cohere" in model:
            models.setdefault("cohere", []).append(model)
        elif "ai21" in model:
            models.setdefault("ai21", []).append(model)
    
    return {
        "supported_models": models,
        "total_models": len(Config.SUPPORTED_MODELS),
        "default_model": Config.DEFAULT_MODEL_ID
    }

if __name__ == "__main__":
    mcp.run()
