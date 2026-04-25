import os
import subprocess
import nodriver as uc
import asyncio

async def main():
    browser = await uc.start(
        headless=False,
        browser_args=[
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )

    try:
        page = await browser.get('https://utah.bonfirehub.com/opportunities/230771')
        await page.wait(10)
        title = await page.evaluate("document.title")
        print(f"Title: {title}")
    finally:
        browser.stop()

if __name__ == '__main__':
    # Launch Xvfb manually
    xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1920x1080x24'])
    os.environ['DISPLAY'] = ':99'

    try:
        uc.loop().run_until_complete(main())
    finally:
        xvfb.terminate()
