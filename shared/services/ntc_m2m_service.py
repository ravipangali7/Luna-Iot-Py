"""
NTC M2M Portal Automation Service
Automates login, data fetching, and Excel download from m2m.ntc.net.np
"""
import os
import time
import pandas as pd
from pathlib import Path
from django.conf import settings
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)

# Download directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOWNLOAD_DIR = BASE_DIR / 'downloads' / 'ntc_m2m'
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def automate_ntc_m2m_download():
    """
    Automate the NTC M2M portal:
    1. Login
    2. Click "Download Report" button (directly, no need for Fetch All)
    3. Wait for download and read Excel file
    
    Returns:
        dict: {
            'success': bool,
            'data': list of dicts (if success),
            'total_records': int (if success),
            'columns': list of str (if success),
            'error': str (if failure)
        }
    """
    try:
        logger.info("Starting NTC M2M automation...")
        
        # Get credentials from Django settings
        ntc_url = getattr(settings, 'NTC_M2M_URL', 'https://m2m.ntc.net.np')
        ntc_username = getattr(settings, 'NTC_M2M_USERNAME', 'pathibhara')
        ntc_password = getattr(settings, 'NTC_M2M_PASSWORD', 'P@bhibhara')
        
        with sync_playwright() as p:
            # Launch browser in headless mode
            logger.info("Launching browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                # Navigate to URL
                logger.info(f"Navigating to {ntc_url}...")
                page.goto(ntc_url, wait_until='networkidle', timeout=30000)
                time.sleep(2)
                
                # Step 1: Login
                logger.info("Attempting to login...")
                # Try multiple possible selectors for username field
                username_selectors = [
                    'input[name="username"]',
                    'input[type="text"]',
                    'input[id*="username"]',
                    'input[id*="user"]',
                    'input[placeholder*="username" i]',
                    'input[placeholder*="user" i]'
                ]
                
                username_filled = False
                for selector in username_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, ntc_username)
                            username_filled = True
                            logger.info(f"Username filled using selector: {selector}")
                            break
                    except Exception as e:
                        continue
                
                if not username_filled:
                    raise Exception("Could not find username input field")
                
                # Try multiple possible selectors for password field
                password_selectors = [
                    'input[name="password"]',
                    'input[type="password"]',
                    'input[id*="password"]',
                    'input[id*="pass"]'
                ]
                
                password_filled = False
                for selector in password_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.fill(selector, ntc_password)
                            password_filled = True
                            logger.info(f"Password filled using selector: {selector}")
                            break
                    except Exception as e:
                        continue
                
                if not password_filled:
                    raise Exception("Could not find password input field")
                
                # Click login button
                login_selectors = [
                    'button:has-text("Login")',
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Log In")',
                    'button:has-text("Sign In")',
                    'button[id*="login"]',
                    'button[id*="submit"]'
                ]
                
                login_clicked = False
                for selector in login_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            page.click(selector)
                            login_clicked = True
                            logger.info(f"Login button clicked using selector: {selector}")
                            break
                    except Exception as e:
                        continue
                
                if not login_clicked:
                    raise Exception("Could not find login button")
                
                # Wait for login to complete
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)
                
                # Step 2: Download Report (directly, no need for Fetch All)
                logger.info("Clicking 'Download Report' button...")
                # Use specific selectors based on the actual HTML structure
                download_selectors = [
                    'button[name="numberListForm:j_idt7"]',  # Specific name attribute
                    'button#numberListForm\\:j_idt7',  # ID with escaped colon
                    'button:has-text("Download Report")',  # Text matching (fallback)
                    'button:has-text("Download")',  # Partial text match
                    'button[id*="j_idt7"]',  # Partial ID match
                ]
                
                download_clicked = False
                for selector in download_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            # Set up download handler
                            with page.expect_download(timeout=60000) as download_info:
                                page.click(selector)
                            download = download_info.value
                            
                            # Save the file
                            file_path = DOWNLOAD_DIR / download.suggested_filename
                            download.save_as(file_path)
                            logger.info(f"File downloaded: {file_path}")
                            download_clicked = True
                            break
                    except Exception as e:
                        logger.warning(f"Download selector {selector} failed: {str(e)}")
                        continue
                
                if not download_clicked:
                    raise Exception("Could not find or click 'Download Report' button")
                
                # Wait a bit for file to be fully written
                time.sleep(2)
                
                # Step 3: Read Excel file
                # Find the most recently downloaded Excel file
                excel_files = list(DOWNLOAD_DIR.glob("*.xlsx"))
                if not excel_files:
                    excel_files = list(DOWNLOAD_DIR.glob("*.xls"))
                
                if not excel_files:
                    raise Exception("No Excel file found in download directory")
                
                # Get the most recently downloaded file
                latest_file = max(excel_files, key=os.path.getctime)
                logger.info(f"Reading Excel file: {latest_file}")
                
                # Read Excel file
                df = pd.read_excel(latest_file, engine='openpyxl')
                
                # Convert DataFrame to list of dictionaries
                data = df.to_dict('records')
                
                # Clean up downloaded file (optional - comment out if you want to keep files)
                # latest_file.unlink()
                
                logger.info(f"Successfully read {len(data)} records from Excel file")
                
                return {
                    'success': True,
                    'data': data,
                    'total_records': len(data),
                    'columns': list(df.columns)
                }
                
            except Exception as e:
                logger.error(f"Error during automation: {str(e)}", exc_info=True)
                return {
                    'success': False,
                    'error': str(e),
                    'data': []
                }
            finally:
                browser.close()
                logger.info("Browser closed")
                
    except Exception as e:
        logger.error(f"Error in automate_ntc_m2m_download: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'data': []
        }

