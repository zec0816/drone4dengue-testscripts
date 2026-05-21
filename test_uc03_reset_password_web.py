# test_web_uc03_reset_password.py
# Drone4Dengue – UC-03 Reset Password (Web Based)
# Automated test suite using Selenium WebDriver (Python)
#
# Test Coverage:
#   TC-03-001 → Reset password successfully with registered email and valid code
#   TC-03-002 → Reject reset request for unregistered email
#   TC-03-003 → Reject invalid email format using browser validation
#   TC-03-004 → Reject empty email field using browser validation
#   TC-03-005 → Reject invalid or expired verification code
#   TC-03-006 → Reject mismatched new password and confirm password
#   TC-03-007 → Resend verification code
#   TC-03-008 → Handle server or internet problem
#
# Notes:
# - This test file focuses on the web reset-password flow.
# - Chrome is used as the browser for automation.
# - VALID_CODE must be changed to a real email verification code when testing the success flow.
# - Selectors are written flexibly with XPath so the tests can still work if UI text/case changes slightly.
#
# Run with:
#   python -m pytest test_web_uc03_reset_password.py -v


import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# Test Data
# =========================
# Environment variables are used so the URL, email, password, and reset code
# can be changed without editing the test script directly.
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")

REGISTERED_EMAIL = os.getenv("REGISTERED_EMAIL", "ledlow0405@gmail.com")
NEW_PASSWORD = os.getenv("NEW_PASSWORD", "a1b2c3d4E?")

# IMPORTANT:
# Change this to the real code received from email when testing TC-03-001 / TC-03-006.
VALID_CODE = os.getenv("VALID_CODE", "123456")


# =========================
# Selectors for your actual UI
# =========================
# Each selector stores the UI element locator used by Selenium.
# XPath is used here because the actual UI may use different tags, classes, or text cases.

# Locate the Forgot Password link/button on the login page.
FORGOT_PASSWORD_LINK = (
    By.XPATH,
    "//*[self::a or self::button or @role='button' or contains(@class, 'cursor-pointer') or contains(@class, 'forgot')][contains(normalize-space(.), 'Forgot Password')]"
)

# Confirm that the reset password page or modal is displayed.
RESET_PAGE_TITLE = (
    By.XPATH,
    "//*[contains(normalize-space(.), 'Reset Password')]"
)

# Locate the email input used to request a password reset code.
EMAIL_INPUT = (
    By.XPATH,
    "(//input[@type='email' or @name='email' or @id='email' or contains(@placeholder, 'Email') or contains(@placeholder, 'email') or not(@type)])[1]"
)

# Locate the button that sends the reset verification code.
SEND_CODE_BUTTON = (
    By.XPATH,
    "//button[contains(normalize-space(.), 'SEND CODE') or contains(normalize-space(.), 'Send Code') or contains(normalize-space(.), 'Send code')]"
)

# Locate the verification code input field.
CODE_INPUT = (
    By.XPATH,
    "(//input[@name='code' or @id='code' or contains(@placeholder, 'Code') or contains(@placeholder, 'code') or @type='text'])[1]"
)

# Locate the button that verifies the entered reset code.
VERIFY_CODE_BUTTON = (
    By.XPATH,
    "//button[contains(normalize-space(.), 'VERIFY') or contains(normalize-space(.), 'Verify') or contains(normalize-space(.), 'SUBMIT') or contains(normalize-space(.), 'Submit') or contains(normalize-space(.), 'Continue')]"
)

# Locate the new password input field.
NEW_PASSWORD_INPUT = (
    By.XPATH,
    "//input[@name='newPassword' or @id='newPassword' or contains(@placeholder, 'New Password') or contains(@placeholder, 'new password')]"
)

# Locate the confirm password input field.
CONFIRM_PASSWORD_INPUT = (
    By.XPATH,
    "//input[@name='confirmPassword' or @id='confirmPassword' or contains(@placeholder, 'Confirm Password') or contains(@placeholder, 'confirm password')]"
)

# Locate the final button that submits the new password.
RESET_PASSWORD_BUTTON = (
    By.XPATH,
    "//button[contains(normalize-space(.), 'RESET PASSWORD') or contains(normalize-space(.), 'Reset Password') or contains(normalize-space(.), 'SUBMIT') or contains(normalize-space(.), 'Submit')]"
)

# Locate the resend-code option shown after requesting a reset code.
RESEND_CODE_BUTTON = (
    By.XPATH,
    "//*[contains(normalize-space(.), 'Resend') or contains(normalize-space(.), 'Did not receive')]"
)


# =========================
# Message Selectors
# =========================
# These selectors are used to detect success or error messages after each action.
# translate() is used to make the text matching case-insensitive.

# Detect positive feedback such as code sent, success, or password updated.
SUCCESS_MESSAGE = (
    By.XPATH,
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'success') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sent') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'updated')]"
)

# Detect validation message when the email does not belong to any user account.
EMAIL_NOT_FOUND_MESSAGE = (
    By.XPATH,
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not found') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'not registered') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'no account') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'user not found')]"
)

# Detect validation message for an invalid, wrong, or expired reset code.
INVALID_CODE_MESSAGE = (
    By.XPATH,
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'invalid') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'expired') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wrong code')]"
)

# Detect validation message when new password and confirm password do not match.
PASSWORD_MISMATCH_MESSAGE = (
    By.XPATH,
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'match') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'same')]"
)

# Detect error feedback when the browser is offline or the server cannot respond.
NETWORK_ERROR_MESSAGE = (
    By.XPATH,
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'network') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'server') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'unable') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'failed') "
    "or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'error')]"
)


# =========================
# Pytest Fixture
# =========================
# This fixture creates a new Chrome browser session for each test case
# and closes the browser after the test finishes.

@pytest.fixture
def driver():
    # Start Chrome in maximized mode to reduce element visibility issues.
    options = Options()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)

    # Give the test function access to the browser instance.
    yield driver

    # Close Chrome after each test to keep the next test independent.
    driver.quit()


# =========================
# Helper Functions
# =========================
# Helper functions reduce repeated Selenium code and make each test case easier to read.

def wait(driver, locator, timeout=15):
    # Wait until an element is visible before using it.
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )


def click(driver, locator, timeout=15):
    # Wait until an element can be clicked, then scroll it into view first.
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator)
    )

    # Scroll to the element to avoid click interception caused by hidden/off-screen elements.
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    try:
        element.click()
    except Exception:
        # JavaScript click is used as a fallback if normal Selenium click fails.
        driver.execute_script("arguments[0].click();", element)


def type_text(driver, locator, text, timeout=15):
    # Clear the field first, then enter the required test data.
    element = wait(driver, locator, timeout)
    element.clear()
    element.send_keys(text)
    return element


def get_email_input(driver):
    # Reuse the email input locator when browser validation needs to be checked.
    return wait(driver, EMAIL_INPUT)


def open_forgot_password_page(driver):
    # Open the login page and navigate to the Reset Password page/modal.
    driver.get(BASE_URL)

    # Click Forgot Password from the login page.
    click(driver, FORGOT_PASSWORD_LINK)

    # Ensure the reset password screen is loaded before continuing.
    wait(driver, RESET_PAGE_TITLE)


def request_reset_code(driver, email):
    # Common flow: open reset page, type email, and send reset code.
    open_forgot_password_page(driver)

    # Enter the email address that will receive the verification code.
    type_text(driver, EMAIL_INPUT, email)

    # Submit the reset code request.
    click(driver, SEND_CODE_BUTTON)


def browser_validation_message(element):
    # Read the browser's built-in validation message for required/invalid input fields.
    return element.get_attribute("validationMessage")


# =========================
# TC-03-001
# =========================
# Positive test: registered user completes the full reset password flow.

def test_tc_03_001_reset_password_successfully(driver):
    """
    Verify user can reset password using registered email,
    valid verification code, and matching new passwords.
    """
    # Request reset code using an existing registered account.
    request_reset_code(driver, REGISTERED_EMAIL)

    # Enter and verify the reset code received from email.
    type_text(driver, CODE_INPUT, VALID_CODE)
    click(driver, VERIFY_CODE_BUTTON)

    # Enter matching passwords and submit the reset request.
    type_text(driver, NEW_PASSWORD_INPUT, NEW_PASSWORD)
    type_text(driver, CONFIRM_PASSWORD_INPUT, NEW_PASSWORD)
    click(driver, RESET_PASSWORD_BUTTON)

    # Test passes if success feedback is displayed.
    assert wait(driver, SUCCESS_MESSAGE).is_displayed()


# =========================
# TC-03-002
# =========================
# Negative test: system should not send reset code to an unregistered email.

def test_tc_03_002_reject_unregistered_email(driver):
    """
    Verify system rejects reset password request
    when email address is not registered.
    """
    # Use an email address that should not exist in the system.
    request_reset_code(driver, "nonuser@gmail.com")

    # Test passes if the system shows an account-not-found message.
    assert wait(driver, EMAIL_NOT_FOUND_MESSAGE).is_displayed()


# =========================
# TC-03-003
# =========================
# Negative test: invalid email format should be blocked by browser validation.

def test_tc_03_003_reject_invalid_email_format(driver):
    """
    Verify system rejects invalid email format
    during reset password request.
    """
    # Open reset password page without using the common request helper
    # because this test needs to inspect the email input validation.
    open_forgot_password_page(driver)

    # Type an invalid email value that does not follow email format.
    email_element = type_text(driver, EMAIL_INPUT, "invalidemailaddress")
    click(driver, SEND_CODE_BUTTON)

    # Read HTML5 browser validation message from the email field.
    validation_message = browser_validation_message(email_element)

    # Test passes if the browser blocks the invalid email input.
    assert validation_message != ""


# =========================
# TC-03-004
# =========================
# Negative test: empty email field should be blocked before sending reset request.

def test_tc_03_004_reject_empty_email_field(driver):
    """
    Verify system rejects empty email field
    during reset password request.
    """
    # Open reset password page and leave the email field empty.
    open_forgot_password_page(driver)

    # Get the email field so its browser validation message can be checked.
    email_element = get_email_input(driver)
    click(driver, SEND_CODE_BUTTON)

    # Empty required input should trigger browser validation.
    validation_message = browser_validation_message(email_element)

    # Test passes if the browser blocks the empty required field.
    assert validation_message != ""


# =========================
# TC-03-005
# =========================
# Negative test: wrong or expired verification code should show an error message.

def test_tc_03_005_reject_invalid_or_expired_code(driver):
    """
    Verify system rejects invalid or expired verification code.
    """
    # Request reset code first so the verification-code page is opened.
    request_reset_code(driver, REGISTERED_EMAIL)

    # Enter an intentionally invalid code.
    type_text(driver, CODE_INPUT, "000000")
    click(driver, VERIFY_CODE_BUTTON)

    # Test passes if invalid/expired code feedback is displayed.
    assert wait(driver, INVALID_CODE_MESSAGE).is_displayed()


# =========================
# TC-03-006
# =========================
# Negative test: password reset should fail when both password fields are different.

def test_tc_03_006_reject_mismatched_passwords(driver):
    """
    Verify mismatched new password and confirm password are rejected.
    """
    # Request reset code using a valid registered email.
    request_reset_code(driver, REGISTERED_EMAIL)

    # Verify the reset code to move to the password update step.
    type_text(driver, CODE_INPUT, VALID_CODE)
    click(driver, VERIFY_CODE_BUTTON)

    # Enter two different passwords to trigger mismatch validation.
    type_text(driver, NEW_PASSWORD_INPUT, NEW_PASSWORD)
    type_text(driver, CONFIRM_PASSWORD_INPUT, "wrongPassword123?")
    click(driver, RESET_PASSWORD_BUTTON)

    # Test passes if password mismatch feedback is displayed.
    assert wait(driver, PASSWORD_MISMATCH_MESSAGE).is_displayed()


# =========================
# TC-03-007
# =========================
# Functional test: user can request another verification code.

def test_tc_03_007_resend_verification_code(driver):
    """
    Verify system provides option to resend verification code
    or check spam folder.
    """
    # Request the first reset code using a registered email.
    request_reset_code(driver, REGISTERED_EMAIL)

    # Click the resend code option.
    click(driver, RESEND_CODE_BUTTON)

    # Test passes if the system confirms that another code was sent.
    assert wait(driver, SUCCESS_MESSAGE).is_displayed()


# =========================
# TC-03-008
# =========================
# Error-handling test: simulate offline network and verify error feedback is displayed.

def test_tc_03_008_handle_server_or_internet_problem(driver):
    """
    Verify system handles reset password failure
    due to server or internet problem.
    """
    open_forgot_password_page(driver)

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {
            "offline": True,
            "latency": 0,
            "downloadThroughput": 0,
            "uploadThroughput": 0,
        },
    )

    type_text(driver, EMAIL_INPUT, REGISTERED_EMAIL)
    click(driver, SEND_CODE_BUTTON)

    assert wait(driver, NETWORK_ERROR_MESSAGE).is_displayed()

    driver.execute_cdp_cmd(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 0,
            "downloadThroughput": -1,
            "uploadThroughput": -1,
        },
    )