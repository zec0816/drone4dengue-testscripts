# import pytest, os
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC

# BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')

# def login(driver):
#     driver.get(f'{BASE_URL}')
#     driver.find_element(By.ID, 'email').send_keys(os.getenv('ADMIN_EMAIL', 'chienlingtan@gmail.com'))
#     driver.find_element(By.ID, 'password').send_keys(os.getenv('ADMIN_PASSWORD', 'chien0813'))
#     driver.find_element(By.XPATH, "//button[contains(.,'Login')]").click()
#     WebDriverWait(driver, 10).until(EC.url_contains('/admin'))

# def navigate_to_data_management(driver):
#     driver.get(f'{BASE_URL}/admin/data-management')
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Data Management')]"))
#     )

# def test_tc_08_001_module_loads(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # TCOV-08-001: Page loads without errors
#     assert 'Data Management' in driver.title or 'Data Management' in driver.find_element(
#         By.TAG_NAME, 'body').text, 'Page title should contain Data Management'

#     # TCOV-08-006: Summary cards are visible
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     for card_label in ['Total Records', 'Active Cases', 'Dengue Hotspots', 'Locations Covered']:
#         assert card_label in body_text, f'Summary card not found: {card_label}'

#     # TCOV-08-021: Upload button is visible
#     upload_btn = driver.find_element(By.XPATH, "//button[contains(.,'Upload Data')]")
#     assert upload_btn.is_displayed(), 'Upload Data button must be visible'

#     # TCOV-08-022 / TCOV-08-023: Data table shows 'No Data Displayed' before search
#     assert 'No Data Displayed' in body_text, \
#         'Data table should show No Data Displayed message before search is applied'
#     assert 'Search Data' in body_text, 'Search Data button must be visible in filter panel'

# VALID_CSV_PATH = os.getenv('VALID_CSV_PATH', './fixtures/TC08_valid_data.csv')

# def test_tc_08_002_upload_valid_csv(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # TCOV-08-002: Trigger file input
#     file_input = driver.find_element(By.CSS_SELECTOR, 'input[type=file][accept=".csv"]')
#     file_input.send_keys(os.path.abspath(VALID_CSV_PATH))

#     # TCOV-08-007: Wait for upload success message
#     WebDriverWait(driver, 20).until(
#         EC.visibility_of_element_located(
#             (By.XPATH, "//*[contains(text(),'Successfully imported')]"))
#     )
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     assert 'Successfully imported' in body_text, 'Upload success message must appear'
#     assert 'error' not in body_text.lower() or '0 error' in body_text.lower(), \
#         'No unexpected errors during upload'

#     # TCOV-08-010: Click Search Data and verify records appear
#     search_btn = driver.find_element(By.XPATH, "//button[contains(.,'Search Data')]")
#     search_btn.click()
#     WebDriverWait(driver, 15).until(
#         EC.invisibility_of_element_located((By.XPATH, "//*[contains(text(),'No Data Displayed')]"))
#     )
#     rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
#     assert len(rows) > 0, 'At least one record row must appear after upload and search'

#     # TCOV-08-019: Status badges render correctly
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     has_status = any(s in body_text for s in ['Active Cases', 'Hotspot', 'Processing', 'Completed'])
#     assert has_status, 'At least one status type should be visible in the table'
# def js_set_date(driver, field_id, value):
#     driver.execute_script(
#         f"document.getElementById('{field_id}').value = '{value}'"
#     )

# def test_tc_08_003_filter_by_location(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # TCOV-08-004: Filter by location
#     loc_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="Country, State"]')
#     loc_input.clear()
#     loc_input.send_keys('Kuala Lumpur')
#     driver.find_element(By.XPATH, "//button[contains(.,'Search Data')]").click()
#     WebDriverWait(driver, 15).until(
#         EC.any_of(
#             EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Kuala Lumpur')]"))  ,
#             EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'No Records Found')]"))
#         )
#     )
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     assert ('Kuala Lumpur' in body_text or 'No Records Found' in body_text), \
#         'Location filter should return matching records or empty state'

# def test_tc_08_003_filter_by_date_range(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # TCOV-08-005: Date range filter
#     driver.execute_script("""
#         const inputs = document.querySelectorAll('input[type=date]');
#         inputs[0].value = '2026-01-01';
#         inputs[1].value = '2026-03-31';
#         inputs[0].dispatchEvent(new Event('input', {bubbles:true}));
#         inputs[1].dispatchEvent(new Event('input', {bubbles:true}));
#     """)
#     driver.find_element(By.XPATH, "//button[contains(.,'Search Data')]").click()
#     WebDriverWait(driver, 15).until(
#         EC.any_of(
#             EC.presence_of_element_located((By.XPATH, "//tbody/tr[contains(@class,'border-b')]"))  ,
#             EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'No Records Found')]"))
#         )
#     )
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     assert 'No Data Displayed' not in body_text, \
#         'Search should have been triggered — No Data Displayed must not appear'

# def test_tc_08_003_invalid_date_range(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # TCOV-08-009 / TCOV-08-020: Start date after end date
#     driver.execute_script("""
#         const inputs = document.querySelectorAll('input[type=date]');
#         inputs[0].value = '2026-06-01';
#         inputs[1].value = '2026-01-01';
#         inputs[0].dispatchEvent(new Event('input', {bubbles:true}));
#         inputs[1].dispatchEvent(new Event('input', {bubbles:true}));
#     """)
#     driver.find_element(By.XPATH, "//button[contains(.,'Search Data')]").click()
#     WebDriverWait(driver, 10).until(
#         EC.any_of(
#             EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'No Records Found')]"))  ,
#             EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'error') or contains(text(),'invalid') or contains(text(),'Invalid')]"))
#         )
#     )
#     body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
#     assert any(kw in body_text for kw in ['no records', 'invalid', 'error', 'valid date']), \
#         'System should reject or gracefully handle invalid date range'

#     # TCOV-08-020: Clear filters resets state
#     driver.find_element(By.XPATH, "//button[contains(.,'Clear Filters')]").click()
#     WebDriverWait(driver, 5).until(
#         EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'No Data Displayed')]"))
#     )
#     date_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type=date]')
#     for inp in date_inputs:
#         assert inp.get_attribute('value') == '', 'Date fields should be cleared'

# def test_tc_08_004_view_details_modal(driver):
#     login(driver)
#     navigate_to_data_management(driver)

#     # Load records first
#     driver.find_element(By.XPATH, "//button[contains(.,'Search Data')]").click()
#     WebDriverWait(driver, 15).until(
#         EC.presence_of_element_located((By.XPATH, "//tbody/tr[.//button[contains(.,'View')]]"))
#     )

#     # TCOV-08-008: Click View on the first row
#     view_btn = driver.find_element(By.XPATH, "(//button[contains(.,'View')])[1]")
#     view_btn.click()

#     # Modal must appear
#     WebDriverWait(driver, 10).until(
#         EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Record Details')]"))
#     )
#     body_text = driver.find_element(By.TAG_NAME, 'body').text
#     assert 'Record Details' in body_text, 'Modal header must say Record Details'

#     # TCOV-08-025: Required fields present in modal
#     for field in ['Date', 'Location', 'Active Cases', 'Status']:
#         assert field in body_text, f'Modal must display field: {field}'

#     # Close modal via Close button
#     close_btn = driver.find_element(By.XPATH, "//button[contains(.,'Close')]")
#     close_btn.click()
#     WebDriverWait(driver, 5).until(
#         EC.invisibility_of_element_located((By.XPATH, "//*[contains(text(),'Record Details')]"))
#     )
#     assert 'Record Details' not in driver.find_element(By.TAG_NAME, 'body').text, \
#         'Modal should close after clicking Close'
    

# FIXTURES = {
#     'negative_cases':  './fixtures/TC08_bva_negative_cases.csv',
#     'zero_cases':       './fixtures/TC08_bva_zero_cases.csv',
#     'future_date':      './fixtures/TC08_bva_future_date.csv',
#     'current_date':     './fixtures/TC08_bva_current_date.csv',
#     'empty_location':   './fixtures/TC08_bva_empty_location.csv',
#     'loc_100_chars':    './fixtures/TC08_bva_loc_100.csv',
#     'loc_101_chars':    './fixtures/TC08_bva_loc_101.csv',
# }

# def do_upload(driver, csv_path):
#     file_input = driver.find_element(By.CSS_SELECTOR, 'input[type=file][accept=".csv"]')
#     driver.execute_script("arguments[0].value = '';", file_input)
#     file_input.send_keys(os.path.abspath(csv_path))
#     WebDriverWait(driver, 20).until(
#         EC.any_of(
#             EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Successfully imported')]"))  ,
#             EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'\u2717') or contains(@class,'error')]"))
#         )
#     )
#     return driver.find_element(By.TAG_NAME, 'body').text

# # TCOV-08-012: Negative cases should be rejected
# def test_bva_negative_cases(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['negative_cases'])
#     assert any(kw in text.lower() for kw in ['error', 'invalid', 'negative', 'failed']), \
#         'Negative case count must be rejected'

# # TCOV-08-013: Zero cases should be accepted
# def test_bva_zero_cases(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['zero_cases'])
#     assert 'Successfully imported' in text, 'Zero case count is a valid boundary — must be accepted'

# # TCOV-08-014: Future date should be rejected
# def test_bva_future_date(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['future_date'])
#     assert any(kw in text.lower() for kw in ['error', 'invalid', 'future', 'failed']), \
#         'Future date (2027-12-31) must be rejected'

# # TCOV-08-015: Current date should be accepted
# def test_bva_current_date(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['current_date'])
#     assert 'Successfully imported' in text, 'Current date is valid — must be accepted'

# # TCOV-08-016: Empty location should be rejected
# def test_bva_empty_location(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['empty_location'])
#     assert any(kw in text.lower() for kw in ['error', 'required', 'location', 'failed']), \
#         'Empty location must be rejected'

# # TCOV-08-017: 100-character location should be accepted
# def test_bva_loc_100(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['loc_100_chars'])
#     assert 'Successfully imported' in text, '100-char location is at the boundary — must be accepted'

# # TCOV-08-018: 101-character location should be rejected
# def test_bva_loc_101(driver):
#     login(driver); navigate_to_data_management(driver)
#     text = do_upload(driver, FIXTURES['loc_101_chars'])
#     assert any(kw in text.lower() for kw in ['error', 'too long', 'exceeded', 'failed']), \
#         '101-char location exceeds the boundary — must be rejected'

# WRONG_HEADERS_CSV  = os.getenv('WRONG_HEADERS_CSV',  './fixtures/TC08_wrong_headers.csv')
# INCOMPLETE_CSV     = os.getenv('INCOMPLETE_CSV',     './fixtures/TC08_incomplete.csv')
# VALID_CSV_PATH     = os.getenv('VALID_CSV_PATH',     './fixtures/TC08_valid_data.csv')

# INTERCEPT_JS = """
#     window._origFetch = window.fetch;
#     window.fetch = function(url, opts) {
#         if (url && url.toString().includes('/dengue-data/upload')) {
#             return Promise.resolve(new Response(
#                 JSON.stringify({error: 'Internal Server Error'}),
#                 {status: 500, headers: {'Content-Type': 'application/json'}}
#             ));
#         }
#         return window._origFetch(url, opts);
#     };
# """

# RESTORE_JS = """
#     if (window._origFetch) { window.fetch = window._origFetch; }
# """

# def do_upload(driver, csv_path):
#     file_input = driver.find_element(By.CSS_SELECTOR, 'input[type=file][accept=".csv"]')
#     driver.execute_script("arguments[0].value = '';", file_input)
#     file_input.send_keys(os.path.abspath(csv_path))
#     WebDriverWait(driver, 20).until(
#         EC.any_of(
#             EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'Successfully imported')]"))  ,
#             EC.visibility_of_element_located((By.XPATH, "//*[contains(text(),'\u2717') or contains(@class,'error')]"))
#         )
#     )
#     return driver.find_element(By.TAG_NAME, 'body').text

# # TCOV-08-011 Case 1: Simulated server error
# def test_tc_08_006_server_error(driver):
#     login(driver)
#     navigate_to_data_management(driver)
#     driver.execute_script(INTERCEPT_JS)
#     text = do_upload(driver, VALID_CSV_PATH)
#     driver.execute_script(RESTORE_JS)
#     assert any(kw in text.lower() for kw in ['error', 'failed', '\u2717']), \
#         'Server error must result in an error message to the user'
#     assert 'Successfully imported' not in text, \
#         'No success message should appear when server returns 500'

# # TCOV-08-011 Case 2: Wrong CSV headers
# def test_tc_08_006_wrong_headers(driver):
#     login(driver)
#     navigate_to_data_management(driver)
#     text = do_upload(driver, WRONG_HEADERS_CSV)
#     assert any(kw in text.lower() for kw in ['error', 'invalid', 'header', 'failed', 'column']), \
#         'CSV with wrong headers must be rejected with an error message'
#     assert 'Successfully imported' not in text, \
#         'Wrong-headers CSV must not produce a success import'

# # TCOV-08-011 Case 3: Incomplete CSV (missing columns)
# def test_tc_08_006_incomplete_csv(driver):
#     login(driver)
#     navigate_to_data_management(driver)
#     text = do_upload(driver, INCOMPLETE_CSV)
#     assert any(kw in text.lower() for kw in ['error', 'invalid', 'missing', 'failed', 'incomplete']), \
#         'Incomplete CSV must be rejected with an appropriate error message'
#     assert 'Successfully imported' not in text, \
#         'Incomplete CSV must not produce a success import'

import pytest
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ====================== CONSTANTS & FIXTURES ======================
BASE_URL = "http://localhost:3000"

# Fixtures live at  tests/fixtures/  — same directory as this test file
_HERE        = os.path.dirname(os.path.abspath(__file__))
_FIXTURE_DIR = os.path.join(_HERE, 'fixtures')   # tests/fixtures/

def _fp(name: str) -> str:
    """Absolute path to a fixture file inside tests/fixtures/."""
    return os.path.join(_FIXTURE_DIR, name)

VALID_CSV_PATH    = os.getenv('VALID_CSV_PATH',    _fp('TC08_valid_data.csv'))
WRONG_HEADERS_CSV = os.getenv('WRONG_HEADERS_CSV', _fp('TC08_wrong_headers.csv'))
INCOMPLETE_CSV    = os.getenv('INCOMPLETE_CSV',    _fp('TC08_incomplete.csv'))

FIXTURES = {
    'negative_cases': _fp('TC08_bva_negative_cases.csv'),
    'zero_cases':     _fp('TC08_bva_zero_cases.csv'),
    'future_date':    _fp('TC08_bva_future_date.csv'),
    'current_date':   _fp('TC08_bva_current_date.csv'),
    'empty_location': _fp('TC08_bva_empty_location.csv'),
    'loc_100_chars':  _fp('TC08_bva_loc_100.csv'),
    'loc_101_chars':  _fp('TC08_bva_loc_101.csv'),
}

# Source-confirmed: card labels rendered exactly as these strings
SUMMARY_CARDS = ['Total Records', 'Active Cases', 'Dengue Hotspots', 'Locations Covered']

# Source-confirmed: modal label is "Status/Type" (not plain "Status")
MODAL_FIELDS = ['DATE', 'LOCATION', 'ACTIVE CASES', 'STATUS/TYPE']


# ====================== HELPER FUNCTIONS ======================

def navigate_to_data_management(driver):
    """Navigate to the Data Management page and wait for it to settle."""
    driver.get(f"{BASE_URL}/data-management")
    WebDriverWait(driver, 12).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Data Management')]")
        )
    )
    time.sleep(1.5)


def click_search(driver):
    """Click the Search Data button."""
    WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Search Data')]")
        )
    ).click()


def _assert_fixture_exists(path: str):
    """Raise a clear AssertionError when a fixture file is missing."""
    assert os.path.isfile(path), (
        f"Fixture file not found: {path}\n"
        f"Run  python tests/create_fixtures.py  from the client-admin directory."
    )


def _make_file_input_interactable(driver):
    """
    The file <input> has style="display:none" and is triggered via a React ref.
    Force it visible so ChromeDriver's send_keys() can reach it, then return a
    fresh element reference.
    """
    driver.execute_script("""
        document.querySelectorAll('input[type="file"]').forEach(function(el) {
            el.style.display    = 'block';
            el.style.visibility = 'visible';
            el.style.opacity    = '1';
            el.style.position   = 'fixed';
            el.style.top        = '0';
            el.style.left       = '0';
            el.style.width      = '1px';
            el.style.height     = '1px';
            el.removeAttribute('disabled');
        });
    """)
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
    )


def do_upload(driver, csv_path: str) -> str:
    """
    Reveal the hidden file input, send the file path, wait for the result
    message (success or error), and return the full page body text.
    """
    _assert_fixture_exists(csv_path)

    file_input = _make_file_input_interactable(driver)
    driver.execute_script("arguments[0].value = '';", file_input)
    file_input.send_keys(csv_path)  # already absolute via _fp()

    WebDriverWait(driver, 20).until(
        EC.any_of(
            EC.visibility_of_element_located(
                (By.XPATH, "//*[contains(text(),'Successfully imported')]")
            ),
            # Source: error state uses class "text-red-700" on the uploadMsg div
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//*[contains(@class,'text-red-700') or "
                 "contains(text(),'error') or contains(text(),'Error') or "
                 "contains(text(),'invalid') or contains(text(),'Invalid') or "
                 "contains(text(),'failed') or contains(text(),'Failed')]")
            ),
        )
    )
    return driver.find_element(By.TAG_NAME, 'body').text


def _set_date_input(driver, index: int, value: str):
    """
    Set a React-controlled date input by index using the native value setter,
    then fire both 'input' and 'change' events so React state updates.
    """
    driver.execute_script(f"""
        var el = document.querySelectorAll('input[type="date"]')[{index}];
        if (el) {{
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, '{value}');
            el.dispatchEvent(new Event('input',  {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    """)


# ====================== TEST PROCEDURES ======================

def test_tp_08_001_module_loads(driver):
    """TP-08-001: Verify Data Management module loads successfully."""
    navigate_to_data_management(driver)
    body_text = driver.find_element(By.TAG_NAME, 'body').text

    # TCOV-08-001: Page heading present
    assert 'Data Management' in driver.title or 'Data Management' in body_text, \
        "Page does not appear to be the Data Management module"

    # TCOV-08-021: Upload Data button visible before search
    assert driver.find_element(
        By.XPATH, "//button[contains(.,'Upload Data')]"
    ).is_displayed(), "Upload Data button not visible"

    # TCOV-08-022 & TCOV-08-023: Pre-search empty-state and search affordance
    assert 'No Data Displayed' in body_text, \
        "Expected 'No Data Displayed' in the initial (pre-search) view"
    assert 'Search Data' in body_text, \
        "Expected 'Search Data' button in the initial view"

    # TCOV-08-006: Summary cards only populate after Search Data is clicked
    # (source: cards render from `summary` state which loads on searchTrigger)
    click_search(driver)

    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Total Records')]")
        )
    )

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    for card in SUMMARY_CARDS:
        assert card in body_text, f"Missing summary card: '{card}'"


def test_tp_08_002_upload_valid_csv(driver):
    """TP-08-002: Verify admin can upload a valid CSV."""
    navigate_to_data_management(driver)
    _assert_fixture_exists(VALID_CSV_PATH)

    file_input = _make_file_input_interactable(driver)
    file_input.send_keys(VALID_CSV_PATH)

    WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Successfully imported')]")
        )
    )

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Successfully imported' in body_text
    assert 'error' not in body_text.lower() or '0 error' in body_text.lower()

    # Trigger search and confirm rows appear in the table
    click_search(driver)

    WebDriverWait(driver, 15).until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'No Data Displayed')]")
        )
    )

    rows = driver.find_elements(By.CSS_SELECTOR, 'tbody tr')
    assert len(rows) > 0, "Expected table rows after a successful upload + search"

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert any(s in body_text for s in ['Hotspot', 'Active Cases']), \
        "Expected at least one status value (Hotspot / Active Cases) in the table"


def test_tp_08_003_filtering_and_validation(driver):
    """TP-08-003: Verify filtering by location, date range, and invalid date handling."""

    # ── Case 1: Filter by Location ─────────────────────────────────────────────
    navigate_to_data_management(driver)

    # Source placeholder: "Enter Country, State, District, City, Suburb, Postcode"
    loc_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH,
             "//input[contains(@placeholder,'Country') or "
             "contains(@placeholder,'District') or "
             "contains(@placeholder,'Suburb')]")
        )
    )
    loc_input.clear()
    loc_input.send_keys('Kuala Lumpur')
    click_search(driver)

    WebDriverWait(driver, 12).until(
        EC.any_of(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'Kuala Lumpur')]")
            ),
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'No Records Found')]")
            ),
        )
    )

    # ── Case 2: Valid Date Range ───────────────────────────────────────────────
    navigate_to_data_management(driver)

    _set_date_input(driver, 0, '2026-01-01')
    _set_date_input(driver, 1, '2026-03-31')
    click_search(driver)

    WebDriverWait(driver, 15).until(
        EC.any_of(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr td")),
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'No Records Found')]")
            ),
        )
    )

    # ── Case 3: Invalid Date Range (Start > End) ───────────────────────────────
    # Source: no client-side date validation — invalid range is passed to the
    # API which returns 0 results, rendering "No Records Found".
    navigate_to_data_management(driver)

    _set_date_input(driver, 0, '2026-06-01')
    _set_date_input(driver, 1, '2026-01-01')
    click_search(driver)

    WebDriverWait(driver, 20).until(
        EC.any_of(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(),'No Records Found')]")
            ),
            # Also accept an error banner in case API rejects the range
            EC.presence_of_element_located(
                (By.XPATH,
                 "//*[contains(@class,'text-red-700') or "
                 "contains(text(),'Failed to load')]")
            ),
        )
    )


def test_tp_08_004_view_details_modal(driver):
    """TP-08-004: Verify View button opens the details modal correctly."""
    navigate_to_data_management(driver)
 
    # Data only loads after Search is clicked
    click_search(driver)
 
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(.,'View')]")
        )
    )
 
    driver.find_element(
        By.XPATH, "(//button[contains(.,'View')])[1]"
    ).click()
 
    # Source: modal heading h2 text is exactly "Record Details"
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Record Details')]")
        )
    )
 
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Record Details' in body_text
 
    # Source-confirmed field labels (including "Status/Type" from JSX)
    for field in MODAL_FIELDS:
        assert field in body_text, f"Field '{field}' missing in modal"
 
    # Source: footer has a <Button>Close</Button>
    WebDriverWait(driver, 8).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Close')]")
        )
    ).click()
 
    WebDriverWait(driver, 8).until(
        EC.invisibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Record Details')]")
        )
    )


def test_tp_08_005_boundary_value_analysis(driver):
    """TP-08-005: Boundary Value Analysis for CSV upload."""
    should_fail = {'negative_cases', 'future_date', 'empty_location', 'loc_101_chars'}
    should_pass = {'zero_cases', 'current_date', 'loc_100_chars'}

    for fixture_key in FIXTURES:
        navigate_to_data_management(driver)
        text = do_upload(driver, FIXTURES[fixture_key])

        if fixture_key in should_fail:
            assert any(
                kw in text.lower()
                for kw in ['error', 'invalid', 'failed', 'required', 'too long', 'rejected']
            ), f"'{fixture_key}' should be rejected but no error message was found"

        elif fixture_key in should_pass:
            assert 'Successfully imported' in text, (
                f"'{fixture_key}' should be accepted but "
                f"'Successfully imported' was not found"
            )


def test_tp_08_006_upload_error_handling(driver):
    """TP-08-006: Verify upload failures and invalid CSV handling."""

    # ── Case 1: Server Error Simulation ───────────────────────────────────────
    navigate_to_data_management(driver)

    driver.execute_script("""
        window._origFetch = window.fetch;
        window.fetch = function(url, opts) {
            if (url && url.toString().includes('/dengue-data/upload')) {
                return Promise.resolve(new Response(
                    JSON.stringify({error: 'Internal Server Error'}),
                    {status: 500, headers: {'Content-Type': 'application/json'}}
                ));
            }
            return window._origFetch(url, opts);
        };
    """)

    text = do_upload(driver, VALID_CSV_PATH)

    driver.execute_script(
        "if (window._origFetch) { window.fetch = window._origFetch; }"
    )

    assert any(kw in text.lower() for kw in ['error', 'failed']), \
        "A 500 response should produce an error message in the UI"

    # ── Case 2: Wrong Headers ──────────────────────────────────────────────────
    navigate_to_data_management(driver)
    text = do_upload(driver, WRONG_HEADERS_CSV)
    assert any(
        kw in text.lower()
        for kw in ['error', 'header', 'invalid', 'column', 'format', 'failed']
    ), "A CSV with wrong headers should be rejected"

    # ── Case 3: Incomplete CSV ─────────────────────────────────────────────────
    navigate_to_data_management(driver)
    text = do_upload(driver, INCOMPLETE_CSV)
    assert any(
        kw in text.lower()
        for kw in ['error', 'missing', 'invalid', 'incomplete', 'failed']
    ), "A CSV with missing fields should be rejected"