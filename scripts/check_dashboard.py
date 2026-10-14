"""Meaningful local browser smoke checks with isolated headless Chrome.

Run the backend first, then python -m scripts.check_dashboard.
Requires optional playwright and an installed Chrome/Edge executable.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from backend.config import DATASET_DIR, ROOT


def check():
    candidates = [Path(os.getenv("SPEECH_CHROME_PATH", "C:/Program Files/Google/Chrome/Application/chrome.exe")),
                  Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")]
    browser_path = next((path for path in candidates if path.exists()), None)
    if browser_path is None:
        raise ValueError("Set SPEECH_CHROME_PATH to an installed Chrome/Chromium executable")
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    errors = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(browser_path), headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        page.wait_for_selector("#baseline option[value='demo_001']")
        assert page.locator("#transcript-input").input_value().startswith("Small steps")
        page.click("button[data-level='1']")
        page.wait_for_selector("#results:not([hidden])", timeout=60000)
        page.wait_for_function("!document.querySelector('#analyze-button').disabled")
        assert page.locator(".flaw-card").count() > 0
        assert "synthetic" in page.locator("#warnings").inner_text().lower()
        page.click("[data-feature='speech_rate']")
        assert page.locator("#feature-chart svg").count() == 1
        page.wait_for_function("document.querySelector('#player').readyState >= 1")
        page.click("[data-word='3']")
        assert page.locator("#player").evaluate("el => el.currentTime") > 0
        page.locator("#player").evaluate("el => el.pause()")
        with page.expect_download() as info:
            page.click("#export-button")
        downloaded = info.value
        downloaded.save_as(str(output / "browser-analysis.json"))
        assert json.loads((output / "browser-analysis.json").read_text())["flaw_regions"]
        page.screenshot(path=str(output / "dashboard-desktop.png"), full_page=True)
        # Exercise actual multipart upload with supplied timestamps.
        folder = DATASET_DIR / "speeches/demo_001/flawed_level_2"
        page.set_input_files("#audio-file", str(folder / "audio.wav"))
        page.select_option("#alignment-mode", "provided")
        page.set_input_files("#alignment-file", str(folder / "alignment.json"))
        page.click("#analyze-button")
        page.wait_for_function("!document.querySelector('#analyze-button').disabled", timeout=60000)
        assert page.locator("#error").is_hidden(), page.locator("#error").inner_text()
        # A bad transcript must show a useful server validation error.
        page.fill("#transcript-input", "This transcript does not match")
        page.click("#analyze-button")
        page.wait_for_selector("#error:not([hidden])", timeout=60000)
        assert "match" in page.locator("#error").inner_text().lower()
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(output / "dashboard-mobile.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert errors == [], errors
        browser.close()
    print("Browser checks passed: fixture, real multipart upload, errors, chart switching, playback seek, export, mobile layout, no page exceptions")


if __name__ == "__main__":
    check()
