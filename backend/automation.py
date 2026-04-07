"""
Automation script to place orders on mobile.tapin2.co
"""
from playwright.sync_api import sync_playwright
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "https://mobile.tapin2.co/1238"
TIMEOUT = 30000
HEADLESS_MODE = os.getenv("HEADLESS", "false").lower() == "true"
VIEWPORT_WIDTH = 375
VIEWPORT_HEIGHT = 812
USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/14.0 Mobile/15E148 Safari/604.1"
)

def normalize_text(text):
    """We aggressively normalize text by lowercasing and stripping formatting to ensure text-matching is robust against arbitrary UI changes in spacing or casing."""
    if not text:
        return ""
    return text.lower().strip().replace("  ", " ").replace("-", "")

def select_modifiers_in_modal(page, item_name, item_modifiers):
    if not item_modifiers:
        return True
    
    logger.info(f"Selecting modifiers for {item_name}: {item_modifiers}")
    page.wait_for_selector('#product-modal label.modifier', state='visible', timeout=5000)
    
    all_selected = True

    """We cache modifier labels and their normalized text outside the loop to avoid repeated costly IPC round-trips to the browser."""
    modifier_labels = page.locator('#product-modal label.modifier').all()
    cached_labels = []
    for label in modifier_labels:
        cached_labels.append((label, normalize_text(label.inner_text())))

    for modifier_name in item_modifiers:
        try:
            modifier_found = False
            norm_mod_name = normalize_text(modifier_name)
            
            for label, norm_label_text in cached_labels:
                if norm_mod_name in norm_label_text:
                    checkbox = label.locator('input').first
                    label.scroll_into_view_if_needed()
                    
                    if checkbox.count() > 0:
                        if not checkbox.is_checked():
                            label.click(timeout=2000)
                    else:
                        label.click(timeout=2000)
                        
                    modifier_found = True
                    break
            
            if not modifier_found:
                logger.warning(f"⚠ Could not find modifier: '{modifier_name}'")
                all_selected = False
                
        except Exception as e:
            logger.warning(f"Error processing modifier {modifier_name}: {str(e)}")
            all_selected = False
    
    return all_selected

def setup_browser(p):
    """We explicitly set viewport and user-agent strings to mimic a realistic mobile device, which prevents the target site from serving a desktop layout or blocking the request."""
    browser = p.chromium.launch(headless=HEADLESS_MODE)
    context = browser.new_context(
        viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT},
        user_agent=USER_AGENT
    )
    return browser, context.new_page()

def navigate_and_select_location(page, location_name):
    page.goto(TARGET_URL, wait_until="networkidle", timeout=TIMEOUT)
    try:
        page.wait_for_selector("button#go-to-all-locations-button, button:has-text('All Pickup Locations'), li[id^='location']", state="attached", timeout=10000)
    except Exception as e:
        logger.warning(f"Timeout waiting for location elements to appear: {e}")

    if page.locator("button#go-to-all-locations-button").count() > 0:
        page.locator("button#go-to-all-locations-button").first.click()
        page.wait_for_load_state('networkidle', timeout=5000)
    elif page.locator("button:has-text('All Pickup Locations')").count() > 0:
        page.locator("button:has-text('All Pickup Locations')").first.click()
        page.wait_for_load_state('networkidle', timeout=5000)

    location_selected = False
    if location_name:
        logger.info(f"Searching for location: '{location_name}'")
        location_items = page.locator("li[id^='location']").all()

        norm_target = normalize_text(location_name)

        for loc_item in location_items:
            loc_text_raw = loc_item.inner_text()
            norm_loc = normalize_text(loc_text_raw)

            if norm_target in norm_loc or norm_loc in norm_target:
                logger.info(f"✓ Found location match: '{loc_text_raw.splitlines()[0]}'")
                loc_item.click()
                page.wait_for_load_state('networkidle', timeout=5000)
                location_selected = True
                break

        if not location_selected:
            logger.warning(f"❌ Could not find location '{location_name}'. Failing gracefully.")
            return False, f"Location '{location_name}' not found. Check spelling."

    if not location_selected and not location_name:
        first_loc = page.locator("li[id^='location']").first
        if first_loc.count() > 0:
            logger.info(f"Selecting default location: {first_loc.inner_text().splitlines()[0]}")
            first_loc.click()
            page.wait_for_load_state('networkidle', timeout=5000)

    page.wait_for_selector("li.item[data-title]", timeout=15000)
    return True, ""

def add_items_to_cart(page, items):
    items_added = 0
    all_menu_items = page.locator("li.item[data-title]").all()

    for item_data in items:
        item_name = item_data.get("name", "") if isinstance(item_data, dict) else str(item_data)
        item_modifiers = item_data.get("modifiers", []) if isinstance(item_data, dict) else []

        logger.info(f"Looking for item: '{item_name}'")
        target_item = None
        norm_target_name = normalize_text(item_name)

        for menu_item in all_menu_items:
            title = menu_item.get_attribute("data-title")
            if not title: continue
            if norm_target_name in normalize_text(title) or normalize_text(title) in norm_target_name:
                target_item = menu_item
                break

        if target_item:
            target_item.scroll_into_view_if_needed()
            target_item.click(force=True)
            page.wait_for_selector('#product-modal', state='visible', timeout=5000)

            if page.locator('#product-modal').is_visible():
                select_modifiers_in_modal(page, item_name, item_modifiers)
                add_btn = page.locator('#product-modal button.qc.btn-primary').first

                if add_btn.is_disabled():
                    logger.error(f"❌ 'Add to Cart' disabled for {item_name}. Missing modifiers?")
                    page.locator('#product-modal [data-dismiss="modal"]').click()
                    continue
                    
                add_btn.click()
                page.wait_for_selector('#product-modal', state='hidden', timeout=5000)
                items_added += 1
                logger.info(f"✓ Added {item_name}")
        else:
            logger.warning(f"❌ Item '{item_name}' not found.")

    return items_added > 0

def checkout(page, name, phone_number):
    logger.info("Proceeding to checkout...")
    if page.locator("a#cart").count() > 0: page.locator("a#cart").click()
    else: page.locator("[id='cart']").click()
    page.wait_for_load_state('domcontentloaded')

    if page.locator("a#continue-link").count() > 0: page.locator("a#continue-link").click()
    else: page.locator("text=Continue").click()
    page.wait_for_load_state('domcontentloaded')

    if page.locator("input#name").count() > 0: page.locator("input#name").fill(name)
    if page.locator("input#phone").count() > 0: page.locator("input#phone").fill(phone_number)

    submit_btn = page.locator("button#continue-button")
    if submit_btn.is_disabled():
        return False, "Submit button disabled. Check phone number."

    submit_btn.click()
    page.wait_for_url(lambda url: True, wait_until='networkidle', timeout=8000)

    content = page.content().lower()
    if "thank you" in content or "confirmed" in content:
        return True, "Order placed successfully!"
    elif "cooldown" in content or "30 min" in content:
        return False, "Blocked by 30-min cooldown."

    return True, "Order submitted (check phone)."

def run_order_automation(name: str, phone_number: str, items: list, location_name: str = None) -> dict:
    try:
        with sync_playwright() as p:
            logger.info(f"Starting order for {name} at {location_name or 'Default'}")
            browser, page = setup_browser(p)

            try:
                success, msg = navigate_and_select_location(page, location_name)
                if not success:
                    return {"success": False, "message": msg}

                if not add_items_to_cart(page, items):
                    return {"success": False, "message": "No items added to cart."}

                success, msg = checkout(page, name, phone_number)
                return {"success": success, "message": msg}

            except Exception as e:
                logger.error(f"Automation error: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
            finally:
                browser.close()
    except Exception as e:
        return {"success": False, "message": f"Browser launch failed: {str(e)}"}