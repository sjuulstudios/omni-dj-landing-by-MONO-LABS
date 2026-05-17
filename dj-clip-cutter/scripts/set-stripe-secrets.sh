#!/bin/bash
# Push Stripe-related secrets from local .env into Supabase Edge Functions.
#
# Run from project root (dj-clip-cutter):
#   bash scripts/set-stripe-secrets.sh
#
# Safe to re-run — Supabase overwrites existing secrets with the same name.

set -e

# Move to repo root so .env is found regardless of where the script is invoked.
cd "$(dirname "$0")/.."

if [ ! -f ".env" ]; then
  echo "ERROR: .env not found in $(pwd). Run this script from dj-clip-cutter or its scripts/ subfolder."
  exit 1
fi

# Load .env into the shell. set -a auto-exports every assigned var so the
# subsequent supabase invocation sees them via process env, not via interpolation.
set -a
# shellcheck disable=SC1091
source .env
set +a

# Sanity check — refuse to push empty values.
missing=()
for var in STRIPE_SECRET_KEY STRIPE_PRICE_ID_PRO STRIPE_PRICE_ID_STUDIO; do
  if [ -z "${!var}" ]; then
    missing+=("$var")
  fi
done
if [ ${#missing[@]} -ne 0 ]; then
  echo "ERROR: missing values in .env for: ${missing[*]}"
  exit 1
fi

# Optional: include STRIPE_WEBHOOK_SECRET only if it has been set in .env
# (after registering the webhook in Stripe dashboard). Otherwise skip — the
# function won't have a webhook secret yet and will reject events with a
# clean "Bad signature" error, which is what we want pre-config.
extra_args=()
if [ -n "$STRIPE_WEBHOOK_SECRET" ]; then
  extra_args+=("STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET")
fi

echo "Pushing Stripe secrets to Supabase…"
supabase secrets set \
  "STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY" \
  "STRIPE_PRICE_ID_PRO=$STRIPE_PRICE_ID_PRO" \
  "STRIPE_PRICE_ID_STUDIO=$STRIPE_PRICE_ID_STUDIO" \
  "${extra_args[@]}"

echo ""
echo "Done. Verify with: supabase secrets list"
