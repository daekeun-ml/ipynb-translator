"""
URL downloader for Jupyter notebooks
"""
import re
import requests
from pathlib import Path
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class NotebookURLDownloader:
    """Download Jupyter notebooks from URLs"""
    
    @staticmethod
    def convert_github_url(url: str) -> str:
        """Convert GitHub blob URL to raw URL"""
        if 'github.com' in url and '/blob/' in url:
            return url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        return url
    
    @staticmethod
    def extract_filename_from_url(url: str) -> str:
        """Extract filename from URL"""
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        
        if not filename.endswith('.ipynb'):
            filename += '.ipynb'
        
        return filename
    
    @staticmethod
    def download_notebook(url: str, output_path: str = None) -> str:
        """
        Download notebook from URL
        
        Args:
            url: URL to download from
            output_path: Optional output path. If not provided, uses filename from URL
            
        Returns:
            Path to downloaded file
        """
        try:
            # Convert GitHub URLs to raw URLs
            raw_url = NotebookURLDownloader.convert_github_url(url)
            logger.info(f"Downloading from: {raw_url}")
            
            # Download the file
            response = requests.get(raw_url, timeout=30)
            response.raise_for_status()
            
            # Determine output path
            if not output_path:
                filename = NotebookURLDownloader.extract_filename_from_url(url)
                output_path = filename
            
            # Save the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            logger.info(f"Downloaded notebook to: {output_path}")
            return output_path
            
        except requests.RequestException as e:
            raise Exception(f"Failed to download notebook: {str(e)}")
        except Exception as e:
            raise Exception(f"Error saving notebook: {str(e)}")
