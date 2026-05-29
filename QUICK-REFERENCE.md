# Omni DJ — Quick Reference

Keep this open. Two terminal rules and the four commands you actually need.

---

## Two terminal rules

1. **Wrap paths with spaces in double quotes.** "Omni DJ" has a space, so the path always needs quotes:
   `"/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"`
   Without quotes the shell splits on the space and breaks.

2. **Never paste markdown code fences (` ``` `) into the terminal.** Only copy the command on the line between the fences. Pasting ` ```bash ` leaves you stuck at a `>` prompt.

---

## Start the app

Open Terminal. Run these one at a time:

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"

./start.sh

Then open in your browser:

http://127.0.0.1:5555

---

## Stop the app

In the terminal window where it's running, press **Ctrl+C**.

---

## View the redesign mockup

open "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/clip-live-redesign.html"

---

## When something is broken

**Port 5555 already in use:**

lsof -i :5555

kill -9 <PID>

**Reset the venv from scratch (last resort):**

cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter"

rm -rf venv

./start.sh

**Full install guide:** `INSTALL.md` in this same folder.

---

## Key facts

| Thing | Value |
|------|------|
| App folder | `/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/dj-clip-cutter` |
| Start command | `./start.sh` |
| URL | http://127.0.0.1:5555 |
| Stop | Ctrl+C |
| Mockup | `clip-live-redesign.html` (in `Omni DJ/` folder) |
| Install guide | `INSTALL.md` (in `Omni DJ/` folder) |
