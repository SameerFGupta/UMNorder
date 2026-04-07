import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from playwright.sync_api import sync_playwright
import backend.automation as automation

# Set up mock target
MOCK_URL = f"file://{os.path.abspath('mock_site.html')}"
automation.TARGET_URL = MOCK_URL
automation.HEADLESS_MODE = True

def benchmark_navigation():
    times = []
    with sync_playwright() as p:
        browser, page = automation.setup_browser(p)
        try:
            for _ in range(3):
                start_time = time.time()

                # Navigate and wait for location logic
                automation.navigate_and_select_location(page, None)

                duration = time.time() - start_time
                times.append(duration)
                print(f"Run {len(times)}: {duration:.3f}s")
        finally:
            browser.close()

    avg_time = sum(times) / len(times)
    print(f"Average time: {avg_time:.3f}s")

if __name__ == "__main__":
    benchmark_navigation()
