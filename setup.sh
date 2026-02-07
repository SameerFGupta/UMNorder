#!/bin/bash
# Setup script for UMN Order

echo "Setting up UMN Order..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

echo "Setup complete!"
echo "Run 'python run.py' to start the application"
