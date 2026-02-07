"""
Integration test for Forgot Password flow.
Flow: Register new user -> Forgot password -> Reset password.
"""

import sys
import time

import requests
import urllib3

# Suppress SSL warnings for local testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Wait for server to be ready
time.sleep(5)

# When running via frontend (nginx proxy)
# Nginx proxies /api/* to backend:8000/*
# Use HTTPS directly to avoid HTTP->HTTPS redirect issue
BASE_URL = "https://localhost/api"
TEST_EMAIL = "sataho6081@codgal.com"
TEST_USERNAME = "testuser_forgot"
OLD_PASSWORD = "T3stp@ssw0rd"
NEW_PASSWORD = "NewSecure@123"


def log(msg):
    print(f"[TEST] {msg}")


def register(email, username, password):
    """Register a new user."""
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "username": username, "password": password},
        verify=False,
    )
    return resp


def login(email, password):
    """Login and get token."""
    resp = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=False,
    )
    return resp


def run_test():
    log("=== FORGOT PASSWORD FLOW TEST ===\n")

    # Step 0: Register a new user for testing
    log("0. Registering test user...")
    resp = register(TEST_EMAIL, TEST_USERNAME, OLD_PASSWORD)
    if resp.status_code == 201:
        log("✅ Test user registered successfully")
    elif resp.status_code == 400 and "already" in resp.text.lower():
        log("ℹ️  Test user already exists, continuing...")
    else:
        log(f"⚠️  Registration response: {resp.status_code} - {resp.text}")

    # Step 1: Test forgot password endpoint
    log("\n1. Testing forgot-password endpoint...")
    resp = requests.post(
        f"{BASE_URL}/auth/forgot-password", json={"email": TEST_EMAIL}, verify=False
    )
    if resp.status_code != 200:
        log(f"❌ FAIL: Forgot password failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)
    log("✅ Forgot password request accepted")
    try:
        log(f"   Response: {resp.json().get('message', resp.text)}")
    except Exception:
        log(f"   Response: {resp.text[:100]}")

    # Step 2: Generate token locally (simulating email)
    log("\n2. Simulating token from email (generating locally)...")
    from jose import jwt
    from datetime import datetime, timedelta, timezone

    SECRET_KEY = "super-secure-key-with-at-least-32-chars!!"
    ALGORITHM = "HS256"

    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_data = {"sub": TEST_EMAIL, "exp": expire, "type": "password-reset"}
    simulated_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    log(f"✅ Token generated: {simulated_token[:50]}...")

    # Step 3: Test reset password with valid token
    log("\n3. Testing reset-password endpoint with token...")
    resp = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json={"token": simulated_token, "new_password": NEW_PASSWORD},
        verify=False,
    )
    if resp.status_code != 200:
        log(f"❌ FAIL: Reset password failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)
    log("✅ Password reset successful")

    # Step 4: Verify new password works
    log("\n4. Verifying login with NEW password...")
    resp = login(TEST_EMAIL, NEW_PASSWORD)
    if resp.status_code != 200:
        log(f"❌ FAIL: Login with new password failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)
    log("✅ Login with new password successful")

    # Step 5: Verify old password no longer works
    log("\n5. Verifying OLD password is rejected...")
    resp = login(TEST_EMAIL, OLD_PASSWORD)
    if resp.status_code != 401:
        log(f"❌ FAIL: Old password still works! Status: {resp.status_code}")
        sys.exit(1)
    log("✅ Old password correctly rejected")

    # Step 6: Cleanup - revert password to original
    log("\n6. Cleanup: Reverting to original password...")
    token_data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=15)
    cleanup_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    resp = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json={"token": cleanup_token, "new_password": OLD_PASSWORD},
        verify=False,
    )
    if resp.status_code == 200:
        log(f"✅ Password reverted to: {OLD_PASSWORD}")
    else:
        log(f"⚠️  Revert failed: {resp.text}")

    print("\n" + "=" * 40)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 40)


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
