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
                logger.info("Waiting for page to fully render...")
                time.sleep(10)  # Give JSF plenty of time to render
                
                # Try to find the form, but don't fail if it's not found
                logger.info("Checking if form is loaded...")
                try:
                    # Try multiple form selectors
                    form_selectors = [
                        'form#numberListForm',
                        'form[name="numberListForm"]',
                        'form',
                    ]
                    form_found = False
                    for form_selector in form_selectors:
                        try:
                            if page.locator(form_selector).count() > 0:
                                logger.info(f"Form found using selector: {form_selector}")
                                form_found = True
                                break
                        except:
                            continue
                    
                    if not form_found:
                        logger.warning("Form not found, but continuing to look for button...")
                    else:
                        logger.info("Form is present, waiting a bit more for JSF components...")
                        time.sleep(3)
                except Exception as e:
                    logger.warning(f"Form check failed, continuing anyway: {str(e)}")
                
                # Additional wait for JSF components to initialize
                time.sleep(2)
                
                # Step 2: Download Report (directly, no need for Fetch All)
                logger.info("Looking for 'Download Report' button...")
                
                # Try multiple strategies to find and click the button
                download_clicked = False
                download_error_messages = []
                
                # Strategy 1: Wait for button by name attribute (most reliable for JSF)
                try:
                    logger.info("Trying to find button by name attribute 'numberListForm:j_idt7'...")
                    button_locator = page.locator('button[name="numberListForm:j_idt7"]')
                    # Wait longer for button to appear
                    button_locator.wait_for(state='visible', timeout=20000)
                    logger.info("Button found by name attribute!")
                    
                    # Set up download handler before clicking
                    with page.expect_download(timeout=60000) as download_info:
                        button_locator.click()
                    download = download_info.value
                    
                    file_path = DOWNLOAD_DIR / download.suggested_filename
                    download.save_as(file_path)
                    logger.info(f"File downloaded: {file_path}")
                    download_clicked = True
                except Exception as e:
                    error_msg = f"Name attribute strategy failed: {str(e)}"
                    logger.warning(error_msg)
                    download_error_messages.append(error_msg)
                
                # Strategy 2: Try by ID with XPath (more reliable for JSF IDs with colons)
                if not download_clicked:
                    try:
                        logger.info("Trying XPath selector for button ID...")
                        button_locator = page.locator('xpath=//button[@id="numberListForm:j_idt7"]')
                        button_locator.wait_for(state='visible', timeout=10000)
                        logger.info("Button found by XPath ID, clicking...")
                        
                        with page.expect_download(timeout=60000) as download_info:
                            button_locator.click()
                        download = download_info.value
                        
                        file_path = DOWNLOAD_DIR / download.suggested_filename
                        download.save_as(file_path)
                        logger.info(f"File downloaded: {file_path}")
                        download_clicked = True
                    except Exception as e:
                        error_msg = f"XPath ID strategy failed: {str(e)}"
                        logger.warning(error_msg)
                        download_error_messages.append(error_msg)
                
                # Strategy 3: Try by text content
                if not download_clicked:
                    try:
                        logger.info("Trying to find button by text 'Download Report'...")
                        button_locator = page.locator('button:has-text("Download Report")')
                        button_locator.wait_for(state='visible', timeout=10000)
                        logger.info("Button found by text, clicking...")
                        
                        with page.expect_download(timeout=60000) as download_info:
                            button_locator.click()
                        download = download_info.value
                        
                        file_path = DOWNLOAD_DIR / download.suggested_filename
                        download.save_as(file_path)
                        logger.info(f"File downloaded: {file_path}")
                        download_clicked = True
                    except Exception as e:
                        error_msg = f"Text matching strategy failed: {str(e)}"
                        logger.warning(error_msg)
                        download_error_messages.append(error_msg)
                
                # Strategy 4: Try all buttons and find the one with download text
                if not download_clicked:
                    try:
                        logger.info("Trying to find any button containing 'Download'...")
                        buttons = page.locator('button').all()
                        logger.info(f"Found {len(buttons)} buttons on page")
                        
                        for i, button in enumerate(buttons):
                            try:
                                text = button.inner_text()
                                logger.info(f"Button {i} text: {text}")
                                if 'Download' in text and 'Report' in text:
                                    logger.info(f"Found download button at index {i}")
                                    with page.expect_download(timeout=60000) as download_info:
                                        button.click()
                                    download = download_info.value
                                    
                                    file_path = DOWNLOAD_DIR / download.suggested_filename
                                    download.save_as(file_path)
                                    logger.info(f"File downloaded: {file_path}")
                                    download_clicked = True
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        error_msg = f"Button enumeration strategy failed: {str(e)}"
                        logger.warning(error_msg)
                        download_error_messages.append(error_msg)
                
                if not download_clicked:
                    # Take a screenshot for debugging
                    screenshot_path = DOWNLOAD_DIR / 'debug_screenshot.png'
                    try:
                        page.screenshot(path=str(screenshot_path))
                        logger.info(f"Debug screenshot saved to: {screenshot_path}")
                    except:
                        pass
                    
                    # Get page HTML for debugging
                    try:
                        html_snippet = page.locator('form#numberListForm').inner_html()
                        logger.info(f"Form HTML snippet: {html_snippet[:500]}")
                    except:
                        pass
                    
                    error_details = "; ".join(download_error_messages)
                    raise Exception(f"Could not find or click 'Download Report' button. Attempted strategies: {error_details}")
                
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

