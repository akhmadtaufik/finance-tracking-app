import requests
import sys
import time

# Wait for server to be ready
time.sleep(2)

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin_test@example.com"
DEFAULT_PASS = "T3stP@ssw0rd"
NEW_PASS = "TempSecure@456"


def log(msg):
    print(f"[TEST] {msg}")


def login(email, password):
    resp = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return resp


def run_test():
    log("1. Initial Login with Default Credentials...")
    resp = login(ADMIN_EMAIL, DEFAULT_PASS)
    if resp.status_code != 200:
        log(f"❌ FAIL: Initial login failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("✅ Initial Login Success.")

    log("2. Changing Password to New Value...")
    payload = {"current_password": DEFAULT_PASS, "new_password": NEW_PASS}
    resp = requests.put(f"{BASE_URL}/users/password", json=payload, headers=headers)
    if resp.status_code != 200:
        log(f"❌ FAIL: Update API failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)
    log("✅ Password Update API Success.")

    log("3. Verifying OLD Password (Should Fail)...")
    resp = login(ADMIN_EMAIL, DEFAULT_PASS)
    if resp.status_code != 401:
        log(f"❌ FAIL: Old password still works! Status: {resp.status_code}")
        sys.exit(1)
    log("✅ Old Password correctly rejected.")

    log("4. Verifying NEW Password (Should Succeed)...")
    resp = login(ADMIN_EMAIL, NEW_PASS)
    if resp.status_code != 200:
        log(f"❌ FAIL: New password login failed. Status: {resp.status_code}")
        log(f"   Response: {resp.text}")
        sys.exit(1)

    new_token = resp.json()["access_token"]
    log("✅ New Password Login Success.")

    log("5. Cleaning Up (Revert to Original)...")
    revert_headers = {"Authorization": f"Bearer {new_token}"}
    revert_payload = {"current_password": NEW_PASS, "new_password": DEFAULT_PASS}
    resp = requests.put(
        f"{BASE_URL}/users/password", json=revert_payload, headers=revert_headers
    )
    if resp.status_code != 200:
        log(f"⚠️  Warning: Revert failed. Status: {resp.status_code}")
    else:
        log("✅ Password reverted to original.")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
