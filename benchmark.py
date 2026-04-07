import time
import os
import sys

# Override target URL for testing
import backend.automation as automation
automation.TARGET_URL = "http://127.0.0.1:8001/1238"
automation.TIMEOUT = 5000
# Ensure headless
automation.HEADLESS_MODE = True

start = time.time()
result = automation.run_order_automation(
    name="Test User",
    phone_number="1234567890",
    items=["Burger", "Burger", "Burger", "Burger", "Burger"],
    location_name="Mock Location"
)
end = time.time()

print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
print(f"Time taken: {end - start:.2f} seconds")
