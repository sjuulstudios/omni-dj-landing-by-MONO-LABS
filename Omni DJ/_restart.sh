#!/bin/bash
# SESSIE 16 — temporary restart helper used by Claude in Chrome / osascript
# bridge. Sets PATH (osascript shell ships a minimal one) and re-launches
# the Flask server detached so the parent shell can return immediately.
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
cd "$(dirname "$0")"
# Kill any stale instance so we don't end up with two copies fighting on 5555.
# SESSIE 18 — pkill -f was case-sensitive and didn't match the "Python app.py"
# command-line that macOS's launchd starts (capital P from the framework
# binary). Use the case-insensitive flag so both spellings die. Fallback:
# kill anything listening on 5555 if pkill misses.
pkill -if "python.*app\\.py 5555" 2>/dev/null || true
sleep 1
# Belt-and-braces: blow away anything still bound to the port.
PID_ON_PORT=$(lsof -ti :5555 2>/dev/null || true)
if [ -n "$PID_ON_PORT" ]; then
  kill -9 $PID_ON_PORT 2>/dev/null || true
  sleep 1
fi
source venv/bin/activate
nohup python3 app.py 5555 > /tmp/omnidj_restart.log 2>&1 &
disown
echo "started pid=$!"
