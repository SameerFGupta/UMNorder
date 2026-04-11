# UMN Order - Automated Food Ordering System

A web automation wrapper that allows you to save order presets and place orders on [mobile.tapin2.co](https://mobile.tapin2.co/1238) with a single click. Enables autonomous orders at all University of Minnesota dining halls.

## Features

- **Save Order Presets**: Create reusable presets with your favorite items
- **User Management**: Store multiple users with their contact information
- **One-Click Ordering**: Place orders instantly with a single button click
- **Cooldown Tracking**: Automatically prevents orders within the 30-minute cooldown period
- **Browser Automation**: Uses Playwright to automate the ordering process

## Architecture

- **Backend**: FastAPI (Python) with SQLite database
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Automation**: Playwright for browser automation
- **Deployment**: Docker container ready

## Setup Instructions

### Local Development

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```
   Or:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. **Access the website:**
   Open your browser and go to:
   - `http://localhost:8000` (recommended)
   - or `http://127.0.0.1:8000`

5. **Browser visibility (for testing):**
   By default, the browser will pop up when placing orders (headless=False) so you can see what's happening.
   - To see the browser during orders: Leave `HEADLESS` unset or set `HEADLESS=false` (default)
   - To hide the browser: Set `HEADLESS=true` before running
   
   On Windows PowerShell:
   ```powershell
   $env:HEADLESS="false"  # Show browser (default)
   python run.py
   ```
   
   On Windows CMD:
   ```cmd
   set HEADLESS=false
   python run.py
   ```
   
   On Linux/Mac:
   ```bash
   HEADLESS=false python run.py
   ```

6. **Test the automation (optional):**
   You can also test the automation directly:
   ```bash
   python test_automation.py
   ```
   This will open a browser and test the automation with sample items.

### Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t umnorder .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 umnorder
   ```

3. **For production with persistent database:**
   ```bash
   docker run -p 8000:8000 -v $(pwd)/data:/app umnorder
   ```

## Usage

### Using the Web Interface

1. **Start the server:**
   ```bash
   python run.py
   ```

2. **Open the website:**
   Navigate to `http://localhost:8000` in your browser

3. **Add a User:**
   - Click the "Users" tab
   - Enter your name and phone number
   - Click "Add User"

4. **Create a Preset:**
   - Click the "Create Preset" tab
   - Select a user from the dropdown
   - Enter a preset name (e.g., "Late Night Snack")
   - Click "+ Add Item" to add items
   - For each item:
     - Enter the item name exactly as it appears on the menu (e.g., "Hamburger")
     - Optionally add modifiers (comma-separated, e.g., "Bun, American Cheese")
   - Click "Create Preset"

5. **Place an Order:**
   - Click the "My Presets" tab
   - Find your preset card
   - Click the "🚀 ORDER NOW" button
   - **A browser window will pop up** showing the automation in action (if HEADLESS=false)
   - Wait for the automation to complete (usually 10-20 seconds)
   - You'll see a success or error message when done

### Testing with test_automation.py

You can also test the automation directly:
```bash
python test_automation.py
```

This will open a browser and test with sample items. Edit `test_automation.py` to customize the test items.

## Important Notes

### Cooldown System
- The system enforces a 30-minute cooldown per phone number
- If you try to order within 30 minutes, you'll see a cooldown message
- The cooldown is checked both in the app and on the target website

### Item Names
- **Critical**: Item names must match exactly as they appear on the menu
- The automation searches for items by text matching
- If an item isn't found, the order will fail for that item
- **Tip**: Visit the target website first and copy the exact item names as they appear

### Website Changes
- If the target website (mobile.tapin2.co) changes its structure, the automation may break
- You may need to update the selectors in `backend/automation.py`
- The automation uses multiple fallback selectors, but if the site structure changes significantly, manual updates will be needed
- To debug, set `headless=False` in `automation.py` and watch the browser interact with the site

## API Endpoints

- `GET /api/users` - Get all users
- `POST /api/users` - Create a new user
- `GET /api/presets` - Get all presets
- `POST /api/presets` - Create a new preset
- `GET /api/presets/{id}` - Get a specific preset
- `DELETE /api/presets/{id}` - Delete a preset
- `POST /api/order` - Place an order using a preset
- `GET /api/order-history` - Get order history

## Troubleshooting

### Order Fails
1. Check that item names match exactly
2. Verify your phone number is correct
3. Check if you're within the 30-minute cooldown
4. Review the error message in the status modal

### Automation Errors
- The website structure may have changed
- Check the browser console for detailed error messages
- You may need to update selectors in `backend/automation.py`

### Database Issues
- The database file (`umnorder.db`) is created automatically
- If you need to reset, delete the database file and restart the app

## Security Considerations

- This tool is designed for personal use
- Do not abuse the ordering system
- Respect the 30-minute cooldown

## License

This project is for personal use only. Use responsibly and in accordance with the terms of service of the target website.
