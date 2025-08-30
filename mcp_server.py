#!/usr/bin/env python3
"""FastMCP-based MCP server for Jupyter Notebook translation."""

import os
import asyncio
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import BaseModel

from ipynb_translator.main import translate_single_notebook
from ipynb_translator.url_downloader import NotebookURLDownloader
from ipynb_translator.notebook_handler import NotebookHandler
from ipynb_translator.config import Config


class TranslateNotebookArgs(BaseModel):
    notebook_path: str
    target_language: str = "ko"
    output_path: Optional[str] = None
    model_id: Optional[str] = None
    batch_size: int = 20
    translate_code_cells: bool = False
    enable_polishing: bool = True


class TranslateFromUrlArgs(BaseModel):
    url: str
    target_language: str = "ko"
    output_path: Optional[str] = None
    keep_original: bool = False
    translate_code_cells: bool = False
    enable_polishing: bool = True


class NotebookInfoArgs(BaseModel):
    notebook_path: str


# Initialize FastMCP
mcp = FastMCP("Jupyter Notebook Translator")


@mcp.tool()
def translate_notebook(args: TranslateNotebookArgs) -> str:
    """Translate Jupyter notebook to specified language."""
    try:
        notebook_path = Path(args.notebook_path)
        if not notebook_path.exists():
            return f"Error: Notebook file not found: {args.notebook_path}"
        
        success, actual_output_path = translate_single_notebook(
            notebook_path=notebook_path,
            target_language=args.target_language,
            model_id=args.model_id or Config.DEFAULT_MODEL_ID,
            batch_size=args.batch_size,
            output_path=args.output_path
        )
        
        if success:
            return f"Successfully translated notebook to {actual_output_path}"
        else:
            return "Translation failed"
        
    except Exception as e:
        return f"Error translating notebook: {str(e)}"


@mcp.tool()
def translate_from_url(args: TranslateFromUrlArgs) -> str:
    """Download notebook from URL and translate."""
    try:
        # Download notebook
        downloader = NotebookURLDownloader()
        temp_path = downloader.download_notebook(args.url)
        
        # Translate
        success, actual_output_path = translate_single_notebook(
            notebook_path=Path(temp_path),
            target_language=args.target_language,
            model_id=Config.DEFAULT_MODEL_ID,
            batch_size=args.batch_size,
            output_path=args.output_path
        )
        
        # Generate output path
        if args.output_path:
            output_path = args.output_path
        else:
            url_filename = Path(args.url).stem or "notebook"
            output_path = f"{url_filename}_translated_{args.target_language}.ipynb"
        
        # Clean up temp file if not keeping original
        if not args.keep_original:
            os.unlink(temp_path)
        
        if success:
            return f"Successfully downloaded and translated notebook to {output_path}"
        else:
            return "Translation failed"
        
    except Exception as e:
        return f"Error downloading/translating notebook: {str(e)}"


@mcp.tool()
def get_notebook_info(args: NotebookInfoArgs) -> str:
    """Get notebook file information."""
    try:
        handler = NotebookHandler()
        notebook = handler.load_notebook(args.notebook_path)
        info = handler.get_notebook_info(notebook)
        return f"Notebook info: {info}"
    except Exception as e:
        return f"Error getting notebook info: {str(e)}"


@mcp.tool()
def list_supported_languages() -> str:
    """Return list of supported languages."""
    languages = []
    for code, name in Config.LANGUAGE_MAP.items():
        languages.append(f"{code}: {name}")
    return "\n".join(languages)


@mcp.tool()
def list_supported_models() -> str:
    """Return list of supported models."""
    return "\n".join(Config.SUPPORTED_MODELS)


if __name__ == "__main__":
    mcp.run()
