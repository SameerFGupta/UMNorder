"""
Test script to verify the automation works with the target website.
Run this before deploying to ensure the selectors are correct.

Usage:
    python test_automation.py
"""
from backend.automation import run_order_automation

# Test with dummy data (won't actually place an order if you use a fake phone number)
# IMPORTANT: Replace with EXACT item names as they appear in the menu
# Item names must match the data-title attribute in the HTML (e.g., "Hamburger", "Fish Sandwich", "Grilled Cheese")
# You can find these by inspecting the menu page or checking the Context/stages/Stage 2.html file

# Items can be strings (old format) or dicts with name and modifiers (new format)
test_items = [
    {
        "name": "Hamburger",
        "modifiers": ["Bun"]  # Select "Bun" modifier - use exact text as it appears in the modal
        # Alternative: ["No Bun"] to select "No Bun" instead
    },
    "Basket of Fries (limit 1)",   # Old format still works (no modifiers)
]

print("Testing automation...")
print("NOTE: This will open a browser. Make sure you can see it to verify the process.")
print("Using headless=False for testing...")

# You can modify automation.py temporarily to set headless=False for testing
result = run_order_automation(
    name="Test User",
    phone_number="1234567890",  # Use a test number
    items=test_items
)

print(f"\nResult: {result}")
print(f"Success: {result['success']}")
print(f"Message: {result['message']}")
