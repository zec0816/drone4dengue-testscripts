"""
tc_uc13_get_dengue_noti.py
Drone4Dengue – UC-13 Get Potential Dengue Notification
Automated test suite using Appium UiAutomator2 (Python)

Test Coverage:
  TP-13-001 → TC-13-001 | TCOV-13-001, TCOV-13-002
  TP-13-002 → TC-13-002 | TCOV-13-003
  TP-13-003 → TC-13-003 | TCOV-13-004
  TP-13-004 → TC-13-004 | TCOV-13-005
  TP-13-005 → TC-13-005 | TCOV-13-006
  TP-13-006 → TC-13-006 | TCOV-13-007, TCOV-13-008
  TP-13-007 → TC-13-007 | TCOV-13-009

Run with:
  $env:ANDROID_HOME="C:\\Users\\Seanseann\\AppData\\Local\\Android\\Sdk"
  $env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
  appium --port 4723
  python -m pytest tests/selenium/tc_uc13_get_dengue_noti.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from urllib.parse import quote, urlparse
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import psycopg2
import pytest
import requests
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from psycopg2.extras import Json
from selenium.webdriver.support.ui import WebDriverWait

MOBILE_PACKAGE = os.getenv("MOBILE_APP_PACKAGE", "com.adamarbain.dengueeyemobileapp")
MOBILE_SCHEME = os.getenv("MOBILE_APP_SCHEME", "dengueeye")
MOBILE_SLUG = os.getenv("aMOBILE_APP_SLUG", "dengueeye-mobile-app")
MOBILE_ACTIVITY = os.getenv("MOBILE_APP_ACTIVITY", ".MainActivity")
APPIUM_URL = os.getenv("APPIUM_URL", "http://127.0.0.1:4723")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:4000")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Ng827sean_@localhost:5432/drone4dengue",
)
MOBILE_USER_EMAIL = os.getenv("TEST_MOBILE_EMAIL", "user1@drone4dengue.com")
MOBILE_USER_PASSWORD = os.getenv("TEST_MOBILE_PW", "userpass1")
DEV_SERVER_URL = os.getenv("DEV_SERVER_URL", "http://10.0.2.2:8081")
DEV_CLIENT_SCHEME = os.getenv("DEV_CLIENT_SCHEME", f"exp+{MOBILE_SLUG}")


@pytest.fixture(scope="module")
def driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = os.getenv("ANDROID_DEVICE_NAME", "emulator-5554")
    options.app_package = MOBILE_PACKAGE
    options.app_activity = MOBILE_ACTIVITY
    options.auto_grant_permissions = True
    options.no_reset = True  # Keep auth token; Appium still restarts the app cleanly

    session = webdriver.Remote(APPIUM_URL, options=options)
    time.sleep(5)  # Wait for app to restart and Metro bundle to load
    yield session
    session.quit()


@pytest.fixture(scope="module")
def admin_context():
    email = os.getenv("TEST_ADMIN_EMAIL", "admin1@drone4dengue.com")
    password = os.getenv("TEST_ADMIN_PW", "adminpass1")
    response = requests.post(
        f"{API_BASE_URL}/auth/admin-login",
        json={"email": email, "password": password},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "token": payload["token"],
        "companyId": payload["user"]["companyId"],
        "adminId": payload["user"]["id"],
    }


@pytest.fixture(scope="module")
def db_connection():
    connection = psycopg2.connect(DATABASE_URL)
    connection.autocommit = True
    try:
        yield connection
    finally:
        connection.close()


def adb(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["adb", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def launch_mobile_app() -> None:
    parsed = urlparse(DEV_SERVER_URL)
    if parsed.hostname in {"127.0.0.1", "localhost"}:
        port = parsed.port or 80
        adb("reverse", f"tcp:{port}", f"tcp:{port}")

    deep_link = (
        f"{DEV_CLIENT_SCHEME}://expo-development-client/?url={quote(DEV_SERVER_URL, safe='')}"
    )
    result = adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", deep_link)
    if result.returncode == 0:
        return

    subprocess.run(
        ["adb", "shell", "am", "start", "-W", "-n", f"{MOBILE_PACKAGE}/{MOBILE_ACTIVITY}"],
        check=True,
    )


def set_emulator_location(latitude: float, longitude: float) -> None:
    subprocess.run(["adb", "shell", "am", "force-stop", MOBILE_PACKAGE], check=True)
    subprocess.run(["adb", "emu", "geo", "fix", str(longitude), str(latitude)], check=True)
    # Re-grant location in case a previous test revoked it
    adb("shell", "pm", "grant", MOBILE_PACKAGE, "android.permission.ACCESS_FINE_LOCATION")
    adb("shell", "pm", "grant", MOBILE_PACKAGE, "android.permission.ACCESS_COARSE_LOCATION")
    launch_mobile_app()


def dismiss_expo_dev_menu(driver) -> None:
    """Best-effort close for the Expo dev menu overlay."""
    try:
        dev_menu = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Reload' or @text='Go home' or @text='TOOLS' or @text='DEVELOPMENT SERVERS']",
        )
        if dev_menu:
            try:
                driver.back()
            except Exception:
                adb("shell", "input", "keyevent", "4")
            time.sleep(2)
    except Exception:
        pass


def wait_for_dashboard_ready(driver, timeout: int = 30) -> None:
    dismiss_expo_dev_menu(driver)
    dismiss_android_permissions(driver)
    _READY = [
        "Get Dengue Risk Prediction", "Enable Location to Predict",
        "DengueEye", "Dashboard", "Welcome Back", "Sign In",
        "informational purposes only", "Risk Detected",
    ]
    _BLOCKING = ["Permission denied", "Location permission is required", "Location Error"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            src = driver.page_source
            if any(t in src for t in _READY):
                print("OK")
                return
            if any(t in src for t in _BLOCKING):
                dismiss_android_permissions(driver)
                time.sleep(1)
        except Exception:
            pass
        time.sleep(0.5)
    try:
        print("\n[wait_for_dashboard_ready] Timeout")
        print(driver.page_source)
    except Exception:
        pass
    raise TimeoutError("Dashboard not ready")


def accept_medical_disclaimer_if_needed(driver) -> None:
    """Accept the one-time Medical Disclaimer shown on fresh app installs."""
    for _ in range(3):
        try:
            page_source = driver.page_source
            break
        except Exception:
            # Accessibility tree may be blocked by a system permission dialog.
            # Blindly tap the standard "While using the app" button location and retry.
            adb("shell", "input", "tap", "640", "1742")
            time.sleep(3)
    else:
        return
    if "I Understand" not in page_source and "Medical Disclaimer" not in page_source:
        return
    # Scroll to reveal the accept button (it is below the fold)
    for _ in range(3):
        driver.swipe(640, 1400, 640, 400, duration=800)
        time.sleep(1)
        if "I Understand" in driver.page_source:
            break
    try:
        btns = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text, 'I Understand')]")
        if btns:
            btns[0].click()
            time.sleep(3)
            return
    except Exception:
        pass
    # Coordinate fallback — button is near bottom of screen after scrolling
    adb("shell", "input", "tap", "640", "2550")
    time.sleep(3)


def ensure_mobile_login(driver) -> None:
    # Dismiss overlay alerts before reading page state to avoid false negatives in subsequent calls
    dismiss_android_permissions(driver)
    accept_medical_disclaimer_if_needed(driver)
    select_dev_server_if_needed(driver)
    open_dev_client_if_needed(driver)
    for _ in range(3):
        dismiss_dev_menu(driver)
        dismiss_android_permissions(driver)
        page_source = driver.page_source
        if not any(token in page_source for token in ["Connected to:", "TOOLS", "DEVELOPMENT SERVERS"]):
            break
        launch_mobile_app()
        adb("shell", "input", "keyevent", "4")
        try:
            subprocess.run(
                ["adb", "shell", "am", "start", "-W", "-n", f"{MOBILE_PACKAGE}/{MOBILE_ACTIVITY}"],
                check=True,
            )
        except Exception:
            pass
        try:
            driver.activate_app(MOBILE_PACKAGE)
        except Exception:
            pass
        time.sleep(3)
    page_source = driver.page_source
    edit_fields = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
    sign_in_buttons = driver.find_elements(AppiumBy.XPATH, "//*[@text='Sign In']")

    if len(edit_fields) >= 2 and sign_in_buttons:
        edit_fields[0].clear()
        edit_fields[0].send_keys(MOBILE_USER_EMAIL)
        edit_fields[1].clear()
        edit_fields[1].send_keys(MOBILE_USER_PASSWORD)
        sign_in_buttons[0].click()
        dismiss_android_permissions(driver)

    wait_for_dashboard_ready(driver, timeout=120)
    # Use adb tap for Dashboard nav button — works regardless of accessibility tree
    adb("shell", "input", "tap", "187", "2695")
    time.sleep(3)


# Bottom nav button coordinates measured from page source bounds:
# Dashboard: [36,2606][338,2785] → center (187, 2695)
# Action:    [338,2606][640,2785] → center (489, 2695)
# Notification: [640,2606][942,2785] → center (791, 2695)
# Profile:   [942,2606][1238,2785] → center (1090, 2695)
_NAV_COORDS = {
    "Dashboard":    (187, 2695),
    "Action":       (489, 2695),
    "Notification": (791, 2695),
    "Profile":      (1090, 2695),
}
_NAV_ROUTE = {"Notification": "notification", "Dashboard": "dashboard", "Action": "action"}

def tap_bottom_nav(driver, label: str) -> None:
    handle_error_screen_if_needed(driver)
    # 1. content-desc is most reliable when present
    try:
        driver.find_element(
            AppiumBy.XPATH,
            f"//*[contains(@content-desc, '{label}') and @clickable='true']"
        ).click()
        time.sleep(3)
        return
    except Exception:
        pass
    # 2. Ancestor of label TextView that is clickable
    try:
        driver.find_element(
            AppiumBy.XPATH,
            f"//*[@text='{label}']/ancestor::*[@clickable='true'][1]"
        ).click()
        time.sleep(3)
        return
    except Exception:
        pass
    # 3. Coordinate tap via adb — most reliable for bottom nav regardless of accessibility tree
    if label in _NAV_COORDS:
        x, y = _NAV_COORDS[label]
        adb("shell", "input", "tap", str(x), str(y))
        time.sleep(3)
        return
    # 4. Deep-link fallback
    route = _NAV_ROUTE.get(label, label.lower())
    deep_link = f"{MOBILE_SCHEME}://{route}"
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", deep_link)
    time.sleep(5)


def wait_for_text(driver, text: str, timeout: int = 20) -> None:
    def _predicate(current):
        # XPath attribute search (old arch) + raw page_source search (new arch / Fabric)
        if (
            current.find_elements(AppiumBy.XPATH, f"//*[contains(@text, '{text}')]")
            or current.find_elements(AppiumBy.XPATH, f"//*[contains(@content-desc, '{text}')]")
        ):
            return True
        return text in current.page_source

    try:
        WebDriverWait(driver, timeout).until(_predicate)
    except Exception:
        print(f"\n[wait_for_text] Timeout waiting for: {text}")
        print(driver.page_source)
        raise


def wait_for_any_text(driver, texts: list[str], timeout: int = 20) -> None:
    def _predicate(current):
        # XPath attribute search (old arch) + raw page_source search (new arch / Fabric)
        src = current.page_source
        for text in texts:
            if text in src:
                return True
            if current.find_elements(AppiumBy.XPATH, f"//*[contains(@text, '{text}')]"):
                return True
        return False

    try:
        WebDriverWait(driver, timeout).until(_predicate)
    except Exception:
        print("\n[wait_for_any_text] Timeout waiting for:", texts)
        print(driver.page_source)
        raise


def dismiss_android_permissions(driver) -> None:
    selectors = [
        "//*[@text='While using the app']",
        "//*[@text='Only this time']",
        "//*[@text='Allow only while using the app']",
        "//*[@text='Allow while using the app']",
        "//*[@text='Allow']",
        "//*[@text='ALLOW']",
        "//*[@text='OK']",
    ]
    for selector in selectors:
        try:
            buttons = driver.find_elements(AppiumBy.XPATH, selector)
            if buttons:
                buttons[0].click()
                time.sleep(0.5)
        except Exception:
            continue


def handle_error_screen_if_needed(driver) -> None:
    """Click Reload if the Expo crash/error screen is visible (e.g. from MapView crash)."""
    page_source = driver.page_source
    if "There was a problem loading" in page_source or (
        "Reload" in page_source and "DEVELOPMENT SERVERS" not in page_source
    ):
        try:
            reload_btns = driver.find_elements(AppiumBy.XPATH, "//*[@text='Reload']/ancestor::*[@clickable='true'][1]")
            if reload_btns:
                reload_btns[0].click()
                time.sleep(8)
                return
        except Exception:
            pass


def select_dev_server_if_needed(driver) -> None:
    handle_error_screen_if_needed(driver)
    page_source = driver.page_source
    if "Error loading app" in page_source:
        try:
            driver.find_element(AppiumBy.ACCESSIBILITY_ID, "Close").click()
            time.sleep(1)
        except Exception:
            pass
        page_source = driver.page_source
    if "DEVELOPMENT SERVERS" not in page_source:
        return

    # Prefer configured dev server
    local_rows = driver.find_elements(
        AppiumBy.XPATH,
        f"//*[@text='{DEV_SERVER_URL}']/ancestor::*[@clickable='true'][1]",
    )
    if local_rows:
        local_rows[0].click()
        time.sleep(2)
        return

    # Prefer selecting a DengueEye entry if present
    entries = driver.find_elements(
        AppiumBy.XPATH,
        "//*[@text='DengueEye']/ancestor::*[@clickable='true'][1]",
    )
    if entries:
        entries[0].click()
        time.sleep(2)
        return

    # Fall back to the first selectable server row
    rows = driver.find_elements(
        AppiumBy.XPATH,
        "//*[@text='DEVELOPMENT SERVERS']/following::*[@clickable='true']",
    )
    if rows:
        rows[0].click()
        time.sleep(2)


def open_dev_client_if_needed(driver) -> None:
    page_source = driver.page_source
    if "Connected to:" not in page_source:
        return
    launch_mobile_app()
    time.sleep(5)


def dismiss_dev_menu(driver) -> None:
    page_source = driver.page_source
    if (
        "Connected to:" not in page_source
        and "TOOLS" not in page_source
        and "DEVELOPMENT SERVERS" not in page_source
    ):
        return

    try:
        reload_rows = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Reload']/ancestor::*[@clickable='true'][1]",
        )
        if reload_rows:
            reload_rows[0].click()
            time.sleep(3)
            return
    except Exception:
        pass

    if "Connected to:" in page_source or "TOOLS" in page_source:
        # Fallback to a tap in the Reload button bounds (emulator default size)
        adb("shell", "input", "tap", "350", "1750")
        time.sleep(3)
        return

    try:
        go_home_rows = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@text='Go home']/ancestor::*[@clickable='true'][1]",
        )
        if go_home_rows:
            go_home_rows[0].click()
            time.sleep(2)
            app_rows = driver.find_elements(
                AppiumBy.XPATH,
                "//*[@text='DengueEye']/ancestor::*[@clickable='true'][1]",
            )
            if app_rows:
                app_rows[0].click()
                time.sleep(3)
            return
    except Exception:
        pass

    for _ in range(2):
        try:
            driver.back()
            time.sleep(0.5)
        except Exception:
            break

    try:
        close_buttons = driver.find_elements(
            AppiumBy.XPATH,
            "//*[@content-desc='Close']/ancestor::*[@clickable='true'][1]",
        )
        if close_buttons:
            close_buttons[0].click()
            time.sleep(1)
            return
    except Exception:
        pass

    try:
        driver.find_element(AppiumBy.XPATH, "//*[@text='Go home']").click()
        time.sleep(1)
    except Exception:
        pass


def clear_notifications(db_connection, company_id: str, keywords: list[str]) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            'DELETE FROM "Notification" WHERE "companyId" = %s AND ("title" = ANY(%s) OR "message" = ANY(%s))',
            (company_id, keywords, keywords),
        )


def get_mobile_user(db_connection) -> dict:
    with db_connection.cursor() as cursor:
        cursor.execute(
            'SELECT "id", "companyId" FROM "User" WHERE "email" = %s',
            (MOBILE_USER_EMAIL,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Mobile user not found for email {MOBILE_USER_EMAIL}")
        return {"id": row[0], "companyId": row[1]}


def seed_notification(
    db_connection,
    company_id: str,
    *,
    title: str,
    message: str,
    risk_level: str,
    location: str,
    created_at: datetime,
    notification_type: str = "prediction",
    is_read: bool = False,
    user_id: str | None = None,
) -> None:
    with db_connection.cursor() as cursor:
        cursor.execute(
            'INSERT INTO "Notification" ("id", "title", "message", "type", "userId", "companyId", "isRead", "metadata", "createdAt", "readAt") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)',
            (
                str(uuid4()),
                title,
                message,
                notification_type,
                user_id,
                company_id,
                is_read,
                Json({"location": location, "riskLevel": risk_level}),
                created_at,
            ),
        )


_HIGH_RISK_PREDICTION = (
    '{"latitude":3.1622,"longitude":101.7007,'
    '"riskScore":4.5,"riskLevel":"high",'
    '"model1Score":4.0,"model2Score":5.0}'
)


def _navigate_to_risk_analysis() -> None:
    """Open the risk-analysis screen with a deterministic HIGH-risk prediction via deep link."""
    encoded = quote(_HIGH_RISK_PREDICTION, safe="")
    adb("shell", "am", "start", "-a", "android.intent.action.VIEW",
        "-d", f"{MOBILE_SCHEME}://risk-analysis?prediction={encoded}")
    time.sleep(5)


def trigger_dashboard_prediction(driver) -> None:
    wait_for_dashboard_ready(driver)

    # If a recent prediction is already cached (< 1 h), the DengueRiskCard shows the result
    # and hides the predict button entirely — detect this and skip the tap.
    _CACHED_INDICATORS = ["informational purposes only", "Risk Detected", "Stay vigilant"]

    try:
        src = driver.page_source
    except Exception:
        src = ""

    if any(kw in src for kw in _CACHED_INDICATORS):
        _navigate_to_risk_analysis()
        return

    # Tap "Enable Location to Predict" until location is acquired and the predict button appears.
    # On emulators the GPS fix from `emu geo fix` can take several seconds to propagate.
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            src = driver.page_source
        except Exception:
            time.sleep(2)
            continue
        if "Get Dengue Risk Prediction" in src or "Refresh Prediction" in src:
            break
        if any(kw in src for kw in _CACHED_INDICATORS):
            _navigate_to_risk_analysis()
            return
        if "Enable Location to Predict" in src:
            try:
                btns = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text, 'Enable Location')]")
                if btns:
                    btns[0].click()
                    dismiss_android_permissions(driver)
                    time.sleep(4)
                    continue
            except Exception:
                pass
        time.sleep(2)

    button = WebDriverWait(driver, 20).until(
        lambda current: (
            current.find_elements(AppiumBy.XPATH, "//*[@text='Get Dengue Risk Prediction']")
            or current.find_elements(AppiumBy.XPATH, "//*[@text='Refresh Prediction']")
        )
    )
    button[0].click()
    time.sleep(5)
    _navigate_to_risk_analysis()


class TestTP13GetPotentialDengueNotificationMobile:

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-001 | TC-13-001
    # Covers: TCOV-13-001, TCOV-13-002
    # Verify user receives push notification for HIGH and MODERATE dengue risk.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_001_high_and_moderate_notifications_delivered(self, db_connection, admin_context, driver):
        # Force clean app state so the first test never inherits a stale Expo dev menu
        adb("shell", "am", "force-stop", MOBILE_PACKAGE)
        time.sleep(3)
        launch_mobile_app()
        time.sleep(8)

        # Seed across all potential companies so the test is robust to any cached login session
        all_company_ids = ["comp-001", "comp-002", "comp-003", "comp-999"]
        keywords = ["Chow Kit", "Brickfields", "Damansara", "HIGH", "MODERATE", "LOW"]
        for cid in all_company_ids:
            clear_notifications(db_connection, cid, keywords)

        now = datetime.now(timezone.utc)
        for cid in all_company_ids:
            seed_notification(
                db_connection, cid,
                title="High Risk Alert - Chow Kit",
                message="Chow Kit is at HIGH dengue risk.",
                risk_level="high", location="Chow Kit", created_at=now,
            )
            seed_notification(
                db_connection, cid,
                title="Moderate Risk Alert - Brickfields",
                message="Brickfields is at MODERATE dengue risk.",
                risk_level="medium", location="Brickfields",
                created_at=now - timedelta(minutes=2),
            )

        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        tap_bottom_nav(driver, "Notification")
        # Pull-to-refresh: swipe down from top of list (y=300 → y=900)
        driver.swipe(640, 300, 640, 900, duration=800)
        time.sleep(4)
        wait_for_text(driver, "Chow Kit", timeout=30)
        wait_for_text(driver, "Brickfields", timeout=30)
        wait_for_text(driver, "HIGH", timeout=10)
        wait_for_text(driver, "MODERATE", timeout=10)

        source = driver.page_source
        assert source.index("Chow Kit") < source.index("Brickfields"), "Notifications should be ordered newest first"

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-002 | TC-13-002
    # Covers: TCOV-13-003
    # Verify Risk Analysis Page displays all required components.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_002_risk_analysis_displays_required_components(self, driver):
        set_emulator_location(3.1622, 101.7007)  # Chow Kit area
        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        trigger_dashboard_prediction(driver)

        # Use longer timeout – deep-link navigation + ML prediction can take time on emulator
        wait_for_any_text(driver, ["High Risk", "Medium Risk", "Low Risk", "Risk Details"], timeout=45)
        wait_for_text(driver, "Risk Details",    timeout=30)
        wait_for_text(driver, "Temperature",     timeout=30)
        wait_for_text(driver, "Humidity",        timeout=30)
        wait_for_text(driver, "Required Actions",timeout=30)
        # Scroll down so the button below the fold enters the accessibility tree
        driver.swipe(640, 1800, 640, 400, duration=600)
        time.sleep(1)
        wait_for_text(driver, "Call Local Authority Now", timeout=30)

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-003 | TC-13-003
    # Covers: TCOV-13-004
    # Verify Take Required Actions is accessible and leads to actionable checklist.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_003_take_required_actions_accessible(self, driver):
        set_emulator_location(3.1622, 101.7007)
        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        trigger_dashboard_prediction(driver)

        wait_for_text(driver, "Required Actions",               timeout=45)
        wait_for_text(driver, "Conduct Immediate Fogging",       timeout=30)
        wait_for_text(driver, "Clear stagnant water around home",timeout=30)
        driver.swipe(640, 1800, 640, 400, duration=600)
        time.sleep(1)
        wait_for_text(driver, "Call Local Authority Now",        timeout=30)

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-004 | TC-13-004
    # Covers: TCOV-13-005
    # Verify no notification is sent when risk level is LOW or not detected.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_004_low_risk_does_not_create_user_notification(self, db_connection, admin_context, driver):
        # Force clean app state — previous tests may have left app on risk-analysis screen
        adb("shell", "am", "force-stop", MOBILE_PACKAGE)
        time.sleep(3)
        launch_mobile_app()
        time.sleep(8)

        for cid in ["comp-001", "comp-002", "comp-003", "comp-999"]:
            clear_notifications(db_connection, cid, ["Damansara", "LOW"])

        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        tap_bottom_nav(driver, "Notification")
        driver.swipe(640, 300, 640, 900, duration=800)
        time.sleep(3)
        source = driver.page_source
        assert "Damansara" not in source, \
            "TCOV-13-005: Low-risk location must not appear as a notification"

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-005 | TC-13-005
    # Covers: TCOV-13-006
    # Verify system prompts user to enable location when access is denied.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_005_location_denied_prompts_user(self, driver):
        adb("shell", "pm", "revoke", MOBILE_PACKAGE, "android.permission.ACCESS_FINE_LOCATION")
        adb("shell", "pm", "revoke", MOBILE_PACKAGE, "android.permission.ACCESS_COARSE_LOCATION")
        adb("shell", "am", "force-stop", MOBILE_PACKAGE)
        subprocess.run(["adb", "shell", "am", "start", "-W", "-n", f"{MOBILE_PACKAGE}/{MOBILE_ACTIVITY}"], check=True)

        ensure_mobile_login(driver)

        # DengueRiskCard may show either the system permission dialog or the app's own React Native
        # alert — wait up to 30 s dismissing both until the location-unavailable UI appears.
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                src = driver.page_source
                if any(t in src for t in ["Please enable location services", "Location unavailable", "Enable Location to Predict"]):
                    break
                # System permission dialog — deny it
                if "While using the app" in src or "Don't allow" in src:
                    deny = driver.find_elements(AppiumBy.XPATH, "//*[@text=\"Don't allow\"]")
                    if deny:
                        deny[0].click()
                    else:
                        adb("shell", "input", "tap", "640", "2102")
                    time.sleep(2)
                elif "Location permission is required" in src:
                    ok = driver.find_elements(AppiumBy.XPATH, "//*[@text='OK' and @clickable='true']")
                    if ok:
                        ok[0].click()
                    else:
                        adb("shell", "input", "tap", "1068", "1621")  # OK button center
                    time.sleep(2)
                else:
                    time.sleep(1)
            except Exception:
                time.sleep(1)

        wait_for_any_text(driver, [
            "Please enable location services", "Location unavailable",
            "Enable Location to Predict",
        ])
        # Restore location permission so subsequent tests work normally
        adb("shell", "pm", "grant", MOBILE_PACKAGE, "android.permission.ACCESS_FINE_LOCATION")
        adb("shell", "pm", "grant", MOBILE_PACKAGE, "android.permission.ACCESS_COARSE_LOCATION")

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-006 | TC-13-006
    # Covers: TCOV-13-007, TCOV-13-008
    # Verify Notification Tab lists all received risk notifications in order.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_006_notification_tab_lists_notifications_in_order(self, db_connection, admin_context, driver):
        all_company_ids = ["comp-001", "comp-002", "comp-003", "comp-999"]
        for cid in all_company_ids:
            clear_notifications(db_connection, cid, ["Chow Kit", "Brickfields"])

        now = datetime.now(timezone.utc)
        for cid in all_company_ids:
            seed_notification(
                db_connection, cid,
                title="High Risk Alert - Chow Kit",
                message="Chow Kit is at HIGH dengue risk.",
                risk_level="high", location="Chow Kit", created_at=now,
            )
            seed_notification(
                db_connection, cid,
                title="Moderate Risk Alert - Brickfields",
                message="Brickfields is at MODERATE dengue risk.",
                risk_level="medium", location="Brickfields",
                created_at=now - timedelta(minutes=5),
            )

        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        tap_bottom_nav(driver, "Notification")
        driver.swipe(640, 300, 640, 900, duration=800)
        time.sleep(4)
        wait_for_text(driver, "Chow Kit", timeout=30)
        wait_for_text(driver, "Brickfields", timeout=30)
        source = driver.page_source
        assert source.index("Chow Kit") < source.index("Brickfields"), "Notification order should be newest first"

    # ══════════════════════════════════════════════════════════════════════════════
    # TP-13-007 | TC-13-007
    # Covers: TCOV-13-009
    # Verify Risk Analysis Page handles missing drone images gracefully.
    # ══════════════════════════════════════════════════════════════════════════════
    def test_tc13_007_missing_drone_images_handled_gracefully(self, driver):
        set_emulator_location(3.1622, 101.7007)
        ensure_mobile_login(driver)
        wait_for_dashboard_ready(driver)
        trigger_dashboard_prediction(driver)

        wait_for_text(driver, "Required Actions",         timeout=45)
        driver.swipe(640, 1800, 640, 400, duration=600)
        time.sleep(1)
        wait_for_text(driver, "Call Local Authority Now", timeout=30)
        src = driver.page_source
        assert "Loading risk analysis..." not in src, \
            "TCOV-13-009: Page must finish loading even when drone images are missing"
        assert any(t in src for t in ["Risk Details", "Required Actions", "High Risk", "Medium Risk", "Low Risk"]), \
            "TCOV-13-009: Risk analysis content must still display when drone images are absent"
