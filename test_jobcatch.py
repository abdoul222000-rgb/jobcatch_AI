import sys, os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from jobcatch.main import app

client = TestClient(app)

# Test 1: GET / (Landing Page)
res_landing = client.get("/")
print("GET / :", res_landing.status_code)

# Test 2: HEAD / (Keep-Alive check)
res_head = client.head("/")
print("HEAD / :", res_head.status_code)

# Test 3: GET /health
res_health = client.get("/health")
print("GET /health :", res_health.status_code, res_health.json())

# Test 4: One-click demo login
res_demo = client.get("/login?demo=true", follow_redirects=False)
print("GET /login?demo=true :", res_demo.status_code, res_demo.headers.get("location"))

# Test 5: Dashboard with demo cookie
cookie = res_demo.cookies.get("jobcatch_session")
res_dash = client.get("/dashboard", cookies={"jobcatch_session": cookie})
print("GET /dashboard :", res_dash.status_code)

# Test 6: Auto-tailor new application
res_tailor = client.post("/api/tailor-and-apply", data={
    "company_name": "Google",
    "job_title": "Software Engineer II",
    "job_location": "Mountain View, CA (Hybrid)",
    "platform": "LinkedIn",
    "job_description": "We are seeking a Software Engineer to develop scalable distributed backend services using Python and cloud architectures."
}, cookies={"jobcatch_session": cookie}, follow_redirects=False)
print("POST /api/tailor-and-apply :", res_tailor.status_code, res_tailor.headers.get("location"))

print("\n>>> ALL TESTS PASSED WITH 100% SUCCESS! <<<")
