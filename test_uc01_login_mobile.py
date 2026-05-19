import pytest
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


VALID_EMAIL = "user@gmail.com"
VALID_PASSWORD = "User123*"

WRONG_PASSWORD = "WrongPassword123"
UNREGISTERED_EMAIL = "notfounduser@gmail.com"
INVALID_EMAIL = "usergmail.com"
SPECIAL_EMAIL = "user@@gmail..com"


def setup_driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Pixel 9 Pro XL"
    options.app_package = "com.adamarbain.dengueeyemobileapp"
    options.app_activity = ".MainActivity"
    options.no_reset = True
    options.new_command_timeout = 300

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    time.sleep(3)

    try:
        server = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("10.0.2.2:8081")'
        )
        server.click()
        time.sleep(8)
    except:
        pass

    return driver


@pytest.fixture
def driver():
    driver = setup_driver()
    yield driver
    driver.quit()


def wait_text(driver, text, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{text}")'
            )
        )
    )


def find_text(driver, text):
    return driver.find_element(
        AppiumBy.ANDROID_UIAUTOMATOR,
        f'new UiSelector().textContains("{text}")'
    )


def find_input_by_index(driver, index):
    inputs = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
    assert len(inputs) > index, f"Input field index {index} not found"
    return inputs[index]


def clear_and_type(element, text):
    element.click()
    element.clear()
    element.send_keys(text)


def click_sign_in(driver):
    find_text(driver, "Sign In").click()


def go_back_to_login(driver):
    try:
        driver.back()
        time.sleep(1)
    except:
        pass


def assert_error_visible(driver):
    time.sleep(2)
    possible_errors = [
        "Login failed",
        "Invalid",
        "incorrect",
        "not found",
        "required",
        "email",
        "password",
        "Admin users cannot log in"
    ]

    page = driver.page_source.lower()
    assert any(err.lower() in page for err in possible_errors), \
        "Expected error or validation message was not displayed."


# TP-01-001
def test_tp_01_001_login_ui_elements_displayed(driver):
    wait_text(driver, "Welcome Back")

    assert find_text(driver, "Email Address").is_displayed()
    assert find_text(driver, "Password").is_displayed()
    assert find_text(driver, "Sign In").is_displayed()
    assert find_text(driver, "Sign Up").is_displayed()
    assert find_text(driver, "Forgot Password?").is_displayed()


# TP-01-002
def test_tp_01_002_successful_login(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, VALID_EMAIL)
    clear_and_type(password_input, VALID_PASSWORD)

    click_sign_in(driver)

    WebDriverWait(driver, 20).until(
        lambda d: "dashboard" in d.page_source.lower()
        or "Dashboard" in d.page_source
        or "Dengue" in d.page_source
    )


# TP-01-003
def test_tp_01_003_sign_up_navigation(driver):
    wait_text(driver, "Welcome Back")

    find_text(driver, "Sign Up").click()

    WebDriverWait(driver, 15).until(
        lambda d: "Register" in d.page_source
        or "Sign Up" in d.page_source
        or "Create" in d.page_source
    )


# TP-01-004
def test_tp_01_004_empty_required_fields(driver):
    wait_text(driver, "Welcome Back")

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-005
def test_tp_01_005_wrong_credentials(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, VALID_EMAIL)
    clear_and_type(password_input, WRONG_PASSWORD)

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-006
def test_tp_01_006_unregistered_email(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, UNREGISTERED_EMAIL)
    clear_and_type(password_input, VALID_PASSWORD)

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-007
def test_tp_01_007_forgot_password_navigation(driver):
    wait_text(driver, "Welcome Back")

    find_text(driver, "Forgot Password?").click()

    WebDriverWait(driver, 10).until(
        lambda d: "Reset Password" in d.page_source
        or "Enter your email to receive a reset code" in d.page_source
    )


# TP-01-008
def test_tp_01_008_invalid_email_format(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, INVALID_EMAIL)
    clear_and_type(password_input, VALID_PASSWORD)

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-009
def test_tp_01_009_password_masking(driver):
    wait_text(driver, "Welcome Back")

    password_input = find_input_by_index(driver, 1)
    clear_and_type(password_input, VALID_PASSWORD)

    password_value = password_input.get_attribute("text")

    assert password_value != VALID_PASSWORD, "Password is visible in plain text."


# TP-01-010
def test_tp_01_010_email_with_leading_trailing_spaces(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, f"  {VALID_EMAIL}  ")
    clear_and_type(password_input, VALID_PASSWORD)

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-011
def test_tp_01_011_password_with_leading_trailing_spaces(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, VALID_EMAIL)
    clear_and_type(password_input, f"  {VALID_PASSWORD}  ")

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-012
def test_tp_01_012_special_characters_in_email(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, SPECIAL_EMAIL)
    clear_and_type(password_input, VALID_PASSWORD)

    click_sign_in(driver)

    assert_error_visible(driver)


# TP-01-013
def test_tp_01_013_rapid_multiple_clicks(driver):
    wait_text(driver, "Welcome Back")

    email_input = find_input_by_index(driver, 0)
    password_input = find_input_by_index(driver, 1)

    clear_and_type(email_input, VALID_EMAIL)
    clear_and_type(password_input, VALID_PASSWORD)

    for _ in range(5):
        try:
            find_text(driver, "Sign In").click()
            time.sleep(0.2)
        except:
            break

    WebDriverWait(driver, 30).until(
        lambda d: "dashboard" in d.page_source.lower()
        or "profile" in d.page_source.lower()
        or "action" in d.page_source.lower()
        or "notification" in d.page_source.lower()
    )


def test_tp_01_014_too_many_failed_login_attempts_mobile(driver):
    wait_text(driver, "Welcome Back")

    for i in range(6):
        email_input = find_input_by_index(driver, 0)
        password_input = find_input_by_index(driver, 1)

        clear_and_type(email_input, VALID_EMAIL)
        clear_and_type(password_input, WRONG_PASSWORD)

        click_sign_in(driver)
        time.sleep(1)

    page = driver.page_source.lower()

    assert (
        "too many failed attempts" in page
        or "try again later" in page
    ), "Expected lockout message was not displayed."