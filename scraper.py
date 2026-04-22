import asyncio 
import os
import shutil
import warnings
import subprocess
import time
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

from nodriver import start

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

    # ── Start Chrome manually and connect via CDP ─────────────────────────────
    import json
    import aiohttp
    
    # Create user data directory
    user_data_dir = "/tmp/chrome-profile"
    os.makedirs(user_data_dir, exist_ok=True)
    
    # Start Chrome with remote debugging
    chrome_args = [
        chrome,
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        f"--load-extension={CAPSOLVER_EXTENSION}",
        f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
        "--window-size=1920,1080",
        "--lang=en-US",
        "--disable-blink-features=AutomationControlled",
        "--disable-infobars",
        "--disable-breakpad",
        "--disable-crash-reporter",
    ]
    
    print("Starting Chrome process...")
    chrome_process = subprocess.Popen(
        chrome_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":99")}
    )
    
    # Wait for Chrome to start
    await asyncio.sleep(3)
    
    # Connect to Chrome via CDP
    print("Connecting to Chrome via CDP...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9222/json/version") as resp:
                data = await resp.json()
                ws_url = data["webSocketDebuggerUrl"]
                print(f"WebSocket URL: {ws_url}")
                
                # Connect using nodriver's browser
                from nodriver.core.browser import Browser
                from nodriver.core.config import Config
                
                config = Config(
                    headless=False,
                    no_sandbox=True,
                    browser_executable_path=chrome,
                    user_data_dir=user_data_dir,
                    connection_url=ws_url,  # Connect to existing instance
                )
                
                browser = await Browser.create(config)
                print("✓ Browser connected successfully")
                
    except Exception as e:
        print(f"Failed to connect via CDP: {e}")
        # Fallback: Let nodriver start it
        print("Falling back to nodriver start...")
        browser = await start(
            headless=False,
            no_sandbox=True,
            browser_executable_path=chrome,
            browser_args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                f"--load-extension={CAPSOLVER_EXTENSION}",
                f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
                "--window-size=1920,1080",
                "--lang=en-US",
                "--remote-debugging-port=9223",  # Different port
            ],
            lang="en-US"
        )

    try:
        page = await browser.get("https://utah.bonfirehub.com/opportunities/230771")
        
        for attempt in range(40):
            await asyncio.sleep(2)
            title = await page.evaluate("document.title")
            print(f"  [{attempt*2}s] Title: {title}")
            if title and "just a moment" not in title.lower():
                print(f"  ✓ Cloudflare cleared!")
                break
        else:
            print("  ✗ Cloudflare never cleared")
            return

        await asyncio.sleep(5)

        result = await page.evaluate("""
            (() => {
                const el = document.querySelector('div.modalSection.projectDetailSection');
                return el ? '✓ FOUND: ' + el.innerText.substring(0, 300) : '✗ Not found';
            })()
        """)
        print(f"Result: {result}")

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        await browser.stop()
        chrome_process.terminate()
        if USE_VDISPLAY:
            vdisplay.stop()

if __name__ == "__main__":
    asyncio.run(scraper())
