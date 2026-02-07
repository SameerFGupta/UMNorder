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

def normalize_text(text):
    """Helper to normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip().replace("  ", " ").replace("-", "")

def select_modifiers_in_modal(page, item_name, item_modifiers):
    if not item_modifiers:
        return True
    
    logger.info(f"Selecting modifiers for {item_name}: {item_modifiers}")
    time.sleep(2)
    
    all_selected = True
    for modifier_name in item_modifiers:
        try:
            modifier_found = False
            norm_mod_name = normalize_text(modifier_name)
            modifier_labels = page.locator('#product-modal label.modifier').all()
            
            for label in modifier_labels:
                label_text = label.inner_text()
                if norm_mod_name in normalize_text(label_text):
                    checkbox = label.locator('input').first
                    label.scroll_into_view_if_needed()
                    time.sleep(0.2)
                    
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
    
    time.sleep(1)
    return all_selected

def run_order_automation(name: str, phone_number: str, items: list, location_name: str = None) -> dict:
    try:
        with sync_playwright() as p:
            logger.info(f"Starting order for {name} at {location_name or 'Default'}")
            browser = p.chromium.launch(headless=HEADLESS_MODE)
            context = browser.new_context(
                viewport={"width": 375, "height": 812},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            )
            page = context.new_page()
            
            try:
                # 1. Navigate
                page.goto(TARGET_URL, wait_until="networkidle", timeout=TIMEOUT)
                time.sleep(3)

                # 2. Pickup Selection
                if page.locator("button#go-to-all-locations-button").count() > 0:
                    page.locator("button#go-to-all-locations-button").first.click()
                    time.sleep(2)
                elif page.locator("button:has-text('All Pickup Locations')").count() > 0:
                    page.locator("button:has-text('All Pickup Locations')").first.click()
                    time.sleep(2)

                # 3. Location Selection (FIXED)
                location_selected = False
                if location_name:
                    logger.info(f"Searching for location: '{location_name}'")
                    location_items = page.locator("li[id^='location']").all()
                    
                    norm_target = normalize_text(location_name)
                    
                    for loc_item in location_items:
                        loc_text_raw = loc_item.inner_text()
                        norm_loc = normalize_text(loc_text_raw)
                        
                        # FIXED: Bidirectional check (Target in Site OR Site in Target)
                        if norm_target in norm_loc or norm_loc in norm_target:
                            logger.info(f"✓ Found location match: '{loc_text_raw.splitlines()[0]}'")
                            loc_item.click()
                            location_selected = True
                            break
                    
                    if not location_selected:
                        logger.warning(f"❌ Could not find location '{location_name}'. Failing gracefully.")
                        return {"success": False, "message": f"Location '{location_name}' not found. Check spelling."}
                
                # If no location name provided, fallback to first
                if not location_selected and not location_name:
                    first_loc = page.locator("li[id^='location']").first
                    if first_loc.count() > 0:
                        logger.info(f"Selecting default location: {first_loc.inner_text().splitlines()[0]}")
                        first_loc.click()

                # Wait for menu
                page.wait_for_selector("li.item[data-title]", timeout=15000)
                time.sleep(2)

                # 4. Add Items
                items_added = 0
                for item_data in items:
                    item_name = item_data.get("name", "") if isinstance(item_data, dict) else str(item_data)
                    item_modifiers = item_data.get("modifiers", []) if isinstance(item_data, dict) else []

                    logger.info(f"Looking for item: '{item_name}'")
                    all_menu_items = page.locator("li.item[data-title]").all()
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
                        time.sleep(2)
                        
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
                            time.sleep(1)
                    else:
                        logger.warning(f"❌ Item '{item_name}' not found.")

                if items_added == 0:
                    return {"success": False, "message": "No items added to cart."}

                # 5. Checkout
                logger.info("Proceeding to checkout...")
                if page.locator("a#cart").count() > 0: page.locator("a#cart").click()
                else: page.locator("[id='cart']").click()
                time.sleep(2)
                
                if page.locator("a#continue-link").count() > 0: page.locator("a#continue-link").click()
                else: page.locator("text=Continue").click()
                time.sleep(2)
                
                if page.locator("input#name").count() > 0: page.locator("input#name").fill(name)
                if page.locator("input#phone").count() > 0: page.locator("input#phone").fill(phone_number)
                
                submit_btn = page.locator("button#continue-button")
                if submit_btn.is_disabled():
                    return {"success": False, "message": "Submit button disabled. Check phone number."}
                
                submit_btn.click()
                time.sleep(5)
                
                content = page.content().lower()
                if "thank you" in content or "confirmed" in content:
                    return {"success": True, "message": "Order placed successfully!"}
                elif "cooldown" in content or "30 min" in content:
                    return {"success": False, "message": "Blocked by 30-min cooldown."}
                
                return {"success": True, "message": "Order submitted (check phone)."}

            except Exception as e:
                logger.error(f"Automation error: {e}")
                return {"success": False, "message": f"Error: {str(e)}"}
            finally:
                browser.close()
    except Exception as e:
        return {"success": False, "message": f"Browser launch failed: {str(e)}"}