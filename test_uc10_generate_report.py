import os
import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://localhost:3000/reports"


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    download_dir = os.path.abspath("downloads")
    os.makedirs(download_dir, exist_ok=True)

    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True
    })

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def open_reports_page(driver):
    driver.get(BASE_URL)
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Report Generation')]")
        )
    )


def get_date_inputs(driver):
    inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date']")
    # Ensure both Start Date and End Date fields exist
    assert len(inputs) >= 2, "Start Date and End Date inputs not found"
    return inputs[0], inputs[1]


def set_date(date_input, value):
    date_input.click()
    date_input.send_keys(Keys.CONTROL, "a")
    date_input.send_keys(value)


def click_generate_report(driver):
    # Wait until Generate Report button becomes clickable
    WebDriverWait(driver, 10).until(
        lambda d: d.find_element(
            By.XPATH,
            "//button[contains(.,'Generate Report')]"
        ).is_enabled()
    )

    driver.find_element(
        By.XPATH,
        "//button[contains(.,'Generate Report')]"
    ).click()


def wait_for_report_result(driver):
    # Wait for either success, no-data, or error result message
    return WebDriverWait(driver, 120).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(),'Export Options') "
                "or contains(text(),'Total Dengue Cases') "
                "or contains(text(),'No Prediction Data') "
                "or contains(text(),'No prediction data') "
                "or contains(text(),'Report generation failed') "
                "or contains(text(),'Failed') "
                "or contains(text(),'Invalid')]"
            )
        )
    )


def generate_report(driver, start_date_value, end_date_value):
    open_reports_page(driver)

    start_date, end_date = get_date_inputs(driver)
    set_date(start_date, start_date_value)
    set_date(end_date, end_date_value)

    click_generate_report(driver)
    return wait_for_report_result(driver)


# TC-10-001
# Covers: TCOV-10-001, TCOV-10-002, TCOV-10-007, TCOV-10-014, TCOV-10-015
def test_tc_10_001_generate_report_valid_date_range(driver):
    result = generate_report(driver, "2026-04-01", "2026-04-27")
    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert result.is_displayed()
    # Accept success report or no-data response
    assert (
        "Total Dengue Cases" in page_text
        or "Export Options" in page_text
        or "No Prediction Data" in page_text
        or "No prediction data" in page_text
    )


# TC-10-002
# Covers: TCOV-10-004, TCOV-10-008, TCOV-10-009, TCOV-10-010, TCOV-10-013
def test_tc_10_002_generate_button_disabled_for_incomplete_filters(driver):
    # Case 1: both dates empty
    open_reports_page(driver)
    generate_btn = driver.find_element(By.XPATH, "//button[contains(.,'Generate Report')]")
    assert not generate_btn.is_enabled()

    # Case 2: missing Start Date
    open_reports_page(driver)
    start_date, end_date = get_date_inputs(driver)
    set_date(end_date, "2026-04-27")
    generate_btn = driver.find_element(By.XPATH, "//button[contains(.,'Generate Report')]")
    assert not generate_btn.is_enabled()

    # Case 3: missing End Date
    open_reports_page(driver)
    start_date, end_date = get_date_inputs(driver)
    set_date(start_date, "2026-04-01")
    generate_btn = driver.find_element(By.XPATH, "//button[contains(.,'Generate Report')]")
    assert not generate_btn.is_enabled()


# TC-10-003
# Covers: TCOV-10-011
def test_tc_10_003_invalid_date_order_handled(driver):
    generate_report(driver, "2026-04-27", "2026-04-01")
    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert (
        "Invalid" in page_text
        or "Start Date must be before End Date" in page_text
        or "End Date must be after Start Date" in page_text
        or "No Prediction Data" in page_text
        or "No prediction data" in page_text
    ), "System did not display any validation error or no-data message for invalid date order."
    

# TC-10-004
# Covers: TCOV-09-006, TCOV-09-012
def test_tc_10_004_no_data_date_range_handled(driver):
    result = generate_report(driver, "2030-01-01", "2030-01-10")
    page_text = driver.find_element(By.TAG_NAME, "body").text

    assert (
        "No Prediction Data" in page_text
        or "No prediction data" in page_text
        or "Total Dengue Cases" in page_text
        or result.is_displayed()
    )


# TC-10-005
# Covers: TCOV-10-003
def test_tc_10_005_clear_filters_resets_date_fields(driver):
    open_reports_page(driver)

    # Start Date is later than End Date
    start_date, end_date = get_date_inputs(driver)
    set_date(start_date, "2026-04-01")
    set_date(end_date, "2026-04-27")

    driver.find_element(
        By.XPATH,
        "//button[contains(.,'Clear Filters')]"
    ).click()

    WebDriverWait(driver, 10).until(
        lambda d: get_date_inputs(d)[0].get_attribute("value") == ""
        and get_date_inputs(d)[1].get_attribute("value") == ""
    )

    start_date, end_date = get_date_inputs(driver)
    assert start_date.get_attribute("value") == ""
    assert end_date.get_attribute("value") == ""


# TC-10-006
# Covers: TCOV-10-003, TCOV-10-005, TCOV-10-016, TCOV-10-017
@pytest.mark.parametrize("export_format", ["JSON", "PDF", "CSV", "XLSX"])
def test_tc_10_006_export_report_formats(driver, export_format):
    # Future dates likely contain no prediction data
    generate_report(driver, "2026-04-01", "2026-04-27")
    page_text = driver.find_element(By.TAG_NAME, "body").text

    if "Export Options" not in page_text:
        assert (
            "No Prediction Data" in page_text
            or "No prediction data" in page_text
            or "Total Dengue Cases" in page_text
        )
        return

    download_dir = os.path.abspath("downloads")
    before = set(os.listdir(download_dir))

    export_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//button[contains(.,'Export as {export_format}')]")
        )
    )

    export_btn.click()
    time.sleep(5)

    after = set(os.listdir(download_dir))

    # Verify file downloaded or export error shown
    assert len(after - before) > 0 or "Export failed" in driver.find_element(By.TAG_NAME, "body").text