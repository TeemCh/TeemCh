#!/usr/bin/env python3
"""
Script to setup Google Sheets API credentials
"""

import os
import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_credentials_template():
    """Create a template credentials file"""
    template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id", 
        "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
        "client_email": "your-service-account@your-project-id.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project-id.iam.gserviceaccount.com"
    }
    
    return template


def setup_credentials():
    """Interactive setup for Google Sheets credentials"""
    print("🔧 Google Sheets API Credentials Setup")
    print("=" * 50)
    
    # Ensure config directory exists
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    credentials_path = config_dir / "credentials.json"
    
    print("\nThis script will help you setup Google Sheets API credentials.")
    print("You'll need to:")
    print("1. Create a Google Cloud Project")
    print("2. Enable the Google Sheets API")
    print("3. Create a service account")
    print("4. Download the service account key JSON file")
    print("\nDetailed instructions:")
    print("https://developers.google.com/sheets/api/quickstart/python")
    
    choice = input("\nDo you have a service account JSON file? (y/n): ").lower().strip()
    
    if choice == 'y':
        json_path = input("Enter the path to your service account JSON file: ").strip()
        
        if os.path.exists(json_path):
            # Copy the file to our config directory
            import shutil
            shutil.copy2(json_path, credentials_path)
            print(f"✅ Credentials copied to {credentials_path}")
            
            # Validate the JSON
            try:
                with open(credentials_path, 'r') as f:
                    creds = json.load(f)
                
                required_fields = ['type', 'project_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in creds]
                
                if missing_fields:
                    print(f"❌ Invalid credentials file. Missing fields: {missing_fields}")
                    return False
                
                print(f"✅ Valid service account credentials for project: {creds['project_id']}")
                print(f"✅ Service account email: {creds['client_email']}")
                
            except json.JSONDecodeError:
                print("❌ Invalid JSON file")
                return False
                
        else:
            print("❌ File not found")
            return False
    
    else:
        # Create template file
        template = create_credentials_template()
        
        with open(credentials_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"\n📝 Template credentials file created at: {credentials_path}")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable the Google Sheets API")
        print("4. Create a service account:")
        print("   - Go to IAM & Admin > Service Accounts")
        print("   - Click 'Create Service Account'")
        print("   - Give it a name and click 'Create'")
        print("   - Skip role assignment (click 'Continue')")
        print("   - Click 'Done'")
        print("5. Create a key for the service account:")
        print("   - Click on the service account you just created")
        print("   - Go to 'Keys' tab")
        print("   - Click 'Add Key' > 'Create new key'")
        print("   - Choose 'JSON' and click 'Create'")
        print("6. Replace the template file with your downloaded JSON")
        
        return False
    
    # Test the credentials
    print("\n🧪 Testing credentials...")
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        print("✅ Credentials are valid and Google Sheets API is accessible!")
        
        # Offer to create a test spreadsheet
        create_test = input("\nWould you like to create a test spreadsheet? (y/n): ").lower().strip()
        
        if create_test == 'y':
            try:
                from content_scraper import get_google_sheets_storage
                GoogleSheetsStorage = get_google_sheets_storage()
                
                storage = GoogleSheetsStorage(credentials_path=str(credentials_path))
                spreadsheet_id = storage.create_spreadsheet("Content Scraper Test")
                
                if spreadsheet_id:
                    print(f"✅ Test spreadsheet created!")
                    print(f"📊 Spreadsheet URL: {storage.get_spreadsheet_url()}")
                    print(f"📋 Spreadsheet ID: {spreadsheet_id}")
                    
                    # Update .env file
                    env_file = Path(".env")
                    env_content = ""
                    
                    if env_file.exists():
                        with open(env_file, 'r') as f:
                            env_content = f.read()
                    
                    # Update or add the spreadsheet ID
                    lines = env_content.split('\n')
                    found = False
                    for i, line in enumerate(lines):
                        if line.startswith('GOOGLE_SHEETS_SPREADSHEET_ID='):
                            lines[i] = f'GOOGLE_SHEETS_SPREADSHEET_ID={spreadsheet_id}'
                            found = True
                            break
                    
                    if not found:
                        lines.append(f'GOOGLE_SHEETS_SPREADSHEET_ID={spreadsheet_id}')
                    
                    with open(env_file, 'w') as f:
                        f.write('\n'.join(lines))
                    
                    print(f"✅ Spreadsheet ID saved to .env file")
                    
                    print("\n🎉 Setup complete! You can now run the scraper with:")
                    print("python scripts/run_scraper.py")
                    
                else:
                    print("❌ Failed to create test spreadsheet")
                    
            except Exception as e:
                print(f"❌ Error creating test spreadsheet: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing credentials: {str(e)}")
        print("Please check your credentials file and try again.")
        return False


def main():
    """Main entry point"""
    print("Google Sheets API Credentials Setup")
    print("This will help you configure Google Sheets integration")
    
    success = setup_credentials()
    
    if success:
        print("\n✅ Credentials setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit config/accounts.json to add Instagram and TikTok accounts to track")
        print("2. Run the scraper: python scripts/run_scraper.py")
    else:
        print("\n⚠️  Credentials setup incomplete.")
        print("Please complete the manual setup steps and run this script again.")


if __name__ == "__main__":
    main()