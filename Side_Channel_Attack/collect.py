import time
import json
import os
import signal
import sys
import random
import traceback
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
import database
from database import Database

WEBSITES = [
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

TRACES_PER_SITE = 1000
FINGERPRINTING_URL = "http://localhost:5000"
OUTPUT_PATH = "dataset.json"

# Initialize the database to save trace data reliably
database.db = Database(WEBSITES)

# Flag to prevent multiple JSON exports
exported = False

""" Signal handler to ensure data is saved before quitting. """
def signal_handler(sig, frame):
    global exported
    print("\nReceived termination signal. Exiting gracefully...")
    if not exported:
        try:
            database.db.export_to_json(OUTPUT_PATH)
            exported = True
        except:
            print("Error during export on signal handler")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

"""
Some helper functions to make your life easier.
"""

def is_server_running(host='127.0.0.1', port=5000):
    """Check if the Flask server is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def setup_webdriver():
    """Set up the Selenium WebDriver with Chrome options."""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--headless=new")  # Use new headless mode
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def retrieve_traces_from_backend(driver):
    """Retrieve traces from the backend API."""
    try:
        traces = driver.execute_script("""
            return fetch('/api/get_results')
                .then(response => response.ok ? response.json() : {traces: []})
                .then(data => data.traces || [])
                .catch(() => []);
        """)
        count = len(traces) if traces else 0
        print(f"  - Retrieved {count} traces from backend API" if count else "  - No traces found in backend storage")
        return traces or []
    except InvalidSessionIdException:
        return []

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    try:
        clear_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Clear Results')]")))
        clear_button.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.XPATH, "//div[@role='alert']"), "Results cleared successfully!"))
    except InvalidSessionIdException:
        raise

def is_collection_complete():
    """Check if target number of traces have been collected."""
    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, TRACES_PER_SITE - count) 
                      for website, count in current_counts.items()}
    return sum(remaining_counts.values()) == 0

def collect_single_trace(driver, wait, website_url):
    try:
        # Load fingerprinting website only if not already on it
        if driver.current_url != FINGERPRINTING_URL:
            driver.get(FINGERPRINTING_URL)
        wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Collect Trace')]")))

        # Clear previous results
        clear_trace_results(driver, wait)

        # Click the Collect Trace button
        collect_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Collect Trace')]")))
        collect_button.click()

        # Open target website in a new tab
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(website_url)

        # Simulate user activity (random scrolling)
        for _ in range(random.randint(3, 7)):
            scroll_distance = random.randint(100, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            time.sleep(random.uniform(0.5, 2.0))

        # Switch back to fingerprinting tab
        driver.switch_to.window(driver.window_handles[0])

        # Wait for trace collection to complete
        wait.until(EC.text_to_be_present_in_element(
            (By.XPATH, "//div[@role='alert']"), "Trace collected and heatmap generated!"))

        # Retrieve trace data without downloading
        traces = retrieve_traces_from_backend(driver)

        # Close target website tab
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        return traces[-1] if traces else None, True

    except (InvalidSessionIdException, WebDriverException) as e:
        print(f"Error collecting trace for {website_url}: {str(e)}")
        return None, False
    except Exception as e:
        print(f"Error collecting trace for {website_url}: {str(e)}")
        return None, False

def collect_fingerprints(driver, target_counts=None):
    if target_counts is None:
        target_counts = {website: TRACES_PER_SITE for website in WEBSITES}

    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, target_counts.get(website, TRACES_PER_SITE) - current_counts.get(website, 0))
                       for website in WEBSITES}
    
    total_collected = 0
    wait = WebDriverWait(driver, 10)

    while any(remaining_counts[website] > 0 for website in WEBSITES):
        for website in WEBSITES:
            if remaining_counts[website] > 0:
                print(f"Collecting trace for {website}...")
                try:
                    trace, success = collect_single_trace(driver, wait, website)
                    if success and trace:
                        database.db.save_trace(website, WEBSITES.index(website), trace)
                        total_collected += 1
                        remaining_counts[website] -= 1
                        # Print current counts
                        current_counts = database.db.get_traces_collected()
                        print(f"Current trace counts: {current_counts}")
                        print(f"Total traces collected: {sum(current_counts.values())}")
                    else:
                        print(f"Failed to collect trace for {website}")
                except (InvalidSessionIdException, WebDriverException):
                    print(f"Session invalid for {website}, restarting WebDriver...")
                    driver.quit()
                    driver = setup_webdriver()
                    wait = WebDriverWait(driver, 10)
                    continue
                time.sleep(1)  # Avoid overwhelming the server

    return total_collected

def main():
    global exported
    if not is_server_running():
        print("Flask server is not running. Please start the server at http://localhost:5000")
        sys.exit(1)

    database.db.init_database()
    driver = None

    try:
        driver = setup_webdriver()
        while not is_collection_complete():
            print("Starting trace collection...")
            collected = collect_fingerprints(driver)
            print(f"Collected {collected} new traces")
            if collected == 0:
                print("No new traces collected, exiting...")
                break
        if not exported:
            database.db.export_to_json(OUTPUT_PATH)
            exported = True
            print("Collection complete and data exported to", OUTPUT_PATH)

    except Exception as e:
        print(f"Error during collection: {str(e)}")
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        if not exported:
            database.db.export_to_json(OUTPUT_PATH)
            exported = True

if __name__ == "__main__":
    main()