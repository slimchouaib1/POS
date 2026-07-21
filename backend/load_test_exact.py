import urllib.request
import urllib.error
import json
import os
import time
import concurrent.futures
from statistics import mean

BASE_URL = "http://localhost:8000"
CONCURRENT_USERS = 10
REQUESTS_PER_USER = 5
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
    return status, duration

def test_scenario(scenario_name, endpoints, token):
    results = []
    
    def user_session():
        session_results = []
        for _ in range(REQUESTS_PER_USER):
            for ep in endpoints:
                st, dur = make_request(ep, token)
                session_results.append((st, dur))
        return session_results

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(user_session) for _ in range(CONCURRENT_USERS)]
        for future in concurrent.futures.as_completed(futures):
            results.extend(future.result())
            
    total_time = time.time() - start_time
    
    success = sum(1 for st, dur in results if 200 <= st < 400)
    errors = sum(1 for st, dur in results if st >= 400 or st == 0)
    total = success + errors
    error_rate = (errors / total * 100) if total > 0 else 0
    avg_time = mean(dur for st, dur in results) if results else 0
    
    return {
        "Scenario": scenario_name,
        "Endpoints": ", ".join(endpoints),
        "AvgTime": avg_time,
        "ErrorRate": error_rate,
        "Total": total,
        "Success": success,
        "Errors": errors
    }

def main():
    print("Obtaining token...")
    token = get_token()
    if not token:
        print("Could not obtain auth token!")
        return

    scenarios = [
        {
            "name": "Authentication and dashboard access",
            "endpoints": ["/api/auth/me", "/api/reports/dashboard"]
        },
        {
            "name": "POS operational workflow",
            "endpoints": ["/api/products", "/api/orders"]
        },
        {
            "name": "Stock and reporting access",
            "endpoints": ["/api/reports/sales", "/api/reports/products"]
        },
        {
            "name": "AI recommendation endpoint",
            "endpoints": ["/api/ai/recommendations/summary"]
        },
        {
            "name": "AI forecasting endpoint",
            "endpoints": ["/api/ai/forecasting/next-week"]
        },
        {
            "name": "AI anomaly detection endpoint",
            "endpoints": ["/api/ai/anomaly/alerts"]
        },
        {
            "name": "AI segmentation endpoint",
            "endpoints": ["/api/ai/segmentation/overview"]
        }
    ]

    print("Running scenarios...")
    results = []
    for sc in scenarios:
        res = test_scenario(sc["name"], sc["endpoints"], token)
        results.append(res)
        print(f"Completed: {sc['name']}")

    print("\n\n--- RESULTS TABLE ---")
    print(f"{'Test Scenario':<40} | {'Tested Endpoints':<45} | {'Average Response Time':<25} | {'Error Rate':<15}")
    print("-" * 135)
    for r in results:
        print(f"{r['Scenario']:<40} | {r['Endpoints']:<45} | {r['AvgTime']*1000:<20.2f} ms | {r['ErrorRate']:.2f}%")

if __name__ == '__main__':
    main()
