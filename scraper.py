import nodriver as uc
from nodriver import start
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import asyncio
import sys
import os
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080, colordepth=24)
    vdisplay.start()
    os.environ["DISPLAY"] = ":99"
    USE_VDISPLAY = True
    print("Virtual display started")
except ImportError:
    USE_VDISPLAY = False
    print("xvfbwrapper not found")

class FilteredStderr:
    def write(self, msg):
        if "I/O operation on closed pipe" not in msg and "unclosed transport" not in msg:
            sys.__stderr__.write(msg)
    def flush(self):
        sys.__stderr__.flush()
sys.stderr = FilteredStderr()

BASE_URL  = "https://utah.bonfirehub.com/"
CAPSOLVER_API_KEY      = os.environ.get("CAPSOLVER_API_KEY", "")
CAPSOLVER_EXTENSION    = "/opt/capsolver/extension"

async def wait_for_cloudflare(tab, timeout=120):
    """Poll until Cloudflare challenge clears."""
    for attempt in range(timeout // 2):
        await asyncio.sleep(2)
        try:
            title = await tab.evaluate("document.title")
            print(f"  [{attempt*2}s] Title: {title}")
            if title and "just a moment" not in title.lower():
                print(f"  ✓ Cloudflare cleared after {attempt*2}s")
                return True
        except Exception:
            pass
    return False

async def scraper():
    # ── Configure Capsolver extension before launch ───────────────────────────
    capsolver_config = os.path.join(CAPSOLVER_EXTENSION, "assets", "config.js")
    if CAPSOLVER_API_KEY and os.path.exists(capsolver_config):
        with open(capsolver_config, "r") as f:
            config_content = f.read()
        config_content = config_content.replace(
            "apiKey: ''",
            f"apiKey: '{CAPSOLVER_API_KEY}'"
        )
        with open(capsolver_config, "w") as f:
            f.write(config_content)
        print(f"Capsolver configured with API key")
    else:
        print("Warning: Capsolver API key not set or extension not found")

    browser = await start(
        headless=False,   # Xvfb provides the virtual display
        browser_args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            f"--load-extension={CAPSOLVER_EXTENSION}",
            f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
            "--start-maximized",
            "--lang=en-US",
            "--window-size=1920,1080",
        ],
        lang="en-US"
    )

    try:
        # Stealth injection
        tab = await browser.get("about:blank")
        await tab.evaluate("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
            window.chrome = { runtime:{}, app:{}, csi:()=>{}, loadTimes:()=>{} };
        """)

        # ── Load listing page ─────────────────────────────────────────────────
        print("Opening main page...")
        tab = await browser.get(
            "https://utah.bonfirehub.com/portal/?tab=openOpportunities"
        )

        # Wait for listing CF to clear
        cleared = await wait_for_cloudflare(tab, timeout=120)
        if not cleared:
            print("Main page Cloudflare never cleared. Exiting.")
            return

        await asyncio.sleep(10)  # let JS render table

        html_content = await tab.get_content()
        soup = BeautifulSoup(html_content, "html.parser")
        table = soup.select("table#DataTables_Table_0 tbody tr")
        print(f"Found {len(table)} rows")

        links = []
        for row in table[:1]:
            anchor = row.find("a", href=True)
            if anchor:
                full_url = urljoin(BASE_URL, anchor["href"])
                links.append(full_url)

        print(f"Found {len(links)} links:")
        for l in links:
            print(f"  - {l}")

        # ── Scrape each detail page ───────────────────────────────────────────
        all_data = []
        for i, link in enumerate(links):
            print(f"\n[{i+1}/{len(links)}] Visiting: {link}")
            detail_tab = None
            try:
                # Open in new tab — inherits session cookies
                detail_tab = await browser.get(link, new_tab=True)

                # Capsolver auto-solves CF challenge in background
                cleared = await wait_for_cloudflare(detail_tab, timeout=120)
                if not cleared:
                    print("  ✗ Cloudflare never cleared, skipping.")
                    continue

                await asyncio.sleep(8)  # let JS render content

                # Extract via JS from live DOM
                js_content = await detail_tab.evaluate("""
                    (() => {
                        const sections = document.querySelectorAll(
                            'div.modalSection.projectDetailSection'
                        );
                        return Array.from(sections).map(s => s.innerText.trim());
                    })()
                """)

                if js_content and any(js_content):
                    for content in js_content:
                        if content:
                            print(f"  ✓ Extracted: {content[:200]}...")
                            all_data.append({"url": link, "content": content})
                else:
                    print("  No detail section found.")

            except Exception as e:
                print(f"  Error on {link}: {e}")
            finally:
                if detail_tab:
                    try:
                        await detail_tab.close()
                    except Exception:
                        pass

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
