"""
jklm.fun BombParty word finder - prints the best word AND types it out
using pyautogui (real OS-level keystrokes), so it works even if Selenium
can't locate the game's answer input box in the DOM.

Run:
    python bombparty_bot.py

Enter the room code when asked. From then on, every time the in-game
syllable changes, this finds the longest dictionary word containing it,
prints it, then uses pyautogui to type it out on your actual keyboard
(as if you typed it) and presses Enter.

IMPORTANT: pyautogui types wherever your OS currently has keyboard
focus. That means the BombParty answer box in your browser must
actually be focused/clicked when each word gets typed - the bot does
not know how to click it for you. Click into the answer box once after
the round starts, then don't click anywhere else while it's running.

Setup (one-time):
    pip install selenium pyautogui
    Install Chrome + a matching chromedriver:
        https://googlechromelabs.github.io/chrome-for-testing/
"""

import re
import sys
import time
from pathlib import Path
import random

import pyautogui
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


POLL_INTERVAL = 0.15
TYPE_INTERVAL = 0.001  # seconds between simulated keystrokes

DICT_FILE = Path(__file__).parent / "dict.txt"


def ensure_dictionary() -> list[str]:
    if not DICT_FILE.exists():
        sys.exit(f"Dictionary not found: {DICT_FILE}")

    words = []
    with DICT_FILE.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            w = line.strip().lower()
            if w and re.fullmatch(r"[a-z]+(-[a-z]+)*", w):
                words.append(w)
    print(f"Loaded {len(words):,} words from {DICT_FILE.name}")
    return words


def best_word(words: list[str], syllable: str) -> str | None:
    syllable = syllable.lower()
    matches = [w for w in words if syllable in w]
    if not matches:
        return None
    return max(matches, key=len)


def build_room_url(arg: str) -> str:
    arg = arg.strip()
    if arg.startswith("http://") or arg.startswith("https://"):
        return arg
    return f"https://jklm.fun/{arg}"


def enter_game_iframe(driver, timeout: int = 30):
    wait = WebDriverWait(driver, timeout)
    iframe = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.game iframe"))
    )
    driver.switch_to.frame(iframe)


def get_syllable_element(driver, timeout: int = 30):
    wait = WebDriverWait(driver, timeout)
    return wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.round div.syllable"))
    )


def run():
    words = ensure_dictionary()
    room = input("Enter room code or full jklm.fun URL: ").strip()
    room_url = build_room_url(room)

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    driver = webdriver.Chrome(options=options)
    driver.get(room_url)

    enter_game_iframe(driver)
    get_syllable_element(driver)

    print("Click into the game's answer box now. Starting in 5 seconds...")
    time.sleep(5)

    last_value = None
    try:
        while True:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, "div.round div.syllable")
                current_value = elem.text.strip()
            except (NoSuchElementException, StaleElementReferenceException):
                time.sleep(POLL_INTERVAL)
                continue

            if current_value and current_value != last_value:
                last_value = current_value
                word = best_word(words, current_value)
                if word:
                    print(word)
                    pyautogui.typewrite(word, interval=TYPE_INTERVAL)

            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        pass
    finally:
        driver.quit()


if __name__ == "__main__":
    run()

    