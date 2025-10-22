# realtor_playwright_dynamicwait.py
import csv, os, shutil, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

INPUT_CSV = "crawlee.csv"
OUTPUT_CSV = "agents_output_3.csv"
ORIGINAL_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\User Data\Profile 2")
CLONE_PROFILE = Path(r"C:\Users\TK\AppData\Local\Google\Chrome\ScraperProfile")

MAX_RETRIES = 3

XPATHS = {
    "Name": "//*[@id='overview-section']/div/div[1]/div[2]/div[1]/h1",
    "Business_Name": "//*[@id='overview-section']/div/div[1]/div[2]/div[2]/p[1]",
    "Phone": "//div[contains(@class, 'kIPpNw')]//a[contains(@href, 'tel:')]",
    "Address": "//div[contains(@class, 'hTcjfz')]//p[contains(@class, 'idlIli')]",
    "Website": "//div[contains(@class, 'fbBxUf')]//a",
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
            for row in csv.DictReader(f):
                done.add(row["URL"])
    return done

def load_input_urls(done):
    urls = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u = r["agent_profiles"].strip()
            if u and not u.startswith(("http://", "https://")):
                u = "https://" + u
            if u and u not in done:
                urls.append(u)
    return urls

def write_header():
    if not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Business_Name", "Name", "Phone", "Address", "Website", "URL"])

def safe_text(page, xpath, timeout_ms=15000):
    """Wait until element is visible or return empty."""
    try:
        el = page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="visible")
        return el.inner_text().strip()
    except PlaywrightTimeoutError:
        return ""

def safe_all_text(page, xpath, timeout_ms=15000):
    try:
        page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="attached")
        return [t.strip() for t in page.locator(f"xpath={xpath}").all_inner_texts()]
    except PlaywrightTimeoutError:
        return []

def safe_attr(page, xpath, attr="href", timeout_ms=15000):
    try:
        el = page.wait_for_selector(f"xpath={xpath}", timeout=timeout_ms, state="attached")
        return el.get_attribute(attr) or ""
    except PlaywrightTimeoutError:
        return ""

def scrape():
    ensure_clone()
    done = load_done_urls()
    urls = load_input_urls(done)
    print(f"📋 {len(urls)} new URLs to scrape (skipping {len(done)} already done)")

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

        for idx, url in enumerate(urls, 1):
            print(f"\n🌐 [{idx}/{len(urls)}] {url}")
            retries, scraped = MAX_RETRIES, False

            while retries > 0 and not scraped:
                try:
                    # Load page and wait until DOM ready
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)

                    # Fetch fields (will wait until each is available or timeout)
                    Business_Name = safe_text(page, XPATHS["Business_Name"])
                    name = safe_text(page, XPATHS["Name"])
                    phone = safe_text(page, XPATHS["Phone"])
                    addr_lines = safe_all_text(page, XPATHS["Address"])[:2]
                    address = " ".join(addr_lines)
                    website = safe_attr(page, XPATHS["Website"], "href")

                    writer.writerow([Business_Name, name, phone, address, website, url])
                    out.flush()
                    print(f"✅ {Business_Name or '[Business_Name]'} | {name or '[no name]'} | {phone or '[no phone]'} | {address or '[no addr]'} | {website or '[no site]'}")
                    scraped = True

                    # Fresh page each time to avoid leftover data
                    page.close()
                    page = context.new_page()

                except Exception as e:
                    retries -= 1
                    print(f"⚠️ Error {url}: {e} | Retries left: {retries}")
                    time.sleep(2)

            if not scraped:
                print(f"❌ Skipping {url} after retries")
                writer.writerow(["", "", "", "", url])
                out.flush()

        context.close()
    out.close()
    print(f"\n🎉 Done. Results in {OUTPUT_CSV}")

if __name__ == "__main__":
    scrape()
