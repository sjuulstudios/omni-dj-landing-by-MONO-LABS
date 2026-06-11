#!/bin/bash
# tests/run_mid_upgrade_test.sh
# SESSIE 83 - runner voor de mid-analysis-upgrade E2E-test.
#
# Gebruik (vanuit de app-map "Omni DJ/Omni DJ"):
#   OMNI_TEST_EMAIL=... OMNI_TEST_PASSWORD=... OMNI_TEST_SET="/pad/naar/korte_set.mp4" \
#     bash tests/run_mid_upgrade_test.sh
#
# Vereist: dev-server draait op 127.0.0.1:5599 (na herstart met de nieuwe
# app.py: bash _dev_restart_5599.sh) en migratie 012 + edge function staan live.

set -e
cd "$(dirname "$0")/.."

if [ -z "$OMNI_TEST_EMAIL" ] || [ -z "$OMNI_TEST_PASSWORD" ] || [ -z "$OMNI_TEST_SET" ]; then
  echo "Zet eerst OMNI_TEST_EMAIL, OMNI_TEST_PASSWORD en OMNI_TEST_SET (pad naar een korte testset)."
  exit 1
fi

PY="python3"
if [ -x "venv/bin/python3" ]; then
  PY="venv/bin/python3"
fi

"$PY" tests/test_mid_analysis_upgrade.py
