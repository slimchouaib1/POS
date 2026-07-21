import os

import requests

BASE = "http://localhost:8000"
ADMIN_PASSWORD = os.environ.get("POS_TEST_ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise RuntimeError("POS_TEST_ADMIN_PASSWORD is required")

# 1. Login
resp = requests.post(f"{BASE}/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD})
assert resp.status_code == 200, f"Login failed: {resp.text}"
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login: OK")

# 2. Products
resp = requests.get(f"{BASE}/api/products/", headers=headers)
assert resp.status_code == 200, f"Products failed: {resp.text}"
products = resp.json()
print(f"Products: {len(products)} items")

# 3. Users
resp = requests.get(f"{BASE}/api/users/", headers=headers)
assert resp.status_code == 200, f"Users failed: {resp.text}"
users = resp.json()
print(f"Users: {len(users)} items")

# 4. Customers
resp = requests.get(f"{BASE}/api/customers/", headers=headers)
assert resp.status_code == 200, f"Customers failed: {resp.text}"
customers = resp.json()
print(f"Customers: {len(customers)} items")

# 5. Orders
resp = requests.get(f"{BASE}/api/orders/", headers=headers)
assert resp.status_code == 200, f"Orders failed: {resp.text}"
orders = resp.json()
print(f"Orders: {len(orders)} items")

print("\nAll API endpoints verified successfully with PostgreSQL!")
