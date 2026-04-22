import nodriver as uc
from nodriver import start
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# ── Virtual display (Linux only) ──────────────────────────────────────────────
try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080, colordepth=24)
    vdisplay.start()
    USE_VDISPLAY = True
    print("Virtual display started")
except ImportError:
    USE_VDISPLAY = False
    print("xvfbwrapper not found, running without virtual display")
# ─────────────────────────────────────────────────────────────────────────────

class FilteredStderr:
    def write(self, msg):
        if "I/O operation on closed pipe" not in msg and "unclosed transport" not in msg:
            sys.__stderr__.write(msg)
    def flush(self):
        sys.__stderr__.flush()
sys.stderr = FilteredStderr()

BASE_URL = "https://utah.bonfirehub.com/"

async def scraper():
    browser = await start(
        headless=False,          # Keep False — Xvfb handles invisibility
        browser_args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--start-maximized",
            "--lang=en-US",
            "--window-size=1920,1080",
        ],
        lang="en-US"
    )
    try:
        # Inject stealth JS before any navigation
        tab = await browser.get("about:blank")
        await tab.evaluate("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {}, app: {}, csi: () => {}, loadTimes: () => {} };
        """)

        print("Opening main page...")
        tab = await browser.get("https://utah.bonfirehub.com/portal/?tab=openOpportunities")
        await asyncio.sleep(20)

        html_content = await tab.get_content()
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.select("table#DataTables_Table_0 tbody tr")
        print(f"Found {len(table)} rows")

        links = []
        for row in table[:3]:
            anchor = row.find("a", href=True)
            if anchor:
                full_url = urljoin(BASE_URL, anchor["href"])
                links.append(full_url)

        print(f"Found {len(links)} links:")
        for l in links:
            print(f"  - {l}")

        all_data = []
        for i, link in enumerate(links):
            print(f"\n[{i+1}/{len(links)}] Visiting: {link}")
            try:
                tab = await browser.get(link)
                await asyncio.sleep(25)
                sub_html = await tab.get_content()
                sub_soup = BeautifulSoup(sub_html, "html.parser")
                detail_section = sub_soup.select("div.modalSection.projectDetailSection")
                if detail_section:
                    for section in detail_section:
                        # print(f"  Extracted: {section.get_text(strip=True)[:200]}...")
                        all_data.append({"url": link, "content": section.get_text(strip=True)})
                else:
                    print("  No detail section found.")
            except Exception as e:
                print(f"  Error on {link}: {e}")

        print(f"\n===== SCRAPED {len(all_data)} SECTIONS =====")
        for item in all_data:
            print(f"\nURL: {item['url']}")
            print(f"Content: {item['content'][:500]}")
            print("-" * 60)
    finally:
        browser.stop()
        if USE_VDISPLAY:
            vdisplay.stop()

if __name__ == "__main__":
    asyncio.run(scraper())
