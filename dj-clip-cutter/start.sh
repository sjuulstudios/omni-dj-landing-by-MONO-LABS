#!/bin/bash
# DJ Clip Cutter v2 — Launcher script
# Run this from Terminal: ./start.sh

set -e

cd "$(dirname "$0")"

echo ""
echo "=============================================="
echo "  DJ Clip Cutter v2 — Bar-Aware Detection"
echo "=============================================="
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: FFmpeg is not installed."
    echo "Install it with: brew install ffmpeg"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment (first time only)..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo ""
    echo "Setup complete!"
    echo ""
    echo "=============================================="
    echo "  Optional add-ons:"
    echo ""
    echo "  AI Detection (Demucs):"
    echo "    pip install torch demucs"
    echo ""
    echo "  YouTube upload:"
    echo "    pip install google-api-python-client google-auth-oauthlib"
    echo "=============================================="
    echo ""
else
    source venv/bin/activate
fi

# Start the server
python3 app.py 5555
