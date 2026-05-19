import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://localhost:3000"
ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

EXISTING_DRONE_ID = "DRN-002"


@pytest.fixture
def driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


# Helper functions
def wait_short(driver, seconds=3):
    return WebDriverWait(driver, seconds)


def accept_alert_if_present(driver):
    try:
        alert = wait_short(driver, 3).until(EC.alert_is_present())
        text = alert.text
        alert.accept()
        time.sleep(1)
        return text
    except Exception:
        return None


def click_by_js(driver, element):
    driver.execute_script("arguments[0].click();", element)
    time.sleep(1)


def page_has_text(driver, *texts):
    source = driver.page_source.lower()
    return any(text.lower() in source for text in texts)


def login_as_admin(driver, wait):
    driver.get(BASE_URL)

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
    click_by_js(driver, login_button)

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(.,'Dashboard') or contains(.,'Drone')]")
        )
    )


def go_to_drone_management(driver, wait):
    driver.get(BASE_URL + "/drone-management")

    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(.,'Drone Fleet') or contains(.,'Add Drone') or contains(.,'Search drones')]"
            )
        )
    )


def setup_admin_page(driver):
    wait = WebDriverWait(driver, 20)
    login_as_admin(driver, wait)
    go_to_drone_management(driver, wait)
    accept_alert_if_present(driver)
    return wait


def open_add_drone_modal(driver, wait):
    add_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Add Drone')]")
        )
    )
    click_by_js(driver, add_button)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'Add New Drone') or contains(.,'Drone Name')]")
        )
    )


def get_drone_row(driver, wait, drone_id=EXISTING_DRONE_ID):
    return wait.until(
        EC.presence_of_element_located(
            (By.XPATH, f"//tr[contains(.,'{drone_id}')]")
        )
    )


def cleanup_after_submit(driver):
    accept_alert_if_present(driver)
    time.sleep(2)

    try:
        close_button = driver.find_element(
            By.XPATH,
            "//button[contains(.,'Cancel') or contains(.,'Close') or contains(.,'×')]"
        )
        click_by_js(driver, close_button)
    except:
        pass


def click_view_button(driver, wait, drone_id=EXISTING_DRONE_ID):
    row = get_drone_row(driver, wait, drone_id)
    buttons = row.find_elements(By.XPATH, ".//button")
    click_by_js(driver, buttons[-3])


def click_edit_button(driver, wait, drone_id=EXISTING_DRONE_ID):
    row = get_drone_row(driver, wait, drone_id)
    buttons = row.find_elements(By.XPATH, ".//button")
    click_by_js(driver, buttons[-2])


def click_delete_button(driver, wait, drone_id=EXISTING_DRONE_ID):
    row = get_drone_row(driver, wait, drone_id)
    buttons = row.find_elements(By.XPATH, ".//button")
    click_by_js(driver, buttons[-1])


def fill_textbox_by_label_or_placeholder(driver, label_text, value):
    xpath = (
        f"//input[contains(@placeholder,'{label_text}') "
        f"or @name='{label_text}' "
        f"or contains(@name,'{label_text.lower().replace(' ', '')}')]"
    )

    field = driver.find_element(By.XPATH, xpath)
    field.clear()
    field.send_keys(value)


def submit_add_drone_form(driver, wait):
    submit_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@type='submit' and contains(., 'Add Drone')]"
            )
        )
    )
    driver.execute_script("arguments[0].click();", submit_button)


def select_operational_area(driver, area_name="Kuala Lumpur Central"):
    selects = driver.find_elements(By.XPATH, "//select")

    if not selects:
        raise AssertionError("Operational Area dropdown not found.")

    dropdown = selects[-1]

    try:
        Select(dropdown).select_by_visible_text(area_name)
    except Exception:
        Select(dropdown).select_by_index(1)


def open_add_drone_modal(driver, wait):
    add_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[.//text()[contains(.,'Add Drone')] or contains(.,'Add Drone')]")
        )
    )
    click_by_js(driver, add_button)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//h2[contains(.,'Add New Drone')]")
        )
    )


def fill_add_drone_form(driver, wait, drone_name, serial_number, model, choose_area=True):
    # Drone Name
    name_input = wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//input[contains(@placeholder,'Drone Alpha')]")
        )
    )
    name_input.clear()
    name_input.send_keys(drone_name)

    # Model
    model_input = driver.find_element(
        By.XPATH, "//input[contains(@placeholder,'DJI Phantom')]"
    )
    model_input.clear()
    model_input.send_keys(model)

    # Serial Number
    serial_input = driver.find_element(
        By.XPATH, "//input[contains(@placeholder,'SN123456789')]"
    )
    serial_input.clear()
    serial_input.send_keys(serial_number)

    # Operational Area dropdown
    if choose_area:
        dropdown = driver.find_element(
            By.XPATH,
            "//label[contains(.,'Operational Area')]/following::select[1]"
        )
        select = Select(dropdown)

        try:
            select.select_by_visible_text("Kuala Lumpur Central")
        except Exception:
            # fallback: choose first real location, not "No specific location"
            select.select_by_index(1)


def submit_add_drone_form(driver, wait):
    submit_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[@type='submit' and contains(.,'Add Drone')]"
            )
        )
    )

    driver.execute_script("arguments[0].click();", submit_button)


def search_drone(driver, wait, drone_name):
    search_box = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//input[@placeholder='Search drones...']"
            )
        )
    )

    search_box.clear()
    time.sleep(1)

    search_box.send_keys(drone_name)
    time.sleep(2)


def close_success_alert(driver):
    alert_text = accept_alert_if_present(driver)
    return alert_text


# Tp-05-001
# Verify admin can view registered drones and assigned areas
def test_tp_05_001_view_registered_drones(driver):
    wait = setup_admin_page(driver)

    assert page_has_text(driver, "Drone Fleet")
    assert page_has_text(driver, "Drone ID", "Drone Name", "Model", "Operational Area")
    assert page_has_text(driver, EXISTING_DRONE_ID)


# Tp-05-002
# Verify admin can register/assign/edit drone location
def test_tp_05_002_register_assign_drone_location(driver):
    wait = setup_admin_page(driver)

    drone_name = "Location Test Drone " + str(int(time.time()))[-6:]
    serial = "LOC" + str(int(time.time()))[-6:]

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name=drone_name,
        serial_number=serial,
        model="DJI Mini 3",
        choose_area=True
    )

    submit_add_drone_form(driver, wait)
    accept_alert_if_present(driver)

    # Search by Drone Name, not serial number
    search_drone(driver, wait, drone_name)

    assert drone_name in driver.page_source
    assert "Kuala Lumpur Central" in driver.page_source


# TP-05-003
def test_tp_05_003_add_new_drone_record(driver):
    wait = setup_admin_page(driver)

    drone_name = "Add Test Drone " + str(int(time.time()))[-6:]
    serial = "URN008" + str(int(time.time()))[-4:]

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name=drone_name,
        serial_number=serial,
        model="DJI Mini 3",
        choose_area=True
    )

    submit_add_drone_form(driver, wait)
    accept_alert_if_present(driver)

    search_drone(driver, wait, drone_name)

    assert drone_name in driver.page_source
    assert "DJI Mini 3" in driver.page_source


# TP-05-004
def test_tp_05_004_edit_drone_record(driver):
    wait = setup_admin_page(driver)

    drone_name = "Edit Test Drone " + str(int(time.time()))[-6:]
    serial = "EDIT" + str(int(time.time()))[-6:]

    # Add drone first
    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name=drone_name,
        serial_number=serial,
        model="DJI Mini 3",
        choose_area=True
    )

    submit_add_drone_form(driver, wait)
    accept_alert_if_present(driver)

    # Search added drone
    search_drone(driver, wait, drone_name)
    assert drone_name in driver.page_source

    # Open edit modal
    click_edit_button(driver, wait, drone_name)

    wait.until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(.,'Edit Drone')]")
        )
    )

    # Edit status because edit modal supports status
    status_dropdown = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//label[contains(.,'Status')]/following::select[1]")
        )
    )

    Select(status_dropdown).select_by_visible_text("Maintenance")

    save_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Save Changes')]")
        )
    )
    click_by_js(driver, save_button)

    accept_alert_if_present(driver)

    # Search again and verify updated status
    search_drone(driver, wait, drone_name)

    assert drone_name in driver.page_source
    assert "Maintenance" in driver.page_source


# TP-05-005
def test_tp_05_005_delete_drone_record(driver):
    wait = setup_admin_page(driver)

    drone_name = "Delete Test Drone " + str(int(time.time()))[-6:]
    serial = "DEL" + str(int(time.time()))[-6:]

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name=drone_name,
        serial_number=serial,
        model="DJI Mini 3",
        choose_area=True
    )

    submit_add_drone_form(driver, wait)
    accept_alert_if_present(driver)

    search_drone(driver, wait, drone_name)
    assert drone_name in driver.page_source

    # 1. Click delete icon
    click_delete_button(driver, wait, drone_name)

    # 2. Click Confirm in confirmation dialog
    confirm_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(.,'Confirm')]"
            )
        )
    )
    click_by_js(driver, confirm_button)

    # 3. Click Great! in success message
    great_button = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(.,'Great')]"
            )
        )
    )
    click_by_js(driver, great_button)

    # Verify deleted drone no longer appears
    search_drone(driver, wait, drone_name)

    assert "No drones found" in driver.page_source or drone_name not in driver.page_source


# TP-05-006
def test_tp_05_006_save_drone_updates_successfully(driver):
    wait = setup_admin_page(driver)

    drone_name = "Save Update Drone " + str(int(time.time()))[-6:]
    serial = "SAVE" + str(int(time.time()))[-6:]

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name=drone_name,
        serial_number=serial,
        model="DJI Mini 3",
        choose_area=True
    )

    submit_add_drone_form(driver, wait)
    accept_alert_if_present(driver)

    search_drone(driver, wait, drone_name)
    assert drone_name in driver.page_source

    click_edit_button(driver, wait, drone_name)

    status_dropdown = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//label[contains(.,'Status')]/following::select[1]")
        )
    )

    Select(status_dropdown).select_by_visible_text("Maintenance")

    save_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Save Changes')]")
        )
    )

    click_by_js(driver, save_button)
    accept_alert_if_present(driver)

    search_drone(driver, wait, drone_name)

    assert drone_name in driver.page_source
    assert "Maintenance" in driver.page_source


# TP-05-007
# Verify duplicate serial number is rejected
def test_tp_05_007_duplicate_serial_number(driver):
    wait = setup_admin_page(driver)

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name="Duplicate Drone",
        serial_number="SN",
        model="DJI Mini 3",
        choose_area=True
    )

    time.sleep(2)

    error_message = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(.,'This serial number is already in use') or contains(.,'unique serial number')]"
            )
        )
    )

    add_button = driver.find_element(
        By.XPATH,
        "//h2[contains(.,'Add New Drone')]/ancestor::div[contains(@class,'bg-white')]//button[contains(.,'Add Drone')]"
    )

    assert error_message.is_displayed()
    assert not add_button.is_enabled()


# TP-05-008
# Verify database update failure
# Note: Stop backend/database before running this test
def test_tp_05_008_database_update_failure(driver):
    wait = setup_admin_page(driver)

    open_add_drone_modal(driver, wait)

    fill_add_drone_form(
        driver,
        wait,
        drone_name="DB Failure Drone",
        serial_number="DBFAIL" + str(int(time.time()))[-6:],
        model="DJI Mini 3",
        choose_area=False
    )

    # Stop backend/database manually before submitting
    submit_add_drone_form(driver, wait)

    time.sleep(2)

    error_detected = False

    # Case 1: Browser alert error
    try:
        alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
        alert_text = alert.text
        print("Alert Error:", alert_text)

        if (
            "failed" in alert_text.lower()
            or "error" in alert_text.lower()
            or "network" in alert_text.lower()
            or "server" in alert_text.lower()
        ):
            error_detected = True

        alert.accept()

    except:
        pass

    # Case 2: Bottom-left toast/snackbar error
    if not error_detected:
        try:
            error_popup = wait.until(
                EC.visibility_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(@class,'toast') "
                        "or contains(@class,'snackbar') "
                        "or contains(@class,'error') "
                        "or contains(.,'failed') "
                        "or contains(.,'error') "
                        "or contains(.,'server')]"
                    )
                )
            )

            click_by_js(driver, error_popup)

            time.sleep(1)

            assert (
                "failed" in error_popup.text.lower()
                or "error" in error_popup.text.lower()
                or "server" in error_popup.text.lower()
                or "network" in error_popup.text.lower()
            )

            error_detected = True

        except:
            pass

    assert error_detected, \
        "Expected database/server failure message was not displayed."


# TP-05-009
# Verify GPS permission denied
# Admin web version: checks location permission prompt/message
def test_tp_05_009_gps_permission_denied(driver):
    wait = setup_admin_page(driver)

    open_add_drone_modal(driver, wait)

    alert_text = accept_alert_if_present(driver)

    assert (
        alert_text is not None
        and (
            "gps" in alert_text.lower()
            or "location permission" in alert_text.lower()
            or "allow location" in alert_text.lower()
            or "permission denied" in alert_text.lower()
        )
    )


# TP-05-010
# Verify no drone record found
def test_tp_05_010_no_drone_record_found(driver):
    wait = setup_admin_page(driver)

    search_drone(driver, wait, "Drone Beta")

    no_result = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                "//*[contains(.,'No drones found')]"
            )
        )
    )

    assert no_result.is_displayed()


# TP-05-011
# Drone Name boundary validation
def test_tp_05_011_drone_name_boundary(driver):
    wait = setup_admin_page(driver)

    test_values = [
        ("", False),
        ("D", True),
        ("DroneManagementSystemUnitAlphaTestingVersion001", True),
        ("DroneManagementSystemUnitAlphaTestingVersion0001", False),
    ]

    for drone_name, should_accept in test_values:
        go_to_drone_management(driver, wait)
        open_add_drone_modal(driver, wait)

        serial = "DN" + str(int(time.time()))[-6:]

        fill_add_drone_form(
            driver,
            wait,
            drone_name=drone_name,
            serial_number=serial,
            model="DJI Mini 3",
            choose_area=True
        )

        submit_add_drone_form(driver, wait)

        alert_text = accept_alert_if_present(driver)

        if not should_accept:
            assert alert_text is not None, "Expected validation error, but no error message was shown."
            assert (
            "required" in alert_text.lower()
            or "maximum" in alert_text.lower()
            or "invalid" in alert_text.lower()
            or "exceed" in alert_text.lower()
        )
            continue

        search_drone(driver, wait, drone_name)
        assert page_has_text(driver, drone_name)


# TP-05-012
# Model boundary validation
def test_tp_05_012_drone_model_boundary(driver):
    wait = setup_admin_page(driver)

    test_values = [
        ("", False),
        ("D", True),
        ("DJIPhantomEnterpriseAdvancedSeriesVersionModelX" , True),
        ("DJIPhantomEnterpriseAdvancedSeriesVersionModelXX" , False),

    ]

    for drone_model, should_accept in test_values:
        go_to_drone_management(driver, wait)
        open_add_drone_modal(driver, wait)

        serial = "DM" + str(int(time.time()))[-6:]
        drone_name = "Model Boundary Drone " + serial

        fill_add_drone_form(
            driver,
            wait,
            drone_name=drone_name,
            serial_number=serial,
            model=drone_model,
            choose_area=True
        )

        submit_add_drone_form(driver, wait)

        alert_text = accept_alert_if_present(driver)

        if not should_accept:
            assert alert_text is not None, "Expected validation error, but no error message was shown."
            assert (
                "required" in alert_text.lower()
                or "maximum" in alert_text.lower()
                or "invalid" in alert_text.lower()
                or "exceed" in alert_text.lower()
            )
            continue

        cleanup_after_submit(driver)

        search_drone(driver, wait, drone_name)
        assert page_has_text(driver, drone_name)


def test_tp_05_013_serial_number_boundary(driver):
    wait = setup_admin_page(driver)

    test_values = [
        ("", False),
        ("S1", True),
        ("SN202500000000000001", True),
        ("SN2025000000000000001", False),

    ]

    for serial, should_accept in test_values:
        go_to_drone_management(driver, wait)
        open_add_drone_modal(driver, wait)

        drone_name = "Serial Boundary Drone " + str(int(time.time()))[-6:]

        fill_add_drone_form(
            driver,
            wait,
            drone_name=drone_name,
            serial_number=serial,
            model="DJI Mini 3",
            choose_area=True
        )

        submit_add_drone_form(driver, wait)

        alert_text = accept_alert_if_present(driver)
        if not should_accept:
            assert alert_text is not None, "Expected validation error, but no error message was shown."
            assert (
                "required" in alert_text.lower()
                or "maximum" in alert_text.lower()
                or "invalid" in alert_text.lower()
                or "exceed" in alert_text.lower()
            )
            continue

        cleanup_after_submit(driver)

        search_drone(driver, wait, drone_name)
        assert page_has_text(driver, drone_name)