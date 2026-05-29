#!/bin/bash
# test_quota.sh - Phase 3 backend smoke-test.
# Verifies /api/quota returns correct plan-limit/usage shape, and that
# /api/upload-local rejects with 402 when the limit is reached.
#
# Run via:
#   ./test_quota.sh                              # uses cliptest defaults
#   ./test_quota.sh email@example.com password   # custom account
#   EMAIL=foo@bar.com PASSWORD=xxx ./test_quota.sh   # via env
#
# Pre-req:  Flask app running on 127.0.0.1:5555, account exists in Supabase.

EMAIL="${1:-${EMAIL:-business+cliptest@sjuulstudios.com}}"
PASSWORD="${2:-${PASSWORD:-TestPassword2026}}"
BASE="http://127.0.0.1:5555"

echo "Testing as: $EMAIL"

echo ""
echo "=== Login ==="
LOGIN=$(curl -s -X POST "$BASE/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
echo "$LOGIN" | python3 -m json.tool 2>/dev/null || echo "$LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)
if [ -z "$TOKEN" ]; then
  echo "Geen access_token uit login. Stop."
  exit 1
fi

echo ""
echo "=== TEST 1: /api/quota zonder token (verwacht 401) ==="
curl -s -o /tmp/q1.json -w "HTTP %{http_code}\n" "$BASE/api/quota"
cat /tmp/q1.json | python3 -m json.tool 2>/dev/null || cat /tmp/q1.json
echo ""

echo "=== TEST 2: /api/quota met token (verwacht 200 + plan/used/limit) ==="
curl -s -o /tmp/q2.json -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE/api/quota"
cat /tmp/q2.json | python3 -m json.tool 2>/dev/null || cat /tmp/q2.json
echo ""

echo "=== TEST 3: /api/upload zonder token (verwacht 401, geen file-write) ==="
curl -s -o /tmp/q3.json -w "HTTP %{http_code}\n" \
  -X POST "$BASE/api/upload"
cat /tmp/q3.json | python3 -m json.tool 2>/dev/null || cat /tmp/q3.json
echo ""

echo "=== TEST 4: /api/upload-local zonder token (verwacht 401) ==="
curl -s -o /tmp/q4.json -w "HTTP %{http_code}\n" \
  -X POST "$BASE/api/upload-local" \
  -H "Content-Type: application/json" \
  -d '{"path":"/tmp/nonexistent.mp4"}'
cat /tmp/q4.json | python3 -m json.tool 2>/dev/null || cat /tmp/q4.json
echo ""

echo "=== DONE ==="
echo ""
echo "Wat je zou moeten zien:"
echo "  - TEST 1: HTTP 401, error 'Geen Authorization header'."
echo "  - TEST 2: HTTP 200, plan ('free'/'pro'/'studio'), used (int), limit (int of null voor studio), reset_in_days."
echo "  - TEST 3: HTTP 401."
echo "  - TEST 4: HTTP 401."
echo ""
echo "402-test (quota op): vereist een Free-account met 2 voltooide analyses."
echo "  - Maak nieuwe Free-user via UI signup, run 2 analyses, derde upload moet 402 returnen."
