#!/usr/bin/env python3
"""
Main script to run the content scraper
"""

import argparse
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions to get scrapers and storage on demand
from content_scraper import get_instagram_scraper, get_tiktok_scraper, get_google_sheets_storage
from content_scraper.config import get_config
from content_scraper.utils import get_logger, ScrapeLogger


def run_instagram_scraping(config, storage):
    """Run Instagram scraping for configured accounts and hashtags"""
    logger = get_logger(__name__)
    
    InstagramScraper = get_instagram_scraper()
    
    with InstagramScraper(
        headless=config.scraping.headless_browser,
        rate_limit_delay=config.scraping.instagram_rate_delay
    ) as scraper:
        
        all_posts = []
        
        # Scrape accounts
        for account in config.accounts.instagram_accounts:
            try:
                with ScrapeLogger(f"ig_account_{account}", "instagram") as session_logger:
                    session_logger.log_progress(f"Starting to scrape account: {account}")
                    
                    posts = scraper.scrape_account(
                        username=account.lstrip('@'),
                        max_posts=config.scraping.instagram_max_posts
                    )
                    
                    all_posts.extend(posts)
                    session_logger.log_progress(f"Scraped {len(posts)} posts from {account}")
                    
            except Exception as e:
                logger.error(f"Error scraping Instagram account {account}: {str(e)}")
                continue
        
        # Scrape hashtags
        for hashtag in config.accounts.instagram_hashtags:
            try:
                with ScrapeLogger(f"ig_hashtag_{hashtag}", "instagram") as session_logger:
                    session_logger.log_progress(f"Starting to scrape hashtag: {hashtag}")
                    
                    posts = scraper.scrape_hashtag(
                        hashtag=hashtag.lstrip('#'),
                        max_posts=min(30, config.scraping.instagram_max_posts)
                    )
                    
                    all_posts.extend(posts)
                    session_logger.log_progress(f"Scraped {len(posts)} posts from #{hashtag}")
                    
            except Exception as e:
                logger.error(f"Error scraping Instagram hashtag {hashtag}: {str(e)}")
                continue
        
        # Save to Google Sheets
        if all_posts:
            storage.save_instagram_data(all_posts)
            logger.info(f"Saved {len(all_posts)} Instagram posts to Google Sheets")
        else:
            logger.warning("No Instagram posts scraped")
    
    return len(all_posts)


def run_tiktok_scraping(config, storage):
    """Run TikTok scraping for configured accounts and hashtags"""
    logger = get_logger(__name__)
    
    TikTokScraper = get_tiktok_scraper()
    
    with TikTokScraper(
        headless=config.scraping.headless_browser,
        rate_limit_delay=config.scraping.tiktok_rate_delay
    ) as scraper:
        
        all_videos = []
        
        # Scrape accounts
        for account in config.accounts.tiktok_accounts:
            try:
                with ScrapeLogger(f"tt_account_{account}", "tiktok") as session_logger:
                    session_logger.log_progress(f"Starting to scrape account: {account}")
                    
                    videos = scraper.scrape_account(
                        username=account.lstrip('@'),
                        max_videos=config.scraping.tiktok_max_videos
                    )
                    
                    all_videos.extend(videos)
                    session_logger.log_progress(f"Scraped {len(videos)} videos from {account}")
                    
            except Exception as e:
                logger.error(f"Error scraping TikTok account {account}: {str(e)}")
                continue
        
        # Scrape hashtags
        for hashtag in config.accounts.tiktok_hashtags:
            try:
                with ScrapeLogger(f"tt_hashtag_{hashtag}", "tiktok") as session_logger:
                    session_logger.log_progress(f"Starting to scrape hashtag: {hashtag}")
                    
                    videos = scraper.scrape_hashtag(
                        hashtag=hashtag.lstrip('#'),
                        max_videos=min(30, config.scraping.tiktok_max_videos)
                    )
                    
                    all_videos.extend(videos)
                    session_logger.log_progress(f"Scraped {len(videos)} videos from #{hashtag}")
                    
            except Exception as e:
                logger.error(f"Error scraping TikTok hashtag {hashtag}: {str(e)}")
                continue
        
        # Save to Google Sheets
        if all_videos:
            storage.save_tiktok_data(all_videos)
            logger.info(f"Saved {len(all_videos)} TikTok videos to Google Sheets")
        else:
            logger.warning("No TikTok videos scraped")
    
    return len(all_videos)


def setup_google_sheets(config):
    """Setup Google Sheets storage"""
    logger = get_logger(__name__)
    
    GoogleSheetsStorage = get_google_sheets_storage()
    
    storage = GoogleSheetsStorage(
        credentials_path=config.google_sheets.credentials_path,
        spreadsheet_id=config.google_sheets.spreadsheet_id
    )
    
    # Create spreadsheet if needed
    if not config.google_sheets.spreadsheet_id and config.google_sheets.auto_create_spreadsheet:
        logger.info("Creating new Google Sheets spreadsheet...")
        spreadsheet_id = storage.create_spreadsheet(config.google_sheets.spreadsheet_title)
        
        if spreadsheet_id:
            logger.info(f"Created spreadsheet: {storage.get_spreadsheet_url()}")
            logger.info("Please update your config with this spreadsheet ID for future runs")
        else:
            logger.error("Failed to create spreadsheet")
            return None
    
    return storage


def run_full_scrape():
    """Run full scraping process"""
    logger = get_logger(__name__)
    logger.info("Starting full content scraping process")
    
    # Load configuration
    config = get_config()
    
    # Setup Google Sheets
    storage = setup_google_sheets(config)
    if not storage:
        logger.error("Failed to setup Google Sheets storage")
        return
    
    total_instagram = 0
    total_tiktok = 0
    
    # Run Instagram scraping
    if config.accounts.instagram_accounts or config.accounts.instagram_hashtags:
        logger.info("Starting Instagram scraping...")
        total_instagram = run_instagram_scraping(config, storage)
    else:
        logger.info("No Instagram accounts or hashtags configured, skipping")
    
    # Run TikTok scraping
    if config.accounts.tiktok_accounts or config.accounts.tiktok_hashtags:
        logger.info("Starting TikTok scraping...")
        total_tiktok = run_tiktok_scraping(config, storage)
    else:
        logger.info("No TikTok accounts or hashtags configured, skipping")
    
    # Update analytics
    if config.google_sheets.update_analytics and (total_instagram > 0 or total_tiktok > 0):
        logger.info("Updating analytics summary...")
        storage.update_analytics_summary()
    
    # Summary
    logger.info(f"Scraping completed! Total: {total_instagram} Instagram posts, {total_tiktok} TikTok videos")
    logger.info(f"Data saved to: {storage.get_spreadsheet_url()}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Content Scraper for Instagram and TikTok")
    parser.add_argument(
        '--platform', 
        choices=['instagram', 'tiktok', 'all'], 
        default='all',
        help='Platform to scrape (default: all)'
    )
    parser.add_argument(
        '--accounts', 
        nargs='+',
        help='Specific accounts to scrape (overrides config)'
    )
    parser.add_argument(
        '--hashtags',
        nargs='+', 
        help='Specific hashtags to scrape (overrides config)'
    )
    parser.add_argument(
        '--max-posts',
        type=int,
        help='Maximum posts per account/hashtag (overrides config)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser with GUI (for debugging)'
    )
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create default configuration files'
    )
    
    args = parser.parse_args()
    
    # Create default config if requested
    if args.create_config:
        from content_scraper.config import ConfigManager
        config_manager = ConfigManager()
        config_manager.create_default_config()
        print("Default configuration files created!")
        print("Please edit config/accounts.json and config/credentials.json before running the scraper.")
        return
    
    # Load configuration
    config = get_config()
    
    # Override config with command line arguments
    if args.accounts:
        if args.platform == 'instagram' or args.platform == 'all':
            config.accounts.instagram_accounts = [f"@{acc.lstrip('@')}" for acc in args.accounts]
        if args.platform == 'tiktok' or args.platform == 'all':
            config.accounts.tiktok_accounts = [f"@{acc.lstrip('@')}" for acc in args.accounts]
    
    if args.hashtags:
        if args.platform == 'instagram' or args.platform == 'all':
            config.accounts.instagram_hashtags = [f"#{tag.lstrip('#')}" for tag in args.hashtags]
        if args.platform == 'tiktok' or args.platform == 'all':
            config.accounts.tiktok_hashtags = [f"#{tag.lstrip('#')}" for tag in args.hashtags]
    
    if args.max_posts:
        config.scraping.max_posts_per_account = args.max_posts
        config.scraping.instagram_max_posts = args.max_posts
        config.scraping.tiktok_max_videos = args.max_posts
    
    if args.headless:
        config.scraping.headless_browser = True
    elif args.no_headless:
        config.scraping.headless_browser = False
    
    # Run scraping based on platform selection
    if args.platform == 'all':
        run_full_scrape()
    else:
        # Setup Google Sheets
        storage = setup_google_sheets(config)
        if not storage:
            print("Failed to setup Google Sheets storage")
            return
        
        if args.platform == 'instagram':
            total = run_instagram_scraping(config, storage)
            print(f"Scraped {total} Instagram posts")
        elif args.platform == 'tiktok':
            total = run_tiktok_scraping(config, storage)
            print(f"Scraped {total} TikTok videos")
        
        print(f"Data saved to: {storage.get_spreadsheet_url()}")


if __name__ == "__main__":
    main()