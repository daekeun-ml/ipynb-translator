"""
Configuration constants and settings for Jupyter Notebook Translator
"""
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration constants"""
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # Translation settings from environment
    DEFAULT_TARGET_LANGUAGE = os.getenv('DEFAULT_TARGET_LANGUAGE', 'ko')
    DEFAULT_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-3-7-sonnet-20250219-v1:0')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4000'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.1'))
    ENABLE_POLISHING = os.getenv('ENABLE_POLISHING', 'true').lower() == 'true'
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '20'))
    TRANSLATE_CODE_CELLS = os.getenv('TRANSLATE_CODE_CELLS', 'false').lower() == 'true'
    
    # Debug settings
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # Supported models
    SUPPORTED_MODELS = [
        # Amazon Nova models
        "amazon.nova-micro-v1:0",
        "amazon.nova-lite-v1:0", 
        "amazon.nova-pro-v1:0",
        "amazon.nova-premier-v1:0",
        
        # Anthropic Claude models
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        "us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "us.anthropic.claude-opus-4-20250514-v1:0",
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "us.anthropic.claude-opus-4-1-20250805-v1:0",

        # Meta Llama models
        "meta.llama3-8b-instruct-v1:0",
        "meta.llama3-70b-instruct-v1:0",
        "us.meta.llama3-1-8b-instruct-v1:0",
        "us.meta.llama3-1-70b-instruct-v1:0",
        "us.meta.llama3-2-1b-instruct-v1:0",
        "us.meta.llama3-2-3b-instruct-v1:0",
        "us.meta.llama3-2-11b-instruct-v1:0",
        "us.meta.llama3-2-90b-instruct-v1:0",
        "us.meta.llama3-3-70b-instruct-v1:0",
        "us.meta.llama4-scout-17b-instruct-v1:0",
        "us.meta.llama4-maverick-17b-instruct-v1:0",
        
        # DeepSeek models 
        "deepseek.r1-v1:0",
        "us.deepseek.r1-v1:0",        
        
        # Mistral models
        "mistral.mistral-7b-instruct-v0:2",
        "mistral.mixtral-8x7b-instruct-v0:1",
        "mistral.mistral-large-2402-v1:0",
        "mistral.mistral-small-2402-v1:0",
        "mistral.pixtral-large-2502-v1:0",
        
        # Cohere models
        "cohere.command-r-v1:0",
        "cohere.command-r-plus-v1:0",
        
        # AI21 models 
        "ai21.jamba-1-5-large-v1:0",
        "ai21.jamba-1-5-mini-v1:0",
        "ai21.jamba-instruct-v1:0",
    ]
    
    # Language mapping
    LANGUAGE_MAP = {
        'en': 'English',
        'ko': 'Korean',
        'ja': 'Japanese',
        'zh': 'Chinese (Simplified)',
        'zh-CN': 'Chinese (Simplified)',
        'zh-TW': 'Chinese (Traditional)',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'no': 'Norwegian',
        'da': 'Danish',
        'fi': 'Finnish',
        'pl': 'Polish',
        'cs': 'Czech',
        'sk': 'Slovak',
        'hu': 'Hungarian',
        'ro': 'Romanian',
        'bg': 'Bulgarian',
        'hr': 'Croatian',
        'sr': 'Serbian',
        'sl': 'Slovenian',
        'et': 'Estonian',
        'lv': 'Latvian',
        'lt': 'Lithuanian',
        'el': 'Greek',
        'tr': 'Turkish',
        'uk': 'Ukrainian',
        'ar': 'Arabic',
        'he': 'Hebrew',
        'fa': 'Persian (Farsi)',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'te': 'Telugu',
        'mr': 'Marathi',
        'ta': 'Tamil',
        'gu': 'Gujarati',
        'kn': 'Kannada',
        'ml': 'Malayalam',
        'pa': 'Punjabi',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ms': 'Malay',
        'tl': 'Filipino (Tagalog)',
        'ur': 'Urdu',
        'sw': 'Swahili'
    }
    
    # Korean-specific terminology rules
    KOREAN_TERMINOLOGY = {
        "Machine Learning": "머신 러닝",
        "Deep Learning": "딥 러닝",
        "Data Science": "데이터 사이언스",
        "Artificial Intelligence": "인공지능",
        "Neural Network": "신경망",
        "Natural Language Processing": "자연어 처리",
        "Computer Vision": "컴퓨터 비전",
        "Big Data": "빅 데이터",
        "Cloud Computing": "클라우드 컴퓨팅",
        "DevOps": "DevOps",
        "MLOps": "MLOps",
        "API": "API",
        "SDK": "SDK",
        "CLI": "CLI",
        "AWS": "AWS",
        "Amazon": "Amazon"
    }
    
    # Text patterns to skip translation
    SKIP_PATTERNS = [
        r'^\d+$',  # Numbers only
        r'^https?://',  # URLs
        r'\S+@\S+\.\S+',  # Email addresses
        r'^[A-Za-z_][A-Za-z0-9_]*$',  # Variable names
        r'^\$[A-Za-z_][A-Za-z0-9_]*$',  # Shell variables
        r'^[A-Z_][A-Z0-9_]*$',  # Constants
    ]
    
    @classmethod
    def get_language_name(cls, language_code: str) -> str:
        """Get the full language name from language code"""
        return cls.LANGUAGE_MAP.get(language_code, language_code)
    
    @classmethod
    def validate_model_id(cls, model_id: str) -> bool:
        """Validate if the model ID is supported"""
        return model_id in cls.SUPPORTED_MODELS
    
    @classmethod
    def check_aws_credentials(cls):
        """Check if AWS credentials are properly configured"""
        import boto3
        from botocore.exceptions import NoCredentialsError, PartialCredentialsError
        
        try:
            # Try to create a session with the specified profile
            if cls.AWS_PROFILE and cls.AWS_PROFILE != 'default':
                session = boto3.Session(profile_name=cls.AWS_PROFILE)
            else:
                session = boto3.Session()
            
            # Try to get credentials
            credentials = session.get_credentials()
            if credentials is None:
                return False, "No AWS credentials found. Please run 'aws configure' to set up your credentials."
            
            # Try to make a simple AWS call to verify credentials work
            sts = session.client('sts', region_name=cls.AWS_REGION)
            sts.get_caller_identity()
            
            return True, "AWS credentials are properly configured."
            
        except NoCredentialsError:
            return False, "No AWS credentials found. Please run 'aws configure' to set up your credentials."
        except PartialCredentialsError:
            return False, "Incomplete AWS credentials. Please run 'aws configure' to complete your credential setup."
        except Exception as e:
            return False, f"AWS credential verification failed: {str(e)}"
