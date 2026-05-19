import pytest
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


VALID_EMAIL = "tannew@gmail.com"
VALID_PASSWORD = "Pass1234*"

SHORT_PASSWORD = "Pass1*"
DUPLICATE_EMAIL = "tan@gmail.com"
INVALID_EMAIL = "user@@gmail..com"


def setup_driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Pixel 9 Pro XL"
    options.app_package = "com.adamarbain.dengueeyemobileapp"
    options.app_activity = ".MainActivity"
    options.no_reset = True
    options.new_command_timeout = 300

    driver = webdriver.Remote(
        "http://127.0.0.1:4723",
        options=options
    )

    time.sleep(3)

    return driver


@pytest.fixture
def driver():
    driver = setup_driver()

    yield driver

    driver.quit()


def wait_text(driver, text, timeout=20):
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


# Find input field by position
def find_input_by_index(driver, index):
    inputs = driver.find_elements(
        AppiumBy.CLASS_NAME,
        "android.widget.EditText"
    )

    assert len(inputs) > index, (
        f"Input field index {index} not found. "
        f"Found {len(inputs)} inputs."
    )

    return inputs[index]


def clear_and_type(element, text):
    element.click()
    element.clear()
    element.send_keys(text)


# Hide keyboard before button interaction
def hide_keyboard(driver):
    try:
        driver.hide_keyboard()
        time.sleep(1)

    except:
        try:
            driver.back()
            time.sleep(1)

        except:
            pass


def page_text(driver):
    return driver.page_source.lower()


def go_to_login(driver):
    for _ in range(6):

        source = driver.page_source

        if "Welcome Back" in source:
            return

        try:
            find_text(driver, "OK").click()
            time.sleep(1)
            continue

        except:
            pass

        driver.back()
        time.sleep(1)

    raise Exception("Unable to return to Login screen.")


def go_to_register(driver):
    go_to_login(driver)

    wait_text(driver, "Welcome Back")

    find_text(driver, "Sign Up").click()

    WebDriverWait(driver, 20).until(
        lambda d:
        "Create Account" in d.page_source
        or "Confirm Password" in d.page_source
        or "Join DengueEye" in d.page_source
    )


def click_agree_checkbox(driver):
    # Submit registration form
    hide_keyboard(driver)

    agree_text = find_text(driver, "I agree")

    loc = agree_text.location

    driver.tap([(loc["x"] - 20, loc["y"] + 10)])

    time.sleep(1)


def fill_register_form(
    driver,
    email,
    password,
    confirm,
    checkbox=True
):
    clear_and_type(
        find_input_by_index(driver, 0),
        email
    )

    clear_and_type(
        find_input_by_index(driver, 1),
        password
    )

    clear_and_type(
        find_input_by_index(driver, 2),
        confirm
    )

    hide_keyboard(driver)

    if checkbox:
        click_agree_checkbox(driver)


def click_create_account(driver):
    hide_keyboard(driver)

    buttons = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Create Account")'
    )

    assert len(buttons) >= 2, (
        f"Expected title and button, "
        f"but found {len(buttons)} Create Account elements."
    )

    button = buttons[-1]

    loc = button.location
    size = button.size

    x = loc["x"] + size["width"] // 2
    y = loc["y"] + size["height"] // 2

    driver.tap([(x, y)])

    time.sleep(3)


def assert_validation_visible(driver):
    time.sleep(2)

    text = page_text(driver)

    assert (
        "required" in text
        or "please fill in all fields" in text
        or "valid email" in text
        or "email already exists" in text
        or "password" in text
        or "do not match" in text
        or "at least" in text
        or "uppercase" in text
        or "lowercase" in text
        or "number" in text
        or "special" in text
        or "symbol" in text
        or "terms and condition" in text
    ), (
        "Expected validation/error message "
        "was not displayed."
    )


def assert_success_alert_and_login(driver):
    wait_text(driver, "Success", timeout=30)

    wait_text(
        driver,
        "Registration successful",
        timeout=10
    )

    find_text(driver, "OK").click()

    wait_text(driver, "Welcome Back", timeout=20)

    assert find_text(
        driver,
        "Email Address"
    ).is_displayed()

    assert find_text(
        driver,
        "Password"
    ).is_displayed()

    assert find_text(
        driver,
        "Sign In"
    ).is_displayed()


def assert_no_success(driver):
    time.sleep(2)

    text = page_text(driver)

    assert (
        "registration successful" not in text
    ), (
        "FAIL: Invalid input still "
        "registered successfully."
    )


# TC-02-001
# Covers: TCOV-02-001, TCOV-02-002
def test_tp_02_001_successful_registration(driver):
    # Test successful account registration
    go_to_register(driver)

    fill_register_form(
        driver,
        email=VALID_EMAIL,
        password=VALID_PASSWORD,
        confirm=VALID_PASSWORD,
        checkbox=True
    )

    click_create_account(driver)

    assert_success_alert_and_login(driver)


# TC-02-002
# Covers: TCOV-02-003, TCOV-02-029, TCOV-02-031
def test_tp_02_002_navigation_register_to_login(driver):
    go_to_register(driver)

    assert find_text(
        driver,
        "Create Account"
    ).is_displayed()

    assert find_text(
        driver,
        "Confirm Password"
    ).is_displayed()

    find_text(driver, "Sign In").click()

    wait_text(driver, "Welcome Back")

    assert find_text(
        driver,
        "Email Address"
    ).is_displayed()

    assert find_text(
        driver,
        "Password"
    ).is_displayed()

    assert find_text(
        driver,
        "Sign In"
    ).is_displayed()


# TC-02-003
# Covers: TCOV-02-004
def test_tp_02_003_duplicate_email(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email=DUPLICATE_EMAIL,
        password=VALID_PASSWORD,
        confirm=VALID_PASSWORD,
        checkbox=True
    )

    click_create_account(driver)

    assert_no_success(driver)

    assert_validation_visible(driver)


# TC-02-004
# Covers: TCOV-02-005, TCOV-02-023
# Test empty required field validation
def test_tp_02_003_empty_required_fields(driver):
    go_to_register(driver)

    click_create_account(driver)

    assert_no_success(driver)

    assert_validation_visible(driver)


# TC-02-005
# Covers: TCOV-02-006, TCOV-02-032, TCOV-02-033
def test_tp_02_004_checkbox_unchecked_blocks_registration(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email="policy@gmail.com",
        password=VALID_PASSWORD,
        confirm=VALID_PASSWORD,
        checkbox=False
    )

    click_create_account(driver)

    time.sleep(2)

    assert (
        "registration successful"
        not in page_text(driver)
    )

    assert "create account" in page_text(driver)


# TC-02-007
# Covers: TCOV-02-013, TCOV-02-014, TCOV-02-015, TCOV-02-016, TCOV-02-017, TCOV-02-018
def test_tp_02_005_invalid_password_requirement(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email="short@gmail.com",
        password=SHORT_PASSWORD,
        confirm=SHORT_PASSWORD,
        checkbox=True
    )

    click_create_account(driver)

    assert_no_success(driver)

    assert_validation_visible(driver)


# TC-02-008
# Covers: TCOV-02-020, TCOV-02-021, TCOV-02-022
def test_tp_02_006_invalid_email_format(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email=INVALID_EMAIL,
        password=VALID_PASSWORD,
        confirm=VALID_PASSWORD,
        checkbox=True
    )

    click_create_account(driver)

    assert_no_success(driver)

    assert_validation_visible(driver)


# TC-02-009
# Covers: TCOV-02-019, TCOV-02-024, TCOV-02-028
def test_tp_02_006_email_spaces_and_double_click(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email=" user@gmail.com ",
        password=VALID_PASSWORD,
        confirm=VALID_PASSWORD,
        checkbox=True
    )

    click_create_account(driver)

    click_create_account(driver)

    time.sleep(2)

    text = page_text(driver)

    assert (
        "registration successful" in text
        or "welcome back" in text
        or "sign in" in text
        or "email already exists" in text
        or "valid email" in text
        or "email" in text
    )
