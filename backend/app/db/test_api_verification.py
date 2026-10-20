import urllib.request
import json

# Login demo user
login_data = json.dumps({"email": "demo_user@cardwise.local", "password": "Password123!"}).encode("utf-8")
req = urllib.request.Request("http://127.0.0.1:8085/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    token_data = json.loads(resp.read().decode())
    token = token_data["access_token"]

headers = {"Authorization": f"Bearer {token}"}

# Get cards
cards_req = urllib.request.Request("http://127.0.0.1:8085/api/v1/cards", headers=headers)
with urllib.request.urlopen(cards_req) as resp:
    cards = json.loads(resp.read().decode())

print(f"API returned {len(cards)} cards:")
for idx, c in enumerate(cards, 1):
    print(f"  {idx}. {c['issuer']} | {c['variant']} | {c['masked_number']} | Category: {c.get('category')} | Limit: {c.get('credit_limit')} | Status: {c.get('verification_status')}")

# Get statements
stmts_req = urllib.request.Request("http://127.0.0.1:8085/api/v1/statements", headers=headers)
with urllib.request.urlopen(stmts_req) as resp:
    stmts = json.loads(resp.read().decode())

print(f"\nAPI returned {len(stmts)} statements:")
for s in stmts:
    print(f"  - {s.get('card_issuer')} {s.get('card_name')} ({s.get('masked_number')}) | Due: {s.get('payment_due_date')} | Balance: {s.get('total_balance')} | Min: {s.get('minimum_due')} | CreditBal: {s.get('is_credit_balance')}")

# Get dashboard summary
dash_req = urllib.request.Request("http://127.0.0.1:8085/api/v1/dashboard/summary", headers=headers)
with urllib.request.urlopen(dash_req) as resp:
    summary = json.loads(resp.read().decode())

print("\nDashboard Summary:")
print(json.dumps(summary, indent=2))
