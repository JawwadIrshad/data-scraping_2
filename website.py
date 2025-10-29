# # specific_area_scraper.py
# import csv, os, shutil, time
# from pathlib import Path
# from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# import re

# INPUT_CSV = "premierestateproperties.csv"  # CSV containing URLs to scrape
# OUTPUT_CSV = "specific_area_data.csv"
# ORIGINAL_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\User Data\Profile 2")
# CLONE_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\ScraperProfile")

# MAX_RETRIES = 3

# # Your specific XPath for the target area
# SPECIFIC_AREA_XPATH = "//*[@id='inner-page-wrapper']/div/div[2]/div[1]/div[2]/div[2]"

# def ensure_clone():
#     if not CLONE_PROFILE.exists():
#         print("📂 Cloning Profile 2 → ScraperProfile (first run only)...")
#         shutil.copytree(ORIGINAL_PROFILE, CLONE_PROFILE)
#     else:
#         print("📂 Using existing ScraperProfile")

# def is_valid_url(url):
#     """Validate if the URL is proper"""
#     if not url:
#         return False
    
#     url_pattern = re.compile(
#         r'^https?://'  # http:// or https://
#         r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
#         r'localhost|'  # localhost...
#         r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
#         r'(?::\d+)?'  # optional port
#         r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
#     return re.match(url_pattern, url) is not None

# def load_done_urls():
#     """Load already processed URLs"""
#     done = set()
#     if os.path.exists(OUTPUT_CSV):
#         with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 url = row.get("url", "").strip()
#                 if url:
#                     done.add(url)
#     return done

# def load_urls_to_scrape(done):
#     """Load and validate URLs from input CSV"""
#     urls = []
#     invalid_urls = []
    
#     with open(INPUT_CSV, "r", encoding="utf-8") as f:
#         reader = csv.DictReader(f)
#         for row_num, r in enumerate(reader, 2):
#             # Try different possible column names
#             u = (r.get("url", "") or r.get("website_url", "") or r.get("website", "")).strip()
#             if not u:
#                 print(f"⚠️ Row {row_num}: Empty URL, skipping")
#                 continue
            
#             # Add https:// if missing
#             if not u.startswith(("http://", "https://")):
#                 u = "https://" + u
            
#             # Validate URL
#             if is_valid_url(u):
#                 if u not in done:
#                     urls.append(u)
#                 else:
#                     print(f"⏭️ Row {row_num}: URL already processed, skipping: {u}")
#             else:
#                 invalid_urls.append((row_num, u))
#                 print(f"❌ Row {row_num}: Invalid URL, skipping: {u}")
    
#     # Print summary of invalid URLs
#     if invalid_urls:
#         print(f"\n⚠️ Found {len(invalid_urls)} invalid URLs in input file:")
#         for row_num, url in invalid_urls:
#             print(f"   Row {row_num}: {url}")
    
#     return urls

# def write_header():
#     """Write CSV header for scraped data"""
#     if not os.path.exists(OUTPUT_CSV):
#         with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
#             writer = csv.writer(f)
#             writer.writerow(["url", "area_text", "area_html", "element_count", "timestamp"])

# def scroll_to_element(page, xpath):
#     """Scroll to the specific element to ensure it's in view"""
#     try:
#         element = page.locator(f"xpath={xpath}").first
#         if element.count() > 0:
#             element.scroll_into_view_if_needed()
#             time.sleep(1)
#             return True
#     except Exception as e:
#         print(f"⚠️ Could not scroll to element: {e}")
#     return False

# def scrape_specific_area(page, url, xpath):
#     """Scrape data from the specific area defined by XPath"""
#     scraped_data = {
#         "url": url,
#         "area_text": "",
#         "area_html": "",
#         "element_count": 0,
#         "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
#     }
    
#     try:
#         # Wait for the specific area to be present
#         print("🔄 Waiting for specific area to load...")
#         page.wait_for_selector(f"xpath={xpath}", timeout=15000, state="attached")
        
#         # Scroll to the element
#         scroll_to_element(page, xpath)
        
#         # Get the main element
#         area_element = page.locator(f"xpath={xpath}").first
        
#         if area_element.count() > 0:
#             # Get text content
#             scraped_data["area_text"] = area_element.inner_text().strip()
            
#             # Get HTML content
#             scraped_data["area_html"] = area_element.inner_html().strip()
            
#             # Count sub-elements
#             scraped_data["element_count"] = area_element.locator("*").count()
            
#             print(f"✅ Successfully scraped specific area")
#             print(f"   📝 Text length: {len(scraped_data['area_text'])} characters")
#             print(f"   🔧 HTML length: {len(scraped_data['area_html'])} characters")
#             print(f"   🔢 Elements found: {scraped_data['element_count']}")
#         else:
#             print("❌ Specific area element not found")
            
#     except PlaywrightTimeoutError:
#         print("❌ Timeout: Specific area not found within 15 seconds")
#     except Exception as e:
#         print(f"❌ Error scraping specific area: {e}")
    
#     return scraped_data

# def scrape_detailed_elements(page, url, xpath):
#     """More detailed scraping of the specific area"""
#     detailed_data = {
#         "url": url,
#         "main_text": "",
#         "all_links": [],
#         "all_images": [],
#         "headings": [],
#         "paragraphs": [],
#         "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
#     }
    
#     try:
#         # Wait for the specific area
#         page.wait_for_selector(f"xpath={xpath}", timeout=15000, state="attached")
#         scroll_to_element(page, xpath)
        
#         area_element = page.locator(f"xpath={xpath}").first
        
#         if area_element.count() > 0:
#             # Get main text
#             detailed_data["main_text"] = area_element.inner_text().strip()
            
#             # Get all links in the area
#             links = area_element.locator("a")
#             link_count = links.count()
#             for i in range(link_count):
#                 try:
#                     link = links.nth(i)
#                     href = link.get_attribute("href") or ""
#                     text = link.inner_text().strip()
#                     detailed_data["all_links"].append(f"{text} -> {href}")
#                 except:
#                     continue
            
#             # Get all images in the area
#             images = area_element.locator("img")
#             image_count = images.count()
#             for i in range(image_count):
#                 try:
#                     img = images.nth(i)
#                     src = img.get_attribute("src") or ""
#                     alt = img.get_attribute("alt") or ""
#                     detailed_data["all_images"].append(f"{alt} -> {src}")
#                 except:
#                     continue
            
#             # Get headings
#             for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
#                 headings = area_element.locator(tag)
#                 count = headings.count()
#                 for i in range(count):
#                     try:
#                         heading = headings.nth(i)
#                         text = heading.inner_text().strip()
#                         if text:
#                             detailed_data["headings"].append(f"{tag}: {text}")
#                     except:
#                         continue
            
#             # Get paragraphs
#             paragraphs = area_element.locator("p")
#             para_count = paragraphs.count()
#             for i in range(para_count):
#                 try:
#                     para = paragraphs.nth(i)
#                     text = para.inner_text().strip()
#                     if text:
#                         detailed_data["paragraphs"].append(text)
#                 except:
#                     continue
            
#             print(f"✅ Detailed scraping completed:")
#             print(f"   🔗 Links: {len(detailed_data['all_links'])}")
#             print(f"   🖼️ Images: {len(detailed_data['all_images'])}")
#             print(f"   📋 Headings: {len(detailed_data['headings'])}")
#             print(f"   📝 Paragraphs: {len(detailed_data['paragraphs'])}")
            
#     except Exception as e:
#         print(f"❌ Error in detailed scraping: {e}")
    
#     return detailed_data

# def scrape_urls():
#     """Main function to scrape specific area from URLs"""
#     ensure_clone()
#     done = load_done_urls()
#     urls_to_scrape = load_urls_to_scrape(done)
    
#     print(f"\n📊 SCRAPING SUMMARY")
#     print(f"📋 New URLs to scrape: {len(urls_to_scrape)}")
#     print(f"⏭️ Already processed URLs: {len(done)}")
#     print(f"🎯 Target XPath: {SPECIFIC_AREA_XPATH}")
#     print(f"{'='*60}")
    
#     if not urls_to_scrape:
#         print("🎉 No new URLs to scrape. All done!")
#         return
    
#     write_header()
    
#     # Open output file for writing
#     with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as out:
#         writer = csv.writer(out)

#         with sync_playwright() as p:
#             context = p.chromium.launch_persistent_context(
#                 str(CLONE_PROFILE),
#                 headless=False,
#                 viewport={"width": 1280, "height": 900},
#                 args=["--disable-blink-features=AutomationControlled"],
#             )
#             page = context.new_page()

#             successful_scrapes = 0
#             failed_scrapes = 0
            
#             for idx, url in enumerate(urls_to_scrape, 1):
#                 print(f"\n{'#'*60}")
#                 print(f"🌐 [{idx}/{len(urls_to_scrape)}] Processing: {url}")
#                 print(f"{'#'*60}")
                
#                 retries, scraped = MAX_RETRIES, False
#                 scraped_data = None

#                 while retries > 0 and not scraped:
#                     try:
#                         # Load the URL
#                         page.goto(url, wait_until="domcontentloaded", timeout=30000)
#                         print(f"✅ Loaded URL")
                        
#                         # Wait for page to stabilize
#                         time.sleep(2)
                        
#                         # Scrape the specific area
#                         scraped_data = scrape_specific_area(page, url, SPECIFIC_AREA_XPATH)
                        
#                         # If you want detailed scraping, uncomment the line below:
#                         # scraped_data = scrape_detailed_elements(page, url, SPECIFIC_AREA_XPATH)
                        
#                         if scraped_data and scraped_data["area_text"]:
#                             # Write basic data to CSV
#                             writer.writerow([
#                                 scraped_data["url"],
#                                 scraped_data["area_text"],
#                                 scraped_data["area_html"],
#                                 scraped_data["element_count"],
#                                 scraped_data["timestamp"]
#                             ])
#                             out.flush()
                            
#                             successful_scrapes += 1
#                             scraped = True
#                             print(f"✅ Successfully scraped and saved data")
#                         else:
#                             print("⚠️ No data scraped, retrying...")
#                             retries -= 1
#                             time.sleep(2)

#                     except Exception as e:
#                         retries -= 1
#                         print(f"⚠️ Error processing {url}: {e} | Retries left: {retries}")
#                         time.sleep(3)
                        
#                         # Try with fresh page on retry
#                         try:
#                             page.close()
#                         except:
#                             pass
#                         page = context.new_page()

#                 if not scraped:
#                     print(f"❌ Failed to process {url} after retries")
#                     # Write empty record to mark as processed
#                     writer.writerow([url, "", "", "0", time.strftime("%Y-%m-%d %H:%M:%S")])
#                     out.flush()
#                     failed_scrapes += 1

#                 # Delay between URLs
#                 if idx < len(urls_to_scrape):
#                     print("⏳ Waiting before next URL...")
#                     time.sleep(2)

#             context.close()
    
#     print(f"\n🎉 SCRAPING COMPLETED!")
#     print(f"{'='*50}")
#     print(f"✅ Successful scrapes: {successful_scrapes}")
#     print(f"❌ Failed scrapes: {failed_scrapes}")
#     print(f"📁 Results saved to: {OUTPUT_CSV}")

# def create_sample_input():
#     """Create a sample input CSV file if it doesn't exist"""
#     if not os.path.exists(INPUT_CSV):
#         with open(INPUT_CSV, "w", encoding="utf-8", newline="") as f:
#             writer = csv.writer(f)
#             writer.writerow(["url"])
#             writer.writerow(["https://www.example.com"])
#             writer.writerow(["https://www.example.org"])
#         print(f"📝 Created sample input file: {INPUT_CSV}")
#         print("💡 Please edit this file with your actual URLs")

# if __name__ == "__main__":
#     # Create sample input file if it doesn't exist
#     create_sample_input()
    
#     # Start scraping
#     scrape_urls()


# realtor_playwright_dynamicwait.py
import csv
import os
import shutil
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

INPUT_CSV = "premierestateproperties.csv"
OUTPUT_CSV = "agents_output_3.csv"
ORIGINAL_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\User Data\Profile 2")
CLONE_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\ScraperProfile")

MAX_RETRIES = 3

XPATHS = {
    "Email": "//div[@class='ip-agent-det-con-info']//a[starts-with(@href, 'mailto:')]",
    "Phone": "//div[@class='ip-agent-det-con-info']//a[@id='agents-phone']",
    "Website": "//div[@class='ip-agent-det-con-info']//a[starts-with(@href, 'http://')]",
    "Name": "//*[@id='inner-page-wrapper']/div/div[2]/div[1]/div[2]/div[1]/h1",
}

def ensure_clone():
    if not CLONE_PROFILE.exists():
        print("📂 Cloning Profile 2 → ScraperProfile (first run only)...")
        shutil.copytree(ORIGINAL_PROFILE, CLONE_PROFILE)
    else:
        print("📂 Using existing ScraperProfile")

def load_done_urls():
    done = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "URL" in row and row["URL"]:
                    done.add(row["URL"].strip())
    print(f"📊 Found {len(done)} URLs already processed")
    return done

def load_input_urls(done):
    urls = []
    
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file {INPUT_CSV} not found!")
        return urls
    
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Debug: print column names
        if reader.fieldnames:
            print(f"📝 CSV columns: {reader.fieldnames}")
        
        for row_num, row in enumerate(reader, 1):
            # Try different possible column names for URLs
            url = None
            possible_columns = ['agent_profiles', 'url', 'URL', 'website', 'link', 'profile']
            
            for col in possible_columns:
                if col in row and row[col]:
                    url = row[col].strip()
                    break
            
            if not url:
                print(f"⚠️ No URL found in row {row_num}")
                continue
                
            # Ensure URL has protocol
            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url
                
            if url and url not in done:
                urls.append(url)
                print(f"✅ Added URL: {url}")
            elif url in done:
                print(f"⏭️ Skipping (already done): {url}")
    
    return urls

def write_header():
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Business_Name", "Name", "Phone", "Address", "Website", "URL", "Email"])

def safe_text(page, xpath, timeout_ms=15000):
    """Wait until element is visible or return empty."""
    try:
        el = page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="visible")
        return el.inner_text().strip() if el else ""
    except PlaywrightTimeoutError:
        return ""

def safe_all_text(page, xpath, timeout_ms=15000):
    """Get all matching elements text or return empty list."""
    try:
        page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="attached")
        return [t.strip() for t in page.locator(f"xpath={xpath}").all_inner_texts()]
    except PlaywrightTimeoutError:
        return []

def safe_attr(page, xpath, attr="href", timeout_ms=15000):
    """Get attribute value or return empty."""
    try:
        el = page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="attached")
        return el.get_attribute(attr) or "" if el else ""
    except PlaywrightTimeoutError:
        return ""

def scrape():
    ensure_clone()
    done = load_done_urls()
    urls = load_input_urls(done)
    print(f"📋 {len(urls)} new URLs to scrape")

    if not urls:
        print("❌ No URLs to process. Check:")
        print("   - Input file exists and has data")
        print("   - CSV has correct column names")
        print("   - URLs are not already processed")
        return

    write_header()
    
    with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                str(CLONE_PROFILE),
                headless=False,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"],
            )
            page = context.new_page()

            for idx, url in enumerate(urls, 1):
                print(f"\n🌐 [{idx}/{len(urls)}] Processing: {url}")
                retries, scraped = MAX_RETRIES, False

                while retries > 0 and not scraped:
                    try:
                        # Load page and wait until DOM ready
                        page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        
                        # Wait a bit for dynamic content to load
                        page.wait_for_timeout(3000)

                        # Fetch fields
                        name = safe_text(page, XPATHS["Name"])
                        phone = safe_text(page, XPATHS["Phone"])
                        website = safe_attr(page, XPATHS["Website"], "href")
                        email = safe_attr(page, XPATHS["Email"], "href")
                        
                        # Remove mailto: prefix if present
                        if email and email.startswith("mailto:"):
                            email = email[7:]
                        
                        # For now, using empty values for missing fields
                        Business_Name = name  # Using name as business name temporarily
                        address = ""  # You need to define the XPath for this

                        # FIXED: Include email in the writerow call
                        writer.writerow([Business_Name, name, phone, address, website, url, email])
                        out.flush()
                        print(f"✅ Extracted: {name or '[no name]'} | {phone or '[no phone]'} | {email or '[no email]'} | {website or '[no site]'}")
                        scraped = True

                        # Fresh page each time to avoid leftover data
                        page.close()
                        page = context.new_page()

                    except Exception as e:
                        retries -= 1
                        print(f"⚠️ Error scraping {url}: {str(e)[:100]}... | Retries left: {retries}")
                        if retries > 0:
                            time.sleep(2)
                        else:
                            print(f"❌ Failed after retries: {url}")
                            # FIXED: Include empty email field in failed row
                            writer.writerow(["", "", "", "", "", url, ""])
                            out.flush()

            context.close()
    
    print(f"\n🎉 Done. Results in {OUTPUT_CSV}")

if __name__ == "__main__":
    scrape()