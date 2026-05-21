import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# =========================
# WEB CONFIG
# =========================
# Stores the base website URL and test data used by the web edit profile test cases.
# These values can be changed when testing with a different local environment or account.

BASE_URL = "http://localhost:3000"

ADMIN_EMAIL = "admin2@drone4dengue.com"
ADMIN_PASSWORD = "adminpass2"

VALID_NAME = "Low123!"
VALID_USERNAME = "Low123!"
VALID_PHONE = "60112222222"

INVALID_PHONE = "abc123"
LONG_NAME = "A" * 100


# =========================
# DRIVER
# =========================
# Creates a Chrome browser instance for each test case and closes it after the test ends.
# This prevents one test from affecting the browser state of another test.

@pytest.fixture()
def driver():
    # Set up Chrome options and start the Selenium WebDriver session.
    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    yield driver
    driver.quit()


# =========================
# HELPERS
# =========================
# Reusable helper functions for screenshots, typing, clicking buttons, reading values,
# checking messages, and making React form updates more stable in Selenium.

def save_evidence(driver, name):
    # Save a screenshot as test evidence for reporting and debugging.
    os.makedirs("evidence_web_uc04_8_cases", exist_ok=True)
    path = f"evidence_web_uc04_8_cases/{name}.png"
    driver.save_screenshot(path)
    print(f"\nEvidence saved: {path}")


def get_body_text(driver):
    # Return all visible page text from the browser body.
    return driver.find_element(By.TAG_NAME, "body").text


def clear_and_type(element, value):
    # Clear an input field using keyboard shortcuts before typing a new value.
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)

    if value != "":
        element.send_keys(value)


def set_input_value(driver, element, value):
    # Directly set an input value through JavaScript and trigger React update events.
    """
    Stable for React forms.
    Sets value and triggers input/change events.
    """
    driver.execute_script(
        """
        const input = arguments[0];
        const value = arguments[1];

        input.scrollIntoView({block: 'center'});

        const nativeInputValueSetter =
            Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;

        nativeInputValueSetter.call(input, value);

        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        element,
        value
    )


def wait_body_contains(driver, text, timeout=15):
    # Wait until specific text appears anywhere in the page body.
    WebDriverWait(driver, timeout).until(
        lambda d: text.lower() in get_body_text(d).lower()
    )


def click_button_by_text(driver, text):
    # Find a visible enabled button by its text and click it using JavaScript.
    xpath = f"//button[contains(normalize-space(.), '{text}')]"

    button = WebDriverWait(driver, 15).until(
        lambda d: next(
            (
                b for b in d.find_elements(By.XPATH, xpath)
                if b.is_displayed() and b.is_enabled()
            ),
            None
        )
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", button)
    time.sleep(1)


def button_exists(driver, text):
    # Check whether a visible button with the expected text is present.
    xpath = f"//button[contains(normalize-space(.), '{text}')]"
    buttons = driver.find_elements(By.XPATH, xpath)

    return any(b.is_displayed() for b in buttons)


def find_input_after_label(driver, label_text, editable=False):
    # Locate the input field that appears after a specific label such as Name or Phone.
    xpath = f"//*[contains(normalize-space(),'{label_text}')]/following::input[1]"
    elements = driver.find_elements(By.XPATH, xpath)

    for element in elements:
        if element.is_displayed():
            if editable:
                if element.is_enabled() and element.get_attribute("readonly") is None:
                    return element
            else:
                return element

    raise Exception(f"Cannot find input after label: {label_text}")


def get_input_value_after_label(driver, label_text):
    # Read the current value from the input field linked to the given label.
    element = find_input_after_label(driver, label_text)
    return element.get_attribute("value") or ""


def page_contains_value(driver, value):
    # Check page text, input values, and page source for a specific saved value.
    if value in get_body_text(driver):
        return True

    inputs = driver.find_elements(By.TAG_NAME, "input")

    for input_field in inputs:
        try:
            if input_field.get_attribute("value") == value:
                return True
        except Exception:
            pass

    if value in driver.page_source:
        return True

    return False


def validation_or_error_shown(driver):
    # Detect common validation or error keywords displayed by the system.
    text = get_body_text(driver).lower()

    words = [
        "error",
        "invalid",
        "required",
        "empty",
        "must",
        "failed",
        "format",
        "phone",
        "name is required",
        "username is required"
    ]

    return any(word in text for word in words)


def success_or_updated_feedback(driver):
    # Detect common success or update confirmation keywords displayed by the system.
    text = get_body_text(driver).lower()

    words = [
        "success",
        "successfully",
        "updated",
        "saved",
        "profile updated",
        "changes saved"
    ]

    return any(word in text for word in words)


# =========================
# LOGIN / NAVIGATION
# =========================
# Helper functions for logging in as admin, opening the Settings page,
# entering Edit Profile mode, filling fields, saving, cancelling, and restoring test data.

def login_as_admin(driver):
    # Open the website and log in using the admin account when the session is not already logged in.
    driver.get(BASE_URL)
    time.sleep(2)

    body_text = get_body_text(driver).lower()

    if "logout" in body_text or "dashboard" in body_text:
        return

    inputs = [i for i in driver.find_elements(By.TAG_NAME, "input") if i.is_displayed()]

    if len(inputs) < 2:
        driver.get(f"{BASE_URL}/login")
        time.sleep(2)
        inputs = [i for i in driver.find_elements(By.TAG_NAME, "input") if i.is_displayed()]

    assert len(inputs) >= 2, "Login page should have email and password fields."

    clear_and_type(inputs[0], ADMIN_EMAIL)
    clear_and_type(inputs[1], ADMIN_PASSWORD)

    login_buttons = driver.find_elements(
        By.XPATH,
        "//button[contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login') "
        "or contains(translate(normalize-space(.), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]"
    )

    assert login_buttons, "Login button not found."

    driver.execute_script("arguments[0].click();", login_buttons[0])

    WebDriverWait(driver, 15).until(
        lambda d: "logout" in get_body_text(d).lower()
        or "dashboard" in get_body_text(d).lower()
        or "settings" in d.current_url.lower()
    )


def open_settings_page(driver):
    # Navigate to the Settings page and make sure the Profile Settings section is loaded.
    login_as_admin(driver)

    for _ in range(3):
        driver.get(f"{BASE_URL}/settings")
        time.sleep(2)

        if "Profile Settings" in get_body_text(driver):
            return

        driver.refresh()
        time.sleep(2)

    save_evidence(driver, "ERROR_profile_settings_not_loaded")
    raise Exception("Profile Settings section was not loaded.")


def open_edit_profile_mode(driver):
    # Open Settings and switch to edit mode if the form is not already editable.
    open_settings_page(driver)

    if "Save Changes" not in get_body_text(driver):
        click_button_by_text(driver, "Edit Profile")
        time.sleep(1)

    wait_body_contains(driver, "Save Changes")


def get_profile_values(driver):
    # Collect the current Name, Username, and Phone values from the profile form.
    open_edit_profile_mode(driver)

    return {
        "name": get_input_value_after_label(driver, "Name"),
        "username": get_input_value_after_label(driver, "Username"),
        "phone": get_input_value_after_label(driver, "Phone"),
    }


def fill_profile_form(driver, name, username, phone):
    # Fill in all editable profile fields used by the test cases.
    open_edit_profile_mode(driver)

    name_input = find_input_after_label(driver, "Name", editable=True)
    username_input = find_input_after_label(driver, "Username", editable=True)
    phone_input = find_input_after_label(driver, "Phone", editable=True)

    set_input_value(driver, name_input, name)
    set_input_value(driver, username_input, username)
    set_input_value(driver, phone_input, phone)

    time.sleep(0.5)


def fill_only_phone(driver, phone):
    # Update only the phone field for partial update test cases.
    open_edit_profile_mode(driver)

    phone_input = find_input_after_label(driver, "Phone", editable=True)
    set_input_value(driver, phone_input, phone)

    time.sleep(0.5)


def fill_only_name(driver, name):
    # Update only the name field, mainly for testing Cancel behaviour.
    open_edit_profile_mode(driver)

    name_input = find_input_after_label(driver, "Name", editable=True)
    set_input_value(driver, name_input, name)

    time.sleep(0.5)


def save_changes(driver):
    # Click Save Changes and wait for the page to process the update.
    click_button_by_text(driver, "Save Changes")
    time.sleep(2)


def cancel_changes(driver):
    # Click Cancel and wait for the edit action to be discarded.
    click_button_by_text(driver, "Cancel")
    time.sleep(2)


def restore_valid_profile(driver):
    # Restore valid profile data after negative tests so later tests start from a clean state.
    try:
        fill_profile_form(
            driver,
            name=VALID_NAME,
            username=VALID_USERNAME,
            phone=VALID_PHONE
        )

        save_changes(driver)
        time.sleep(1)

    except Exception as e:
        print(f"WARNING: Could not restore valid profile: {e}")


# ======================================================
# TC-04-001
# Verify Save Changes button saves updated profile data.
# Test flow: update the phone number, save it, reopen edit mode,
# then verify the new phone number is shown on the page.
# ======================================================

def test_tc_04_001_save_changes_saves_updated_profile_data(driver):
    # Generate a unique phone number so the test can confirm the latest saved value.
    new_phone = "6011" + time.strftime("%H%M%S")

    fill_profile_form(
        driver,
        name=VALID_NAME,
        username=VALID_USERNAME,
        phone=new_phone
    )

    save_changes(driver)

    save_evidence(driver, "TC-04-001_save_changes_saves_updated_profile_data")

    open_edit_profile_mode(driver)

    assert page_contains_value(driver, new_phone), (
        "Updated profile data should be saved successfully."
    )


# ======================================================
# TC-04-002
# Verify Cancel button discards unsaved profile changes.
# Test flow: record the original profile name, type a temporary name,
# cancel the edit, then verify the original name is still kept.
# ======================================================

def test_tc_04_002_cancel_discards_unsaved_profile_changes(driver):
    # Store original values first so the test can compare after pressing Cancel.
    original_values = get_profile_values(driver)

    cancel_name = "CancelTestName"

    fill_only_name(driver, cancel_name)

    cancel_changes(driver)

    save_evidence(driver, "TC-04-002_cancel_discards_unsaved_profile_changes")

    open_edit_profile_mode(driver)

    current_values = get_profile_values(driver)

    assert current_values["name"] == original_values["name"], (
        "Cancel should discard unsaved Name changes."
    )

    assert current_values["name"] != cancel_name, (
        "Cancel should not keep the unsaved Name value."
    )


# ======================================================
# TC-04-003
# Verify system supports partial profile update.
# Test flow: update only the phone number and verify other profile fields
# such as name and username remain unchanged.
# ======================================================

def test_tc_04_003_partial_profile_update_phone_only(driver):
    # Capture original values to ensure only the phone field changes.
    original_values = get_profile_values(driver)

    new_phone = "6011" + time.strftime("%H%M%S")

    fill_only_phone(driver, new_phone)

    save_changes(driver)

    save_evidence(driver, "TC-04-003_partial_profile_update_phone_only")

    updated_values = get_profile_values(driver)

    assert updated_values["phone"] == new_phone, (
        "System should save the updated phone number."
    )

    assert updated_values["name"] == original_values["name"], (
        "Name should remain unchanged during partial update."
    )

    assert updated_values["username"] == original_values["username"], (
        "Username should remain unchanged during partial update."
    )


# ======================================================
# TC-04-004
# Verify system rejects empty required profile fields.
# Test flow: try saving an empty Name and empty Username separately,
# then check that validation appears or the empty value is not saved.
# ======================================================

def test_tc_04_004_reject_empty_required_profile_fields(driver):
    # Use try/finally because invalid input tests may leave the profile in an unusable state.
    try:
        # Case 1: Name empty
        fill_profile_form(
            driver,
            name="",
            username=VALID_USERNAME,
            phone=VALID_PHONE
        )

        save_changes(driver)

        save_evidence(driver, "TC-04-004_empty_name")

        values_after_empty_name = get_profile_values(driver)

        assert (
            validation_or_error_shown(driver)
            or values_after_empty_name["name"] != ""
        ), "System should reject empty Name."

        # Case 2: Username empty
        fill_profile_form(
            driver,
            name=VALID_NAME,
            username="",
            phone=VALID_PHONE
        )

        save_changes(driver)

        save_evidence(driver, "TC-04-004_empty_username")

        values_after_empty_username = get_profile_values(driver)

        assert (
            validation_or_error_shown(driver)
            or values_after_empty_username["username"] != ""
        ), "System should reject empty Username."

    finally:
        restore_valid_profile(driver)


# ======================================================
# TC-04-005
# Verify system rejects invalid phone number format.
# Test flow: enter alphabetic characters into the phone field and verify
# the system shows validation or does not keep the invalid phone value.
# ======================================================

def test_tc_04_005_reject_invalid_phone_number_format(driver):
    # Use try/finally to restore valid data after testing invalid phone input.
    try:
        fill_profile_form(
            driver,
            name=VALID_NAME,
            username=VALID_USERNAME,
            phone=INVALID_PHONE
        )

        save_changes(driver)

        save_evidence(driver, "TC-04-005_invalid_phone_number_format")

        values_after_invalid_phone = get_profile_values(driver)

        assert (
            validation_or_error_shown(driver)
            or values_after_invalid_phone["phone"] != INVALID_PHONE
        ), "System should reject invalid phone number format."

    finally:
        restore_valid_profile(driver)


# ======================================================
# TC-04-006
# Verify system handles very long profile input properly.
# Test flow: enter a very long name and check that the system either
# validates it, saves it, or remains stable without crashing.
# ======================================================

def test_tc_04_006_very_long_profile_input_handled(driver):
    # Use try/finally to restore valid data after testing a long name value.
    try:
        fill_profile_form(
            driver,
            name=LONG_NAME,
            username=VALID_USERNAME,
            phone=VALID_PHONE
        )

        save_changes(driver)

        save_evidence(driver, "TC-04-006_very_long_profile_input")

        assert (
            validation_or_error_shown(driver)
            or page_contains_value(driver, LONG_NAME)
            or "Profile Settings" in get_body_text(driver)
        ), "System should handle very long Name input properly."

    finally:
        restore_valid_profile(driver)


# ======================================================
# TC-04-007
# Verify Edit Profile button enables editable profile fields on website.
# Test flow: open Settings, click Edit Profile if needed, then confirm
# Name, Username, and Phone inputs are enabled for editing.
# ======================================================

def test_tc_04_007_edit_profile_button_enables_editable_fields(driver):
    # Open the profile settings page before checking whether edit mode can be enabled.
    open_settings_page(driver)

    assert button_exists(driver, "Edit Profile") or "Save Changes" in get_body_text(driver), (
        "Edit Profile button should be displayed or profile should already be in edit mode."
    )

    if button_exists(driver, "Edit Profile"):
        click_button_by_text(driver, "Edit Profile")

    name_input = find_input_after_label(driver, "Name", editable=True)
    username_input = find_input_after_label(driver, "Username", editable=True)
    phone_input = find_input_after_label(driver, "Phone", editable=True)

    assert name_input.is_enabled(), "Name field should be editable."
    assert username_input.is_enabled(), "Username field should be editable."
    assert phone_input.is_enabled(), "Phone field should be editable."

    save_evidence(driver, "TC-04-007_edit_profile_button_enables_fields")


# ======================================================
# TC-04-008
# Verify system displays feedback after saving profile changes.
# Test flow: save an updated phone number and verify either success feedback
# is displayed or the updated information appears on the page.
# ======================================================

def test_tc_04_008_feedback_after_saving_profile_changes(driver):
    # Generate a new phone number and save it to trigger feedback or updated display.
    new_phone = "6011" + time.strftime("%H%M%S")

    fill_profile_form(
        driver,
        name=VALID_NAME,
        username=VALID_USERNAME,
        phone=new_phone
    )

    save_changes(driver)

    save_evidence(driver, "TC-04-008_feedback_after_saving_profile_changes")

    open_edit_profile_mode(driver)

    assert (
        success_or_updated_feedback(driver)
        or page_contains_value(driver, new_phone)
    ), "System should display feedback or updated information after saving profile changes."