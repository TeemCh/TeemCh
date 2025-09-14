# Content Scraping Architecture

A comprehensive system for scraping Instagram and TikTok content metrics and storing them in Google Sheets for content idea generation.

## About Me 👋
- 🔭 I'm ex-Accenture ex-Aramco analyst
- 🌱 I'm currently learning AI in general
- 📫 How to reach me: [LinkedIn](https://www.linkedin.com/in/timur-chepiga-199435b3/)  
- 🎓 Check out my [Master's degree project](https://github.com/TeemCh/MOBO-for-L-PBF-optimization)  
- 🛠️ Check out my pet project: [HHRU Analyst Dashboard Search](https://github.com/TeemCh/HHRU-analysis)  

## Current Project: Content Scraping for Social Media Analytics

## Features

- 📸 **Instagram Content Scraping**: Collect posts, reels, stories metrics (views, likes, comments, shares)
- 🎵 **TikTok Content Scraping**: Extract video metrics and trending content data
- 📊 **Google Sheets Integration**: Automated data storage and organization
- ⏰ **Scheduled Scraping**: Automated data collection at regular intervals
- 🔧 **Configurable**: Easy setup for tracking specific accounts and hashtags
- 📈 **Analytics Ready**: Structured data for content performance analysis

## Architecture Overview

```
├── content_scraper/
│   ├── __init__.py
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── instagram_scraper.py
│   │   └── tiktok_scraper.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── google_sheets.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── content_models.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── rate_limiter.py
├── config/
│   ├── accounts.json
│   └── credentials.json
├── scripts/
│   ├── run_scraper.py
│   └── setup_credentials.py
└── tests/
    ├── test_scrapers.py
    └── test_sheets_integration.py
```

## Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Setup Google Sheets API**
```bash
python scripts/setup_credentials.py
```

3. **Configure Accounts to Track**
Edit `config/accounts.json` with Instagram and TikTok accounts/hashtags

4. **Run Scraper**
```bash
python scripts/run_scraper.py
```

## Configuration

### Google Sheets Setup
1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create service account credentials
4. Share your Google Sheet with the service account email

### Accounts Configuration
```json
{
  "instagram": {
    "accounts": ["@example_account1", "@example_account2"],
    "hashtags": ["#trending", "#viral"]
  },
  "tiktok": {
    "accounts": ["@tiktok_user1", "@tiktok_user2"],
    "hashtags": ["#fyp", "#viral"]
  }
}
```

## Data Structure

### Instagram Content Schema
- Post ID
- Account Username
- Post Type (photo/video/reel)
- Caption
- Likes Count
- Comments Count
- Views Count (for videos)
- Post Date
- Hashtags
- Location

### TikTok Content Schema
- Video ID
- Account Username
- Description
- Likes Count
- Comments Count
- Shares Count
- Views Count
- Upload Date
- Hashtags
- Music/Sound

## Usage Examples

### Manual Scraping
```python
from content_scraper.scrapers import InstagramScraper, TikTokScraper
from content_scraper.storage import GoogleSheetsStorage

# Initialize scrapers
ig_scraper = InstagramScraper()
tiktok_scraper = TikTokScraper()
sheets = GoogleSheetsStorage()

# Scrape content
ig_data = ig_scraper.scrape_account("example_account")
tiktok_data = tiktok_scraper.scrape_account("example_account")

# Store to Google Sheets
sheets.save_instagram_data(ig_data)
sheets.save_tiktok_data(tiktok_data)
```

### Scheduled Scraping
```python
import schedule
import time
from scripts.run_scraper import run_full_scrape

# Schedule scraping every 6 hours
schedule.every(6).hours.do(run_full_scrape)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Legal and Ethical Considerations

- ⚖️ Respect platform terms of service
- 🚦 Implement rate limiting to avoid overwhelming servers
- 🔒 Handle user data responsibly
- 📝 Only scrape public content
- 🤖 Follow robots.txt guidelines

## License

MIT License - See LICENSE file for details