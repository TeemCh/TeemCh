"""
Content Scraper Package
A comprehensive system for scraping Instagram and TikTok content metrics
and storing them in Google Sheets for content idea generation.
"""

__version__ = "1.0.0"
__author__ = "Timur Chepiga"
__email__ = "your-email@example.com"

# Import only models and basic utilities to avoid dependency issues
from .models.content_models import InstagramPost, TikTokVideo

__all__ = [
    "InstagramPost",
    "TikTokVideo"
]

# Scrapers and storage are imported on demand to avoid dependency issues
def get_instagram_scraper():
    """Get Instagram scraper (imports on demand)"""
    from .scrapers.instagram_scraper import InstagramScraper
    return InstagramScraper

def get_tiktok_scraper():
    """Get TikTok scraper (imports on demand)"""
    from .scrapers.tiktok_scraper import TikTokScraper
    return TikTokScraper

def get_google_sheets_storage():
    """Get Google Sheets storage (imports on demand)"""
    from .storage.google_sheets import GoogleSheetsStorage
    return GoogleSheetsStorage