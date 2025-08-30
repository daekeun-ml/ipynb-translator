"""
Main CLI interface for Jupyter Notebook Translator
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List
import click
from .config import Config
from .notebook_handler import NotebookHandler
from .translation_engine import NotebookTranslationEngine
from .url_downloader import NotebookURLDownloader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_notebooks(folder_path: Path, recursive: bool = True) -> List[Path]:
    """Find all .ipynb files in a folder"""
    if recursive:
        return list(folder_path.rglob("*.ipynb"))
    else:
        return list(folder_path.glob("*.ipynb"))


def translate_single_notebook(notebook_path: Path, target_language: str, model_id: str, 
                            batch_size: int, output_path: str = None) -> tuple[bool, str]:
    """Translate a single notebook and return success status"""
    try:
        notebook_handler = NotebookHandler()
        translation_engine = NotebookTranslationEngine(model_id, Config.ENABLE_POLISHING)
        
        # Load and validate notebook
        notebook = notebook_handler.load_notebook(str(notebook_path))
        is_valid, validation_msg = notebook_handler.validate_notebook(notebook)
        if not is_valid:
            click.echo(f"   ⚠️ Skipping {notebook_path.name}: {validation_msg}")
            return False, ""
        
        # Check if there's content to translate
        info = notebook_handler.get_notebook_info(notebook)
        if info['translatable_markdown_cells'] == 0 and (not Config.TRANSLATE_CODE_CELLS or info['translatable_code_cells'] == 0):
            click.echo(f"   ⚠️ Skipping {notebook_path.name}: No translatable content")
            return False, ""
        
        # Extract cells
        markdown_cells = notebook_handler.extract_markdown_cells(notebook)
        markdown_texts = [cell['source'] for cell in markdown_cells]
        
        code_cells = []
        code_texts = []
        if Config.TRANSLATE_CODE_CELLS:
            code_cells = notebook_handler.extract_code_cells(notebook)
            code_texts = [cell['source'] for cell in code_cells]
        
        # Translate markdown cells
        if markdown_texts:
            if len(markdown_texts) <= batch_size:
                markdown_translations = translation_engine.translate_markdown_cells_batch(markdown_texts, target_language)
            else:
                markdown_translations = []
                for i in range(0, len(markdown_texts), batch_size):
                    batch = markdown_texts[i:i+batch_size]
                    batch_translations = translation_engine.translate_markdown_cells_batch(batch, target_language)
                    markdown_translations.extend(batch_translations)
        else:
            markdown_translations = []
        
        # Translate code cells
        if code_texts:
            code_translations = translation_engine.translate_code_cells_batch(code_texts, target_language)
        else:
            code_translations = []
        
        # Generate output path
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = Path(notebook_handler.generate_output_filename(
                str(notebook_path), target_language
            ))
        
        # Update notebook with translations
        translated_notebook = notebook
        if markdown_texts:
            translated_notebook = notebook_handler.update_markdown_cells(translated_notebook, markdown_cells, markdown_translations)
        if code_texts:
            translated_notebook = notebook_handler.update_code_cells(translated_notebook, code_cells, code_translations)
        
        # Save translated notebook
        notebook_handler.save_notebook(translated_notebook, str(output_file))
        
        click.echo(f"   ✅ {notebook_path.name} → {output_file}")
        return True, str(output_file)
        
    except Exception as e:
        click.echo(f"   ❌ Failed to translate {notebook_path.name}: {str(e)}")
        return False, ""


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def cli(debug):
    """Jupyter Notebook Translator using AWS Bedrock"""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--target-language', '-l', default=Config.DEFAULT_TARGET_LANGUAGE, 
              help=f'Target language code (default: {Config.DEFAULT_TARGET_LANGUAGE})')
@click.option('--output-file', '-o', type=click.Path(path_type=Path), 
              help='Output file path (auto-generated if not provided)')
@click.option('--model-id', '-m', default=Config.DEFAULT_MODEL_ID,
              help=f'AWS Bedrock model ID (default: {Config.DEFAULT_MODEL_ID})')
@click.option('--batch-size', '-b', default=Config.BATCH_SIZE, type=int,
              help=f'Batch size for translation (default: {Config.BATCH_SIZE})')
@click.option('--preview', is_flag=True, help='Preview translations before saving')
def translate(input_file: Path, target_language: str, output_file: Optional[Path], 
              model_id: str, batch_size: int, preview: bool):
    """Translate a Jupyter notebook to the specified language"""
    
    try:
        # Validate inputs
        if not Config.validate_model_id(model_id):
            click.echo(f"❌ Unsupported model ID: {model_id}")
            click.echo(f"Supported models: {', '.join(Config.SUPPORTED_MODELS)}")
            sys.exit(1)
        
        if target_language not in Config.LANGUAGE_MAP:
            click.echo(f"❌ Unsupported language: {target_language}")
            click.echo(f"Supported languages: {', '.join(Config.LANGUAGE_MAP.keys())}")
            sys.exit(1)
        
        # Check AWS credentials
        creds_ok, creds_msg = Config.check_aws_credentials()
        if not creds_ok:
            click.echo(f"❌ {creds_msg}")
            sys.exit(1)
        
        click.echo(f"✅ {creds_msg}")
        
        # Initialize components
        notebook_handler = NotebookHandler()
        translation_engine = NotebookTranslationEngine(model_id, Config.ENABLE_POLISHING)
        
        # Load notebook
        click.echo(f"📖 Loading notebook: {input_file}")
        notebook = notebook_handler.load_notebook(str(input_file))
        
        # Validate notebook
        is_valid, validation_msg = notebook_handler.validate_notebook(notebook)
        if not is_valid:
            click.echo(f"❌ {validation_msg}")
            sys.exit(1)
        
        # Get notebook info
        info = notebook_handler.get_notebook_info(notebook)
        click.echo(f"📊 Notebook info:")
        click.echo(f"   Total cells: {info['total_cells']}")
        click.echo(f"   Cell types: {info['cell_counts']}")
        click.echo(f"   Translatable markdown cells: {info['translatable_markdown_cells']}")
        click.echo(f"   Translatable code cells: {info['translatable_code_cells']}")
        
        if info['translatable_markdown_cells'] == 0 and (not Config.TRANSLATE_CODE_CELLS or info['translatable_code_cells'] == 0):
            click.echo("⚠️ No translatable content found. Nothing to translate.")
            sys.exit(0)
        
        # Extract markdown cells
        markdown_cells = notebook_handler.extract_markdown_cells(notebook)
        markdown_texts = [cell['source'] for cell in markdown_cells]
        
        # Extract code cells if enabled
        code_cells = []
        code_texts = []
        if Config.TRANSLATE_CODE_CELLS:
            code_cells = notebook_handler.extract_code_cells(notebook)
            code_texts = [cell['source'] for cell in code_cells]
        
        # Translate
        target_lang_name = Config.get_language_name(target_language)
        click.echo(f"🌐 Translating to {target_lang_name} using {model_id}...")
        
        # Translate markdown cells
        if markdown_texts:
            if len(markdown_texts) <= batch_size:
                # Use batch translation
                markdown_translations = translation_engine.translate_markdown_cells_batch(markdown_texts, target_language)
            else:
                # Process in batches
                markdown_translations = []
                for i in range(0, len(markdown_texts), batch_size):
                    batch = markdown_texts[i:i+batch_size]
                    batch_translations = translation_engine.translate_markdown_cells_batch(batch, target_language)
                    markdown_translations.extend(batch_translations)
                    click.echo(f"✅ Processed markdown batch {i//batch_size + 1}/{(len(markdown_texts)-1)//batch_size + 1}")
        else:
            markdown_translations = []
        
        # Translate code cells
        if code_texts:
            click.echo(f"💻 Translating comments in {len(code_texts)} code cells...")
            code_translations = translation_engine.translate_code_cells_batch(code_texts, target_language)
        else:
            code_translations = []
        
        # Generate statistics
        if markdown_texts:
            markdown_stats = translation_engine.get_translation_stats(markdown_texts, markdown_translations)
            click.echo(f"📈 Markdown translation statistics:")
            click.echo(f"   Translated cells: {markdown_stats['translated_cells']}")
            click.echo(f"   Skipped cells: {markdown_stats['skipped_cells']}")
            click.echo(f"   Original characters: {markdown_stats['original_chars']:,}")
            click.echo(f"   Translated characters: {markdown_stats['translated_chars']:,}")
        
        if code_texts:
            code_stats = translation_engine.get_translation_stats(code_texts, code_translations)
            click.echo(f"💻 Code translation statistics:")
            click.echo(f"   Translated cells: {code_stats['translated_cells']}")
            click.echo(f"   Skipped cells: {code_stats['skipped_cells']}")
        
        # Preview if requested
        if preview and markdown_texts:
            preview_text = notebook_handler.preview_translations(markdown_cells, markdown_translations)
            click.echo(preview_text)
            
            if not click.confirm("Do you want to save the translated notebook?"):
                click.echo("❌ Translation cancelled by user")
                sys.exit(0)
        
        # Generate output filename if not provided
        if not output_file:
            output_file = Path(notebook_handler.generate_output_filename(
                str(input_file), target_language
            ))
        
        # Update notebook with translations
        translated_notebook = notebook
        if markdown_texts:
            translated_notebook = notebook_handler.update_markdown_cells(translated_notebook, markdown_cells, markdown_translations)
        if code_texts:
            translated_notebook = notebook_handler.update_code_cells(translated_notebook, code_cells, code_translations)
        
        # Save translated notebook
        notebook_handler.save_notebook(translated_notebook, str(output_file))
        
        click.echo(f"✅ Translation completed successfully!")
        click.echo(f"📁 Output file: {output_file}")
        
    except KeyboardInterrupt:
        click.echo("\n❌ Translation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        click.echo(f"❌ Translation failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('folder_path', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option('--target-language', '-l', default=Config.DEFAULT_TARGET_LANGUAGE, 
              help=f'Target language code (default: {Config.DEFAULT_TARGET_LANGUAGE})')
@click.option('--model-id', '-m', default=Config.DEFAULT_MODEL_ID,
              help=f'AWS Bedrock model ID (default: {Config.DEFAULT_MODEL_ID})')
@click.option('--batch-size', '-b', default=Config.BATCH_SIZE, type=int,
              help=f'Batch size for translation (default: {Config.BATCH_SIZE})')
@click.option('--recursive/--no-recursive', default=True,
              help='Search for notebooks recursively in subdirectories (default: True)')
def translate_folder(folder_path: Path, target_language: str, 
                    model_id: str, batch_size: int, recursive: bool):
    """Translate all Jupyter notebooks in a folder"""
    
    try:
        # Validate inputs
        if not Config.validate_model_id(model_id):
            click.echo(f"❌ Unsupported model ID: {model_id}")
            click.echo(f"Supported models: {', '.join(Config.SUPPORTED_MODELS)}")
            sys.exit(1)
        
        if target_language not in Config.LANGUAGE_MAP:
            click.echo(f"❌ Unsupported language: {target_language}")
            click.echo(f"Supported languages: {', '.join(Config.LANGUAGE_MAP.keys())}")
            sys.exit(1)
        
        # Check AWS credentials
        creds_ok, creds_msg = Config.check_aws_credentials()
        if not creds_ok:
            click.echo(f"❌ {creds_msg}")
            sys.exit(1)
        
        click.echo(f"✅ {creds_msg}")
        
        # Find all notebooks
        click.echo(f"🔍 Searching for notebooks in: {folder_path}")
        notebooks = find_notebooks(folder_path, recursive)
        
        if not notebooks:
            click.echo("❌ No Jupyter notebooks found in the specified folder")
            sys.exit(1)
        
        click.echo(f"📚 Found {len(notebooks)} notebook(s)")
        for nb in notebooks:
            click.echo(f"   📓 {nb.relative_to(folder_path)}")
        
        if not click.confirm(f"\nTranslate {len(notebooks)} notebook(s) to {Config.get_language_name(target_language)}?"):
            click.echo("❌ Translation cancelled by user")
            sys.exit(0)
        
        # Create output directory if specified
        
        # Translate each notebook
        target_lang_name = Config.get_language_name(target_language)
        click.echo(f"\n🌐 Translating notebooks to {target_lang_name} using {model_id}...")
        
        success_count = 0
        for i, notebook_path in enumerate(notebooks, 1):
            click.echo(f"\n📖 [{i}/{len(notebooks)}] Processing: {notebook_path.relative_to(folder_path)}")
            
            success, _ = translate_single_notebook(notebook_path, target_language, model_id, batch_size)
            if success:
                success_count += 1
        
        # Summary
        click.echo(f"\n📈 Translation Summary:")
        click.echo(f"   ✅ Successfully translated: {success_count}")
        click.echo(f"   ❌ Failed/Skipped: {len(notebooks) - success_count}")
        click.echo(f"   📁 Output location: Same folder as input files")
        
        if success_count > 0:
            click.echo(f"🎉 Folder translation completed!")
        else:
            click.echo(f"⚠️ No notebooks were successfully translated")
        
    except KeyboardInterrupt:
        click.echo("\n❌ Translation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Folder translation failed: {str(e)}")
        click.echo(f"❌ Folder translation failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--target-language', '-l', default=Config.DEFAULT_TARGET_LANGUAGE, 
              help=f'Target language code (default: {Config.DEFAULT_TARGET_LANGUAGE})')
@click.option('--output-file', '-o', type=click.Path(path_type=Path), 
              help='Output file path (auto-generated if not provided)')
@click.option('--model-id', '-m', default=Config.DEFAULT_MODEL_ID,
              help=f'AWS Bedrock model ID (default: {Config.DEFAULT_MODEL_ID})')
@click.option('--batch-size', '-b', default=Config.BATCH_SIZE, type=int,
              help=f'Batch size for translation (default: {Config.BATCH_SIZE})')
@click.option('--keep-original', is_flag=True, help='Keep the downloaded original file')
def translate_url(url: str, target_language: str, output_file: Optional[Path], 
                  model_id: str, batch_size: int, keep_original: bool):
    """Download and translate a Jupyter notebook from URL"""
    
    try:
        # Validate inputs
        if not Config.validate_model_id(model_id):
            click.echo(f"❌ Unsupported model ID: {model_id}")
            click.echo(f"Supported models: {', '.join(Config.SUPPORTED_MODELS)}")
            sys.exit(1)
        
        if target_language not in Config.LANGUAGE_MAP:
            click.echo(f"❌ Unsupported language: {target_language}")
            click.echo(f"Supported languages: {', '.join(Config.LANGUAGE_MAP.keys())}")
            sys.exit(1)
        
        # Check AWS credentials
        creds_ok, creds_msg = Config.check_aws_credentials()
        if not creds_ok:
            click.echo(f"❌ {creds_msg}")
            sys.exit(1)
        
        click.echo(f"✅ {creds_msg}")
        
        # Download notebook
        click.echo(f"⬇️ Downloading notebook from: {url}")
        downloader = NotebookURLDownloader()
        downloaded_file = downloader.download_notebook(url)
        click.echo(f"✅ Downloaded to: {downloaded_file}")
        
        # Initialize components
        notebook_handler = NotebookHandler()
        translation_engine = NotebookTranslationEngine(model_id, Config.ENABLE_POLISHING)
        
        # Load notebook
        click.echo(f"📖 Loading notebook: {downloaded_file}")
        notebook = notebook_handler.load_notebook(downloaded_file)
        
        # Validate notebook
        is_valid, validation_msg = notebook_handler.validate_notebook(notebook)
        if not is_valid:
            click.echo(f"❌ {validation_msg}")
            sys.exit(1)
        
        # Get notebook info
        info = notebook_handler.get_notebook_info(notebook)
        click.echo(f"📊 Notebook info:")
        click.echo(f"   Total cells: {info['total_cells']}")
        click.echo(f"   Cell types: {info['cell_counts']}")
        click.echo(f"   Translatable markdown cells: {info['translatable_markdown_cells']}")
        
        if info['translatable_markdown_cells'] == 0:
            click.echo("⚠️ No translatable markdown cells found. Nothing to translate.")
            if not keep_original:
                Path(downloaded_file).unlink()
            sys.exit(0)
        
        # Extract markdown cells
        markdown_cells = notebook_handler.extract_markdown_cells(notebook)
        markdown_texts = [cell['source'] for cell in markdown_cells]
        
        # Translate
        target_lang_name = Config.get_language_name(target_language)
        click.echo(f"🌐 Translating to {target_lang_name} using {model_id}...")
        
        if len(markdown_texts) <= batch_size:
            # Use batch translation
            translations = translation_engine.translate_markdown_cells_batch(markdown_texts, target_language)
        else:
            # Process in batches
            translations = []
            for i in range(0, len(markdown_texts), batch_size):
                batch = markdown_texts[i:i+batch_size]
                batch_translations = translation_engine.translate_markdown_cells_batch(batch, target_language)
                translations.extend(batch_translations)
                click.echo(f"✅ Processed batch {i//batch_size + 1}/{(len(markdown_texts)-1)//batch_size + 1}")
        
        # Generate statistics
        stats = translation_engine.get_translation_stats(markdown_texts, translations)
        click.echo(f"📈 Translation statistics:")
        click.echo(f"   Translated cells: {stats['translated_cells']}")
        click.echo(f"   Skipped cells: {stats['skipped_cells']}")
        click.echo(f"   Original characters: {stats['original_chars']:,}")
        click.echo(f"   Translated characters: {stats['translated_chars']:,}")
        
        # Generate output filename if not provided
        if not output_file:
            output_file = Path(notebook_handler.generate_output_filename(
                downloaded_file, target_language
            ))
        
        # Update notebook with translations
        translated_notebook = notebook_handler.update_markdown_cells(notebook, markdown_cells, translations)
        
        # Save translated notebook
        notebook_handler.save_notebook(translated_notebook, str(output_file))
        
        # Clean up original file if not keeping it
        if not keep_original:
            Path(downloaded_file).unlink()
            click.echo(f"🗑️ Removed original file: {downloaded_file}")
        
        click.echo(f"✅ Translation completed successfully!")
        click.echo(f"📁 Output file: {output_file}")
        
    except KeyboardInterrupt:
        click.echo("\n❌ Translation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        click.echo(f"❌ Translation failed: {str(e)}")
        sys.exit(1)


@cli.command()
@click.argument('notebook_file', type=click.Path(exists=True, path_type=Path))
def info(notebook_file: Path):
    """Show information about a Jupyter notebook"""
    try:
        notebook_handler = NotebookHandler()
        notebook = notebook_handler.load_notebook(str(notebook_file))
        
        info = notebook_handler.get_notebook_info(notebook)
        
        click.echo(f"📖 Notebook: {notebook_file}")
        click.echo(f"📊 Total cells: {info['total_cells']}")
        click.echo(f"📝 Cell types:")
        for cell_type, count in info['cell_counts'].items():
            click.echo(f"   {cell_type}: {count}")
        click.echo(f"🌐 Translatable markdown cells: {info['translatable_markdown_cells']}")
        click.echo(f"📋 Notebook format: {info['notebook_format']}.{info['notebook_format_minor']}")
        
        if 'kernel' in info:
            click.echo(f"🐍 Kernel:")
            click.echo(f"   Name: {info['kernel']['name']}")
            click.echo(f"   Display name: {info['kernel']['display_name']}")
            click.echo(f"   Language: {info['kernel']['language']}")
        
    except Exception as e:
        click.echo(f"❌ Failed to read notebook: {str(e)}")
        sys.exit(1)


@cli.command()
def list_languages():
    """List all supported target languages"""
    click.echo("🌐 Supported target languages:")
    for code, name in sorted(Config.LANGUAGE_MAP.items()):
        click.echo(f"   {code}: {name}")


@cli.command()
def list_models():
    """List all supported AWS Bedrock models"""
    click.echo("🤖 Supported AWS Bedrock models:")
    for model in Config.SUPPORTED_MODELS:
        click.echo(f"   {model}")


@cli.command()
def check_credentials():
    """Check AWS credentials configuration"""
    creds_ok, creds_msg = Config.check_aws_credentials()
    if creds_ok:
        click.echo(f"✅ {creds_msg}")
    else:
        click.echo(f"❌ {creds_msg}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
