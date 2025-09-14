"""
Configuration settings for the content scraper
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Try to load dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables will still work
    pass


@dataclass
class ScrapingConfig:
    """Configuration for scraping parameters"""
    max_posts_per_account: int = 50
    max_videos_per_account: int = 50
    rate_limit_delay: float = 2.0
    headless_browser: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Instagram specific
    instagram_rate_delay: float = 2.0
    instagram_max_posts: int = 50
    
    # TikTok specific
    tiktok_rate_delay: float = 3.0
    tiktok_max_videos: int = 50


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets integration"""
    credentials_path: str = "config/credentials.json"
    spreadsheet_id: Optional[str] = None
    auto_create_spreadsheet: bool = True
    spreadsheet_title: str = "Content Scraping Data"
    update_analytics: bool = True


@dataclass
class AccountsConfig:
    """Configuration for accounts and hashtags to track"""
    instagram_accounts: List[str] = field(default_factory=list)
    instagram_hashtags: List[str] = field(default_factory=list)
    tiktok_accounts: List[str] = field(default_factory=list)
    tiktok_hashtags: List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    """Main application configuration"""
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    google_sheets: GoogleSheetsConfig = field(default_factory=GoogleSheetsConfig)
    accounts: AccountsConfig = field(default_factory=AccountsConfig)
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Scheduling
    enable_scheduling: bool = False
    schedule_interval_hours: int = 6
    
    # Environment
    environment: str = "development"  # development, production


class ConfigManager:
    """Configuration manager for loading and saving settings"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "settings.json")
        self.accounts_file = os.path.join(config_dir, "accounts.json")
        self.env_file = ".env"
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """Load configuration from files and environment"""
        config = AppConfig()
        
        # Load from JSON files
        self._load_from_json(config)
        
        # Load accounts
        self._load_accounts(config)
        
        # Override with environment variables
        self._load_from_env(config)
        
        return config
    
    def _load_from_json(self, config: AppConfig):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update scraping config
                if 'scraping' in data:
                    for key, value in data['scraping'].items():
                        if hasattr(config.scraping, key):
                            setattr(config.scraping, key, value)
                
                # Update Google Sheets config
                if 'google_sheets' in data:
                    for key, value in data['google_sheets'].items():
                        if hasattr(config.google_sheets, key):
                            setattr(config.google_sheets, key, value)
                
                # Update app-level config
                for key in ['log_level', 'log_file', 'enable_scheduling', 
                           'schedule_interval_hours', 'environment']:
                    if key in data:
                        setattr(config, key, data[key])
                        
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Error loading config file {self.config_file}: {e}")
    
    def _load_accounts(self, config: AppConfig):
        """Load accounts configuration"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                
                if 'instagram' in data:
                    config.accounts.instagram_accounts = data['instagram'].get('accounts', [])
                    config.accounts.instagram_hashtags = data['instagram'].get('hashtags', [])
                
                if 'tiktok' in data:
                    config.accounts.tiktok_accounts = data['tiktok'].get('accounts', [])
                    config.accounts.tiktok_hashtags = data['tiktok'].get('hashtags', [])
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Error loading accounts file {self.accounts_file}: {e}")
    
    def _load_from_env(self, config: AppConfig):
        """Load configuration from environment variables"""
        # Google Sheets
        if os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH'):
            config.google_sheets.credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        
        if os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'):
            config.google_sheets.spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
        
        # Scraping
        if os.getenv('RATE_LIMIT_DELAY'):
            config.scraping.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY'))
        
        if os.getenv('HEADLESS_BROWSER'):
            config.scraping.headless_browser = os.getenv('HEADLESS_BROWSER').lower() == 'true'
        
        if os.getenv('MAX_POSTS_PER_ACCOUNT'):
            config.scraping.max_posts_per_account = int(os.getenv('MAX_POSTS_PER_ACCOUNT'))
        
        # Logging
        if os.getenv('LOG_LEVEL'):
            config.log_level = os.getenv('LOG_LEVEL')
        
        # Environment
        if os.getenv('ENVIRONMENT'):
            config.environment = os.getenv('ENVIRONMENT')
    
    def save_config(self, config: AppConfig = None):
        """Save configuration to JSON file"""
        if config is None:
            config = self.config
        
        config_data = {
            'scraping': {
                'max_posts_per_account': config.scraping.max_posts_per_account,
                'max_videos_per_account': config.scraping.max_videos_per_account,
                'rate_limit_delay': config.scraping.rate_limit_delay,
                'headless_browser': config.scraping.headless_browser,
                'max_retries': config.scraping.max_retries,
                'timeout_seconds': config.scraping.timeout_seconds,
                'instagram_rate_delay': config.scraping.instagram_rate_delay,
                'instagram_max_posts': config.scraping.instagram_max_posts,
                'tiktok_rate_delay': config.scraping.tiktok_rate_delay,
                'tiktok_max_videos': config.scraping.tiktok_max_videos
            },
            'google_sheets': {
                'credentials_path': config.google_sheets.credentials_path,
                'spreadsheet_id': config.google_sheets.spreadsheet_id,
                'auto_create_spreadsheet': config.google_sheets.auto_create_spreadsheet,
                'spreadsheet_title': config.google_sheets.spreadsheet_title,
                'update_analytics': config.google_sheets.update_analytics
            },
            'log_level': config.log_level,
            'log_file': config.log_file,
            'enable_scheduling': config.enable_scheduling,
            'schedule_interval_hours': config.schedule_interval_hours,
            'environment': config.environment
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def save_accounts(self, config: AppConfig = None):
        """Save accounts configuration to JSON file"""
        if config is None:
            config = self.config
        
        accounts_data = {
            'instagram': {
                'accounts': config.accounts.instagram_accounts,
                'hashtags': config.accounts.instagram_hashtags
            },
            'tiktok': {
                'accounts': config.accounts.tiktok_accounts,
                'hashtags': config.accounts.tiktok_hashtags
            }
        }
        
        with open(self.accounts_file, 'w') as f:
            json.dump(accounts_data, f, indent=2)
    
    def create_default_config(self):
        """Create default configuration files"""
        # Default settings
        self.save_config()
        
        # Default accounts (with examples)
        default_accounts = {
            'instagram': {
                'accounts': ['@example_account1', '@example_account2'],
                'hashtags': ['#trending', '#viral', '#content']
            },
            'tiktok': {
                'accounts': ['@tiktok_user1', '@tiktok_user2'],
                'hashtags': ['#fyp', '#viral', '#trending']
            }
        }
        
        with open(self.accounts_file, 'w') as f:
            json.dump(default_accounts, f, indent=2)
        
        # Default .env file
        env_content = """# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=config/credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=

# Scraping Configuration
RATE_LIMIT_DELAY=2.0
HEADLESS_BROWSER=true
MAX_POSTS_PER_ACCOUNT=50

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=development
"""
        
        if not os.path.exists(self.env_file):
            with open(self.env_file, 'w') as f:
                f.write(env_content)
    
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        return self.config


# Global config manager instance
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """Get application configuration"""
    return config_manager.get_config()

def reload_config() -> AppConfig:
    """Reload configuration from files"""
    config_manager.config = config_manager.load_config()
    return config_manager.config