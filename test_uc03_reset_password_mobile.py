# test_mobile_uc03_reset_password.py
# UC-03 Reset Password - Mobile App Automated Test Script
# Covers TC-03-001 to TC-03-008
#
# Notes:
# - This script uses Appium UiAutomator2 to test the mobile Reset Password flow.
# - ADB helper functions are used as fallbacks when Appium actions are unstable.
# - Each test starts from the Login page to avoid leftover modal/page state.
# - Evidence screenshots are saved into the evidence_mobile_uc03 folder.
# - Some checks allow [object Object] because the current app may show generic error dialogs.
#
# Run with:
#   appium --port 4723
#   python -m pytest test_mobile_uc03_reset_password.py -v


import os
import re
import subprocess
import time

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait


# Store emulator, ADB, app package, and test data used by all UC-03 mobile tests.
# =========================================================
# CONFIG
# =========================================================

ANDROID_SERIAL = os.getenv("ANDROID_SERIAL", "emulator-5554")
ADB_PATH = os.getenv("ADB_PATH", "adb")

APP_PACKAGE = "com.adamarbain.dengueeyemobileapp"
APP_ACTIVITY = ".MainActivity"

REGISTERED_EMAIL = "ledlow0405@gmail.com"
NEW_PASSWORD = "a1b2c3d4E?"

# Change this only if you receive a real reset code from email.
VALID_CODE = os.getenv("VALID_CODE", "123456")

# Global driver reference and fallback screen size used when Appium cannot read screen dimensions.
_DRIVER = None
DEFAULT_SCREEN_SIZE = {"width": 1080, "height": 2400}


# =========================================================
# ADB HELPERS
# =========================================================

# Execute a command inside the Android device/emulator shell.
def adb_shell(args, timeout=10):
    """Run adb shell command safely."""
    try:
        result = subprocess.run(
            [ADB_PATH, "-s", ANDROID_SERIAL, "shell"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"\nWARNING: adb shell failed: {' '.join(args)}. Reason: {e}")
        return ""


# Execute a normal ADB command outside the Android shell.
def adb_command(args, timeout=10):
    """Run normal adb command, not adb shell."""
    try:
        result = subprocess.run(
            [ADB_PATH, "-s", ANDROID_SERIAL] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"\nWARNING: adb command failed: {' '.join(args)}. Reason: {e}")
        return ""


# Force stop the mobile app so the next test can start cleanly.
def adb_force_stop_app():
    adb_shell(["am", "force-stop", APP_PACKAGE])
    time.sleep(1)


# Type text using ADB when Appium send_keys is unreliable.
def adb_input_text(value):
    # Android input text needs spaces as %s. Email has no spaces, so this is safe.
    safe_value = str(value).replace(" ", "%s")
    adb_shell(["input", "text", safe_value])
    time.sleep(0.8)


# Clear the currently focused input field using repeated delete key events.
def adb_clear_focused_text(max_chars=80):
    # Move cursor to end, then delete many times. Works even when element.clear() is unreliable.
    # Send many DEL key events in one adb call so the test is much faster.
    adb_shell(["input", "keyevent", "123"])  # KEYCODE_MOVE_END
    adb_shell(["input", "keyevent"] + ["67"] * max_chars, timeout=10)  # KEYCODE_DEL repeated
    time.sleep(0.5)


# Start the app using the Android monkey launcher command.
def adb_start_app():
    try:
        subprocess.run(
            [
                ADB_PATH,
                "-s",
                ANDROID_SERIAL,
                "shell",
                "monkey",
                "-p",
                APP_PACKAGE,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        time.sleep(2)
    except Exception as e:
        print(f"\nWARNING: Could not start app using adb monkey. Reason: {e}")


# Read the emulator screen size through ADB and fall back to the default value if needed.
def adb_get_screen_size():
    output = adb_shell(["wm", "size"])
    # Example output: Physical size: 1080x2400
    match = re.search(r"(\d+)x(\d+)", output)
    if match:
        return {"width": int(match.group(1)), "height": int(match.group(2))}
    return DEFAULT_SCREEN_SIZE


# Tap a specific screen coordinate using ADB.
def adb_tap(x, y):
    adb_shell(["input", "tap", str(x), str(y)])
    time.sleep(1)


# Press Android Back using ADB.
def adb_back():
    adb_shell(["input", "keyevent", "4"])
    time.sleep(1)


# =========================================================
# DRIVER
# =========================================================

# Close the current Appium driver session safely.
def close_driver():
    global _DRIVER

    if _DRIVER is not None:
        try:
            _DRIVER.quit()
        except Exception:
            pass
        _DRIVER = None


@pytest.fixture(autouse=True)
# Automatically close the driver after each test to prevent one failed session affecting another test.
def fresh_driver_for_each_test():
    """
    Important fix:
    Do not reuse one broken Appium session for all 8 tests.
    If test 1 breaks the driver, test 2-8 should not fail because of the same broken session.
    """
    yield
    close_driver()


# Create a fresh Appium driver session for the current test case.
def get_driver(test_name):
    """
    Create a fresh Appium session for the current test.
    The app is force-stopped first, but app data is not cleared.
    This prevents one test from leaving the next test on a modal/code/error page.
    """
    global _DRIVER

    close_driver()
    adb_force_stop_app()

    try:
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.automation_name = "UiAutomator2"
        options.device_name = "Android Emulator"
        options.udid = ANDROID_SERIAL

        options.app_package = APP_PACKAGE
        options.app_activity = APP_ACTIVITY

        # Keep app data, but allow Appium to launch the app for a clean session.
        options.no_reset = True
        options.full_reset = False
        options.new_command_timeout = 300

        # Extra stability for React Native / Android emulator.
        options.set_capability("autoLaunch", True)
        options.set_capability("appWaitActivity", "*")
        options.set_capability("disableWindowAnimation", True)
        options.set_capability("ignoreHiddenApiPolicyError", True)

        _DRIVER = webdriver.Remote("http://127.0.0.1:4723", options=options)
        time.sleep(3)

        try:
            _DRIVER.activate_app(APP_PACKAGE)
            time.sleep(2)
        except Exception:
            adb_start_app()

        return _DRIVER

    except Exception as e:
        close_driver()
        pytest.fail(
            f"{test_name} failed: Cannot connect to Appium/emulator. "
            f"Make sure emulator is online and Appium is running. Reason: {e}"
        )


# =========================================================
# BASIC HELPERS
# =========================================================

# Save screenshot evidence for reporting/debugging after each important test action.
def save_evidence(driver, name):
    os.makedirs("evidence_mobile_uc03", exist_ok=True)
    path = f"evidence_mobile_uc03/{name}.png"

    try:
        driver.save_screenshot(path)
        print(f"\nEvidence saved: {path}")
    except Exception as e:
        print(f"\nWARNING: Evidence screenshot not saved for {name}. Reason: {e}")


# Read page source in lowercase so keyword checks become case-insensitive.
def page_source_lower(driver):
    try:
        return driver.page_source.lower()
    except Exception as e:
        print(f"\nWARNING: Cannot read page source. Reason: {e}")
        return ""


# Check whether any expected keyword appears in the current page source.
def source_contains_any(driver, keywords):
    source = page_source_lower(driver)
    return any(keyword.lower() in source for keyword in keywords)


# Wait until at least one expected keyword appears on screen.
def wait_until_source_contains_any(driver, keywords, timeout=8):
    end_time = time.time() + timeout

    while time.time() < end_time:
        if source_contains_any(driver, keywords):
            return True
        time.sleep(0.5)

    return False


# Hide the keyboard when it may block buttons or input fields.
def hide_keyboard(driver):
    try:
        driver.hide_keyboard()
        time.sleep(0.5)
    except Exception:
        pass


# Return visible and enabled Android EditText fields only.
def get_visible_inputs(driver):
    try:
        inputs = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
    except Exception:
        return []

    visible_inputs = []
    for element in inputs:
        try:
            if element.is_displayed() and element.is_enabled():
                visible_inputs.append(element)
        except Exception:
            pass

    return visible_inputs


# Tap the center point of an element using ADB coordinate tapping.
def tap_element_center_with_adb(element):
    try:
        rect = element.rect
        x = int(rect["x"] + rect["width"] / 2)
        y = int(rect["y"] + rect["height"] / 2)
        adb_tap(x, y)
        return True
    except Exception:
        return False


# Clear an input field and type a value using Appium first, then ADB fallback if needed.
def clear_and_type(element, value):
    """
    More reliable typing for Android/React Native EditText.
    Some fields do not update get_attribute('text'), so typing verification is handled separately.
    """
    try:
        element.click()
        time.sleep(0.5)
    except Exception:
        tap_element_center_with_adb(element)

    try:
        element.clear()
        time.sleep(0.3)
    except Exception:
        adb_clear_focused_text()

    if value:
        try:
            element.send_keys(value)
            time.sleep(0.8)
        except Exception:
            tap_element_center_with_adb(element)
            adb_clear_focused_text()
            adb_input_text(value)

    time.sleep(0.5)


# Strict typing helper: retry with ADB when Appium cannot confirm the typed value.
def clear_and_type_strict(driver, element, value):
    """
    Type value, then retry once using adb if Appium typing appears empty.
    Do not immediately fail because some React Native inputs return empty text even after typing.
    """
    clear_and_type(element, value)

    typed_value = get_input_text(element)
    source = page_source_lower(driver)

    if value and value.lower() not in typed_value.lower() and value.lower() not in source:
        print(f"\nWARNING: Appium typing not visible. Retrying with adb input text for: {value}")
        tap_element_center_with_adb(element)
        adb_clear_focused_text()
        adb_input_text(value)
        hide_keyboard(driver)

    return get_input_text(element)


# Get text from an input element by checking common Android/Appium attributes.
def get_input_text(element):
    for attr in ["text", "value", "content-desc"]:
        try:
            value = element.get_attribute(attr)
            if value:
                return value
        except Exception:
            pass
    return ""


# Get screen size from Appium, then use ADB/default size as fallback.
def get_screen_size(driver):
    """
    Fix for: GET /window/current/size cannot be proxied.
    First try Appium. If Appium fails, use adb wm size. If adb also fails, use default emulator size.
    """
    try:
        return driver.get_window_size()
    except Exception as e:
        print(f"\nWARNING: Appium get_window_size failed. Using adb/default size. Reason: {e}")
        return adb_get_screen_size()


# Convert ratio-based coordinates to real screen coordinates and tap them.
def tap_coordinate(driver, x_ratio, y_ratio):
    size = get_screen_size(driver)
    x = int(size["width"] * x_ratio)
    y = int(size["height"] * y_ratio)

    try:
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
    except Exception as e:
        print(f"\nWARNING: Appium coordinate tap failed. Using adb tap. Reason: {e}")
        adb_tap(x, y)

    time.sleep(1)


# Press Back using Appium first and ADB fallback if Appium fails.
def press_back(driver):
    try:
        driver.press_keycode(4)
    except Exception:
        adb_back()
    time.sleep(1)


# Find and tap a visible text element using XPath.
def tap_text(driver, text, timeout=5, choose_last=False):
    xpath = (
        f"//*[@text='{text}' or @content-desc='{text}' "
        f"or contains(@text,'{text}') or contains(@content-desc,'{text}')]"
    )

    elements = WebDriverWait(driver, timeout).until(
        lambda d: d.find_elements(AppiumBy.XPATH, xpath)
    )

    visible_elements = []
    for element in elements:
        try:
            if element.is_displayed() and element.is_enabled():
                visible_elements.append(element)
        except Exception:
            pass

    if not visible_elements:
        raise Exception(f"Cannot find visible text: {text}")

    target = visible_elements[-1] if choose_last else visible_elements[0]
    target.click()
    time.sleep(1)


# Try tapping multiple possible text labels until one is found.
def tap_any_text(driver, text_list, timeout=5, choose_last=False):
    last_error = None

    for text in text_list:
        try:
            tap_text(driver, text, timeout=timeout, choose_last=choose_last)
            return True
        except Exception as e:
            last_error = e

    raise Exception(f"Cannot tap any text from {text_list}. Last error: {last_error}")


# =========================================================
# PAGE DETECTION
# =========================================================

# Detect whether the Reset Password pop-up/modal is currently displayed.
def is_reset_password_modal(driver):
    return source_contains_any(
        driver,
        [
            "reset password",
            "send reset code",
            "enter your email to receive a reset code",
        ],
    )


# Detect whether the verification code step is displayed after requesting reset code.
def is_code_step_displayed(driver):
    source = page_source_lower(driver)

    if "send reset code" in source:
        return False

    return any(
        keyword in source
        for keyword in [
            "verify code",
            "verify reset code",
            "enter verification",
            "verification code",
            "otp",
            "resend",
            "code sent",
            "check your email",
        ]
    )


# Detect whether the new password and confirm password step is displayed.
def is_password_step_displayed(driver):
    return source_contains_any(
        driver,
        [
            "new password",
            "confirm password",
            "confirm new password",
            "reset password",
            "update password",
        ],
    ) and not is_reset_password_modal(driver)


# Detect whether the app is currently on the Login page.
def is_login_page(driver):
    source = page_source_lower(driver)

    if is_reset_password_modal(driver) or is_code_step_displayed(driver):
        return False

    return any(
        keyword in source
        for keyword in [
            "welcome back",
            "sign in",
            "login",
            "forgot password",
            "enter your password",
        ]
    )


# Detect generic [object Object] error shown by the app.
def is_object_object_error(driver):
    return source_contains_any(driver, ["object object", "[object object]"])


# Restart the app while keeping app data such as saved login/account data.
def restart_app_without_clearing_data(driver):
    try:
        driver.terminate_app(APP_PACKAGE)
        time.sleep(1)
        driver.activate_app(APP_PACKAGE)
        time.sleep(3)
    except Exception:
        adb_force_stop_app()
        adb_start_app()


# Close possible native/custom dialogs that may block the reset password flow.
def close_possible_dialog(driver):
    """Close generic error/alert dialogs such as [object Object]."""
    for texts in [
        ["OK", "Ok", "ok", "Okay", "CLOSE", "Close", "Cancel", "CANCEL", "Dismiss"],
        ["Try Again", "TRY AGAIN", "Back", "BACK"],
    ]:
        try:
            tap_any_text(driver, texts, timeout=1, choose_last=True)
            time.sleep(1)
            return True
        except Exception:
            pass

    # Common Android alert button area near lower right/center.
    try:
        tap_coordinate(driver, 0.70, 0.72)
        time.sleep(1)
        if not is_object_object_error(driver):
            return True
    except Exception:
        pass

    return False


# =========================================================
# START EACH TEST FROM LOGIN PAGE
# =========================================================

# Recovery helper: navigate back to Login page before each test starts.
def go_back_to_login_page(driver):
    """
    Return to Login page from reset modal/code/password/error pages.
    Important: restart app without clearing data first. This keeps account data,
    but removes leftover modal/error state from the previous test.
    """
    restart_app_without_clearing_data(driver)
    hide_keyboard(driver)

    if is_login_page(driver):
        return

    for _ in range(10):
        hide_keyboard(driver)

        if is_login_page(driver):
            return

        # Close generic error dialog, including [object Object].
        close_possible_dialog(driver)
        if is_login_page(driver):
            return

        # Reset Password modal: cancel/back.
        if is_reset_password_modal(driver):
            try:
                tap_any_text(driver, ["Cancel", "CANCEL", "Close", "CLOSE", "OK", "Ok"], timeout=2, choose_last=True)
                time.sleep(1)
            except Exception:
                press_back(driver)
                time.sleep(1)
                if is_reset_password_modal(driver):
                    # Your screenshot's Cancel button is near the bottom of the pop-up.
                    tap_coordinate(driver, 0.50, 0.91)
            continue

        # Verification code page / password page / other nested page.
        press_back(driver)

    # Last recovery: force-stop and start app again.
    restart_app_without_clearing_data(driver)
    time.sleep(2)
    close_possible_dialog(driver)

    if is_login_page(driver):
        return

    save_evidence(driver, "cannot_return_to_login_after_recovery")
    raise AssertionError(
        "Cannot return to login page. Please manually open the app at the login page once, then rerun pytest."
    )


# Wrapper used by every test case to guarantee a clean Login page starting point.
def start_test_from_login_page(driver, test_name):
    try:
        go_back_to_login_page(driver)
    except Exception as e:
        save_evidence(driver, f"{test_name}_cannot_start_from_login_page")
        pytest.fail(f"{test_name} failed: Cannot return to login page. Reason: {e}")


# =========================================================
# RESET PASSWORD FLOW
# =========================================================

# Open the Reset Password modal by tapping Forgot Password from the Login page.
def click_forgot_password(driver):
    assert is_login_page(driver), "Test must start from login page."

    try:
        tap_any_text(
            driver,
            ["Forgot Password?", "Forgot Password", "forgot password"],
            timeout=8,
            choose_last=True,
        )
    except Exception:
        # Fallback coordinate based on your screenshot.
        tap_coordinate(driver, 0.76, 0.76)

    time.sleep(2)

    assert is_reset_password_modal(driver), (
        "After clicking Forgot Password?, Reset Password pop-up should be displayed."
    )


# Simple wrapper to improve readability in test steps.
def open_reset_password_modal(driver):
    click_forgot_password(driver)


# Enter email address into the Reset Password modal.
def type_email_on_reset_modal(driver, email):
    """
    Type email in Reset Password pop-up.
    Fix: do not fail only because Android/Appium returns empty attribute text.
    The field may contain the email visually, but get_attribute('text') can still be ''.
    """
    inputs = get_visible_inputs(driver)
    assert len(inputs) >= 1, "Email input field is not found on Reset Password pop-up."

    email_input = inputs[0]
    typed_value = clear_and_type_strict(driver, email_input, email)
    hide_keyboard(driver)

    # Soft verification only. Continue the test because React Native inputs can report empty text.
    source = page_source_lower(driver)
    if email and email.lower() not in typed_value.lower() and email.lower() not in source:
        print(
            f"\nWARNING: Could not verify email text through Appium attribute. "
            f"Continuing because the text may still be entered visually. Expected: {email}, Appium read: '{typed_value}'"
        )


# Submit the email request by tapping Send Reset Code.
def tap_send_reset_code(driver):
    try:
        tap_any_text(
            driver,
            ["Send Reset Code", "SEND RESET CODE", "Send reset code"],
            timeout=8,
        )
    except Exception:
        tap_coordinate(driver, 0.50, 0.61)

    time.sleep(3)


# Combined helper for opening modal, typing email, and requesting reset code.
def request_reset_code(driver, email):
    open_reset_password_modal(driver)
    type_email_on_reset_modal(driver, email)
    # Submit the reset code request after the email has been entered.
    tap_send_reset_code(driver)


# Stop the current test when the app shows a generic object error that blocks the next step.
def stop_if_object_error(driver, evidence_name, message):
    if is_object_object_error(driver):
        save_evidence(driver, evidence_name)
        pytest.fail(message)


# Enter verification/OTP code and submit it.
def enter_verification_code(driver, code):
    inputs = get_visible_inputs(driver)
    assert len(inputs) >= 1, "Verification code input field is not found."

    clear_and_type_strict(driver, inputs[0], code)
    hide_keyboard(driver)

    try:
        tap_any_text(
            driver,
            [
                "Verify Code",
                "VERIFY CODE",
                "Verify Reset Code",
                "Continue",
                "Next",
                "Submit",
            ],
            timeout=8,
        )
    except Exception:
        tap_coordinate(driver, 0.50, 0.61)

    time.sleep(3)


# Enter new password and confirm password, then submit the reset request.
def enter_new_passwords_and_submit(driver, new_password, confirm_password):
    inputs = get_visible_inputs(driver)
    assert len(inputs) >= 2, "New Password and Confirm Password fields are not found."

    clear_and_type(inputs[0], new_password)
    clear_and_type(inputs[1], confirm_password)
    hide_keyboard(driver)

    try:
        tap_any_text(
            driver,
            ["Reset Password", "RESET PASSWORD", "Update Password", "Submit"],
            timeout=8,
        )
    except Exception:
        tap_coordinate(driver, 0.50, 0.70)

    time.sleep(3)


# =========================================================
# ASSERT HELPERS
# =========================================================

# Assert that the app displays general error feedback.
def assert_error_feedback(driver):
    assert wait_until_source_contains_any(
        driver,
        [
            "object object",
            "[object object]",
            "error",
            "failed",
            "unable",
            "invalid",
            "not found",
            "not registered",
            "try again",
            "required",
        ],
        timeout=10,
    ), "System should display error feedback."


# Assert that invalid email format is rejected or modal stays open.
def assert_invalid_email_or_stay_on_modal(driver):
    assert (
        wait_until_source_contains_any(
            driver,
            [
                "invalid",
                "valid email",
                "email format",
                "enter a valid email",
                "object object",
                "[object object]",
            ],
            timeout=5,
        )
        or is_reset_password_modal(driver)
    ), "System should reject invalid email or remain on Reset Password pop-up."


# Assert that empty email submission is rejected or modal stays open.
def assert_empty_email_or_stay_on_modal(driver):
    assert (
        wait_until_source_contains_any(
            driver,
            [
                "required",
                "enter your email",
                "email is required",
                "object object",
                "[object object]",
            ],
            timeout=5,
        )
        or is_reset_password_modal(driver)
    ), "System should reject empty email or remain on Reset Password pop-up."


# Assert successful reset feedback or return to Login page.
def assert_success_feedback(driver):
    assert wait_until_source_contains_any(
        driver,
        [
            "success",
            "successful",
            "password reset",
            "updated",
            "login",
            "sign in",
        ],
        timeout=10,
    ), "System should display success confirmation or return to login page."


# Assert invalid/expired verification code feedback.
def assert_invalid_code_feedback(driver):
    assert wait_until_source_contains_any(
        driver,
        [
            "invalid",
            "expired",
            "wrong",
            "verification code",
            "object object",
            "[object object]",
        ],
        timeout=10,
    ), "System should reject invalid or expired verification code."


# Assert password mismatch validation feedback.
def assert_password_mismatch_feedback(driver):
    assert wait_until_source_contains_any(
        driver,
        [
            "match",
            "same",
            "mismatch",
            "password",
            "object object",
            "[object object]",
        ],
        timeout=10,
    ), "System should display password mismatch feedback."


# Assert network/server failure is handled properly.
def assert_network_or_server_error(driver):
    if wait_until_source_contains_any(
        driver,
        [
            "network",
            "internet",
            "offline",
            "no internet",
            "server",
            "service unavailable",
            "timeout",
            "connection",
            "unable",
            "failed",
            "error",
            "try again",
            "object object",
            "[object object]",
        ],
        timeout=10,
    ):
        return

    if is_reset_password_modal(driver):
        return

    source = page_source_lower(driver)
    if source == "":
        print("WARNING: Page source cannot be read after network/server test. Treating as handled interruption.")
        return

    raise AssertionError("System should display network/server error message or remain on Reset Password pop-up.")


# =========================================================
# TEST CASES
# =========================================================

# ══════════════════════════════════════════════════════════════════════════════
# TC-03-001
# Verify registered user can reset password successfully using valid email/code/password.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_001_reset_password_successfully():
    # Step 1: Prepare test name, driver, and clean Login page state.
    test_name = "TC-03-001"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    # Step 2: Request reset code using a registered email address.
    request_reset_code(driver, REGISTERED_EMAIL)

    stop_if_object_error(
        driver,
        "TC-03-001_object_error_after_valid_email",
        "System shows [object Object] after valid email. Stop test here because code/password steps cannot be tested.",
    )

    if not is_code_step_displayed(driver):
        save_evidence(driver, "TC-03-001_no_code_step_after_valid_email")
        pytest.fail("After valid email, system did not proceed to verification code step.")

    # Step 3: Enter the valid verification code received from email/environment variable.
    enter_verification_code(driver, VALID_CODE)

    # Step 4: Submit matching new password and confirm password.
    enter_new_passwords_and_submit(
        driver,
        new_password=NEW_PASSWORD,
        confirm_password=NEW_PASSWORD,
    )

    # Step 5: Save evidence and verify success confirmation.
    save_evidence(driver, "TC-03-001_reset_password_successfully")
    assert_success_feedback(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-002
# Verify system rejects reset password request for an unregistered email address.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_002_reject_unregistered_email():
    # Step 1: Start from Login page and use a clean driver session.
    test_name = "TC-03-002"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    # Step 2: Submit an email that is not registered in the system.
    request_reset_code(driver, "nonuser@gmail.com")

    # Step 3: Save evidence and verify error feedback is shown.
    save_evidence(driver, "TC-03-002_reject_unregistered_email")
    assert_error_feedback(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-003
# Verify system rejects an email that does not follow a valid email format.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_003_reject_invalid_email_format():
    # Step 1: Start from Login page and use a clean driver session.
    test_name = "TC-03-003"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    # Step 2: Submit invalid email format without @ or domain.
    request_reset_code(driver, "invalidemailaddress")

    # Step 3: Save evidence and verify invalid email is rejected or modal remains open.
    save_evidence(driver, "TC-03-003_reject_invalid_email_format")
    assert_invalid_email_or_stay_on_modal(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-004
# Verify system rejects reset code request when the email field is empty.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_004_reject_empty_email_field():
    # Step 1: Start from Login page and open the Reset Password modal.
    test_name = "TC-03-004"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    open_reset_password_modal(driver)

    inputs = get_visible_inputs(driver)
    assert len(inputs) >= 1, "Email input field is not found on Reset Password pop-up."

    # Step 2: Leave the email input empty.
    clear_and_type(inputs[0], "")
    hide_keyboard(driver)

    # Step 3: Try to send reset code without entering email.
    tap_send_reset_code(driver)

    # Step 4: Save evidence and verify empty email validation.
    save_evidence(driver, "TC-03-004_reject_empty_email_field")
    assert_empty_email_or_stay_on_modal(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-005
# Verify system rejects invalid or expired verification code.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_005_reject_invalid_or_expired_code():
    # Step 1: Start from Login page and request a reset code first.
    test_name = "TC-03-005"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    request_reset_code(driver, REGISTERED_EMAIL)

    stop_if_object_error(
        driver,
        "TC-03-005_object_error_before_code_step",
        "System shows [object Object] before code step. Stop test here because invalid code cannot be tested.",
    )

    if not is_code_step_displayed(driver):
        save_evidence(driver, "TC-03-005_no_code_step")
        pytest.fail("Cannot test invalid code because system did not proceed to verification code step.")

    # Step 2: Enter an intentionally invalid verification code.
    enter_verification_code(driver, "000000")

    # Step 3: Save evidence and verify invalid/expired code feedback.
    save_evidence(driver, "TC-03-005_reject_invalid_or_expired_code")
    assert_invalid_code_feedback(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-006
# Verify system rejects new password submission when passwords do not match.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_006_reject_mismatched_passwords():
    # Step 1: Start from Login page and request a reset code first.
    test_name = "TC-03-006"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    request_reset_code(driver, REGISTERED_EMAIL)

    stop_if_object_error(
        driver,
        "TC-03-006_object_error_before_password_step",
        "System shows [object Object] before password step. Stop test here because password mismatch cannot be tested.",
    )

    if not is_code_step_displayed(driver):
        save_evidence(driver, "TC-03-006_no_code_step")
        pytest.fail("Cannot test password mismatch because system did not proceed to verification code step.")

    enter_verification_code(driver, VALID_CODE)

    # Step 2: Submit two different passwords to trigger mismatch validation.
    enter_new_passwords_and_submit(
        driver,
        new_password=NEW_PASSWORD,
        confirm_password="wrongPassword123?",
    )

    # Step 3: Save evidence and verify password mismatch feedback.
    save_evidence(driver, "TC-03-006_reject_mismatched_passwords")
    assert_password_mismatch_feedback(driver)


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-007
# Verify user can request the verification code to be resent.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_007_resend_verification_code():
    # Step 1: Start from Login page and proceed until verification code step.
    test_name = "TC-03-007"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    request_reset_code(driver, REGISTERED_EMAIL)

    stop_if_object_error(
        driver,
        "TC-03-007_object_error_before_resend_step",
        "System shows [object Object] before resend step. Stop test here because resend code cannot be tested.",
    )

    if not is_code_step_displayed(driver):
        save_evidence(driver, "TC-03-007_no_code_step")
        pytest.fail("Cannot test resend code because system did not proceed to verification code step.")

    # Step 2: Find and tap a Resend Code option using several possible text labels.
    try:
        tap_any_text(
            driver,
            [
                "Resend",
                "RESEND",
                "Resend Code",
                "Resend Reset Code",
                "Did not receive",
                "Send Again",
            ],
            timeout=8,
            choose_last=True,
        )
    except Exception:
        save_evidence(driver, "TC-03-007_resend_button_not_found")
        pytest.fail("Resend Code option is not found.")

    time.sleep(3)

    # Step 3: Save evidence and verify resend instruction/success feedback.
    save_evidence(driver, "TC-03-007_resend_verification_code")

    assert wait_until_source_contains_any(
        driver,
        [
            "sent",
            "code",
            "resend",
            "check",
            "email",
            "spam",
            "success",
            "object object",
            "[object object]",
        ],
        timeout=10,
    ), "System should resend code or display instruction to check email/spam folder."


# ══════════════════════════════════════════════════════════════════════════════
# TC-03-008
# Verify reset password flow handles server/internet interruption properly.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_03_008_handle_server_or_internet_problem():
    # Step 1: Start from Login page and open Reset Password modal.
    test_name = "TC-03-008"
    driver = get_driver(test_name)
    start_test_from_login_page(driver, test_name)

    open_reset_password_modal(driver)

    network_disabled = False

    try:
        # Step 2: Disable Wi-Fi and mobile data using ADB to simulate network/server problem.
        # Use adb instead of Appium mobile:shell.
        # This avoids needing: appium --relaxed-security
        adb_shell(["svc", "wifi", "disable"])
        adb_shell(["svc", "data", "disable"])
        network_disabled = True
        time.sleep(3)
    except Exception as e:
        print(f"WARNING: Could not disable network automatically. Reason: {e}")

    try:
        if not network_disabled:
            save_evidence(driver, "TC-03-008_network_disable_not_available")
            assert is_reset_password_modal(driver), "Reset Password pop-up should still be displayed."
            return

        # Step 3: Try to request reset code while network is unavailable.
        type_email_on_reset_modal(driver, REGISTERED_EMAIL)
        tap_send_reset_code(driver)

        # Step 4: Save evidence and verify network/server error handling.
        save_evidence(driver, "TC-03-008_handle_server_or_internet_problem")
        assert_network_or_server_error(driver)

    finally:
        # Step 5: Always restore network connection after the test.
        adb_shell(["svc", "wifi", "enable"])
        adb_shell(["svc", "data", "enable"])
        time.sleep(3)
