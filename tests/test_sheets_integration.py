"""
Tests for Google Sheets integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import tempfile
import os
import json

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_scraper.storage import GoogleSheetsStorage
from content_scraper.models import InstagramPost, TikTokVideo


class TestGoogleSheetsStorage(unittest.TestCase):
    """Test Google Sheets storage functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        # Create a temporary credentials file
        self.temp_creds = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        creds_data = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
            "client_email": "test@test-project.iam.gserviceaccount.com",
            "client_id": "test-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        json.dump(creds_data, self.temp_creds)
        self.temp_creds.close()
        
        # Mock the Google API service
        self.mock_service = Mock()
        
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary credentials file
        os.unlink(self.temp_creds.name)
    
    @patch('content_scraper.storage.google_sheets.build')
    @patch('content_scraper.storage.google_sheets.service_account')
    def test_storage_initialization(self, mock_service_account, mock_build):
        """Test Google Sheets storage initialization"""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        mock_build.return_value = self.mock_service
        
        storage = GoogleSheetsStorage(
            credentials_path=self.temp_creds.name,
            spreadsheet_id="test_spreadsheet_id"
        )
        
        self.assertIsNotNone(storage)
        self.assertEqual(storage.spreadsheet_id, "test_spreadsheet_id")
        mock_service_account.Credentials.from_service_account_file.assert_called_once()
        mock_build.assert_called_once()
    
    @patch('content_scraper.storage.google_sheets.build')
    @patch('content_scraper.storage.google_sheets.service_account')
    def test_create_spreadsheet(self, mock_service_account, mock_build):
        """Test spreadsheet creation"""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        # Mock the spreadsheet creation response
        mock_create_response = {'spreadsheetId': 'new_test_id'}
        mock_spreadsheets = Mock()
        mock_spreadsheets.create.return_value.execute.return_value = mock_create_response
        
        self.mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_build.return_value = self.mock_service
        
        storage = GoogleSheetsStorage(credentials_path=self.temp_creds.name)
        
        # Mock the batch update for formatting
        mock_spreadsheets.batchUpdate.return_value.execute.return_value = {}
        mock_spreadsheets.get.return_value.execute.return_value = {
            'sheets': [
                {'properties': {'title': 'Instagram Content', 'sheetId': 0}},
                {'properties': {'title': 'TikTok Content', 'sheetId': 1}},
                {'properties': {'title': 'Analytics Summary', 'sheetId': 2}}
            ]
        }
        
        # Mock the values update for headers
        mock_values = Mock()
        mock_values.update.return_value.execute.return_value = {}
        mock_spreadsheets.values.return_value = mock_values
        
        spreadsheet_id = storage.create_spreadsheet("Test Spreadsheet")
        
        self.assertEqual(spreadsheet_id, 'new_test_id')
        mock_spreadsheets.create.assert_called_once()
    
    def test_instagram_post_data_conversion(self):
        """Test Instagram post data conversion"""
        post = InstagramPost(
            post_id="test_123",
            username="testuser",
            post_type="photo",
            caption="Test caption with #hashtag",
            likes_count=100,
            comments_count=10,
            views_count=1000
        )
        
        # Test the to_dict method which is used for Google Sheets
        post_data = post.to_dict()
        
        self.assertIn('post_id', post_data)
        self.assertIn('username', post_data)
        self.assertIn('post_type', post_data)
        self.assertIn('caption', post_data)
        self.assertIn('likes_count', post_data)
        self.assertIn('engagement_rate', post_data)
        self.assertIn('scraped_at', post_data)
    
    def test_tiktok_video_data_conversion(self):
        """Test TikTok video data conversion"""
        video = TikTokVideo(
            video_id="test_456",
            username="testuser",
            description="Test description with #fyp",
            likes_count=500,
            comments_count=50,
            shares_count=25,
            views_count=10000
        )
        
        # Test the to_dict method which is used for Google Sheets
        video_data = video.to_dict()
        
        self.assertIn('video_id', video_data)
        self.assertIn('username', video_data)
        self.assertIn('description', video_data)
        self.assertIn('likes_count', video_data)
        self.assertIn('comments_count', video_data)
        self.assertIn('shares_count', video_data)
        self.assertIn('views_count', video_data)
        self.assertIn('engagement_rate', video_data)
        self.assertIn('scraped_at', video_data)
    
    @patch('content_scraper.storage.google_sheets.build')
    @patch('content_scraper.storage.google_sheets.service_account')
    def test_save_instagram_data(self, mock_service_account, mock_build):
        """Test saving Instagram data to sheets"""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        # Mock the values append response
        mock_values = Mock()
        mock_values.append.return_value.execute.return_value = {}
        
        mock_spreadsheets = Mock()
        mock_spreadsheets.values.return_value = mock_values
        
        self.mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_build.return_value = self.mock_service
        
        storage = GoogleSheetsStorage(
            credentials_path=self.temp_creds.name,
            spreadsheet_id="test_id"
        )
        
        # Create test posts
        posts = [
            InstagramPost(
                post_id="test_1",
                username="user1",
                post_type="photo",
                caption="Test caption 1",
                likes_count=100,
                comments_count=10
            ),
            InstagramPost(
                post_id="test_2", 
                username="user2",
                post_type="video",
                caption="Test caption 2",
                likes_count=200,
                comments_count=20
            )
        ]
        
        storage.save_instagram_data(posts)
        
        # Verify that append was called
        mock_values.append.assert_called_once()
    
    @patch('content_scraper.storage.google_sheets.build')
    @patch('content_scraper.storage.google_sheets.service_account')
    def test_save_tiktok_data(self, mock_service_account, mock_build):
        """Test saving TikTok data to sheets"""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        # Mock the values append response
        mock_values = Mock()
        mock_values.append.return_value.execute.return_value = {}
        
        mock_spreadsheets = Mock()
        mock_spreadsheets.values.return_value = mock_values
        
        self.mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_build.return_value = self.mock_service
        
        storage = GoogleSheetsStorage(
            credentials_path=self.temp_creds.name,
            spreadsheet_id="test_id"
        )
        
        # Create test videos
        videos = [
            TikTokVideo(
                video_id="test_1",
                username="user1",
                description="Test description 1",
                likes_count=500,
                comments_count=50,
                shares_count=25,
                views_count=10000
            ),
            TikTokVideo(
                video_id="test_2",
                username="user2", 
                description="Test description 2",
                likes_count=1000,
                comments_count=100,
                shares_count=50,
                views_count=20000
            )
        ]
        
        storage.save_tiktok_data(videos)
        
        # Verify that append was called
        mock_values.append.assert_called_once()
    
    def test_spreadsheet_url_generation(self):
        """Test spreadsheet URL generation"""
        storage = GoogleSheetsStorage(
            credentials_path=self.temp_creds.name,
            spreadsheet_id="test_spreadsheet_123"
        )
        
        expected_url = "https://docs.google.com/spreadsheets/d/test_spreadsheet_123/edit"
        actual_url = storage.get_spreadsheet_url()
        
        self.assertEqual(actual_url, expected_url)
    
    def test_spreadsheet_url_without_id(self):
        """Test spreadsheet URL generation without ID"""
        storage = GoogleSheetsStorage(credentials_path=self.temp_creds.name)
        
        url = storage.get_spreadsheet_url()
        
        self.assertEqual(url, "Spreadsheet ID not set")
    
    @patch('content_scraper.storage.google_sheets.build')
    @patch('content_scraper.storage.google_sheets.service_account') 
    def test_get_existing_data(self, mock_service_account, mock_build):
        """Test getting existing data from sheets"""
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        # Mock the values get response
        mock_response = {
            'values': [
                ['Post ID', 'Username', 'Likes'],  # Headers
                ['123', 'user1', '100'],
                ['456', 'user2', '200']
            ]
        }
        
        mock_values = Mock()
        mock_values.get.return_value.execute.return_value = mock_response
        
        mock_spreadsheets = Mock()
        mock_spreadsheets.values.return_value = mock_values
        
        self.mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_build.return_value = self.mock_service
        
        storage = GoogleSheetsStorage(
            credentials_path=self.temp_creds.name,
            spreadsheet_id="test_id"
        )
        
        df = storage.get_existing_data("Instagram Content")
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)  # 2 data rows
        self.assertIn('Post ID', df.columns)
        self.assertIn('Username', df.columns)
        self.assertIn('Likes', df.columns)


if __name__ == '__main__':
    unittest.main(verbosity=2)