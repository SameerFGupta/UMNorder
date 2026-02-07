@echo off
REM Setup script for UMN Order (Windows)

echo Setting up UMN Order...

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium

echo Setup complete!
echo Run 'python run.py' to start the application
