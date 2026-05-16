from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest
import time

BASE_URL = "http://localhost:3000"


@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    driver.maximize_window()
    yield driver
    driver.quit()


def wait(driver):
    return WebDriverWait(driver, 10)


def go_to_register(driver):
    driver.get(BASE_URL)

    wait(driver).until(
        EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Sign up']"))
    ).click()

    wait(driver).until(
        lambda d: len(d.find_elements(By.TAG_NAME, "input")) >= 6
    )


def clear_and_type(element, value):
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)
    element.send_keys(value)


def body_text(driver):
    return driver.find_element(By.TAG_NAME, "body").text.lower()


def assert_visible_error_contains(driver, expected_keywords, fail_message):
    text = body_text(driver)
    assert any(keyword.lower() in text for keyword in expected_keywords), fail_message


def fill_register_form(
    driver,
    email="",
    name="",
    username="",
    phone="",
    password="",
    confirm="",
    checkbox=False
):
    wait(driver).until(
        lambda d: len(d.find_elements(By.TAG_NAME, "input")) >= 6
    )

    inputs = driver.find_elements(By.TAG_NAME, "input")

    if email != "":
        clear_and_type(inputs[0], email)

    if name != "":
        clear_and_type(inputs[1], name)

    if username != "":
        clear_and_type(inputs[2], username)

    if phone != "":
        clear_and_type(inputs[3], phone)

    if password != "":
        clear_and_type(inputs[4], password)

    if confirm != "":
        clear_and_type(inputs[5], confirm)

    if checkbox:
        try:
            checkbox_el = driver.find_element(By.XPATH, "//input[@type='checkbox']")
            if not checkbox_el.is_selected():
                driver.execute_script("arguments[0].click();", checkbox_el)
        except:
            driver.find_element(By.XPATH, "//*[contains(text(),'By signing up')]").click()


def click_signup_submit(driver):
    wait(driver).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'SIGN UP')]"))
    ).click()


# TC-02-001
# Covers: TCOV-02-001, TCOV-02-002
def test_successful_registration(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        name="Tan",
        username="tan123",
        email="tan123@gmail.com",
        phone="+60123456789",
        password="Pass1234",
        confirm="Pass1234",
        checkbox=True
    )

    click_signup_submit(driver)
    time.sleep(2)

    assert "login" in driver.current_url.lower() or "Login" in driver.page_source


# TC-02-002
# Covers: TCOV-02-003, TCOV-02-029, TCOV-02-031
def test_navigation(driver):
    driver.get(BASE_URL)

    wait(driver).until(
        EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Sign up']"))
    ).click()

    wait(driver).until(
        lambda d: len(d.find_elements(By.TAG_NAME, "input")) >= 6
    )

    assert len(driver.find_elements(By.TAG_NAME, "input")) >= 6

    wait(driver).until(
        EC.element_to_be_clickable((By.XPATH, "//*[normalize-space()='Login']"))
    ).click()

    wait(driver).until(
        lambda d: len(d.find_elements(By.TAG_NAME, "input")) <= 2
    )

    assert "LOGIN" in driver.page_source or len(driver.find_elements(By.TAG_NAME, "input")) <= 2


# TC-02-003
# Covers: TCOV-02-004
def test_duplicate_email(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        email="existing@gmail.com",
        password="Pass1234",
        confirm="Pass1234",
        checkbox=True
    )

    click_signup_submit(driver)
    time.sleep(2)

    assert (
        "already" in driver.page_source.lower()
        or "registered" in driver.page_source.lower()
        or "email" in driver.page_source.lower()
    )


# TC-02-004
# Covers: TCOV-02-005, TCOV-02-023
def test_empty_fields(driver):
    go_to_register(driver)

    click_signup_submit(driver)
    time.sleep(1)

    assert "required" in driver.page_source.lower() or "field" in driver.page_source.lower() or "email" in driver.page_source.lower()

# TC-02-005
# Covers: TCOV-02-006, TCOV-02-032, TCOV-02-033
def test_checkbox_and_policy(driver):
    go_to_register(driver)

    register_tab = driver.current_window_handle
    tabs_before = driver.window_handles

    policy_link = wait(driver).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(),'Terms') or contains(text(),'Privacy')]")
        )
    )
    policy_link.click()

    wait(driver).until(lambda d: len(d.window_handles) > len(tabs_before))

    policy_tab = [tab for tab in driver.window_handles if tab != register_tab][0]
    driver.switch_to.window(policy_tab)

    wait(driver).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Terms') or contains(text(),'Privacy Policy')]")
        )
    )

    assert "terms" in driver.current_url.lower() or "privacy" in driver.page_source.lower()

    driver.close()
    driver.switch_to.window(register_tab)

    wait(driver).until(
        lambda d: len(d.find_elements(By.TAG_NAME, "input")) >= 6
    )

    assert len(driver.find_elements(By.TAG_NAME, "input")) >= 6


# TC-02-006
# Covers: TCOV-02-007, TCOV-02-008, TCOV-02-009, TCOV-02-010, TCOV-02-011, TCOV-02-012
def test_name_username_boundaries(driver):
    boundary_data = [
        ("A", "u"),  
        ("Tan", "tan123"),  
        ("abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz", 
         "user123456789012345678901234567890"),  
    ]

    for name, username in boundary_data:
        go_to_register(driver)

        fill_register_form(
            driver,
            name=name,
            username=username,
            email="boundaryuser@gmail.com",
            phone="+60123456789",
            password="Pass1234",
            confirm="Pass1234",
            checkbox=True
        )

        click_signup_submit(driver)
        time.sleep(1)

        text = body_text(driver)

        # Only check length-related validation
        assert (
            "too long" in text
            or "maximum" in text
            or "must not exceed" in text
            or "minimum" in text
            or "too short" in text
            or "required" in text
            or "success" in text
        ), "FAIL: Boundary length validation not handled correctly."


# TC-02-007
# Covers: TCOV-02-013, TCOV-02-014, TCOV-02-015, TCOV-02-016, TCOV-02-017, TCOV-02-018
def test_password_boundaries(driver):
    very_long_password = (
        "Abc123Abc123Abc123Abc123Abc123Abc123Abc123"
        "Abc123Abc123Abc123Abc123Abc123Abc123"
    )

    go_to_register(driver)

    fill_register_form(
        driver,
        name="Tan",
        username="tan123",
        email="passwordtest@gmail.com",
        phone="+60123456789",
        password=very_long_password,
        confirm=very_long_password,
        checkbox=True
    )

    click_signup_submit(driver)
    time.sleep(1)

    text = body_text(driver)

    assert "at least 8 characters" not in text, (
        "FAIL: Very long password shows wrong prompt: "
        "'password must be at least 8 characters'."
    )

    assert_visible_error_contains(
        driver,
        ["password too long", "maximum", "must not exceed", "less than", "too long"],
        "FAIL: Very long password does not show correct too-long password prompt."
    )


# TC-02-008
# Covers: TCOV-02-020, TCOV-02-021, TCOV-02-022
def test_invalid_format(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        name="123456",
        username="987654",
        email="user@@gmail..com",
        phone="abc123",
        password="Pass1234",
        confirm="Pass1234",
        checkbox=True
    )

    click_signup_submit(driver)
    time.sleep(1)

    assert_visible_error_contains(
        driver,
        [
            "invalid name",
            "invalid username",
            "invalid email",
            "invalid phone",
            "valid phone",
            "only letters",
            "alphanumeric"
        ],
        "FAIL: Invalid name/username/email/phone accepted without correct validation."
    )


# TC-02-009
# Covers: TCOV-02-019, TCOV-02-024, TCOV-02-028
def test_robustness(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        name="Tan",
        username="tan123",
        email=" user@gmail.com ",
        phone="abc123",
        password="Pass1234",
        confirm="Pass1234",
        checkbox=True
    )

    before_visible_text = body_text(driver)

    click_signup_submit(driver)
    time.sleep(2)

    after_visible_text = body_text(driver)

    validation_keywords = [
        "invalid",
        "error",
        "required",
        "valid email",
        "valid phone",
        "phone number",
        "please enter"
    ]

    new_validation_shown = False

    for keyword in validation_keywords:
        if keyword in after_visible_text and keyword not in before_visible_text:
            new_validation_shown = True

    assert new_validation_shown, (
        "FAIL: No visible validation/error message shown after invalid input submission."
    )


# TC-02-010
# Covers: TCOV-02-025, TCOV-02-026, TCOV-02-027, TCOV-02-030
def test_extreme_inputs(driver):
    go_to_register(driver)

    fill_register_form(
        driver,
        name="abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz",
        username="user123456789012345678901234567890",
        email="extreme@gmail.com",
        phone="abc123",
        password=(
            "Abc123Abc123Abc123Abc123Abc123Abc123Abc123"
            "Abc123Abc123Abc123Abc123Abc123Abc123"
        ),
        confirm=(
            "Abc123Abc123Abc123Abc123Abc123Abc123Abc123"
            "Abc123Abc123Abc123Abc123Abc123Abc123"
        ),
        checkbox=True
    )

    click_signup_submit(driver)
    time.sleep(1)

    assert_visible_error_contains(
        driver,
        [
            "name too long",
            "username too long",
            "password too long",
            "invalid phone",
            "maximum",
            "must not exceed",
            "too long"
        ],
        "FAIL: Extreme invalid inputs accepted or wrong validation message shown."
    )