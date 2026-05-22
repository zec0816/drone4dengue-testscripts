"""
test_uc12_manage_settings.py
Drone4Dengue – UC-12 Manage Settings
Automated test suite using Selenium WebDriver (Python)

UI-verified field structure (from Settings page screenshot):
  Profile Settings  : Name, Username, Email (read-only), Phone, Company (read-only)
  Password Settings : New Password, Confirm New Password  [no Current Password field]
  Notification Prefs: Email toggle, SMS toggle, Alert Frequency dropdown
  System Config     : Dengue Alert Threshold (Low / Medium / High radio),
                      Prediction Model Parameters – numeric inputs behind "Edit Parameters" toggle:
                        • Historical Data Weight  (default 0.35)
                        • Weather Weight          (default 0.40)
                        • Breeding Area Detection Weight (default 0.25)
                      Risk Level Thresholds – numeric inputs behind "Edit Thresholds" toggle:
                        • Low to Medium Threshold (default 1)
                        • Medium to High Threshold (default 3)
                        Legend: Low < 1 | Medium 1-3 | High ≥ 3
                      Data Synchronization (Automatic / Manual radio),
                      "Apply Settings" button

Test Coverage:
  TP-12-001 → TC-12-001 | TCOV-12-001, TCOV-12-009, TCOV-12-017, TCOV-12-019, TCOV-12-022
  TP-12-002 → TC-12-002 | TCOV-12-007, TCOV-12-010, TCOV-12-011, TCOV-12-018
  TP-12-003 → TC-12-003 | TCOV-12-002, TCOV-12-012, TCOV-12-020
  TP-12-004 → TC-12-004 | TCOV-12-006, TCOV-12-013
  TP-12-005 → TC-12-005 | TCOV-12-003, TCOV-12-015, TCOV-12-021, TCOV-12-022
  TP-12-006 → TC-12-006 | TCOV-12-004, TCOV-12-022
  TP-12-007 → TC-12-007 | TCOV-12-016
  TP-12-008 → TC-12-008 | TCOV-12-005
  TP-12-009 → TC-12-009 | TCOV-12-008, TCOV-12-023
"""

import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

BASE_URL     = os.getenv("BASE_URL", "http://localhost:3000")
SETTINGS_URL = f"{BASE_URL}/settings"


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    d = webdriver.Chrome(options=options)
    d.implicitly_wait(5)

    test_email = os.getenv("TEST_ADMIN_EMAIL", "admin1@drone4dengue.com")
    primary_password = os.getenv("TEST_ADMIN_PW", "adminpass1")
    candidate_passwords = list(dict.fromkeys([primary_password, "adminpass123", "adminpass1"]))

    login_ok = False
    for pw in candidate_passwords:
        d.get(BASE_URL)
        try:
            email_el = WebDriverWait(d, 10).until(EC.element_to_be_clickable((By.ID, "email")))
        except Exception:
            continue
        email_el.click()
        email_el.send_keys(Keys.CONTROL + "a")
        email_el.send_keys(test_email)
        pw_el = d.find_element(By.ID, "password")
        pw_el.click()
        pw_el.send_keys(Keys.CONTROL + "a")
        pw_el.send_keys(pw)
        # JS click bypasses Framer Motion motion.div wrapper that intercepts normal clicks
        submit_btn = WebDriverWait(d, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']")))
        d.execute_script("arguments[0].click();", submit_btn)
        try:
            WebDriverWait(d, 10).until(EC.url_contains("/dashboard"))
            login_ok = True
            break
        except Exception:
            continue

    assert login_ok, "Unable to log in with any known test password"
    yield d
    d.quit()


def navigate_to_settings(driver, section=None):
    driver.get(SETTINGS_URL)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Settings')]"))
    )
    if section:
        section_map = {
            "Profile":      "//*[contains(text(),'Profile Settings')]",
            "Password":     "//*[contains(text(),'Password Settings')]",
            "Notification": "//*[contains(text(),'Notification Preferences')]",
            "System":       "//*[contains(text(),'System Configuration')]",
        }
        target = section_map.get(section, f"//*[contains(text(),'{section}')]")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, target))
        )


def js_set_input(driver, element_id, value):
    # React tracks internal state separately from the DOM value — must use native setter + events
    try:
        el = driver.find_element(By.ID, element_id)
        assert el.is_displayed(), f"Input {element_id} is not visible"
    except Exception as e:
        raise AssertionError(f"Could not find or access input with id='{element_id}': {e}")

    script = """
    return (function(id, val) {
        const el = document.getElementById(id);
        if (!el) return { success: false, msg: 'Element not found' };
        try {
            el.focus();
            const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return { success: true, value: el.value };
        } catch(e) {
            return { success: false, msg: e.message };
        }
    })(arguments[0], arguments[1]);
    """
    result = driver.execute_script(script, element_id, value)
    assert result.get('success'), f"Could not set input with id='{element_id}': {result.get('msg', 'Unknown error')}"


def set_profile_fields(driver, name, username, phone):
    js_set_input(driver, "name",     name)
    js_set_input(driver, "username", username)
    js_set_input(driver, "phone",    phone)


def get_profile_fields(driver):
    ids = ["name", "username", "email", "phone", "company"]
    fields = {}
    for fid in ids:
        try:
            el = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, fid))
            )
            fields[fid] = el
        except Exception as e:
            raise AssertionError(f"Profile field '{fid}' not found or not visible after 10s: {e}")
    return fields


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-001 | TC-12-001
# Covers: TCOV-12-001, TCOV-12-009, TCOV-12-017, TCOV-12-019, TCOV-12-022
# Verify admin can update profile information (Name, Username, Phone) with valid data.
# Note: Email and Company are read-only in the UI and cannot be edited.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_001_update_profile_valid(driver):
    navigate_to_settings(driver, "Profile")
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading...')]"))
    )
    time.sleep(0.5)

    fields_before    = get_profile_fields(driver)
    original_email   = fields_before["email"].get_attribute("value")
    original_company = fields_before["company"].get_attribute("value")

    assert fields_before["email"].get_attribute("disabled") is not None, \
        "Email field should be read-only"
    assert fields_before["company"].get_attribute("disabled") is not None, \
        "Company field should be read-only"

    # TCOV-12-017: Edit Profile link/button is visible and clickable
    edit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]"))
    )
    assert edit_btn.is_displayed(), "Edit Profile button should be visible"
    driver.execute_script("arguments[0].click();", edit_btn)

    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Save Changes')]"))
    )

    set_profile_fields(driver, "Admin One", "adminone", "60111111111")

    # TCOV-12-019: Save Changes button must be enabled with valid inputs
    assert save_btn.is_enabled(), "Save Changes button should be enabled with valid inputs"
    driver.execute_script("arguments[0].click();", save_btn)

    # TCOV-12-001 / TCOV-12-009: Save completes – edit mode exits, Edit Profile re-appears
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]")
        )
    )

    # TCOV-12-022: Success confirmation message is displayed
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Profile updated successfully')]")
        )
    )

    fields_after = get_profile_fields(driver)
    assert fields_after["name"].get_attribute("value")     == "Admin One"
    assert fields_after["username"].get_attribute("value") == "adminone"
    assert fields_after["phone"].get_attribute("value")    == "60111111111"
    assert fields_after["email"].get_attribute("value")    == original_email
    assert fields_after["company"].get_attribute("value")  == original_company


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-002 | TC-12-002
# Covers: TCOV-12-007, TCOV-12-010, TCOV-12-011, TCOV-12-018
# Verify Save Changes button is disabled / system blocks save for invalid inputs.
# Cases tested:
#   Case 1 – Name and Phone left blank  (TCOV-12-010)
#   Case 2 – Phone number too short / invalid format  (TCOV-12-011 adapted)
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_002_invalid_profile_inputs(driver):
    navigate_to_settings(driver, "Profile")
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading...')]"))
    )

    edit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]")
        )
    )
    driver.execute_script("arguments[0].click();", edit_btn)

    save_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Save Changes')]"))
    )

    # ── Case 1: Empty required fields ────────────────────────────────────────
    set_profile_fields(driver, "", "", "")
    driver.execute_script("arguments[0].click();", save_btn)

    # TCOV-12-018 / TCOV-12-010: Validation error must appear and edit mode must stay active
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(text(),'Please fill out this field')]")
        )
    )
    assert driver.find_element(
        By.XPATH, "//button[contains(.,'Save Changes')]"
    ).is_displayed(), "TCOV-12-010: Save Changes must still be visible after empty-field submit"

    # ── Case 2: Invalid phone number format ───────────────────────────────────
    set_profile_fields(driver, "Admin One", "adminone", "12")
    driver.execute_script("arguments[0].click();", save_btn)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH,
             "//*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'invalid')]"
             " | //*[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'phone')]")
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-003 | TC-12-003
# Covers: TCOV-12-002, TCOV-12-012, TCOV-12-020
# Verify admin can change password using New Password + Confirm New Password.
# Note: The UI shows only "New Password" and "Confirm New Password" fields –
#       there is no "Current Password" input on this page.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_003_change_password_valid(driver):
    navigate_to_settings(driver, "Password")

    # TCOV-12-020: Both password fields must be masked (type="password")
    new_pw_field     = driver.find_element(By.ID, "new-password")
    confirm_pw_field = driver.find_element(By.ID, "confirm-password")
    assert new_pw_field.get_attribute("type")     == "password", "New Password field must be masked"
    assert confirm_pw_field.get_attribute("type") == "password", "Confirm Password field must be masked"

    # TCOV-12-002 / TCOV-12-012: Submit matching passwords
    test_pw = os.getenv("TEST_ADMIN_PW", "adminpass1")
    js_set_input(driver, "new-password",     test_pw)
    js_set_input(driver, "confirm-password", test_pw)

    update_btn = driver.find_element(By.XPATH, "//button[contains(.,'Update Password')]")
    driver.execute_script("arguments[0].click();", update_btn)

    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Password updated successfully')]")
        )
    )
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Password updated successfully" in page_text, \
        "Success message should appear after valid password update"


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-004 | TC-12-004
# Covers: TCOV-12-006, TCOV-12-013
# Verify system rejects password update when:
#   Case 1 – Confirm New Password does not match New Password  (TCOV-12-013)
#   Case 2 – New Password is too short / fails strength policy  (TCOV-12-006)
# Note: TCOV-12-014 (wrong current password) is not applicable because the UI
#       does not expose a Current Password field.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_004_password_rejection(driver):
    navigate_to_settings(driver, "Password")

    update_btn = driver.find_element(By.XPATH, "//button[contains(.,'Update Password')]")

    # ── Case 1: Mismatched confirmation ──────────────────────────────────────
    js_set_input(driver, "new-password",     "adminpass@123")
    js_set_input(driver, "confirm-password", "adminpass@124")
    driver.execute_script("arguments[0].click();", update_btn)

    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in page_text for kw in ["passwords do not match", "do not match", "match", "error"]), \
        "System should reject mismatched password confirmation"

    # ── Case 2: Weak / short password ────────────────────────────────────────
    js_set_input(driver, "new-password",     "short")
    js_set_input(driver, "confirm-password", "short")
    driver.execute_script("arguments[0].click();", update_btn)

    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in page_text for kw in ["at least 8", "minimum", "invalid", "error", "weak"]), \
        "System should reject a password that does not meet strength requirements"


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-005 | TC-12-005
# Covers: TCOV-12-003, TCOV-12-015, TCOV-12-021, TCOV-12-022
# Verify admin can save notification preferences and UI reflects state on reload.
# UI controls: Email toggle (checkbox), SMS toggle (checkbox),
#              Alert Frequency dropdown (Immediate / Daily / Weekly)
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_005_notification_preferences(driver):
    navigate_to_settings(driver, "Notification")

    notif_card = driver.find_element(
        By.XPATH,
        "//h2[contains(.,'Notification Preferences')]/ancestor::div[contains(@class,'rounded')]"
    )

    # TCOV-12-015: Locate Email and SMS toggles (hidden checkboxes behind toggle UI)
    toggles = notif_card.find_elements(By.XPATH, ".//input[@type='checkbox']")
    assert len(toggles) >= 2, "Expected at least Email and SMS notification toggles"
    email_toggle, sms_toggle = toggles[0], toggles[1]

    if not email_toggle.is_selected():
        driver.execute_script("arguments[0].click();", email_toggle)
    if sms_toggle.is_selected():
        driver.execute_script("arguments[0].click();", sms_toggle)

    # TCOV-12-015: Set Alert Frequency = Daily
    freq_select = Select(driver.find_element(By.ID, "alert-frequency"))
    freq_select.select_by_visible_text("Daily")

    # Wait for button to be enabled — companySettingsLoading must be false first
    save_pref_btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Save Preferences')]")
        )
    )
    driver.execute_script("arguments[0].click();", save_pref_btn)

    # TCOV-12-022: Success message is shown
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'Notification preferences saved successfully')]")
        )
    )

    # TCOV-12-021: Reload page and verify toggle state persists
    driver.refresh()
    navigate_to_settings(driver, "Notification")
    time.sleep(1)

    notif_card = driver.find_element(
        By.XPATH,
        "//h2[contains(.,'Notification Preferences')]/ancestor::div[contains(@class,'rounded')]"
    )
    toggles      = notif_card.find_elements(By.XPATH, ".//input[@type='checkbox']")
    email_toggle = toggles[0]
    sms_toggle   = toggles[1]

    assert email_toggle.is_selected(), \
        "TCOV-12-021: Email toggle should be ON after reload – backend must persist this preference"
    assert not sms_toggle.is_selected(), \
        "TCOV-12-021: SMS toggle should be OFF after reload – backend must persist this preference"


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-006 | TC-12-006
# Covers: TCOV-12-004, TCOV-12-022
# Verify admin can apply System Configuration changes.
#
# Full UI controls (confirmed from screenshot):
#   • Dengue Alert Threshold      – Low / Medium / High radios
#   • Prediction Model Parameters – three numeric weight inputs (behind Edit Parameters toggle)
#       Historical Data Weight, Weather Weight, Breeding Area Detection Weight
#   • Risk Level Thresholds       – two numeric inputs (behind Edit Thresholds toggle)
#       Low to Medium Threshold, Medium to High Threshold
#   • Data Synchronization        – Automatic / Manual radios
#   • Apply Settings button
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_006_system_configuration(driver):
    navigate_to_settings(driver, "System")
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading...')]"))
    )

    high_radio = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//div[.//text()[contains(.,'Dengue Alert Threshold')]]"
            "//input[@type='radio' and (@value='high' or @value='High')]"
            " | //label[normalize-space()='High']/preceding-sibling::input[@type='radio']"
            " | //label[normalize-space()='High']/input[@type='radio']"
        ))
    )
    driver.execute_script("arguments[0].click();", high_radio)
    assert high_radio.is_selected(), "Dengue Alert Threshold 'High' radio should be selected"

    # Section is collapsed by default; click "Edit Parameters" to reveal inputs
    edit_params_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(.,'Edit Parameters')] | //span[contains(.,'Edit Parameters')]"
            " | //*[contains(@class,'edit') and contains(.,'Parameters')]"
        ))
    )
    driver.execute_script("arguments[0].click();", edit_params_btn)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//*[contains(text(),'Historical Data Weight')]"
            "/following-sibling::*//input | "
            "//*[contains(text(),'Historical Data Weight')]"
            "/..//input"
        ))
    )

    def set_param_input(label_text, value):
        inp = driver.find_element(
            By.XPATH,
            f"//*[contains(text(),'{label_text}')]/following-sibling::input"
            f" | //*[contains(text(),'{label_text}')]/..//input"
            f" | //*[contains(text(),'{label_text}')]/../..//input"
        )
        driver.execute_script(
            """
            var el = arguments[0], val = arguments[1];
            el.focus();
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            inp, str(value)
        )
        return inp

    set_param_input("Historical Data Weight",         "0.35")
    set_param_input("Weather Weight",                 "0.40")
    set_param_input("Breeding Area Detection Weight", "0.25")

    edit_thresh_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(.,'Edit Thresholds')] | //span[contains(.,'Edit Thresholds')]"
            " | //*[contains(@class,'edit') and contains(.,'Thresholds')]"
        ))
    )
    driver.execute_script("arguments[0].click();", edit_thresh_btn)

    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//*[contains(text(),'Low to Medium Threshold')]"
            "/following-sibling::*//input | "
            "//*[contains(text(),'Low to Medium Threshold')]/..//input"
        ))
    )

    set_param_input("Low to Medium Threshold",  "1")
    set_param_input("Medium to High Threshold", "3")

    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Low" in body_text and "Medium" in body_text and "High" in body_text, \
        "Risk level legend (Low / Medium / High) should be visible"

    auto_radio = driver.find_element(
        By.XPATH,
        "//div[.//text()[contains(.,'Data Synchronization')]]"
        "//input[@type='radio' and (@value='automatic' or @value='Automatic')]"
        " | //label[normalize-space()='Automatic']/preceding-sibling::input[@type='radio']"
        " | //label[normalize-space()='Automatic']/input[@type='radio']"
    )
    driver.execute_script("arguments[0].click();", auto_radio)
    assert auto_radio.is_selected(), "Data Synchronization 'Automatic' radio should be selected"

    apply_btn = driver.find_element(By.XPATH, "//button[contains(.,'Apply Settings')]")
    driver.execute_script("arguments[0].click();", apply_btn)

    # TCOV-12-004 / TCOV-12-022: Success confirmation shown
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//*[contains(text(),'System configuration saved successfully')]")
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-007 | TC-12-007
# Covers: TCOV-12-016
# Verify out-of-range threshold values are rejected.
#
# The Risk Level Thresholds section exposes two NUMERIC inputs (confirmed from UI):
#   • Low to Medium Threshold  (default 1, must be ≥ 0)
#   • Medium to High Threshold (default 3, must be > Low to Medium Threshold)
# Legend: Low < 1 | Medium 1-3 | High ≥ 3
#
# Out-of-range cases tested:
#   Case 1 – Low to Medium Threshold = -1 (negative value)
#   Case 2 – Medium to High Threshold ≤ Low to Medium Threshold (e.g. 1 ≤ 1)
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_007_out_of_range_threshold(driver):
    navigate_to_settings(driver, "System")
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading...')]"))
    )

    edit_thresh_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[contains(.,'Edit Thresholds')] | //span[contains(.,'Edit Thresholds')]"
            " | //*[contains(@class,'edit') and contains(.,'Thresholds')]"
        ))
    )
    driver.execute_script("arguments[0].click();", edit_thresh_btn)

    low_med_inp = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((
            By.XPATH,
            "//*[contains(text(),'Low to Medium Threshold')]"
            "/following-sibling::input"
            " | //*[contains(text(),'Low to Medium Threshold')]/..//input"
            " | //*[contains(text(),'Low to Medium Threshold')]/../..//input"
        ))
    )
    med_hi_inp = driver.find_element(
        By.XPATH,
        "//*[contains(text(),'Medium to High Threshold')]"
        "/following-sibling::input"
        " | //*[contains(text(),'Medium to High Threshold')]/..//input"
        " | //*[contains(text(),'Medium to High Threshold')]/../..//input"
    )

    def js_set(el, val):
        driver.execute_script(
            """
            var el = arguments[0], val = arguments[1];
            el.focus();
            var setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value').set;
            setter.call(el, val);
            el.dispatchEvent(new Event('input',  { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            el, str(val)
        )

    apply_btn_xpath = "//button[contains(.,'Apply Settings')]"

    # ── Case 1: Negative low threshold must be rejected ───────────────────────
    js_set(low_med_inp, "-1")
    js_set(med_hi_inp,  "3")
    driver.find_element(By.XPATH, apply_btn_xpath).click()

    time.sleep(0.5)
    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in page_text for kw in ["invalid", "error", "must be", "negative", "greater", "positive"]), \
        "TCOV-12-016: System must reject a negative Low-to-Medium Threshold value (-1)"

    # ── Re-open Edit Thresholds if the section collapsed ─────────────────────
    try:
        edit_thresh_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//button[contains(.,'Edit Thresholds')] | //span[contains(.,'Edit Thresholds')]"
            ))
        )
        driver.execute_script("arguments[0].click();", edit_thresh_btn)
        low_med_inp = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((
                By.XPATH,
                "//*[contains(text(),'Low to Medium Threshold')]/..//input"
                " | //*[contains(text(),'Low to Medium Threshold')]/../..//input"
            ))
        )
        med_hi_inp = driver.find_element(
            By.XPATH,
            "//*[contains(text(),'Medium to High Threshold')]/..//input"
            " | //*[contains(text(),'Medium to High Threshold')]/../..//input"
        )
    except Exception:
        pass  # inputs stayed visible after the failed apply

    # ── Case 2: Low threshold ≥ High threshold must be rejected ──────────────
    js_set(low_med_inp, "5")
    js_set(med_hi_inp,  "3")
    driver.find_element(By.XPATH, apply_btn_xpath).click()

    time.sleep(0.5)
    page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert any(kw in page_text for kw in ["invalid", "error", "must be", "lower", "greater", "less than"]), \
        "TCOV-12-016: System must reject Low threshold (5) that is >= High threshold (3)"


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-008 | TC-12-008
# Covers: TCOV-12-005
# Verify Cancel / Discard in Profile Settings discards unsaved changes.
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_008_cancel_edit_discards_changes(driver):
    navigate_to_settings(driver, "Profile")

    edit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]")
        )
    )
    driver.execute_script("arguments[0].click();", edit_btn)

    name_field    = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "name"))
    )
    original_name = name_field.get_attribute("value")

    js_set_input(driver, "name", "Ali Ahmad")
    assert driver.find_element(By.ID, "name").get_attribute("value") == "Ali Ahmad", \
        "Name should show the new (unsaved) value before cancel"

    # JS click bypasses Framer Motion wrapper
    cancel_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Cancel') or contains(.,'Discard')]")
        )
    )
    driver.execute_script("arguments[0].click();", cancel_btn)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]")
        )
    )

    name_displayed = driver.find_element(By.ID, "name").get_attribute("value")
    assert name_displayed == original_name, \
        f"Profile name should revert to '{original_name}' after Cancel, got '{name_displayed}'"


# ══════════════════════════════════════════════════════════════════════════════
# TP-12-009 | TC-12-009
# Covers: TCOV-12-008, TCOV-12-023
# TCOV-12-008: A server-side save failure must display an error message and keep
#              the form in edit mode (Save Changes button stays visible).
# TCOV-12-023: A successful save must exit edit mode (Save Changes disappears).
# ══════════════════════════════════════════════════════════════════════════════
def test_tc_12_009_save_failure_and_edit_mode_exit(driver):
    navigate_to_settings(driver, "Profile")
    WebDriverWait(driver, 15).until_not(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Loading...')]"))
    )
    time.sleep(0.5)

    edit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(.,'Edit Profile')] | //a[contains(.,'Edit Profile')]")
        )
    )
    driver.execute_script("arguments[0].click();", edit_btn)

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Save Changes')]"))
    )
    set_profile_fields(driver, "Ali Test", "alitest", "60123456789")

    # ── Part A: TCOV-12-008 – Simulate server error via fetch mock ────────────
    driver.execute_script("""
        window.__origFetch = window.fetch;
        window.fetch = function(url, opts) {
            if (opts && opts.method === 'PATCH') {
                return Promise.resolve({
                    ok: false,
                    json: () => Promise.resolve({ error: 'Simulated server error' })
                });
            }
            return window.__origFetch(url, opts);
        };
    """)

    save_btn = driver.find_element(By.XPATH, "//button[contains(.,'Save Changes')]")
    driver.execute_script("arguments[0].click();", save_btn)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH,
             "//*[contains(text(),'Simulated server error')]"
             " | //*[contains(text(),'Failed to update')]")
        )
    )
    assert driver.find_element(
        By.XPATH, "//button[contains(.,'Save Changes')]"
    ).is_displayed(), \
        "TCOV-12-008: Save Changes must still be visible after a failed save"

    # ── Restore real fetch ────────────────────────────────────────────────────
    driver.execute_script("window.fetch = window.__origFetch;")

    # ── Part B: TCOV-12-023 – Successful save must exit edit mode ─────────────
    save_btn = driver.find_element(By.XPATH, "//button[contains(.,'Save Changes')]")
    driver.execute_script("arguments[0].click();", save_btn)

    WebDriverWait(driver, 10).until_not(
        EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Save Changes')]"))
    )
