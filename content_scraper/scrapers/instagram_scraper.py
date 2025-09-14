"""
Instagram content scraper using Instaloader and web scraping techniques
"""

import time
import re
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..models.content_models import InstagramPost, ScrapingSession
from ..utils.rate_limiter import RateLimiter
from ..utils.logger import get_logger


class InstagramScraper:
    """Instagram content scraper with rate limiting and error handling"""
    
    def __init__(self, headless: bool = True, rate_limit_delay: float = 2.0):
        """
        Initialize Instagram scraper
        
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.stylesheets": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(
            service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        return driver
    
    def scrape_account(self, username: str, max_posts: int = 50) -> List[InstagramPost]:
        """
        Scrape posts from an Instagram account
        
        Args:
            username: Instagram username (without @)
            max_posts: Maximum number of posts to scrape
            
        Returns:
            List of InstagramPost objects
        """
        posts = []
        session_id = f"ig_{username}_{int(time.time())}"
        scraping_session = ScrapingSession(session_id=session_id, platform="instagram")
        
        try:
            self.logger.info(f"Starting to scrape Instagram account: {username}")
            
            # Remove @ if present
            username = username.lstrip('@')
            
            # Setup driver
            if not self.driver:
                self.driver = self._setup_driver()
            
            # Navigate to user profile
            profile_url = f"https://www.instagram.com/{username}/"
            self.driver.get(profile_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Get post links
            post_links = self._get_post_links(max_posts)
            
            for i, post_url in enumerate(post_links[:max_posts]):
                try:
                    self.rate_limiter.wait()
                    post = self._scrape_single_post(post_url, username)
                    
                    if post:
                        posts.append(post)
                        scraping_session.total_posts_scraped += 1
                        self.logger.info(f"Scraped post {i+1}/{len(post_links)}: {post.post_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping post {post_url}: {str(e)}")
                    scraping_session.errors_count += 1
                    continue
            
            scraping_session.total_accounts_scraped = 1
            
        except Exception as e:
            self.logger.error(f"Error scraping account {username}: {str(e)}")
            scraping_session.errors_count += 1
            
        finally:
            scraping_session.finish_session()
            self.logger.info(f"Scraping session completed: {scraping_session.to_dict()}")
            
        return posts
    
    def _get_post_links(self, max_posts: int) -> List[str]:
        """Extract post links from profile page"""
        post_links = []
        
        try:
            # Scroll to load more posts
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(post_links) < max_posts:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Get current post links
                post_elements = self.driver.find_elements(By.CSS_SELECTOR, "article a[href*='/p/']")
                current_links = [elem.get_attribute('href') for elem in post_elements]
                
                # Check if new posts loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                    
                last_height = new_height
                post_links = list(set(current_links))  # Remove duplicates
                
                if len(post_links) >= max_posts:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error getting post links: {str(e)}")
            
        return post_links[:max_posts]
    
    def _scrape_single_post(self, post_url: str, username: str) -> Optional[InstagramPost]:
        """
        Scrape a single Instagram post
        
        Args:
            post_url: URL of the post
            username: Account username
            
        Returns:
            InstagramPost object or None if failed
        """
        try:
            self.driver.get(post_url)
            time.sleep(2)
            
            # Extract post ID from URL
            post_id = re.search(r'/p/([^/]+)/', post_url)
            if not post_id:
                return None
            post_id = post_id.group(1)
            
            # Get post type
            post_type = self._determine_post_type()
            
            # Get caption
            caption = self._extract_caption()
            
            # Get metrics
            likes_count = self._extract_likes_count()
            comments_count = self._extract_comments_count()
            views_count = self._extract_views_count() if post_type in ['video', 'reel'] else None
            
            # Get hashtags from caption
            hashtags = self._extract_hashtags(caption)
            
            # Get post date
            post_date = self._extract_post_date()
            
            # Get location
            location = self._extract_location()
            
            # Get media URL
            media_url = self._extract_media_url()
            
            return InstagramPost(
                post_id=post_id,
                username=username,
                post_type=post_type,
                caption=caption,
                likes_count=likes_count,
                comments_count=comments_count,
                views_count=views_count,
                post_date=post_date,
                hashtags=hashtags,
                location=location,
                media_url=media_url
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping post {post_url}: {str(e)}")
            return None
    
    def _determine_post_type(self) -> str:
        """Determine if post is photo, video, or reel"""
        try:
            # Check for video indicators
            video_elements = self.driver.find_elements(By.CSS_SELECTOR, "video")
            if video_elements:
                # Check if it's a reel
                if "reel" in self.driver.current_url:
                    return "reel"
                return "video"
            
            # Check for multiple images (carousel)
            carousel_indicators = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='carousel']")
            if carousel_indicators:
                return "carousel"
                
            return "photo"
            
        except Exception:
            return "photo"
    
    def _extract_caption(self) -> str:
        """Extract post caption"""
        try:
            # Try multiple selectors for caption
            caption_selectors = [
                "article div[data-testid='post-caption'] span",
                "article h1",
                "[data-testid='post-caption']",
                "article span[dir='auto']"
            ]
            
            for selector in caption_selectors:
                caption_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if caption_elements:
                    return caption_elements[0].text.strip()
                    
            return ""
            
        except Exception:
            return ""
    
    def _extract_likes_count(self) -> int:
        """Extract likes count"""
        try:
            # Try multiple selectors for likes
            likes_selectors = [
                "article button span[aria-label*='like']",
                "section button span",
                "[aria-label*='like'] span"
            ]
            
            for selector in likes_selectors:
                likes_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in likes_elements:
                    text = elem.text.strip()
                    if text and text.replace(',', '').isdigit():
                        return int(text.replace(',', ''))
                        
            return 0
            
        except Exception:
            return 0
    
    def _extract_comments_count(self) -> int:
        """Extract comments count"""
        try:
            comment_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "article section div span, article button span"
            )
            
            for elem in comment_elements:
                text = elem.text.strip()
                # Look for patterns like "View all 123 comments"
                comment_match = re.search(r'(\d+)\s*comment', text, re.IGNORECASE)
                if comment_match:
                    return int(comment_match.group(1))
                    
            return 0
            
        except Exception:
            return 0
    
    def _extract_views_count(self) -> Optional[int]:
        """Extract views count for videos"""
        try:
            view_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "span[aria-label*='view'], span:contains('views')"
            )
            
            for elem in view_elements:
                text = elem.text.strip()
                view_match = re.search(r'([\d,]+)\s*view', text, re.IGNORECASE)
                if view_match:
                    return int(view_match.group(1).replace(',', ''))
                    
            return None
            
        except Exception:
            return None
    
    def _extract_hashtags(self, caption: str) -> List[str]:
        """Extract hashtags from caption"""
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, caption)
        return [tag.lower() for tag in hashtags]
    
    def _extract_post_date(self) -> datetime:
        """Extract post date"""
        try:
            time_elements = self.driver.find_elements(By.CSS_SELECTOR, "time")
            if time_elements:
                datetime_attr = time_elements[0].get_attribute('datetime')
                if datetime_attr:
                    return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _extract_location(self) -> Optional[str]:
        """Extract post location"""
        try:
            location_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "article header div a[href*='/locations/']"
            )
            
            if location_elements:
                return location_elements[0].text.strip()
                
            return None
            
        except Exception:
            return None
    
    def _extract_media_url(self) -> Optional[str]:
        """Extract media URL"""
        try:
            # Try to get image/video URL
            media_elements = self.driver.find_elements(By.CSS_SELECTOR, "article img, article video")
            if media_elements:
                return media_elements[0].get_attribute('src')
                
            return None
            
        except Exception:
            return None
    
    def scrape_hashtag(self, hashtag: str, max_posts: int = 30) -> List[InstagramPost]:
        """
        Scrape posts from a hashtag page
        
        Args:
            hashtag: Hashtag to scrape (without #)
            max_posts: Maximum number of posts to scrape
            
        Returns:
            List of InstagramPost objects
        """
        posts = []
        hashtag = hashtag.lstrip('#')
        
        try:
            self.logger.info(f"Starting to scrape hashtag: #{hashtag}")
            
            if not self.driver:
                self.driver = self._setup_driver()
            
            # Navigate to hashtag page
            hashtag_url = f"https://www.instagram.com/explore/tags/{hashtag}/"
            self.driver.get(hashtag_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            
            # Get post links
            post_links = self._get_post_links(max_posts)
            
            for i, post_url in enumerate(post_links[:max_posts]):
                try:
                    self.rate_limiter.wait()
                    
                    # Extract username from post URL
                    username = self._extract_username_from_url(post_url)
                    post = self._scrape_single_post(post_url, username)
                    
                    if post:
                        posts.append(post)
                        self.logger.info(f"Scraped hashtag post {i+1}/{len(post_links)}: {post.post_id}")
                    
                except Exception as e:
                    self.logger.error(f"Error scraping hashtag post {post_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error scraping hashtag #{hashtag}: {str(e)}")
            
        return posts
    
    def _extract_username_from_url(self, post_url: str) -> str:
        """Extract username from post URL by visiting the post page"""
        try:
            self.driver.get(post_url)
            time.sleep(1)
            
            # Look for username in profile link
            username_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "article header a[href^='/']"
            )
            
            if username_elements:
                href = username_elements[0].get_attribute('href')
                username = href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]
                return username
                
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