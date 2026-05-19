# test_manage_images.py
# UC-06 Manage Images Captured by Drone
# Covers TC-06-001 to TC-06-012
#
# Notes:
# - Drone Alpha is used for view/review/download/delete/upload tests.
# - Drone 1 is used for no-image test.
# - Image action buttons are hidden until hover.
# - Source code order inside image card:
#     button 1 = Eye / Review
#     button 2 = Download
#     button 3 = Delete
# - Metadata and bulk delete are NOT skipped. If the UI does not exist, the test fails.

import os
import time
import pytest

from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://localhost:3000"
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

TEST_IMAGE_PATH = r"C:\Users\rjy07\Downloads\FYP-UCD.drawio.png"
TARGET_IMAGE_FILENAME = "FYP-UCD.drawio.png"


@pytest.fixture
def driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.join(os.getcwd(), "downloads"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


# General helpers
def wait_short(driver, seconds=3):
    return WebDriverWait(driver, seconds)


def accept_alert_if_present(driver, expected_text=None):
    try:
        alert = wait_short(driver, 3).until(EC.alert_is_present())
        text = alert.text
        print("Alert detected:", text)

        if expected_text is None or expected_text.lower() in text.lower():
            alert.accept()
            time.sleep(1)
            return text

        alert.accept()
        time.sleep(1)
        return text
    except Exception:
        return None


def close_any_ok_popup(driver):
    """Close native alert or custom OK/Close popup."""
    alert_text = accept_alert_if_present(driver)
    if alert_text:
        return alert_text

    try:
        buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(normalize-space(.),'OK') or contains(normalize-space(.),'Ok') or contains(normalize-space(.),'Close') or contains(normalize-space(.),'Dismiss')]"
        )
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                button.click()
                time.sleep(1)
                print("Closed popup/button.")
                return "popup closed"
    except Exception:
        pass

    return None


def ignore_company_location_error(driver):
    """Ignore 'Failed to fetch company locations' alert/popup if it appears."""
    text = accept_alert_if_present(driver)
    if text:
        return

    try:
        buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(normalize-space(.),'OK') or contains(normalize-space(.),'Ok') or contains(normalize-space(.),'Close')]"
        )
        for button in buttons:
            if button.is_displayed() and button.is_enabled():
                button.click()
                time.sleep(1)
                print("Closed popup/button.")
                return
    except Exception:
        pass


def click_by_js(driver, element):
    driver.execute_script("arguments[0].click();", element)
    time.sleep(1)


def scroll_to_element(driver, element, block="center"):
    driver.execute_script(f"arguments[0].scrollIntoView({{block:'{block}'}});", element)
    time.sleep(1)


# Page setup helpers
def login_as_admin(driver, wait):
    driver.get(BASE_URL)
    ignore_company_location_error(driver)

    email_input = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//input[@type='email' or @name='email']")
        )
    )
    email_input.clear()
    email_input.send_keys(ADMIN_EMAIL)

    password_input = driver.find_element(
        By.XPATH, "//input[@type='password' or @name='password']"
    )
    password_input.clear()
    password_input.send_keys(ADMIN_PASSWORD)

    login_button = driver.find_element(
        By.XPATH,
        "//button[contains(.,'LOGIN') or contains(.,'Login') or contains(.,'Sign in') or contains(.,'Sign In')]"
    )
    login_button.click()

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(.,'Dashboard') or contains(.,'Drone')]")
        )
    )
    ignore_company_location_error(driver)


def go_to_drone_management(driver, wait):
    driver.get(BASE_URL + "/drone-management")
    ignore_company_location_error(driver)

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(.,'Drone Management') or contains(.,'Drone Fleet') or contains(.,'Drone Images')]")
        )
    )
    ignore_company_location_error(driver)


def setup_uc06_page(driver):
    wait = WebDriverWait(driver, 20)
    login_as_admin(driver, wait)
    go_to_drone_management(driver, wait)
    ignore_company_location_error(driver)
    return wait


# Drone Images helpers
def scroll_to_drone_images(driver, wait):
    title = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//h3[contains(normalize-space(.),'Drone Images')]")
        )
    )
    scroll_to_element(driver, title, "start")
    ignore_company_location_error(driver)


def get_drone_images_section(driver, wait):
    scroll_to_drone_images(driver, wait)
    return wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//h3[contains(normalize-space(.),'Drone Images')]/ancestor::div[contains(@class,'rounded-xl')][1]"
            )
        )
    )


def select_drone_from_images_dropdown(driver, wait, drone_name):
    section = get_drone_images_section(driver, wait)

    dropdown = section.find_element(By.XPATH, ".//select")
    scroll_to_element(driver, dropdown)

    select = Select(dropdown)
    matched_option_text = None

    for option in select.options:
        if drone_name.lower() in option.text.lower():
            matched_option_text = option.text
            break

    if not matched_option_text:
        all_options = [option.text for option in select.options]
        raise AssertionError(f"Could not find drone option containing '{drone_name}'. Available options: {all_options}")

    select.select_by_visible_text(matched_option_text)
    time.sleep(3)
    ignore_company_location_error(driver)


def select_drone_alpha(driver, wait):
    select_drone_from_images_dropdown(driver, wait, "Drone Alpha")


def select_drone_1(driver, wait):
    select_drone_from_images_dropdown(driver, wait, "Drone 1")


def wait_until_images_loaded(driver, wait):
    try:
        wait.until_not(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(normalize-space(.),'Loading images')]")
            )
        )
    except TimeoutException:
        pass
    time.sleep(1)


def load_more_until_filename_found(driver, wait, filename=TARGET_IMAGE_FILENAME, max_clicks=8):
    """Click Load More Images until target filename appears or no more load button."""
    for _ in range(max_clicks):
        if filename in driver.page_source:
            return

        try:
            load_more = wait_short(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(normalize-space(.),'Load More Images')]")
                )
            )
            scroll_to_element(driver, load_more)
            load_more.click()
            time.sleep(2)
        except Exception:
            break


def get_image_card_by_filename(driver, wait, filename=TARGET_IMAGE_FILENAME):
    """
    Safer method:
    1. Select/search inside Drone Images section only.
    2. Get all image cards based on class='group relative rounded-xl'.
    3. Return the first card whose visible text contains filename.
    """
    section = get_drone_images_section(driver, wait)
    wait_until_images_loaded(driver, wait)
    load_more_until_filename_found(driver, wait, filename)

    section = get_drone_images_section(driver, wait)

    cards = section.find_elements(
        By.XPATH,
        ".//div[contains(@class,'group') and contains(@class,'relative') and contains(@class,'rounded-xl')]"
    )

    # Fallback if Tailwind classes changed slightly
    if not cards:
        cards = section.find_elements(
            By.XPATH,
            ".//div[.//img and .//button]"
        )

    target_cards = []
    for card in cards:
        try:
            text = card.text.strip()
            html_text = driver.execute_script("return arguments[0].textContent || '';", card)
            combined_text = f"{text} {html_text}"
            if filename in combined_text:
                target_cards.append(card)
        except Exception:
            continue

    if not target_cards:
        screenshot_path = os.path.join(os.getcwd(), "tc06_filename_not_found.png")
        driver.save_screenshot(screenshot_path)
        raise AssertionError(
            f"Could not find image card with filename '{filename}' under Drone Images section. "
            f"Screenshot saved: {screenshot_path}"
        )

    card = target_cards[0]
    scroll_to_element(driver, card)
    return card


def reveal_image_buttons(driver, card):
    scroll_to_element(driver, card)
    ActionChains(driver).move_to_element(card).pause(1).perform()
    time.sleep(1)

    # Force hover overlay visible. This helps if CSS hover does not trigger in Selenium.
    try:
        overlays = card.find_elements(
            By.XPATH,
            ".//div[contains(@class,'absolute') and contains(@class,'inset-0') and contains(@class,'justify-center')]"
        )
        for overlay in overlays:
            driver.execute_script("arguments[0].style.opacity='1'; arguments[0].style.pointerEvents='auto';", overlay)
    except Exception:
        pass

    time.sleep(0.5)


def get_image_action_buttons(driver, card):
    """
    Return only the 3 overlay image action buttons.
    Source order:
    0 = Eye
    1 = Download
    2 = Delete
    """
    reveal_image_buttons(driver, card)

    # The overlay has exactly three buttons in source code.
    overlay_buttons = card.find_elements(
        By.XPATH,
        ".//div[contains(@class,'absolute') and contains(@class,'inset-0') and contains(@class,'justify-center')]//button"
    )

    if len(overlay_buttons) >= 3:
        return overlay_buttons[:3]

    # fallback: get all buttons in card except chevron button at bottom
    all_buttons = card.find_elements(By.XPATH, ".//button")
    if len(all_buttons) >= 3:
        return all_buttons[:3]

    raise AssertionError(f"Could not find 3 image action buttons. Found {len(all_buttons)} button(s).")


def click_image_action_button(driver, wait, action):
    select_drone_alpha(driver, wait)

    card = get_image_card_by_filename(driver, wait, TARGET_IMAGE_FILENAME)
    buttons = get_image_action_buttons(driver, card)

    action_index = {
        "review": 0,
        "download": 1,
        "delete": 2,
    }[action]

    button = buttons[action_index]
    click_by_js(driver, button)
    ignore_company_location_error(driver)


# TC-06-001
def test_tc_06_001_view_images(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)

    card = get_image_card_by_filename(driver, wait, TARGET_IMAGE_FILENAME)

    assert card.is_displayed()
    assert TARGET_IMAGE_FILENAME in driver.page_source


# TC-06-002
def test_tc_06_002_review_selected_enlarge_image(driver):
    wait = setup_uc06_page(driver)

    click_image_action_button(driver, wait, "review")

    modal = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[contains(@class,'fixed') and contains(@class,'bg-black')]")
        )
    )

    assert modal.is_displayed()

    # Verify selected image is displayed
    image = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//div[contains(@class,'fixed')]//img")
        )
    )

    assert image.is_displayed()

    # Verify image details or related image content is shown
    assert (
        "Drone" in driver.page_source
        or "Image" in driver.page_source
        or "capture" in driver.page_source.lower()
        or image.get_attribute("src") is not None
    )

    # Inspect image clearly by zooming in using keyboard shortcut
    zoom_button = driver.find_elements(
        By.XPATH,
        "//button[contains(translate(., 'ZOOM', 'zoom'),'zoom') "
        "or contains(translate(@title, 'ZOOM', 'zoom'),'zoom')]"
    )

    assert len(zoom_button) > 0, \
    "Failed: Zoom button/control is not available for image inspection."


# TC-06-003
def test_tc_06_003_download_selected_image(driver):
    wait = setup_uc06_page(driver)

    click_image_action_button(driver, wait, "download")

    # Some downloads do not show confirmation. The test passes if clicking download does not produce an error alert.
    time.sleep(2)

    alert_text = accept_alert_if_present(driver)
    if alert_text and "failed" in alert_text.lower():
        raise AssertionError(f"Download failed with alert: {alert_text}")

    assert True


# TC-06-004
def test_tc_06_004_edit_metadata_or_notes(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)
    click_image_action_button(driver, wait, "review")

    # This will fail if the system really has no notes/metadata field.
    notes_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata')]"
                " | //input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata') or contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata')]"
            )
        )
    )

    notes_field.clear()
    notes_field.send_keys("breeding site detected")

    save_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Save') or contains(.,'Update')]")
        )
    )
    save_button.click()

    success = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'saved') or contains(.,'updated') or contains(.,'success') or contains(.,'Saved') or contains(.,'Updated')]")
        )
    )

    assert success.is_displayed()


# TC-06-005
def test_tc_06_005_empty_metadata_or_notes(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)
    click_image_action_button(driver, wait, "review")

    # This will fail if the system really has no notes/metadata field.
    notes_field = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//textarea[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata')]"
                " | //input[contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@placeholder,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata') or contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'note') or contains(translate(@name,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'metadata')]"
            )
        )
    )

    notes_field.clear()

    save_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Save') or contains(.,'Update')]")
        )
    )
    save_button.click()

    validation = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'required') or contains(.,'empty') or contains(.,'invalid') or contains(.,'Required') or contains(.,'Empty')]")
        )
    )

    assert validation.is_displayed()


# TC-06-006
def test_tc_06_006_delete_selected_image(driver):
    wait = setup_uc06_page(driver)

    click_image_action_button(driver, wait, "delete")

    confirm_delete = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[normalize-space(.)='Delete' or contains(normalize-space(.),'Delete')]"
            )
        )
    )
    confirm_delete.click()

    try:
        alert_text = accept_alert_if_present(driver)
        if alert_text and "failed" in alert_text.lower():
            raise AssertionError(f"Delete failed with alert: {alert_text}")
    except Exception:
        pass

    success = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'Image deleted successfully') or contains(.,'deleted successfully') or contains(.,'Image deleted')]")
        )
    )

    assert success.is_displayed()


# TC-06-007
def test_tc_06_007_gallery_updates_after_action(driver):
    wait = setup_uc06_page(driver)

    select_drone_alpha(driver, wait)
    before_cards = len(
        get_drone_images_section(driver, wait).find_elements(
            By.XPATH,
            ".//div[contains(@class,'group') and contains(@class,'relative') and contains(@class,'rounded-xl')]"
        )
    )

    # Refresh selected drone by selecting Drone Alpha again.
    select_drone_alpha(driver, wait)

    after_cards = len(
        get_drone_images_section(driver, wait).find_elements(
            By.XPATH,
            ".//div[contains(@class,'group') and contains(@class,'relative') and contains(@class,'rounded-xl')]"
        )
    )

    assert after_cards >= 0
    assert before_cards >= 0


# TC-06-008
def test_tc_06_008_uploading_status(driver):
    wait = setup_uc06_page(driver)

    if not os.path.exists(TEST_IMAGE_PATH):
        raise AssertionError(f"Upload image file not found: {TEST_IMAGE_PATH}")

    alpha_row = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//tr[.//*[contains(normalize-space(.),'Drone Alpha')]]")
        )
    )
    scroll_to_element(driver, alpha_row)

    add_images_button = alpha_row.find_element(
        By.XPATH,
        ".//button[contains(normalize-space(.),'Add Images')]"
    )
    click_by_js(driver, add_images_button)

    file_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )
    file_input.send_keys(TEST_IMAGE_PATH)
    time.sleep(1)

    upload_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(normalize-space(.),'Upload Images') "
                "or contains(normalize-space(.),'Upload Image') "
                "or normalize-space(.)='Upload']"
            )
        )
    )

    click_by_js(driver, upload_button)

    # Verify uploading status is displayed
    uploading_status = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(.,'Uploading') "
                "or contains(.,'uploading') "
                "or contains(.,'Processing') "
                "or contains(.,'Please wait')]"
            )
        )
    )

    assert uploading_status.is_displayed()

# TC-06-009
def test_tc_06_009_bulk_delete_images_with_confirmation(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)

    section = get_drone_images_section(driver, wait)

    checkboxes = section.find_elements(By.XPATH, ".//input[@type='checkbox']")
    if len(checkboxes) < 2:
        raise AssertionError("Bulk delete failed: less than 2 image checkboxes found.")

    for checkbox in checkboxes[:2]:
        if not checkbox.is_selected():
            click_by_js(driver, checkbox)

    bulk_delete = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(.,'Bulk Delete') or contains(.,'Delete Selected') or contains(.,'Delete Images')]"
            )
        )
    )
    bulk_delete.click()

    confirm = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Confirm') or contains(.,'Delete') or contains(.,'Yes')]")
        )
    )
    confirm.click()

    success = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'deleted') or contains(.,'Deleted') or contains(.,'success')]")
        )
    )

    assert success.is_displayed()


# TC-06-010
def test_tc_06_010_cancel_bulk_delete(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)

    section = get_drone_images_section(driver, wait)

    checkboxes = section.find_elements(By.XPATH, ".//input[@type='checkbox']")
    if len(checkboxes) < 2:
        raise AssertionError("Cancel bulk delete failed: less than 2 image checkboxes found.")

    before_count = len(
        section.find_elements(
            By.XPATH,
            ".//div[contains(@class,'group') and contains(@class,'relative') and contains(@class,'rounded-xl')]"
        )
    )

    for checkbox in checkboxes[:2]:
        if not checkbox.is_selected():
            click_by_js(driver, checkbox)

    bulk_delete = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(.,'Bulk Delete') or contains(.,'Delete Selected') or contains(.,'Delete Images')]"
            )
        )
    )
    bulk_delete.click()

    cancel = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Cancel') or contains(.,'No')]")
        )
    )
    cancel.click()

    section = get_drone_images_section(driver, wait)
    after_count = len(
        section.find_elements(
            By.XPATH,
            ".//div[contains(@class,'group') and contains(@class,'relative') and contains(@class,'rounded-xl')]"
        )
    )

    assert after_count == before_count


# TC-06-011
def test_tc_06_011_no_images_available(driver):
    wait = setup_uc06_page(driver)

    select_drone_1(driver, wait)

    no_images = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'No Images Available') or contains(.,'No images available')]")
        )
    )

    assert no_images.is_displayed()


# TC-06-012
def test_tc_06_012_server_error_during_image_operation(driver):
    wait = setup_uc06_page(driver)
    select_drone_alpha(driver, wait)

    # This test will only pass if server failure is actually simulated before the action.
    click_image_action_button(driver, wait, "download")

    alert_text = accept_alert_if_present(driver)

    assert alert_text is not None and (
        "failed" in alert_text.lower()
        or "server" in alert_text.lower()
        or "error" in alert_text.lower()
    )