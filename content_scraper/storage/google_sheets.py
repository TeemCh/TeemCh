"""
Google Sheets integration for storing scraped content data
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..models.content_models import InstagramPost, TikTokVideo
from ..utils.logger import get_logger


class GoogleSheetsStorage:
    """Google Sheets storage for scraped content data"""
    
    def __init__(self, credentials_path: str = "config/credentials.json", 
                 spreadsheet_id: Optional[str] = None):
        """
        Initialize Google Sheets storage
        
        Args:
            credentials_path: Path to Google service account credentials JSON
            spreadsheet_id: Google Sheets spreadsheet ID (optional, can be set later)
        """
        self.logger = get_logger(__name__)
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        
        # Sheet names for different content types
        self.instagram_sheet_name = "Instagram Content"
        self.tiktok_sheet_name = "TikTok Content"
        self.analytics_sheet_name = "Analytics Summary"
        
        self._setup_service()
    
    def _setup_service(self):
        """Setup Google Sheets API service"""
        try:
            if not os.path.exists(self.credentials_path):
                self.logger.error(f"Credentials file not found: {self.credentials_path}")
                return
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build service
            self.service = build('sheets', 'v4', credentials=credentials)
            self.logger.info("Google Sheets service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error setting up Google Sheets service: {str(e)}")
    
    def set_spreadsheet_id(self, spreadsheet_id: str):
        """Set the spreadsheet ID to work with"""
        self.spreadsheet_id = spreadsheet_id
        self.logger.info(f"Spreadsheet ID set to: {spreadsheet_id}")
    
    def create_spreadsheet(self, title: str = "Content Scraping Data") -> str:
        """
        Create a new spreadsheet with proper structure
        
        Args:
            title: Title for the new spreadsheet
            
        Returns:
            Spreadsheet ID
        """
        try:
            if not self.service:
                self.logger.error("Google Sheets service not initialized")
                return None
            
            # Create spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': title
                },
                'sheets': [
                    {
                        'properties': {
                            'title': self.instagram_sheet_name
                        }
                    },
                    {
                        'properties': {
                            'title': self.tiktok_sheet_name
                        }
                    },
                    {
                        'properties': {
                            'title': self.analytics_sheet_name
                        }
                    }
                ]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet_body).execute()
            spreadsheet_id = result['spreadsheetId']
            
            self.logger.info(f"Created new spreadsheet: {spreadsheet_id}")
            
            # Setup headers
            self.spreadsheet_id = spreadsheet_id
            self._setup_instagram_headers()
            self._setup_tiktok_headers()
            self._setup_analytics_headers()
            
            return spreadsheet_id
            
        except HttpError as e:
            self.logger.error(f"Error creating spreadsheet: {str(e)}")
            return None
    
    def _setup_instagram_headers(self):
        """Setup headers for Instagram sheet"""
        headers = [
            "Post ID", "Username", "Post Type", "Caption", "Likes Count",
            "Comments Count", "Views Count", "Post Date", "Hashtags",
            "Location", "Media URL", "Engagement Rate", "Scraped At"
        ]
        
        self._write_headers(self.instagram_sheet_name, headers)
    
    def _setup_tiktok_headers(self):
        """Setup headers for TikTok sheet"""
        headers = [
            "Video ID", "Username", "Description", "Likes Count",
            "Comments Count", "Shares Count", "Views Count", "Upload Date",
            "Hashtags", "Music Title", "Music Artist", "Video URL",
            "Duration (seconds)", "Engagement Rate", "Scraped At"
        ]
        
        self._write_headers(self.tiktok_sheet_name, headers)
    
    def _setup_analytics_headers(self):
        """Setup headers for Analytics sheet"""
        headers = [
            "Date", "Platform", "Total Posts", "Total Likes", "Total Comments",
            "Total Views", "Average Engagement Rate", "Top Hashtags",
            "Top Performing Post", "Scraping Sessions"
        ]
        
        self._write_headers(self.analytics_sheet_name, headers)
    
    def _write_headers(self, sheet_name: str, headers: List[str]):
        """Write headers to a sheet"""
        try:
            range_name = f"{sheet_name}!A1:{chr(65 + len(headers) - 1)}1"
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Format headers (bold)
            self._format_headers(sheet_name, len(headers))
            
            self.logger.info(f"Headers set for {sheet_name}")
            
        except HttpError as e:
            self.logger.error(f"Error writing headers to {sheet_name}: {str(e)}")
    
    def _format_headers(self, sheet_name: str, num_columns: int):
        """Format header row as bold"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in sheet_metadata['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                return
            
            # Format request
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_columns
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold'
                }
            }]
            
            body = {'requests': requests}
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
        except HttpError as e:
            self.logger.error(f"Error formatting headers: {str(e)}")
    
    def save_instagram_data(self, posts: List[InstagramPost]):
        """
        Save Instagram posts to Google Sheets
        
        Args:
            posts: List of InstagramPost objects
        """
        if not posts:
            self.logger.warning("No Instagram posts to save")
            return
        
        try:
            # Convert posts to rows
            rows = []
            for post in posts:
                post_data = post.to_dict()
                row = [
                    post_data['post_id'],
                    post_data['username'],
                    post_data['post_type'],
                    post_data['caption'][:500] if post_data['caption'] else '',  # Limit caption length
                    post_data['likes_count'],
                    post_data['comments_count'],
                    post_data['views_count'] or '',
                    post_data['post_date'],
                    post_data['hashtags'],
                    post_data['location'] or '',
                    post_data['media_url'] or '',
                    post_data['engagement_rate'] or '',
                    post_data['scraped_at']
                ]
                rows.append(row)
            
            # Append to sheet
            self._append_rows(self.instagram_sheet_name, rows)
            
            self.logger.info(f"Saved {len(posts)} Instagram posts to Google Sheets")
            
        except Exception as e:
            self.logger.error(f"Error saving Instagram data: {str(e)}")
    
    def save_tiktok_data(self, videos: List[TikTokVideo]):
        """
        Save TikTok videos to Google Sheets
        
        Args:
            videos: List of TikTokVideo objects
        """
        if not videos:
            self.logger.warning("No TikTok videos to save")
            return
        
        try:
            # Convert videos to rows
            rows = []
            for video in videos:
                video_data = video.to_dict()
                row = [
                    video_data['video_id'],
                    video_data['username'],
                    video_data['description'][:500] if video_data['description'] else '',  # Limit description length
                    video_data['likes_count'],
                    video_data['comments_count'],
                    video_data['shares_count'],
                    video_data['views_count'],
                    video_data['upload_date'],
                    video_data['hashtags'],
                    video_data['music_title'] or '',
                    video_data['music_artist'] or '',
                    video_data['video_url'] or '',
                    video_data['duration_seconds'] or '',
                    video_data['engagement_rate'] or '',
                    video_data['scraped_at']
                ]
                rows.append(row)
            
            # Append to sheet
            self._append_rows(self.tiktok_sheet_name, rows)
            
            self.logger.info(f"Saved {len(videos)} TikTok videos to Google Sheets")
            
        except Exception as e:
            self.logger.error(f"Error saving TikTok data: {str(e)}")
    
    def _append_rows(self, sheet_name: str, rows: List[List]):
        """Append rows to a sheet"""
        try:
            range_name = f"{sheet_name}!A:Z"
            
            body = {
                'values': rows
            }
            
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
        except HttpError as e:
            self.logger.error(f"Error appending rows to {sheet_name}: {str(e)}")
    
    def get_existing_data(self, sheet_name: str) -> pd.DataFrame:
        """
        Get existing data from a sheet
        
        Args:
            sheet_name: Name of the sheet to read
            
        Returns:
            DataFrame with existing data
        """
        try:
            range_name = f"{sheet_name}!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
            
        except HttpError as e:
            self.logger.error(f"Error reading data from {sheet_name}: {str(e)}")
            return pd.DataFrame()
    
    def update_analytics_summary(self):
        """Update analytics summary sheet with aggregated data"""
        try:
            # Get Instagram data
            ig_df = self.get_existing_data(self.instagram_sheet_name)
            
            # Get TikTok data
            tt_df = self.get_existing_data(self.tiktok_sheet_name)
            
            # Calculate analytics
            today = datetime.now().strftime('%Y-%m-%d')
            
            analytics_rows = []
            
            # Instagram analytics
            if not ig_df.empty:
                ig_analytics = self._calculate_platform_analytics(ig_df, 'Instagram')
                analytics_rows.append([today, 'Instagram'] + ig_analytics)
            
            # TikTok analytics
            if not tt_df.empty:
                tt_analytics = self._calculate_platform_analytics(tt_df, 'TikTok')
                analytics_rows.append([today, 'TikTok'] + tt_analytics)
            
            if analytics_rows:
                # Clear existing data and write new analytics
                self._clear_sheet_data(self.analytics_sheet_name)
                self._setup_analytics_headers()
                self._append_rows(self.analytics_sheet_name, analytics_rows)
                
                self.logger.info("Analytics summary updated")
            
        except Exception as e:
            self.logger.error(f"Error updating analytics summary: {str(e)}")
    
    def _calculate_platform_analytics(self, df: pd.DataFrame, platform: str) -> List:
        """Calculate analytics for a platform"""
        try:
            total_posts = len(df)
            
            # Convert numeric columns
            likes_col = 'Likes Count' if 'Likes Count' in df.columns else 'likes_count'
            comments_col = 'Comments Count' if 'Comments Count' in df.columns else 'comments_count'
            views_col = 'Views Count' if 'Views Count' in df.columns else 'views_count'
            
            total_likes = pd.to_numeric(df[likes_col], errors='coerce').sum()
            total_comments = pd.to_numeric(df[comments_col], errors='coerce').sum()
            total_views = pd.to_numeric(df[views_col], errors='coerce').sum()
            
            # Calculate average engagement rate
            engagement_col = 'Engagement Rate' if 'Engagement Rate' in df.columns else 'engagement_rate'
            avg_engagement = pd.to_numeric(df[engagement_col], errors='coerce').mean()
            
            # Get top hashtags
            hashtags_col = 'Hashtags' if 'Hashtags' in df.columns else 'hashtags'
            all_hashtags = []
            for hashtags_str in df[hashtags_col].dropna():
                if hashtags_str:
                    all_hashtags.extend(hashtags_str.split(','))
            
            # Count hashtag frequency
            hashtag_counts = pd.Series(all_hashtags).value_counts()
            top_hashtags = ', '.join(hashtag_counts.head(5).index.tolist())
            
            # Get top performing post
            if platform == 'Instagram':
                top_post_idx = pd.to_numeric(df[likes_col], errors='coerce').idxmax()
                top_post = df.iloc[top_post_idx]['Post ID'] if not pd.isna(top_post_idx) else 'N/A'
            else:
                top_post_idx = pd.to_numeric(df[views_col], errors='coerce').idxmax()
                top_post = df.iloc[top_post_idx]['Video ID'] if not pd.isna(top_post_idx) else 'N/A'
            
            return [
                total_posts,
                int(total_likes) if not pd.isna(total_likes) else 0,
                int(total_comments) if not pd.isna(total_comments) else 0,
                int(total_views) if not pd.isna(total_views) else 0,
                f"{avg_engagement:.4f}" if not pd.isna(avg_engagement) else '0',
                top_hashtags,
                top_post,
                1  # Number of scraping sessions (simplified)
            ]
            
        except Exception as e:
            self.logger.error(f"Error calculating analytics for {platform}: {str(e)}")
            return [0, 0, 0, 0, '0', '', 'N/A', 0]
    
    def _clear_sheet_data(self, sheet_name: str):
        """Clear all data from a sheet except headers"""
        try:
            range_name = f"{sheet_name}!A2:Z1000"
            
            body = {
                'values': []
            }
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                body=body
            ).execute()
            
        except HttpError as e:
            self.logger.error(f"Error clearing sheet {sheet_name}: {str(e)}")
    
    def get_spreadsheet_url(self) -> str:
        """Get the URL to access the spreadsheet"""
        if self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        return "Spreadsheet ID not set"