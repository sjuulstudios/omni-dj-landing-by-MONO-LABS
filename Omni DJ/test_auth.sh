#!/bin/bash
# test_auth.sh - tests signup -> login -> me endpoints end-to-end
# Run via: ./test_auth.sh

EMAIL="business+cliptest@sjuulstudios.com"
PASSWORD="TestPassword2026"
BASE="http://127.0.0.1:5555"

echo ""
echo "=== TEST 1: signup ==="
SIGNUP=$(curl -s -X POST "$BASE/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
echo "$SIGNUP" | python3 -m json.tool 2>/dev/null || echo "$SIGNUP"
echo ""

echo "=== TEST 2: login ==="
LOGIN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
echo "$LOGIN" | python3 -m json.tool 2>/dev/null || echo "$LOGIN"
echo ""

TOKEN=$(echo "$LOGIN" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "Geen access_token uit login - kan /api/auth/me niet testen."
  exit 1
fi

echo "=== TEST 3: GET /api/auth/me (met token) ==="
curl -s -X GET "$BASE/api/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool 2>/dev/null || echo "(no JSON)"
echo ""

echo "=== DONE ==="
echo ""
echo "Wat je hier zou moeten zien:"
echo "  - Test 1: ok=true bij eerste run (user wordt aangemaakt). Bij 2e run: ok=false met 'already registered' - dat is OK."
echo "  - Test 2: ok=true met access_token, refresh_token, user_id, email."
echo "  - Test 3: ok=true met email + profile{plan: 'free', usage_this_period: 0, signup_date, quota_reset_date}."
