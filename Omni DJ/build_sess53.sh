#!/bin/bash
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
cd "/Users/sjuulsmits/Documents/Claude/Projects/Omni DJ/Omni DJ"
source venv/bin/activate
exec ./build_macos.sh dmg
