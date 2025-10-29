# realtor_playwright_agent_url_scraper_with_pagination.py
import csv, os, shutil, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re

INPUT_CSV = "realtor_office.csv"
OUTPUT_CSV = "agent_urls_output.csv"
ORIGINAL_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\User Data\Profile 2")
CLONE_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\ScraperProfile")

MAX_RETRIES = 3
SCROLL_PAUSE_TIME = 8
MAX_SCROLL_ATTEMPTS = 50
MAX_PAGES_TO_SCRAPE = 20  # Increased maximum pages

# XPaths for agent profile links
AGENT_LINK_XPATHS = [
    "//a[contains(@href, 'agent')]",
    "//a[contains(@href, 'realtor')]",
    "//a[contains(@href, 'profile')]",
    "//a[contains(@class, 'agent')]",
    "//a[contains(@class, 'profile')]",
    "//div[contains(@class, 'agent')]//a",
    "//div[contains(@class, 'profile')]//a",
    "//a[.//*[contains(text(), 'Agent')]]",
    "//a[.//*[contains(text(), 'Realtor')]]",
]

# Enhanced XPaths for next page navigation
NEXT_PAGE_XPATHS = [
    "//a[contains(., 'next')]",
    "//a[contains(., 'Next')]",
    "//button[contains(., 'next')]",
    "//button[contains(., 'Next')]",
    "//a[@aria-label='Next']",
    "//a[contains(@class, 'next')]",
    "//button[contains(@class, 'next')]",
    "//li[contains(@class, 'next')]//a",
    "//li[contains(@class, 'pagination-next')]//a",
    "//a[contains(@href, 'page')]",
    "//a[contains(@href, 'p=')]",
    "//a[contains(@href, 'pagenum')]",
    "//a[contains(@data-page, 'next')]",
    "//a[contains(@title, 'Next')]",
    "//button[contains(@title, 'Next')]",
    "//a[contains(@id, 'next')]",
    "//button[contains(@id, 'next')]",
    "//a[.//i[contains(@class, 'chevron-right')]]",
    "//a[.//span[contains(@class, 'next')]]",
]

def ensure_clone():
    if not CLONE_PROFILE.exists():
        print("📂 Cloning Profile 2 → ScraperProfile (first run only)...")
        shutil.copytree(ORIGINAL_PROFILE, CLONE_PROFILE)
    else:
        print("📂 Using existing ScraperProfile")

def is_valid_website_url(url):
    """Validate if the URL is a proper website URL"""
    if not url:
        return False
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not re.match(url_pattern, url):
        return False
    
    # Exclude common non-website URLs
    excluded_patterns = [
        r'\.pdf$', r'\.doc$', r'\.docx$', r'\.xls$', r'\.xlsx$',
        r'\.jpg$', r'\.jpeg$', r'\.png$', r'\.gif$', r'\.zip$', r'\.rar$',
        r'mailto:', r'tel:', r'javascript:', r'#',
    ]
    
    for pattern in excluded_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    return True

def load_done_websites():
    """Load already processed website URLs"""
    done = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use lowercase column name to match your CSV header
                website_url = row.get("website_url", "").strip()
                if website_url:
                    done.add(website_url)
    return done

def load_existing_agent_urls():
    """Load all existing agent URLs to avoid duplicates"""
    existing_urls = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Use lowercase column name to match your CSV header
                agent_url = row.get("agent_url", "").strip()
                if agent_url:
                    existing_urls.add(agent_url)
    return existing_urls

def load_website_urls(done):
    """Load and validate website URLs from input CSV"""
    urls = []
    invalid_urls = []
    
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, r in enumerate(reader, 2):  # row_num starts from 2 (header is row 1)
            u = r.get("website_url", "").strip()
            if not u:
                print(f"⚠️ Row {row_num}: Empty URL, skipping")
                continue
            
            # Add https:// if missing
            if not u.startswith(("http://", "https://")):
                u = "https://" + u
            
            # Validate URL
            if is_valid_website_url(u):
                if u not in done:
                    urls.append(u)
                else:
                    print(f"⏭️ Row {row_num}: URL already processed, skipping: {u}")
            else:
                invalid_urls.append((row_num, u))
                print(f"❌ Row {row_num}: Invalid website URL, skipping: {u}")
    
    # Print summary of invalid URLs
    if invalid_urls:
        print(f"\n⚠️ Found {len(invalid_urls)} invalid URLs in input file:")
        for row_num, url in invalid_urls:
            print(f"   Row {row_num}: {url}")
    
    return urls

def write_header():
    """Write CSV header for agent URLs"""
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            # Use lowercase column names consistently
            writer.writerow(["agent_name", "agent_url", "website_url", "page_number", "timestamp"])

def scroll_page(page):
    """Scroll to bottom of page to load all content"""
    print("🔄 Scrolling to load all content...")
    
    last_height = page.evaluate("document.body.scrollHeight")
    scroll_attempts = 0
    
    while scroll_attempts < MAX_SCROLL_ATTEMPTS:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        
        new_height = page.evaluate("document.body.scrollHeight")
        
        if new_height == last_height:
            break
            
        last_height = new_height
        scroll_attempts += 1
        print(f"📜 Scroll {scroll_attempts}, height: {new_height}")
    
    # Scroll back to top to ensure all elements are visible
    page.evaluate("window.scrollTo(0, 0);")
    time.sleep(1)
    
    print(f"✅ Finished scrolling after {scroll_attempts} attempts")

def find_agent_links(page, website_url, existing_agent_urls):
    """Find all agent profile links on the page and filter duplicates"""
    agent_links = []
    new_agents_count = 0
    duplicate_agents_count = 0
    
    for xpath in AGENT_LINK_XPATHS:
        try:
            links = page.locator(f"xpath={xpath}")
            count = links.count()
            
            if count > 0:
                print(f"🔍 Found {count} links with xpath: {xpath}")
                
                for i in range(count):
                    try:
                        link = links.nth(i)
                        href = link.get_attribute("href")
                        text = link.inner_text().strip()
                        
                        if href and is_agent_link(href, text):
                            # Convert relative URLs to absolute
                            if href.startswith("/"):
                                href = urljoin(website_url, href)
                            elif href.startswith("#") or href.startswith("javascript:"):
                                continue
                            
                            # Normalize URL for comparison
                            normalized_url = normalize_url(href)
                            
                            # Check if agent URL already exists
                            if normalized_url in existing_agent_urls:
                                duplicate_agents_count += 1
                                print(f"   ⏭️ Duplicate agent URL, skipping: {text}")
                                continue
                                
                            agent_links.append({
                                "name": text or "Unknown",
                                "url": href,
                                "normalized_url": normalized_url
                            })
                            existing_agent_urls.add(normalized_url)
                            new_agents_count += 1
                            print(f"   👤 New Agent: {text} -> {href}")
                            
                    except Exception as e:
                        print(f"   ⚠️ Error processing link {i}: {e}")
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error with xpath {xpath}: {e}")
            continue
    
    # Remove duplicates based on normalized URLs (additional safety)
    unique_links = []
    seen_urls = set()
    
    for link in agent_links:
        if link["normalized_url"] not in seen_urls:
            unique_links.append(link)
            seen_urls.add(link["normalized_url"])
    
    print(f"📊 New agents found: {new_agents_count}, Duplicates skipped: {duplicate_agents_count}")
    
    return unique_links

def normalize_url(url):
    """Normalize URL for duplicate checking"""
    try:
        parsed = urlparse(url)
        # Remove fragments and normalize scheme/hostname
        normalized = parsed._replace(
            fragment="",
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower()
        ).geturl()
        return normalized
    except:
        return url.lower()

def is_agent_link(href, text):
    """Determine if a link is likely an agent profile"""
    href_lower = href.lower()
    text_lower = text.lower() if text else ""
    
    # Check href for agent-related patterns
    href_patterns = [
        '/agent/', '/realtor/', '/profile/',
        'agent', 'realtor', 'profile',
        '/members/', '/team/', '/staff/',
        '/broker/', '/about/', '/people/'
    ]
    
    # Check text for agent-related keywords
    text_patterns = [
        'agent', 'realtor', 'broker', 'associate',
        'view profile', 'profile', 'meet', 'team',
        'about', 'bio', 'contact'
    ]
    
    # Exclude patterns that are not agent profiles
    exclude_patterns = [
        'login', 'signin', 'register', 'signup',
        'admin', 'dashboard', 'logout'
    ]
    
    # Check if href contains agent patterns
    href_match = any(pattern in href_lower for pattern in href_patterns)
    
    # Check if text contains agent patterns (if text exists)
    text_match = any(pattern in text_lower for pattern in text_patterns) if text else False
    
    # Exclude links with unwanted patterns
    exclude_match = any(pattern in href_lower for pattern in exclude_patterns)
    
    return (href_match or text_match) and not exclude_match

def find_and_click_next_page(page, website_url, current_page):
    """Find and click the next page button with multiple strategies"""
    
    # Strategy 1: Try to find and click next button
    for xpath in NEXT_PAGE_XPATHS:
        try:
            next_element = page.locator(f"xpath={xpath}").first
            if next_element.count() > 0:
                # Check if element is visible and enabled
                is_visible = next_element.is_visible()
                is_enabled = next_element.is_enabled()
                
                if is_visible and is_enabled:
                    print(f"✅ Found next page button with xpath: {xpath}")
                    
                    # Get the URL before clicking
                    current_url = page.url
                    
                    # Click the next button
                    next_element.click()
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(5)
                    
                    # Check if URL changed
                    new_url = page.url
                    if new_url != current_url:
                        print(f"✅ Successfully moved to page {current_page + 1}: {new_url}")
                        return new_url
                    else:
                        print("⚠️ URL didn't change after clicking next button")
                        break
                        
        except Exception as e:
            print(f"⚠️ Error with next page xpath {xpath}: {e}")
            continue
    
    # Strategy 2: Try to increment page number in URL
    next_url = increment_page_in_url(page.url, current_page + 1)
    if next_url:
        try:
            page.goto(next_url, wait_until="domcontentloaded", timeout=50000)
            print(f"✅ Navigated to page {current_page + 1} via URL: {next_url}")
            return next_url
        except Exception as e:
            print(f"⚠️ Failed to navigate via URL increment: {e}")
    
    # Strategy 3: Look for pagination numbers and click the next one
    try:
        next_page_number = current_page + 1
        page_link_xpath = f"//a[contains(., '{next_page_number}')]"
        page_link = page.locator(f"xpath={page_link_xpath}").first
        
        if page_link.count() > 0 and page_link.is_visible():
            current_url = page.url
            page_link.click()
            page.wait_for_load_state("domcontentloaded")
            time.sleep(6)
            
            new_url = page.url
            if new_url != current_url:
                print(f"✅ Successfully moved to page {next_page_number} via page number")
                return new_url
    except Exception as e:
        print(f"⚠️ Error clicking page number {next_page_number}: {e}")
    
    print("❌ No next page found")
    return None

def increment_page_in_url(url, next_page):
    """Try to increment page number in URL parameters"""
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Common pagination parameters
        pagination_params = ['page', 'p', 'pagenum', 'pg', 'pagination']
        
        for param in pagination_params:
            if param in query_params:
                query_params[param] = [str(next_page)]
                new_query = urlencode(query_params, doseq=True)
                new_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                return new_url
        
        # If no pagination params found, try to append /page/X
        if not any('page' in part for part in url.split('/')):
            if url.endswith('/'):
                return f"{url}page/{next_page}/"
            else:
                return f"{url}/page/{next_page}/"
                
    except Exception as e:
        print(f"⚠️ Error incrementing page in URL: {e}")
    
    return None

def scrape_website_pages(page, website_url, writer, existing_agent_urls):
    """Scrape multiple pages of a website with improved navigation"""
    current_page = 1
    total_agents = 0
    current_url = website_url
    consecutive_failures = 0
    max_consecutive_failures = 2
    
    while current_page <= MAX_PAGES_TO_SCRAPE and consecutive_failures < max_consecutive_failures:
        print(f"\n{'='*50}")
        print(f"📄 Processing page {current_page}: {current_url}")
        print(f"{'='*50}")
        
        try:
            # Load the current page
            page.goto(current_url, wait_until="domcontentloaded", timeout=50000)
            print(f"✅ Loaded page {current_page}")
            
            # Wait for page to stabilize
            time.sleep(6)
            
            # Scroll to load all content
            scroll_page(page)
            
            # Find agent links on current page (with duplicate checking)
            agent_links = find_agent_links(page, website_url, existing_agent_urls)
            page_agents = len(agent_links)
            total_agents += page_agents
            
            # Write agent URLs to CSV
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            for agent in agent_links:
                writer.writerow([
                    agent["name"],
                    agent["url"],
                    website_url,
                    current_page,
                    timestamp
                ])
            
            print(f"✅ Page {current_page}: Found {page_agents} new agents (Total: {total_agents})")
            
            if page_agents == 0 and current_page > 1:
                print("⚠️ No new agents found on this page, might be the end")
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            
            # Try to find and navigate to next page
            next_page_url = find_and_click_next_page(page, website_url, current_page)
            
            if not next_page_url:
                print("🏁 No more pages to scrape or cannot navigate to next page")
                break
                
            # Check if we're stuck in a loop
            if next_page_url == current_url:
                print("🔄 Same URL as current page, stopping pagination")
                break
                
            current_url = next_page_url
            current_page += 1
            
            # Small delay before next page
            time.sleep(6)
            
        except Exception as e:
            print(f"⚠️ Error processing page {current_page}: {e}")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print("🚫 Too many consecutive failures, stopping pagination")
                break
    
    print(f"\n📊 Finished scraping {website_url}")
    print(f"📄 Total pages processed: {current_page - 1}")
    print(f"👤 Total new agents found: {total_agents}")
    
    return total_agents

def scrape_agent_urls():
    """Main function to scrape agent URLs from websites with pagination"""
    ensure_clone()
    done = load_done_websites()
    website_urls = load_website_urls(done)
    existing_agent_urls = load_existing_agent_urls()
    
    print(f"\n📊 SCRAPING SUMMARY")
    print(f"📋 New websites to scrape: {len(website_urls)}")
    print(f"⏭️ Already processed websites: {len(done)}")
    print(f"🔗 Existing agent URLs in database: {len(existing_agent_urls)}")
    print(f"{'='*60}")
    
    if not website_urls:
        print("🎉 No new websites to scrape. All done!")
        return
    
    write_header()
    out = open(OUTPUT_CSV, "a", encoding="utf-8", newline="")
    writer = csv.writer(out)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            str(CLONE_PROFILE),
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.new_page()

        total_new_agents = 0
        
        for idx, website_url in enumerate(website_urls, 1):
            print(f"\n{'#'*60}")
            print(f"🌐 [{idx}/{len(website_urls)}] Processing website: {website_url}")
            print(f"{'#'*60}")
            
            retries, scraped = MAX_RETRIES, False

            while retries > 0 and not scraped:
                try:
                    # Scrape multiple pages for this website
                    website_agents = scrape_website_pages(page, website_url, writer, existing_agent_urls)
                    out.flush()
                    
                    total_new_agents += website_agents
                    print(f"✅ Completed website: {website_url}")
                    print(f"📊 New agents from this website: {website_agents}")
                    scraped = True

                    # Fresh page for next website
                    page.close()
                    page = context.new_page()

                except Exception as e:
                    retries -= 1
                    print(f"⚠️ Error processing website {website_url}: {e} | Retries left: {retries}")
                    time.sleep(6)
                    
                    # Try with fresh page on retry
                    try:
                        page.close()
                    except:
                        pass
                    page = context.new_page()

            if not scraped:
                print(f"❌ Failed to process {website_url} after retries")
                # Still mark as processed to avoid infinite retries
                writer.writerow(["", "", website_url, "0", time.strftime("%Y-%m-%d %H:%M:%S")])
                out.flush()

            # Delay between websites
            if idx < len(website_urls):
                print("⏳ Waiting before next website...")
                time.sleep(6)

        context.close()
    out.close()
    
    print(f"\n🎉 SCRAPING COMPLETED!")
    print(f"{'='*50}")
    print(f"📊 Total new agents found: {total_new_agents}")
    print(f"📁 Results saved to: {OUTPUT_CSV}")
    print(f"🔗 Total agent URLs in database: {len(existing_agent_urls) + total_new_agents}")

if __name__ == "__main__":
    scrape_agent_urls()