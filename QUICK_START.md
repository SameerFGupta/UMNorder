# Quick Start Guide

## Running the Website

1. **Start the server:**
   ```bash
   python run.py
   ```

2. **Open your browser:**
   Go to `http://localhost:8000` or `http://127.0.0.1:8000`
   
   ⚠️ **Important:** Use `localhost` or `127.0.0.1`, NOT `0.0.0.0`!

3. **The browser will pop up automatically** when you place orders (for testing/debugging)

## Using the Website

### Step 1: Add a User
1. Click the **"Users"** tab
2. Enter your name and phone number
3. Click **"Add User"**

### Step 2: Create a Preset
1. Click the **"Create Preset"** tab
2. Select a user from the dropdown
3. Enter a preset name (e.g., "My Favorite Meal")
4. Click **"+ Add Item"** for each item you want
5. For each item:
   - **Item Name**: Enter exactly as it appears on the menu (e.g., "Hamburger")
   - **Modifiers**: Optional, comma-separated (e.g., "Bun, American Cheese")
6. Click **"Create Preset"**

### Step 3: Place an Order
1. Click the **"My Presets"** tab
2. Find your preset
3. Click **"🚀 ORDER NOW"**
4. **Watch the browser window** that pops up - you'll see the automation in action!
5. Wait for the success/error message

## Browser Visibility

By default, the browser **will pop up** when placing orders so you can see what's happening.

- **To see the browser** (default): Just run `python run.py` - no configuration needed!
- **To hide the browser**: Set environment variable `HEADLESS=true` before running

### Windows PowerShell:
```powershell
# Show browser (default)
python run.py

# Hide browser
$env:HEADLESS="true"
python run.py
```

### Windows CMD:
```cmd
# Show browser (default)
python run.py

# Hide browser
set HEADLESS=true
python run.py
```

### Linux/Mac:
```bash
# Show browser (default)
python run.py

# Hide browser
HEADLESS=true python run.py
```

## Testing

You can also test the automation directly:
```bash
python test_automation.py
```

Edit `test_automation.py` to customize test items and modifiers.
