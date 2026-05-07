#!/usr/bin/env python3
"""Screenshot script for Neshama dashboard"""

from playwright.sync_api import sync_playwright
import time

def take_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # Screenshot 1: Dashboard (home page)
        print("Taking screenshot of dashboard...")
        page.goto("http://localhost:8420", wait_until="networkidle", timeout=30000)
        time.sleep(2)  # Wait for animations
        page.screenshot(path="./Neshama/demo-screenshots/dashboard.png", full_page=False)
        print("Dashboard screenshot saved.")
        
        # Screenshot 2: Demo page
        print("Taking screenshot of demo page...")
        page.goto("http://localhost:8420#demo", wait_until="networkidle", timeout=30000)
        time.sleep(3)  # Wait for animations
        page.screenshot(path="./Neshama/demo-screenshots/demo.png", full_page=False)
        print("Demo screenshot saved.")
        
        browser.close()
        print("Done!")

if __name__ == "__main__":
    take_screenshots()
