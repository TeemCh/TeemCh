"""
TikTok content scraper using web scraping techniques
"""

import time
import re
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..models.content_models import TikTokVideo, ScrapingSession
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger


class TikTokScraper:
    """TikTok content scraper with rate limiting and error handling"""
    
    def __init__(self, headless: bool = True, rate_limit_delay: float = 3.0):
        """
        Initialize TikTok scraper
        
        Args:
            headless: Run browser in headless mode
            rate_limit_delay: Delay between requests in seconds
        """
        self.logger = get_logger(__name__)
        self.rate_limiter = RateLimiter(delay=rate_limit_delay)
        self.headless = headless
        self.driver = None
        self.session = requests.Session()
        
        # Setup user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # TikTok-specific user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Execute script to hide automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def scrape_account(self, username: str, max_videos: int = 50) -> List[TikTokVideo]:
        """
        Scrape videos from a TikTok account
        
        Args:
            username: TikTok username (without @)
            max_videos: Maximum number of videos to scrape
            
        Returns:
            List of TikTokVideo objects
        """
        videos = []
        session_id = f"tt_{username}_{int(time.time())}"
        scraping_session = ScrapingSession(session_id=session_id, platform="tiktok")
        
        try:
            self.logger.info(f"Starting to scrape TikTok account: {username}")
            
            # Remove @ if present
            username = username.lstrip('@')
            
            # Setup driver
            if not self.driver:
                self.driver = self._setup_driver()
            
            # Navigate to user profile
            profile_url = f"https://www.tiktok.com/@{username}"
            self.driver.get(profile_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Handle potential age verification or login popup
            self._handle_popups()
            
            # Get video links
            video_links = self._get_video_links(max_videos)
            
            for i, video_url in enumerate(video_links[:max_videos]):
                try:
                    self.rate_limiter.wait()
                    video = self._scrape_single_video(video_url, username)
                    
                    if video:
                        videos.append(video)
                        scraping_session.total_posts_scraped += 1
                        self.logger.info(f"Scraped video {i+1}/{len(video_links)}: {video.video_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping video {video_url}: {str(e)}")
                    scraping_session.errors_count += 1
                    continue
            
            scraping_session.total_accounts_scraped = 1
            
        except Exception as e:
            self.logger.error(f"Error scraping account {username}: {str(e)}")
            scraping_session.errors_count += 1
            
        finally:
            scraping_session.finish_session()
            self.logger.info(f"Scraping session completed: {scraping_session.to_dict()}")
            
        return videos
    
    def _handle_popups(self):
        """Handle age verification and other popups"""
        try:
            # Wait for potential popups
            time.sleep(2)
            
            # Handle age verification
            age_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-e2e='age-gate-button']")
            if age_buttons:
                age_buttons[0].click()
                time.sleep(2)
            
            # Handle login suggestions (close them)
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[data-e2e='close-button'], [aria-label='Close']")
            for button in close_buttons:
                try:
                    button.click()
                    time.sleep(1)
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"No popups to handle: {str(e)}")
    
    def _get_video_links(self, max_videos: int) -> List[str]:
        """Extract video links from profile page"""
        video_links = []
        
        try:
            # Scroll to load more videos
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(video_links) < max_videos:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Get current video links
                video_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "div[data-e2e='user-post-item'] a, a[href*='/video/']"
                )
                
                current_links = []
                for elem in video_elements:
                    href = elem.get_attribute('href')
                    if href and '/video/' in href:
                        current_links.append(href)
                
                # Check if new videos loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height and len(current_links) == len(video_links):
                    break
                    
                last_height = new_height
                video_links = list(set(current_links))  # Remove duplicates
                
                if len(video_links) >= max_videos:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error getting video links: {str(e)}")
            
        return video_links[:max_videos]
    
    def _scrape_single_video(self, video_url: str, username: str) -> Optional[TikTokVideo]:
        """
        Scrape a single TikTok video
        
        Args:
            video_url: URL of the video
            username: Account username
            
        Returns:
            TikTokVideo object or None if failed
        """
        try:
            self.driver.get(video_url)
            time.sleep(3)
            
            # Extract video ID from URL
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None
            
            # Get description
            description = self._extract_description()
            
            # Get metrics
            likes_count = self._extract_likes_count()
            comments_count = self._extract_comments_count()
            shares_count = self._extract_shares_count()
            views_count = self._extract_views_count()
            
            # Get hashtags from description
            hashtags = self._extract_hashtags(description)
            
            # Get upload date
            upload_date = self._extract_upload_date()
            
            # Get music info
            music_title, music_artist = self._extract_music_info()
            
            # Get video URL
            video_src_url = self._extract_video_url()
            
            # Get duration
            duration_seconds = self._extract_duration()
            
            return TikTokVideo(
                video_id=video_id,
                username=username,
                description=description,
                likes_count=likes_count,
                comments_count=comments_count,
                shares_count=shares_count,
                views_count=views_count,
                upload_date=upload_date,
                hashtags=hashtags,
                music_title=music_title,
                music_artist=music_artist,
                video_url=video_src_url,
                duration_seconds=duration_seconds
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping video {video_url}: {str(e)}")
            return None
    
    def _extract_video_id(self, video_url: str) -> Optional[str]:
        """Extract video ID from URL"""
        try:
            # TikTok video URLs: https://www.tiktok.com/@username/video/1234567890
            video_id_match = re.search(r'/video/(\d+)', video_url)
            if video_id_match:
                return video_id_match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _extract_description(self) -> str:
        """Extract video description"""
        try:
            # Try multiple selectors for description
            description_selectors = [
                "div[data-e2e='browse-video-desc'] span",
                "h1[data-e2e='browse-video-desc']",
                "div[data-e2e='video-desc'] span",
                "[data-e2e='browse-video-desc']"
            ]
            
            for selector in description_selectors:
                desc_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if desc_elements:
                    return desc_elements[0].text.strip()
                    
            return ""
            
        except Exception:
            return ""
    
    def _extract_likes_count(self) -> int:
        """Extract likes count"""
        try:
            # Try multiple selectors for likes
            likes_selectors = [
                "button[data-e2e='browse-like-icon'] + span",
                "button[data-e2e='like-icon'] + span",
                "span[data-e2e='like-count']",
                "strong[data-e2e='like-count']"
            ]
            
            for selector in likes_selectors:
                likes_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if likes_elements:
                    text = likes_elements[0].text.strip()
                    return self._parse_count(text)
                    
            return 0
            
        except Exception:
            return 0
    
    def _extract_comments_count(self) -> int:
        """Extract comments count"""
        try:
            comments_selectors = [
                "button[data-e2e='browse-comment-icon'] + span",
                "button[data-e2e='comment-icon'] + span",
                "span[data-e2e='comment-count']",
                "strong[data-e2e='comment-count']"
            ]
            
            for selector in comments_selectors:
                comments_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if comments_elements:
                    text = comments_elements[0].text.strip()
                    return self._parse_count(text)
                    
            return 0
            
        except Exception:
            return 0
    
    def _extract_shares_count(self) -> int:
        """Extract shares count"""
        try:
            shares_selectors = [
                "button[data-e2e='browse-share-icon'] + span",
                "button[data-e2e='share-icon'] + span",
                "span[data-e2e='share-count']",
                "strong[data-e2e='share-count']"
            ]
            
            for selector in shares_selectors:
                shares_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if shares_elements:
                    text = shares_elements[0].text.strip()
                    return self._parse_count(text)
                    
            return 0
            
        except Exception:
            return 0
    
    def _extract_views_count(self) -> int:
        """Extract views count"""
        try:
            # Views are often displayed differently on TikTok
            views_selectors = [
                "strong[data-e2e='video-views']",
                "span[data-e2e='video-views']",
                "div[data-e2e='video-views']"
            ]
            
            for selector in views_selectors:
                views_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if views_elements:
                    text = views_elements[0].text.strip()
                    return self._parse_count(text)
            
            # Sometimes views are in the video metadata
            # Try to extract from page source as fallback
            page_source = self.driver.page_source
            views_match = re.search(r'"playCount":(\d+)', page_source)
            if views_match:
                return int(views_match.group(1))
                
            return 0
            
        except Exception:
            return 0
    
    def _parse_count(self, count_text: str) -> int:
        """Parse count text (e.g., '1.2K', '3.4M') to integer"""
        try:
            count_text = count_text.strip().upper()
            
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            elif 'B' in count_text:
                return int(float(count_text.replace('B', '')) * 1000000000)
            else:
                # Remove any non-digit characters except decimal point
                clean_text = re.sub(r'[^\d.]', '', count_text)
                return int(float(clean_text)) if clean_text else 0
                
        except (ValueError, TypeError):
            return 0
    
    def _extract_hashtags(self, description: str) -> List[str]:
        """Extract hashtags from description"""
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, description)
        return [tag.lower() for tag in hashtags]
    
    def _extract_upload_date(self) -> datetime:
        """Extract upload date"""
        try:
            # Try to find timestamp in page source
            page_source = self.driver.page_source
            
            # Look for createTime in JSON data
            create_time_match = re.search(r'"createTime":(\d+)', page_source)
            if create_time_match:
                timestamp = int(create_time_match.group(1))
                return datetime.fromtimestamp(timestamp)
            
            # Look for date elements
            date_selectors = [
                "span[data-e2e='browser-nickname'] + span",
                "time",
                "[datetime]"
            ]
            
            for selector in date_selectors:
                date_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if date_elements:
                    datetime_attr = date_elements[0].get_attribute('datetime')
                    if datetime_attr:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _extract_music_info(self) -> tuple[Optional[str], Optional[str]]:
        """Extract music title and artist"""
        try:
            music_selectors = [
                "div[data-e2e='browse-sound-name'] a",
                "a[data-e2e='music-title']",
                "h4[data-e2e='browse-sound-name']"
            ]
            
            for selector in music_selectors:
                music_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if music_elements:
                    music_text = music_elements[0].text.strip()
                    # Try to split artist and title
                    if ' - ' in music_text:
                        parts = music_text.split(' - ', 1)
                        return parts[1], parts[0]  # title, artist
                    else:
                        return music_text, None
                        
            return None, None
            
        except Exception:
            return None, None
    
    def _extract_video_url(self) -> Optional[str]:
        """Extract video source URL"""
        try:
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "video")
            if video_elements:
                return video_elements[0].get_attribute('src')
                
            return None
            
        except Exception:
            return None
    
    def _extract_duration(self) -> Optional[int]:
        """Extract video duration in seconds"""
        try:
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "video")
            if video_elements:
                duration = video_elements[0].get_attribute('duration')
                if duration:
                    return int(float(duration))
                    
            return None
            
        except Exception:
            return None
    
    def scrape_hashtag(self, hashtag: str, max_videos: int = 30) -> List[TikTokVideo]:
        """
        Scrape videos from a hashtag page
        
        Args:
            hashtag: Hashtag to scrape (without #)
            max_videos: Maximum number of videos to scrape
            
        Returns:
            List of TikTokVideo objects
        """
        videos = []
        hashtag = hashtag.lstrip('#')
        
        try:
            self.logger.info(f"Starting to scrape hashtag: #{hashtag}")
            
            if not self.driver:
                self.driver = self._setup_driver()
            
            # Navigate to hashtag page
            hashtag_url = f"https://www.tiktok.com/tag/{hashtag}"
            self.driver.get(hashtag_url)
            time.sleep(5)
            
            # Handle popups
            self._handle_popups()
            
            # Get video links
            video_links = self._get_video_links(max_videos)
            
            for i, video_url in enumerate(video_links[:max_videos]):
                try:
                    self.rate_limiter.wait()
                    
                    # Extract username from video URL
                    username = self._extract_username_from_url(video_url)
                    video = self._scrape_single_video(video_url, username)
                    
                    if video:
                        videos.append(video)
                        self.logger.info(f"Scraped hashtag video {i+1}/{len(video_links)}: {video.video_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping hashtag video {video_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping hashtag #{hashtag}: {str(e)}")
            
        return videos
    
    def _extract_username_from_url(self, video_url: str) -> str:
        """Extract username from video URL"""
        try:
            # TikTok URLs: https://www.tiktok.com/@username/video/1234567890
            username_match = re.search(r'/@([^/]+)/video/', video_url)
            if username_match:
                return username_match.group(1)
                
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()