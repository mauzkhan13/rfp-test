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

from nodriver import start, Browser

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

    # ── Test Chrome manually before nodriver ─────────────────────────────────
    print("Testing Chrome directly...")
    import subprocess
    result = subprocess.run([
        chrome,
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--headless=new",
        "--dump-dom",
        "about:blank"
    ], capture_output=True, text=True, timeout=15)
    print(f"Chrome exit code: {result.returncode}")
    if result.returncode != 0:
        print(f"Chrome stderr: {result.stderr[:500]}")
    else:
        print("✓ Chrome manual test passed")
    
    # ── Start nodriver with more explicit configuration ─────────────────────
    print("Starting browser via nodriver...")
    
    # Create user data directory for persistent profile
    user_data_dir = "/tmp/chrome-profile"
    os.makedirs(user_data_dir, exist_ok=True)
    
    browser_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-blink-features=AutomationControlled",
        f"--load-extension={CAPSOLVER_EXTENSION}",
        f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
        "--window-size=1920,1080",
        "--lang=en-US",
        "--remote-debugging-port=9222",  # Add remote debugging
        f"--user-data-dir={user_data_dir}",
        "--disable-infobars",
        "--disable-breakpad",
        "--disable-crash-reporter",
    ]
    
    try:
        browser = await start(
            headless=False,
            no_sandbox=True,
            browser_executable_path=chrome,
            browser_args=browser_args,
            lang="en-US",
            user_data_dir=user_data_dir,
        )
        print("✓ Browser started")
    except Exception as e:
        print(f"Failed to start browser: {e}")
        # Try alternative method
        print("Trying alternative start method...")
        from nodriver.core.config import Config
        config = Config(
            headless=False,
            no_sandbox=True,
            browser_executable_path=chrome,
            arguments=browser_args,
            user_data_dir=user_data_dir,
        )
        browser = await Browser.create(config)
        print("✓ Browser started with alternative method")

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
        if USE_VDISPLAY:
            vdisplay.stop()

if __name__ == "__main__":
    asyncio.run(scraper())
