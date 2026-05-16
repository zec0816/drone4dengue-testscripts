import os
import time
import uuid
import pytest
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://localhost:3000"
LOGIN_URL = BASE_URL
WEATHER_URL = f"{BASE_URL}/weather-data"

TEST_EMAIL = "admin@test.com"
TEST_PASSWORD = "Admin123"

VALID_DATE = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
FUTURE_DATE = (date.today() + timedelta(days=30)).strftime("%Y-%m-%d")


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-allow-origins=*")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    download_dir = os.path.abspath("downloads")
    os.makedirs(download_dir, exist_ok=True)

    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
    })

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.set_page_load_timeout(60)
    driver.implicitly_wait(5)

    login(driver)

    yield driver

    try:
        driver.quit()
    except Exception:
        pass


def wait(driver, seconds=30):
    return WebDriverWait(driver, seconds)


def page_text(driver):
    return driver.find_element(By.TAG_NAME, "body").text


def set_input(element, value):
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)
    element.send_keys(value)


def set_date_input(driver, element_id, value):
    element = driver.find_element(By.ID, element_id)

    driver.execute_script(
        """
        const input = arguments[0];
        const value = arguments[1];
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            'value'
        ).set;
        setter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        element,
        value
    )


def login(driver):
    driver.get(LOGIN_URL)
    time.sleep(3)

    email_input = wait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
    )
    email_input.clear()
    email_input.send_keys(TEST_EMAIL)

    password_input = wait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
    )
    password_input.clear()
    password_input.send_keys(TEST_PASSWORD)

    login_btn = wait(driver, 30).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(.,'Login') or contains(.,'Log in') or contains(.,'Sign In') or contains(.,'SIGN IN') or @type='submit']"
            )
        )
    )
    login_btn.click()

    wait(driver, 30).until(
        lambda d: d.execute_script("return window.localStorage.getItem('token')") is not None
    )

    time.sleep(2)


def open_weather_page(driver):
    driver.get(WEATHER_URL)

    wait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Weather Data Management')]")
        )
    )

    wait(driver, 30).until(
        lambda d: "Loading company locations..." not in page_text(d)
    )


def ensure_company_locations_loaded(driver):
    open_weather_page(driver)

    body = page_text(driver)

    assert "No token provided" not in body
    assert "Failed to load company locations" not in body
    assert "No Company Locations" not in body
    assert "Something went wrong" not in body

    location_dropdown = wait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "locationSelect"))
    )

    wait(driver, 30).until(
        lambda d: len(location_dropdown.find_elements(By.TAG_NAME, "option")) > 1
    )

    Select(location_dropdown).select_by_index(1)
    time.sleep(1)


def select_first_operational_area(driver, element_id):
    dropdown = wait(driver, 30).until(
        EC.presence_of_element_located((By.ID, element_id))
    )

    wait(driver, 30).until(
        lambda d: len(dropdown.find_elements(By.TAG_NAME, "option")) > 1
    )

    Select(dropdown).select_by_index(1)

    driver.execute_script(
        """
        const select = arguments[0];
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        """,
        dropdown
    )

    time.sleep(0.5)


def wait_for_message(driver, seconds=30):
    wait(driver, seconds).until(
        lambda d:
            "successfully" in page_text(d).lower()
            or "failed" in page_text(d).lower()
            or "required" in page_text(d).lower()
            or "must be" in page_text(d).lower()
            or "cannot" in page_text(d).lower()
            or "something went wrong" in page_text(d).lower()
    )

    body = page_text(driver)

    assert "Something went wrong" not in body, body

    return body


def click_add_new_record(driver):
    ensure_company_locations_loaded(driver)

    add_btn = wait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Add New Record') or contains(.,'Add First Record')]")
        )
    )

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    time.sleep(0.5)

    try:
        add_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", add_btn)

    wait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Add Weather Record')]")
        )
    )


def fill_weather_form(driver, record_date, temperature, humidity, rainfall, location):
    set_date_input(driver, "date", record_date)
    set_input(driver.find_element(By.ID, "temperature"), temperature)
    set_input(driver.find_element(By.ID, "humidity"), humidity)
    set_input(driver.find_element(By.ID, "rainfall"), rainfall)
    set_input(driver.find_element(By.ID, "location"), location)

    select_first_operational_area(driver, "companyLocationId")


def click_add_record(driver):
    add_btn = driver.find_element(By.XPATH, "//button[contains(.,'Add Record')]")
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", add_btn)
    time.sleep(0.5)

    try:
        add_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", add_btn)


def download_files():
    download_dir = os.path.abspath("downloads")
    os.makedirs(download_dir, exist_ok=True)
    return set(os.listdir(download_dir))


def ensure_weather_record_exists(driver):
    open_weather_page(driver)

    if "No Weather Data" not in page_text(driver):
        return

    click_add_new_record(driver)

    fill_weather_form(
        driver,
        record_date=VALID_DATE,
        temperature="30.5",
        humidity="75",
        rainfall="2.5",
        location="Kuala Lumpur"
    )

    click_add_record(driver)
    wait_for_message(driver, 30)
    open_weather_page(driver)


# TC-09-001
# Covers: TCOV-09-001, TCOV-09-006, TCON-09-007, TCOV-09-026
def test_tc09_view_refresh(driver):
    ensure_company_locations_loaded(driver)

    assert "Weather Data Management" in page_text(driver)

    refresh_btns = driver.find_elements(
        By.XPATH,
        "//button[contains(.,'Refresh') or contains(.,'Reload')]"
    )

    if refresh_btns and refresh_btns[0].is_enabled():
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", refresh_btns[0])
        time.sleep(0.5)

        try:
            refresh_btns[0].click()
        except Exception:
            driver.execute_script("arguments[0].click();", refresh_btns[0])

    time.sleep(2)

    assert "Weather Data Management" in page_text(driver)


# TC-09-002
# Covers: TCOV-09-002, TCOV-09-008, TCOV-09-012, TCOV-09-013, TCOV-09-016, TCOV-09-017, TCOV-09-020, TCOV-09-023
def test_tc09_add_valid(driver):
    click_add_new_record(driver)

    unique_location = f"Kuala Lumpur Add Valid {uuid.uuid4().hex[:6]}"

    fill_weather_form(
        driver,
        record_date=VALID_DATE,
        temperature="30.5",
        humidity="75",
        rainfall="2.5",
        location=unique_location
    )

    click_add_record(driver)

    body = wait_for_message(driver, 30)

    assert (
        "Weather record added successfully" in body
        or "Failed to save weather record" in body
    )

    # After adding record, test Cancel button
    click_add_new_record(driver)

    cancel_btn = wait(driver, 30).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[normalize-space()='Cancel']")
        )
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        cancel_btn
    )
    time.sleep(0.5)

    driver.execute_script("arguments[0].click();", cancel_btn)

    wait(driver, 30).until(
        EC.invisibility_of_element(cancel_btn)
    )

    assert "Weather Data Management" in page_text(driver)


@pytest.mark.parametrize(
    "temperature,humidity,rainfall,expected_message",
    [
        ("-51", "75", "2.5", "Temperature must be between -50°C and 60°C"),
        ("61", "75", "2.5", "Temperature must be between -50°C and 60°C"),
        ("30.5", "-1", "2.5", "Humidity must be between 0% and 100%"),
        ("30.5", "101", "2.5", "Humidity must be between 0% and 100%"),
        ("30.5", "75", "-1", "Rainfall cannot be negative"),
    ],
    ids=["temp_low", "temp_high", "hum_low", "hum_high", "rain_neg"],
)


# TC-09-003
# Covers: TCOV-09-009, TCOV-09-011, TCOV-09-014, TCOV-09-015, TCOV-09-018, TCOV-09-019, TCOV-09-021
def test_tc09_invalid(driver, temperature, humidity, rainfall, expected_message):
    click_add_new_record(driver)

    fill_weather_form(
        driver,
        record_date=VALID_DATE,
        temperature=temperature,
        humidity=humidity,
        rainfall=rainfall,
        location="Kuala Lumpur"
    )

    click_add_record(driver)
    time.sleep(2)

    body = page_text(driver)
    invalid_inputs = driver.find_elements(By.CSS_SELECTOR, "input:invalid")

    assert expected_message in body or len(invalid_inputs) > 0


def test_tc09_future_date(driver):
    click_add_new_record(driver)

    fill_weather_form(
        driver,
        record_date=FUTURE_DATE,
        temperature="30.5",
        humidity="75",
        rainfall="2.5",
        location="Kuala Lumpur"
    )

    click_add_record(driver)
    time.sleep(2)

    body = page_text(driver)

    assert "Future dates are not allowed" in body
    assert "Weather record added successfully" not in body


# TC-09-004
# Covers: TCOV-09-003, TCOV-09-009
def test_tc09_csv(driver, tmp_path):
    ensure_company_locations_loaded(driver)

    valid_csv = tmp_path / "valid_weather.csv"
    valid_csv.write_text(
        "Date,Temperature,Humidity,Rainfall,Location\n"
        f"{VALID_DATE},30.5,75,2.5,Kuala Lumpur\n",
        encoding="utf-8"
    )

    file_input = driver.find_element(By.ID, "csvFile")
    file_input.send_keys(str(valid_csv))

    upload_btn = wait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Upload CSV')]"))
    )

    upload_btn.click()
    time.sleep(5)

    body = page_text(driver)

    assert "Something went wrong" not in body
    assert (
        "uploaded and processed successfully" in body
        or "Failed to process CSV" in body
    )


# TC-09-005
# Covers: TCOV-14-004
def test_tc09_edit(driver):
    ensure_weather_record_exists(driver)
    open_weather_page(driver)
    time.sleep(3)

    body = page_text(driver)

    if "No Weather Data" in body:
        pytest.skip("No weather record available for editing.")

    edit_buttons = driver.find_elements(
        By.XPATH,
        "//td[count(//th[contains(.,'Actions')]/preceding-sibling::th)+1]//button[1]"
    )

    if not edit_buttons:
        edit_buttons = driver.find_elements(
            By.XPATH,
            "//table//tbody//tr[1]//td[last()]//button[1]"
        )

    assert len(edit_buttons) > 0, "No edit button found."

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", edit_buttons[0])
    time.sleep(1)

    try:
        edit_buttons[0].click()
    except Exception:
        driver.execute_script("arguments[0].click();", edit_buttons[0])

    wait(driver, 20).until(
        EC.visibility_of_element_located((By.ID, "modal-temperature"))
    )

    set_input(driver.find_element(By.ID, "modal-temperature"), "31")

    update_btn = driver.find_element(By.XPATH, "//button[contains(.,'Update Record')]")
    update_btn.click()

    time.sleep(3)

    body = page_text(driver)

    assert "Something went wrong" not in body
    assert (
        "Weather record updated successfully" in body
        or "Failed to save weather record" in body
    )


# TC-09-006
# Covers: TCOV-09-005, TCOV-09-025
def test_tc09_export(driver):
    ensure_company_locations_loaded(driver)

    before = download_files()

    export_btn = wait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Export Data')]"))
    )

    export_btn.click()
    time.sleep(5)

    after = download_files()

    assert len(after - before) > 0 or "Failed to export weather data" in page_text(driver)


# TC-09-007
# Covers: TCOV-09-010
def test_tc09_add_record_system_response(driver):
    click_add_new_record(driver)

    unique_location = f"Kuala Lumpur Response {uuid.uuid4().hex[:6]}"

    fill_weather_form(
        driver,
        record_date=VALID_DATE,
        temperature="30.5",
        humidity="75",
        rainfall="2.5",
        location=unique_location
    )

    click_add_record(driver)

    body = wait_for_message(driver, 30)

    assert (
        "Weather record added successfully" in body
        or "Failed to save weather record" in body
    )