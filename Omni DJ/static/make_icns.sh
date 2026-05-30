#!/usr/bin/env bash
# Bouwt static/icon.icns uit de meegeleverde iconset.
# Draai dit op je Mac (iconutil is Mac-only) vanuit de map static/:
#   cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ/static"
#   ./make_icns.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
iconutil -c icns "Omni DJ.iconset" -o icon.icns
echo "Klaar: $HERE/icon.icns"
