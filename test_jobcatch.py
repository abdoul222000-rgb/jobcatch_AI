import sys, os
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from jobcatch.main import app

client = TestClient(app)

# Test 1: GET / (Landing Page)
res_landing = client.get("/")
print("GET / :", res_landing.status_code)
assert res_landing.status_code == 200

# Test 2: HEAD / (Keep-Alive check)
res_head = client.head("/")
print("HEAD / :", res_head.status_code)
assert res_head.status_code == 200

# Test 3: GET /health
res_health = client.get("/health")
print("GET /health :", res_health.status_code, res_health.json())
assert res_health.status_code == 200

# Test 4: One-click demo login
res_demo = client.get("/login?demo=true", follow_redirects=False)
print("GET /login?demo=true :", res_demo.status_code, res_demo.headers.get("location"))
assert res_demo.status_code == 303

# Test 5: Dashboard with demo cookie
demo_cookie = res_demo.cookies.get("jobcatch_session")
res_dash = client.get("/dashboard", cookies={"jobcatch_session": demo_cookie})
print("GET /dashboard :", res_dash.status_code)
assert res_dash.status_code == 200

# Test 6: Auto-tailor new application
res_tailor = client.post("/api/tailor-and-apply", data={
    "company_name": "Google",
    "job_title": "Software Engineer II",
    "job_location": "Mountain View, CA (Hybrid)",
    "platform": "LinkedIn",
    "job_description": "We are seeking a Software Engineer to develop scalable distributed backend services using Python and cloud architectures."
}, cookies={"jobcatch_session": demo_cookie}, follow_redirects=False)
print("POST /api/tailor-and-apply :", res_tailor.status_code, res_tailor.headers.get("location"))
assert res_tailor.status_code == 303

# Test 7: Register with Credit Card Upfront ($0 today, 3-day trial)
res_reg = client.post("/register", data={
    "full_name": "Jordan Smith",
    "email": "jordan.smith.us@example.com",
    "password": "securepassword2026",
    "target_role": "Backend Engineer",
    "cardholder_name": "Jordan Smith",
    "card_number": "4242 4242 4242 1234",
    "card_exp": "08/29",
    "card_cvc": "999",
    "card_zip": "94107"
}, follow_redirects=False)
print("POST /register (Card Upfront) :", res_reg.status_code, res_reg.headers.get("location"))
assert res_reg.status_code == 303

jordan_cookie = res_reg.cookies.get("jobcatch_session")

# Test 8: Billing Page displays card on file
res_billing = client.get("/billing", cookies={"jobcatch_session": jordan_cookie})
print("GET /billing :", res_billing.status_code)
assert res_billing.status_code == 200
assert "1234" in res_billing.text
assert "Visa" in res_billing.text

# Test 9: 1-Click Subscription Cancellation (Card never debited)
res_cancel = client.post("/api/subscription/cancel", cookies={"jobcatch_session": jordan_cookie}, follow_redirects=False)
print("POST /api/subscription/cancel :", res_cancel.status_code)
assert res_cancel.status_code == 303

res_billing_cancelled = client.get("/billing", cookies={"jobcatch_session": jordan_cookie})
assert "Subscription Cancelled" in res_billing_cancelled.text

# Test 10: 1-Click Subscription Reactivation
res_reactivate = client.post("/api/subscription/reactivate", cookies={"jobcatch_session": jordan_cookie}, follow_redirects=False)
print("POST /api/subscription/reactivate :", res_reactivate.status_code)
assert res_reactivate.status_code == 303

# Test 11: Automated Day 4 Rebill Cron Job ($39.00 auto-debit)
res_rebills = client.post("/api/cron/process-rebills")
print("POST /api/cron/process-rebills :", res_rebills.status_code, res_rebills.json())
assert res_rebills.status_code == 200

print("\n>>> ALL 11 TESTS PASSED WITH 100% SUCCESS! <<<")
