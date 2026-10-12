"""
Extract the current syllable from a jklm.fun BombParty game room, polling
for changes (the syllable updates roughly once per second).

Setup:
    pip install selenium

You also need a matching browser + webdriver:
    - Chrome + chromedriver (https://googlechromelabs.github.io/chrome-for-testing/)
    - Or Firefox + geckodriver

Usage:
    python extract_syllable.py ROOMCODE
    python extract_syllable.py "https://jklm.fun/ROOMCODE"   # full URL also works
"""

import sys
import time

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def build_driver(headless: bool = False):
    """Create a Chrome webdriver instance."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    return driver


def enter_game_iframe(driver, timeout: int = 20):
    """
    The game board lives inside:
        div.main.page > div.game > iframe (src -> phoenix.jklm.fun/games/bombparty)

    We need to switch Selenium's focus into that iframe before we can find
    .syllable, since it's a separate document.
    """
    wait = WebDriverWait(driver, timeout)

    # Wait for the iframe to exist and switch into it.
    iframe = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.game iframe"))
    )
    driver.switch_to.frame(iframe)


def get_syllable_element(driver, timeout: int = 20):
    wait = WebDriverWait(driver, timeout)
    return wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.round div.syllable"))
    )


def watch_syllable(url: str, poll_interval: float = 0.2):
    driver = build_driver(headless=False)
    driver.get(url)

    print("Waiting for the game iframe to load...")
    enter_game_iframe(driver)

    print("Waiting for the .syllable element to appear...")
    get_syllable_element(driver)  # just to confirm it's there first

    print("Watching for syllable changes. Press Ctrl+C to stop.\n")

    last_value = None
    try:
        while True:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, "div.round div.syllable")
                current_value = elem.text.strip()
            except (NoSuchElementException, StaleElementReferenceException):
                # Element temporarily gone (e.g. between rounds) - just retry.
                time.sleep(poll_interval)
                continue

            if current_value and current_value != last_value:
                last_value = current_value
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Syllable: {current_value}")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nStopped watching.")
    finally:
        driver.quit()


def build_room_url(arg: str) -> str:
    """Accepts either a bare room code (e.g. 'AbCdEf') or a full URL."""
    if arg.startswith("http://") or arg.startswith("https://"):
        return arg
    return f"https://jklm.fun/{arg}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_syllable.py <ROOM_CODE_or_full_url>")
        sys.exit(1)

    room_url = build_room_url(sys.argv[1])
    watch_syllable(room_url)