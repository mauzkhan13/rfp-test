import asyncio
import os
from nodriver import start

CAPSOLVER_API_KEY = "CAP-4DA12EBE6D7D01089210F3BECC75A576CD4542D38CCFB4BFB0E03372A78BFA03"
CAPSOLVER_EXTENSION = r"C:\Users\Mauz Khan\Downloads\CapSolver.Browser.Extension-chrome-v1.17.0\capsolver_extension"

async def test_capsolver():
    config_path = os.path.join(CAPSOLVER_EXTENSION, "assets", "config.js")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            content = f.read()
        if "apiKey: ''" in content:
            content = content.replace("apiKey: ''", f"apiKey: '{CAPSOLVER_API_KEY}'")
            with open(config_path, "w") as f:
                f.write(content)
        print("✓ Capsolver API key configured")
    else:
        print(f"✗ config.js not found at: {config_path}")
        return

    browser = await start(
        headless=False,
        browser_args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            f"--load-extension={CAPSOLVER_EXTENSION}",
            f"--disable-extensions-except={CAPSOLVER_EXTENSION}",
            "--window-size=1920,1080",
            "--lang=en-US",
        ],
        lang="en-US"
    )

    try:
        print("Opening Cloudflare test page...")
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
                return el ? '✓ Element found: ' + el.innerText.substring(0, 200) : '✗ Element not found';
            })()
        """)
        print(f"\nResult: {result}")

    finally:
        input("\nPress Enter to close browser...")
        browser.stop()

if __name__ == "__main__":
    asyncio.run(test_capsolver())
