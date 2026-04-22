import nodriver as uc
from nodriver import start
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import asyncio
import sys
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080, colordepth=24)
    vdisplay.start()
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

BASE_URL = "https://utah.bonfirehub.com/"

async def wait_for_cloudflare(tab, timeout=80):
    """Poll until Cloudflare challenge clears. Returns True if cleared."""
    for attempt in range(timeout // 2):
        await asyncio.sleep(2)
        try:
            title = await tab.evaluate("document.title")
            print(f"  [{attempt*2}s] Title: {title}")
            if title and "just a moment" not in title.lower():
                return True
        except Exception:
            pass
    return False

async def scraper():
    browser = await start()
        
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
        tab = await browser.get("https://utah.bonfirehub.com/portal/?tab=openOpportunities")
        await asyncio.sleep(30)

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
                # Open in NEW TAB — inherits Cloudflare session cookies
                detail_tab = await browser.get(link, new_tab=True)

                cleared = await wait_for_cloudflare(detail_tab, timeout=80)
                if not cleared:
                    print("  ✗ Cloudflare never cleared, skipping.")
                    continue

                print("  ✓ Cloudflare cleared, waiting for JS render...")
                await asyncio.sleep(3)

                # Extract via JS directly from live DOM
                js_content = await detail_tab.evaluate("""
                    (() => {
                        const sections = document.querySelectorAll('div.modalSection.projectDetailSection');
                        return Array.from(sections).map(s => s.innerText.trim());
                    })()
                """)

                if js_content and any(js_content):
                    for content in js_content:
                        if content:
                            print(f"  Extracted: {content[:200]}...")
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
