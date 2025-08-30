#!/usr/bin/env python3

import asyncio
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from ipynb_translator.translation_engine import NotebookTranslationEngine
from ipynb_translator.config import Config

# MCP 서버 초기화
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
        # 설정 로드
        config = Config()
        if model_id:
            config.bedrock_model_id = model_id
        if batch_size != 20:
            config.batch_size = batch_size
        config.translate_code_cells = translate_code_cells
        config.enable_polishing = enable_polishing
        
        # 번역기 초기화
        translator = NotebookTranslationEngine(config)
        
        # 입력 파일 경로 처리
        input_path = Path(notebook_path)
        if not input_path.exists():
            return {"error": f"File not found: {notebook_path}"}
        
        # 출력 파일 경로 설정
        if not output_path:
            output_path = str(input_path.parent / f"{input_path.stem}_{target_language}{input_path.suffix}")
        
        # 번역 실행
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
        
        # 노트북 다운로드
        downloaded_path = download_notebook(url)
        
        # 번역 실행
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
        
        # 원본 파일 정리
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
        
        # 노트북 로드
        with open(input_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
        
        # 셀 정보 수집
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

if __name__ == "__main__":
    mcp.run()
