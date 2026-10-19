#!/usr/bin/env bash
# One-time setup. Usage: bash setup.sh [work_dir]
#   work_dir (default ./motion) gets clips/ dist/ out/ work/ inputs/ and Playwright + Chromium in node_modules.
#   A Python venv with numpy + faster-whisper (local speech-to-text) goes in
#   ~/Library/Application Support/kb-ytvideo/venv (override with KB_YTVIDEO_VENV). Scripts that need it are run with $PY.
set -e
WORK="${1:-./motion}"
VENV="${KB_YTVIDEO_VENV:-$HOME/Library/Application Support/kb-ytvideo/venv}"
mkdir -p "$WORK"/{clips,dist,out,work,inputs}
missing=()
command -v node >/dev/null || missing+=("node (https://nodejs.org)")
command -v ffmpeg >/dev/null || missing+=("ffmpeg (macOS: brew install ffmpeg)")
if [ ${#missing[@]} -gt 0 ]; then echo "Missing: ${missing[*]}"; exit 1; fi
# faster-whisper needs a Python that ctranslate2 ships wheels for; prefer 3.12/3.13 when present.
if [ ! -x "$VENV/bin/python" ]; then
  PYBIN=""
  for c in python3.12 python3.13 python3.11 python3; do command -v "$c" >/dev/null && { PYBIN="$c"; break; }; done
  [ -z "$PYBIN" ] && { echo "Missing: python3"; exit 1; }
  mkdir -p "$(dirname "$VENV")"; "$PYBIN" -m venv "$VENV"
fi
"$VENV/bin/python" -c "import numpy, faster_whisper" 2>/dev/null || "$VENV/bin/pip" install --quiet --upgrade pip numpy faster-whisper
if [ ! -d "$WORK/node_modules/playwright" ]; then
  [ -f "$WORK/package.json" ] || echo '{"private":true}' > "$WORK/package.json"
  (cd "$WORK" && npm install --silent playwright && npx playwright install chromium)
fi
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q prores_ks || echo "Note: ffmpeg has no prores_ks encoder; transparent clips (.mov) will fail."
echo "Ready."
echo "  WORK=$(cd "$WORK" && pwd)"
echo "  PY=$VENV/bin/python"
echo "  NODE_PATH=$(cd "$WORK" && pwd)/node_modules"
