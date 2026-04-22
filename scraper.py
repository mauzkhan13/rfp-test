import asyncio
import os
import sys
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

# ── Virtual display ───────────────────────────────────────────────────────────
try:
    from xvfbwrapper import Xvfb
    vdisplay = Xvfb(width=1920, height=1080, colordepth=24)
    vdisplay.start()
    os.environ["DISPLAY"] = ":99"
    USE_VDISPLAY = True
    print("✓ Virtual display started on :99")
except Exception as e:
    USE_VDISPLAY = False
    print(f"✗ Xvfb failed: {e}")

from nodriver import start
import nodriver as uc

CAPSOLVER_API_KEY  = "CAP-4DA12EBE6D7D01089210F3BECC75A576CD4542D38CCFB4BFB0E03372A78BFA03"  
CAPSOLVER_EXTENSION = "/opt/capsolver/extension"

async def scraper():
    # ── Configure Capsolver ───────────────────────────────────────────────────
    config_path = os.path.join(CAPSOLVER_EXTENSION, "assets", "config.js")
    print(f"Looking for config at: {config_path}")
    print(f"Extension folder exists: {os.path.exists(CAPSOLVER_EXTENSION)}")
    print(f"Config file exists: {os.path.exists(config_path)}")

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        if "apiKey: ''" in content:
            content = content.replace("apiKey: ''", f"apiKey: '{CAPSOLVER_API_KEY}'")
            with open(config_path, "w") as f:
                f.write(content)
        print("✓ Capsolver API key configured")
    else:
        print("✗ config.js not found — listing extension folder:")
        for root, dirs, files in os.walk(CAPSOLVER_EXTENSION):
            for f in files:
                print(f"  {os.path.join(root, f)}")

    # ── Find Chrome binary ────────────────────────────────────────────────────
    import shutil
    chrome_path = (
        shutil.which("chromium") or
        shutil.which("chromium-browser") or
        shutil.which("google-chrome") or
        "/usr/bin/chromium"
    )
    print(f"✓ Chrome binary: {chrome_path}")
    print(f"✓ Chrome exists: {os.path.exists(chrome_path)}")
    print(f"✓ DISPLAY env: {os.environ.get('DISPLAY', 'NOT SET')}")
    print(f"✓ Running as UID: {os.getuid()}")

    # ── Start browser ─────────────────────────────────────────────────────────
    print("Starting browser...")
    try:
        browser = await start(
            headless=False,
            no_sandbox=True,
            browser_executable_path=chrome_path,
            browser_args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                f"--load-extension={CAPSOLVER_EXTENSION}",
                f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
                "--window-size=1920,1080",
                "--lang=en-US",
            ],
            lang="en-US"
        )
        print("✓ Browser started successfully")
    except Exception as e:
        print(f"✗ Browser start failed: {e}")
        raise

    try:
        print("Opening Cloudflare page...")
        tab = await browser.get("https://utah.bonfirehub.com/opportunities/230771")

        for attempt in range(40):
            await asyncio.sleep(2)
            title = await tab.evaluate("document.title")
            print(f"  [{attempt*2}s] Title: {title}")
            if title and "just a moment" not in title.lower():
                print(f"  ✓ Cloudflare cleared after {attempt*2}s!")
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
        print(f"\nResult: {result}")

    finally:
        browser.stop()
        if USE_VDISPLAY:
            vdisplay.stop()

if __name__ == "__main__":
    asyncio.run(scraper())
