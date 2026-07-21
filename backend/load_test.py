import urllib.request
import urllib.error
import json
import os
import time
import concurrent.futures
from statistics import mean

BASE_URL = "http://localhost:8000"
CONCURRENT_USERS = 10
REQUESTS_PER_USER = 5  # Adjusted for quick execution
ADMIN_PASSWORD = os.environ.get("POS_TEST_ADMIN_PASSWORD")

def get_token():
    if not ADMIN_PASSWORD:
        raise RuntimeError("POS_TEST_ADMIN_PASSWORD is required")
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=json.dumps({"username": "admin", "password": ADMIN_PASSWORD}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["access_token"]
    except Exception as e:
        print(f"Failed to login: {e}")
        return None

def make_request(endpoint, token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    req = urllib.request.Request(f"{BASE_URL}{endpoint}", headers=headers)
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            response.read()
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        status = 0
    duration = time.time() - start_time
    return endpoint, status, duration

def user_session(user_id, token, endpoints):
    results = []
    for _ in range(REQUESTS_PER_USER):
        for endpoint in endpoints:
            results.append(make_request(endpoint, token))
    return results

def main():
    print(f"--- Starting Load Test ---")
    print(f"Concurrent Users: {CONCURRENT_USERS}")
    print(f"Requests per user per endpoint: {REQUESTS_PER_USER}")
    
    token = get_token()
    if not token:
        print("Aborting. Could not obtain auth token. Ensure the backend is running.")
        return

    endpoints = [
        "/api/health",
        "/api/ai/segmentation/overview",
        "/api/ai/recommendations/summary",
        "/api/ai/anomaly/alerts",
        "/api/products"
    ]
    
    print(f"Testing endpoints: {endpoints}")
    
    start_time = time.time()
    all_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(user_session, i, token, endpoints) for i in range(CONCURRENT_USERS)]
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())
            
    total_time = time.time() - start_time
    
    # Analyze
    stats = {}
    for ep, status, duration in all_results:
        if ep not in stats:
            stats[ep] = {"times": [], "success": 0, "errors": 0}
        stats[ep]["times"].append(duration)
        if 200 <= status < 400:
            stats[ep]["success"] += 1
        else:
            stats[ep]["errors"] += 1
            
    print("\n--- Results ---")
    print(f"{'Endpoint':<35} | {'Avg Time (s)':<12} | {'Success':<8} | {'Errors':<8} | {'Error Rate'}")
    print("-" * 85)
    for ep, data in stats.items():
        avg_time = mean(data["times"]) if data["times"] else 0
        total = data["success"] + data["errors"]
        error_rate = (data["errors"] / total * 100) if total > 0 else 0
        print(f"{ep:<35} | {avg_time:<12.4f} | {data['success']:<8} | {data['errors']:<8} | {error_rate:.2f}%")
        
    print(f"\nTotal Requests: {len(all_results)}")
    print(f"Total Time Elapsed: {total_time:.2f}s")
    print(f"Requests per second: {len(all_results) / total_time:.2f}")

if __name__ == '__main__':
    main()
