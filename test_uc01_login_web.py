import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000"

VALID_EMAIL = "admin@gmail.com"
VALID_PASSWORD = "admin123"
WRONG_PASSWORD = "wrongpassword"
UNREGISTERED_EMAIL = "unknown@email.com"
INVALID_EMAIL = "invalidemail"

EMAIL_INPUT = (By.ID, "email")
PASSWORD_INPUT = (By.ID, "password")
LOGIN_BUTTON = (By.XPATH, "//button[contains(., 'LOGIN')]")
SIGN_UP_LINK = (By.XPATH, "//*[contains(., 'Sign up') or contains(., 'SIGN UP')]")
FORGOT_PASSWORD_LINK = (By.XPATH, "//*[contains(., 'Forgot Password') or contains(., 'Forgot password')]")


@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def open_login_page(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(BASE_URL)
    wait.until(EC.visibility_of_element_located(EMAIL_INPUT))
    wait.until(EC.visibility_of_element_located(PASSWORD_INPUT))


def type_into(driver, locator, text):
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.element_to_be_clickable(locator))
    element.click()
    element.clear()
    element.send_keys(text)


def click_login(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable(LOGIN_BUTTON)).click()


def test_tp_01_001_login_page_ui_elements(driver):
    open_login_page(driver)

    assert driver.find_element(*EMAIL_INPUT).is_displayed()
    assert driver.find_element(*PASSWORD_INPUT).is_displayed()
    assert driver.find_element(*LOGIN_BUTTON).is_displayed()
    assert driver.find_element(*SIGN_UP_LINK).is_displayed()
    assert driver.find_element(*FORGOT_PASSWORD_LINK).is_displayed()


def test_tp_01_002_successful_login(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, VALID_EMAIL)
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)
    click_login(driver)

    dashboard = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Dashboard') or contains(., 'dashboard')]")
        )
    )

    assert dashboard.is_displayed()


def test_tp_01_003_sign_up_navigation(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    wait.until(EC.element_to_be_clickable(SIGN_UP_LINK)).click()

    register_page = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Register') or contains(., 'Sign up')]")
        )
    )

    assert register_page.is_displayed()


def test_tp_01_004_empty_required_fields(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    click_login(driver)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'required') or contains(., 'Required') or contains(., 'Please')]")
        )
    )

    assert error_message.is_displayed()


def test_tp_01_004_empty_required_fields(driver):
    open_login_page(driver)

    # Click login without entering anything
    click_login(driver)

    # Get input fields
    email_input = driver.find_element(*EMAIL_INPUT)
    password_input = driver.find_element(*PASSWORD_INPUT)

    # Check HTML5 validation
    email_valid = driver.execute_script(
        "return arguments[0].validity.valid;", email_input
    )
    password_valid = driver.execute_script(
        "return arguments[0].validity.valid;", password_input
    )

    assert email_valid is False
    assert password_valid is False


def test_tp_01_005_wrong_credentials(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, VALID_EMAIL)
    type_into(driver, PASSWORD_INPUT, WRONG_PASSWORD)
    click_login(driver)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Wrong Credentials') or contains(., 'Invalid') or contains(., 'invalid') or contains(., 'wrong')]")
        )
    )

    assert error_message.is_displayed()


def test_tp_01_006_unregistered_email(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, UNREGISTERED_EMAIL)
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)
    click_login(driver)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'User not found') or contains(., 'not found') or contains(., 'Invalid') or contains(., 'invalid')]")
        )
    )

    assert error_message.is_displayed()


def test_tp_01_007_forgot_password_navigation(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    wait.until(EC.element_to_be_clickable(FORGOT_PASSWORD_LINK)).click()

    reset_page = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Reset Password') or contains(., 'Forgot Password')]")
        )
    )

    assert reset_page.is_displayed()


def test_tp_01_008_invalid_email_format(driver):
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, INVALID_EMAIL)
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)
    click_login(driver)

    email_input = driver.find_element(*EMAIL_INPUT)
    is_valid = driver.execute_script("return arguments[0].validity.valid;", email_input)

    assert is_valid is False


def test_tp_01_009_password_masking(driver):
    open_login_page(driver)

    password_field = driver.find_element(*PASSWORD_INPUT)
    password_field.send_keys(VALID_PASSWORD)

    assert password_field.get_attribute("type") == "password"


def test_tp_01_010_email_with_leading_trailing_spaces(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, "  admin@gmail.com  ")
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)
    click_login(driver)

    # Expect rejection (error message OR validation fail)
    error_message = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Invalid') or contains(., 'invalid') or contains(., 'Wrong')]")
        )
    )

    assert error_message.is_displayed()


def test_tp_01_011_password_with_spaces(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, VALID_EMAIL)
    type_into(driver, PASSWORD_INPUT, "  admin123  ")
    click_login(driver)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(., 'Wrong') or contains(., 'Invalid')]")
        )
    )

    assert error_message.is_displayed()


def test_tp_01_012_special_character_email(driver):
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, "test@@email.com")
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)
    click_login(driver)

    email_input = driver.find_element(*EMAIL_INPUT)
    is_valid = driver.execute_script(
        "return arguments[0].validity.valid;", email_input
    )

    assert is_valid is False


def test_tp_01_013_multiple_clicks(driver):
    wait = WebDriverWait(driver, 10)
    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, VALID_EMAIL)
    type_into(driver, PASSWORD_INPUT, VALID_PASSWORD)

    for _ in range(5):
        try:
            click_login(driver)
            time.sleep(0.2)
        except:
            break

    # Verify successful login
    wait.until(
        EC.url_contains("dashboard")
    )

    # Ensure only one dashboard/page loaded
    assert "dashboard" in driver.current_url.lower()


def test_tp_01_014_too_many_failed_login_attempts(driver):
    wait = WebDriverWait(driver, 10)

    open_login_page(driver)

    for i in range(6):
        type_into(driver, EMAIL_INPUT, VALID_EMAIL)
        type_into(driver, PASSWORD_INPUT, WRONG_PASSWORD)

        click_login(driver)
        time.sleep(1)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(., 'Too many failed attempts') or contains(., 'try again later')]"
            )
        )
    )

    assert error_message.is_displayed()


def test_tp_01_015_non_admin_user_cannot_access_admin_web(driver):
    wait = WebDriverWait(driver, 10)

    open_login_page(driver)

    type_into(driver, EMAIL_INPUT, "user@gmail.com")
    type_into(driver, PASSWORD_INPUT, "User123*")

    click_login(driver)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(., 'Access denied') or contains(., 'Admin privileges required')]"
            )
        )
    )

    assert error_message.is_displayed()

    # Ensure user stays on login page
    assert driver.current_url.rstrip("/") == BASE_URL.rstrip("/")