"""
Data models for content scraped from social media platforms
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class InstagramPost:
    """Instagram post data model"""
    post_id: str
    username: str
    post_type: str  # photo, video, reel, story
    caption: str
    likes_count: int
    comments_count: int
    views_count: Optional[int] = None
    post_date: datetime = field(default_factory=datetime.now)
    hashtags: List[str] = field(default_factory=list)
    location: Optional[str] = None
    media_url: Optional[str] = None
    engagement_rate: Optional[float] = None
    
    def __post_init__(self):
        """Calculate engagement rate after initialization"""
        if self.views_count and self.views_count > 0:
            self.engagement_rate = (self.likes_count + self.comments_count) / self.views_count
        elif self.likes_count > 0:
            # Estimate based on likes if views not available
            self.engagement_rate = self.comments_count / self.likes_count if self.likes_count > 0 else 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'post_id': self.post_id,
            'username': self.username,
            'post_type': self.post_type,
            'caption': self.caption,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'views_count': self.views_count,
            'post_date': self.post_date.isoformat(),
            'hashtags': ','.join(self.hashtags),
            'location': self.location,
            'media_url': self.media_url,
            'engagement_rate': self.engagement_rate,
            'scraped_at': datetime.now().isoformat()
        }


@dataclass
class TikTokVideo:
    """TikTok video data model"""
    video_id: str
    username: str
    description: str
    likes_count: int
    comments_count: int
    shares_count: int
    views_count: int
    upload_date: datetime = field(default_factory=datetime.now)
    hashtags: List[str] = field(default_factory=list)
    music_title: Optional[str] = None
    music_artist: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    engagement_rate: Optional[float] = None
    
    def __post_init__(self):
        """Calculate engagement rate after initialization"""
        if self.views_count > 0:
            total_engagements = self.likes_count + self.comments_count + self.shares_count
            self.engagement_rate = total_engagements / self.views_count
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        return {
            'video_id': self.video_id,
            'username': self.username,
            'description': self.description,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'views_count': self.views_count,
            'upload_date': self.upload_date.isoformat(),
            'hashtags': ','.join(self.hashtags),
            'music_title': self.music_title,
            'music_artist': self.music_artist,
            'video_url': self.video_url,
            'duration_seconds': self.duration_seconds,
            'engagement_rate': self.engagement_rate,
            'scraped_at': datetime.now().isoformat()
        }


@dataclass
class ScrapingSession:
    """Track scraping session metadata"""
    session_id: str
    platform: str  # instagram, tiktok
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_posts_scraped: int = 0
    total_accounts_scraped: int = 0
    errors_count: int = 0
    success_rate: Optional[float] = None
    
    def finish_session(self):
        """Mark session as finished"""
        self.end_time = datetime.now()
        if self.total_posts_scraped > 0:
            self.success_rate = (self.total_posts_scraped - self.errors_count) / self.total_posts_scraped
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging"""
        return {
            'session_id': self.session_id,
            'platform': self.platform,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_posts_scraped': self.total_posts_scraped,
            'total_accounts_scraped': self.total_accounts_scraped,
            'errors_count': self.errors_count,
            'success_rate': self.success_rate
        }