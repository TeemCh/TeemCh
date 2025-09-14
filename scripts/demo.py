#!/usr/bin/env python3
"""
Demo script to showcase the content scraping architecture
This demonstrates the key features without requiring actual credentials
"""

import sys
import os
from datetime import datetime, timedelta
import json
import random

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_scraper.models.content_models import InstagramPost, TikTokVideo, ScrapingSession
from content_scraper.utils.rate_limiter import RateLimiter, AdaptiveRateLimiter
from content_scraper.utils.logger import get_logger, ScrapeLogger
from content_scraper.config.settings import AppConfig, ConfigManager


def create_sample_instagram_posts(num_posts=10):
    """Create sample Instagram posts for demonstration"""
    posts = []
    
    sample_usernames = ["creator1", "influencer2", "artist3", "brand4", "trendsetter5"]
    sample_hashtags = ["#viral", "#trending", "#content", "#creative", "#inspiration"]
    sample_captions = [
        "Amazing sunset today! 🌅",
        "New project coming soon...",
        "Behind the scenes content",
        "Grateful for this moment ✨",
        "Creating something special"
    ]
    
    for i in range(num_posts):
        post = InstagramPost(
            post_id=f"ig_post_{i+1}_{random.randint(1000, 9999)}",
            username=random.choice(sample_usernames),
            post_type=random.choice(["photo", "video", "reel"]),
            caption=f"{random.choice(sample_captions)} {' '.join(random.sample(sample_hashtags, 2))}",
            likes_count=random.randint(50, 5000),
            comments_count=random.randint(5, 500),
            views_count=random.randint(1000, 50000) if random.random() > 0.3 else None,
            post_date=datetime.now() - timedelta(days=random.randint(0, 30)),
            hashtags=random.sample(sample_hashtags, random.randint(1, 3)),
            location="Sample Location" if random.random() > 0.5 else None
        )
        posts.append(post)
    
    return posts


def create_sample_tiktok_videos(num_videos=10):
    """Create sample TikTok videos for demonstration"""
    videos = []
    
    sample_usernames = ["tiktoker1", "dancer2", "comedian3", "educator4", "creator5"]
    sample_hashtags = ["#fyp", "#viral", "#trending", "#funny", "#educational"]
    sample_descriptions = [
        "Dance challenge time! 💃",
        "Quick tutorial for you",
        "Can't believe this happened",
        "Day in my life",
        "You have to try this!"
    ]
    sample_music = [
        ("Popular Song", "Artist Name"),
        ("Trending Audio", "Various Artists"),
        ("Original Sound", "Creator"),
        ("Dance Track", "DJ Name"),
        ("Viral Audio", "Unknown")
    ]
    
    for i in range(num_videos):
        music_title, music_artist = random.choice(sample_music)
        
        video = TikTokVideo(
            video_id=f"tt_video_{i+1}_{random.randint(10000, 99999)}",
            username=random.choice(sample_usernames),
            description=f"{random.choice(sample_descriptions)} {' '.join(random.sample(sample_hashtags, 2))}",
            likes_count=random.randint(100, 50000),
            comments_count=random.randint(10, 5000),
            shares_count=random.randint(5, 1000),
            views_count=random.randint(10000, 1000000),
            upload_date=datetime.now() - timedelta(days=random.randint(0, 30)),
            hashtags=random.sample(sample_hashtags, random.randint(1, 4)),
            music_title=music_title,
            music_artist=music_artist,
            duration_seconds=random.randint(15, 60)
        )
        videos.append(video)
    
    return videos


def demo_data_models():
    """Demonstrate data models functionality"""
    print("🎭 Data Models Demo")
    print("=" * 50)
    
    # Create sample data
    ig_posts = create_sample_instagram_posts(3)
    tiktok_videos = create_sample_tiktok_videos(3)
    
    print("\n📸 Instagram Posts:")
    for post in ig_posts:
        print(f"  📝 {post.post_id} by @{post.username}")
        print(f"      Type: {post.post_type} | Likes: {post.likes_count} | Comments: {post.comments_count}")
        engagement_str = f"{post.engagement_rate:.4f}" if post.engagement_rate is not None else "N/A"
        print(f"      Engagement Rate: {engagement_str}")
        print(f"      Hashtags: {', '.join(post.hashtags[:3])}")
        print()
    
    print("🎵 TikTok Videos:")
    for video in tiktok_videos:
        print(f"  📹 {video.video_id} by @{video.username}")
        print(f"      Views: {video.views_count:,} | Likes: {video.likes_count:,} | Shares: {video.shares_count}")
        print(f"      Engagement Rate: {video.engagement_rate:.4f}")
        print(f"      Music: {video.music_title} by {video.music_artist}")
        print()
    
    return ig_posts, tiktok_videos


def demo_rate_limiting():
    """Demonstrate rate limiting functionality"""
    print("⏱️  Rate Limiting Demo")
    print("=" * 50)
    
    # Basic rate limiter
    print("\n🔄 Basic Rate Limiter (0.5s delay):")
    limiter = RateLimiter(delay=0.5)
    
    start_time = datetime.now()
    for i in range(3):
        limiter.wait()
        print(f"  Request {i+1} completed at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    duration = (datetime.now() - start_time).total_seconds()
    print(f"  Total time: {duration:.2f}s")
    
    # Adaptive rate limiter
    print("\n🧠 Adaptive Rate Limiter:")
    adaptive_limiter = AdaptiveRateLimiter(initial_delay=0.2)
    
    # Simulate some successes and failures
    for i in range(3):
        adaptive_limiter.wait()
        if random.random() > 0.3:  # 70% success rate
            adaptive_limiter.on_success()
            print(f"  ✅ Request {i+1} succeeded | Current delay: {adaptive_limiter.base_delay:.2f}s")
        else:
            adaptive_limiter.on_failure()
            print(f"  ❌ Request {i+1} failed | Current delay: {adaptive_limiter.base_delay:.2f}s")
    
    stats = adaptive_limiter.get_stats()
    print(f"  📊 Final stats: {stats['success_count']}/{stats['total_requests']} success rate")


def demo_logging():
    """Demonstrate logging functionality"""
    print("\n📝 Logging Demo")
    print("=" * 50)
    
    logger = get_logger("demo_logger")
    
    # Regular logging
    logger.info("Starting demo logging session")
    logger.warning("This is a warning message")
    logger.error("This is an error message (for demo purposes)")
    
    # Context manager logging
    with ScrapeLogger("demo_session", "instagram") as session_logger:
        session_logger.log_progress("Processing account @demo_user")
        session_logger.log_progress("Found 25 posts to scrape")
        session_logger.log_warning("Rate limit approaching, slowing down")
        session_logger.log_progress("Completed scraping for @demo_user")
    
    print("  ✅ Check the logs/ directory for detailed log files")


def demo_configuration():
    """Demonstrate configuration management"""
    print("\n⚙️  Configuration Demo")
    print("=" * 50)
    
    # Create config manager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    print(f"  📋 Current configuration:")
    print(f"     Environment: {config.environment}")
    print(f"     Log Level: {config.log_level}")
    print(f"     Max Posts per Account: {config.scraping.max_posts_per_account}")
    print(f"     Rate Limit Delay: {config.scraping.rate_limit_delay}s")
    print(f"     Headless Browser: {config.scraping.headless_browser}")
    print(f"     Google Sheets Auto-create: {config.google_sheets.auto_create_spreadsheet}")
    
    print(f"\n  🎯 Configured accounts to track:")
    print(f"     Instagram: {len(config.accounts.instagram_accounts)} accounts, {len(config.accounts.instagram_hashtags)} hashtags")
    print(f"     TikTok: {len(config.accounts.tiktok_accounts)} accounts, {len(config.accounts.tiktok_hashtags)} hashtags")


def demo_session_tracking():
    """Demonstrate scraping session tracking"""
    print("\n📊 Session Tracking Demo")
    print("=" * 50)
    
    # Create sample sessions
    ig_session = ScrapingSession(
        session_id="demo_ig_session_001",
        platform="instagram"
    )
    
    # Simulate scraping activity
    ig_session.total_accounts_scraped = 3
    ig_session.total_posts_scraped = 45
    ig_session.errors_count = 2
    ig_session.finish_session()
    
    tiktok_session = ScrapingSession(
        session_id="demo_tt_session_001", 
        platform="tiktok"
    )
    
    tiktok_session.total_accounts_scraped = 2
    tiktok_session.total_posts_scraped = 30
    tiktok_session.errors_count = 1
    tiktok_session.finish_session()
    
    print(f"  📸 Instagram Session:")
    print(f"     Session ID: {ig_session.session_id}")
    print(f"     Duration: {(ig_session.end_time - ig_session.start_time).total_seconds():.2f}s")
    print(f"     Posts Scraped: {ig_session.total_posts_scraped}")
    print(f"     Success Rate: {ig_session.success_rate:.2%}")
    
    print(f"\n  🎵 TikTok Session:")
    print(f"     Session ID: {tiktok_session.session_id}")
    print(f"     Duration: {(tiktok_session.end_time - tiktok_session.start_time).total_seconds():.2f}s")
    print(f"     Videos Scraped: {tiktok_session.total_posts_scraped}")
    print(f"     Success Rate: {tiktok_session.success_rate:.2%}")


def demo_data_export():
    """Demonstrate data export functionality"""
    print("\n💾 Data Export Demo")
    print("=" * 50)
    
    # Create sample data
    ig_posts = create_sample_instagram_posts(2)
    tiktok_videos = create_sample_tiktok_videos(2)
    
    print("  📸 Instagram Data Structure:")
    for i, post in enumerate(ig_posts[:1]):  # Show just one for brevity
        data = post.to_dict()
        print(f"     Post {i+1} fields:")
        for key, value in data.items():
            if len(str(value)) > 50:
                value = str(value)[:47] + "..."
            print(f"       {key}: {value}")
    
    print("\n  🎵 TikTok Data Structure:")
    for i, video in enumerate(tiktok_videos[:1]):  # Show just one for brevity
        data = video.to_dict()
        print(f"     Video {i+1} fields:")
        for key, value in data.items():
            if len(str(value)) > 50:
                value = str(value)[:47] + "..."
            print(f"       {key}: {value}")


def main():
    """Main demo function"""
    print("🚀 Content Scraping Architecture Demo")
    print("=" * 80)
    print("This demo showcases the key features of the content scraping system")
    print("without requiring actual social media credentials or API access.")
    print("=" * 80)
    
    try:
        # Run all demos
        ig_posts, tiktok_videos = demo_data_models()
        demo_rate_limiting()
        demo_logging()
        demo_configuration()
        demo_session_tracking()
        demo_data_export()
        
        print("\n🎉 Demo Complete!")
        print("=" * 50)
        print("✅ All core components demonstrated successfully")
        print("\n📚 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Setup Google Sheets: python scripts/setup_credentials.py") 
        print("3. Configure accounts: edit config/accounts.json")
        print("4. Run scraper: python scripts/run_scraper.py")
        print("\n📖 See README.md for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()