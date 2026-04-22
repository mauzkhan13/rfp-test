import asyncio
import os
import shutil
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080, colordepth=24)
    vdisplay.start()
    os.environ["DISPLAY"] = ":99"
    USE_VDISPLAY = True
    print("✓ Virtual display started")
except Exception as e:
    USE_VDISPLAY = False
    print(f"✗ Xvfb failed: {e}")

import nodriver as uc
from nodriver import Browser, Config

CAPSOLVER_API_KEY   = "CAP-4DA12EBE6D7D01089210F3BECC75A576CD4542D38CCFB4BFB0E03372A78BFA03"
CAPSOLVER_EXTENSION = "/opt/capsolver/extension"

async def scraper():
    print(f"DISPLAY: {os.environ.get('DISPLAY')}")
    print(f"UID    : {os.getuid()}")

    chrome = (
        shutil.which("chromium") or
        shutil.which("chromium-browser") or
        "/usr/bin/chromium"
    )
    print(f"Chrome : {chrome}")

    # ── Configure Capsolver ───────────────────────────────────────────────────
    config_path = os.path.join(CAPSOLVER_EXTENSION, "assets", "config.js")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        if "apiKey: ''" in content:
            content = content.replace("apiKey: ''", f"apiKey: '{CAPSOLVER_API_KEY}'")
            with open(config_path, "w") as f:
                f.write(content)
        print("✓ Capsolver configured")
    else:
        print(f"✗ config.js not found")

    # ── Build config manually — bypasses root user check ─────────────────────
    config = Config(
        headless=False,
        browser_executable_path=chrome,
        add_arguments=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
            f"--load-extension={CAPSOLVER_EXTENSION}",
            f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
            "--window-size=1920,1080",
            "--lang=en-US",
        ]
    )
    config.sandbox = False  # force disable sandbox check

    print("Starting browser...")
    browser = await Browser.create(config)
    print("✓ Browser started")

    try:
        tab = await browser.get("https://utah.bonfirehub.com/opportunities/230771")

        for attempt in range(40):
            await asyncio.sleep(2)
            title = await tab.evaluate("document.title")
            print(f"  [{attempt*2}s] Title: {title}")
            if title and "just a moment" not in title.lower():
                print(f"  ✓ Cloudflare cleared!")
                break
        else:
            print("  ✗ Cloudflare never cleared")
            return

        await asyncio.sleep(5)

        result = await tab.evaluate("""
            (() => {
                const el = document.querySelector('div.modalSection.projectDetailSection');
                return el ? '✓ FOUND: ' + el.innerText.substring(0, 300) : '✗ Not found';
            })()
        """)
        print(f"Result: {result}")

    finally:
        browser.stop()
        if USE_VDISPLAY:
            vdisplay.stop()

if __name__ == "__main__":
    asyncio.run(scraper())
