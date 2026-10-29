#!/usr/bin/env bash
# Take a full-window screenshot of a URL with a separate headless Chrome profile.
# Usage: screenshot.sh <url> <out.png> [width=1440] [height=900]
set -euo pipefail

url="${1:?usage: screenshot.sh <url> <out.png> [width] [height]}"
out="${2:?usage: screenshot.sh <url> <out.png> [width] [height]}"
width="${3:-1440}"
height="${4:-900}"

chrome=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "$(command -v google-chrome 2>/dev/null || true)" \
  "$(command -v chromium 2>/dev/null || true)" \
  "$(command -v chromium-browser 2>/dev/null || true)"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ]; then chrome="$candidate"; break; fi
done
[ -n "$chrome" ] || { echo "Chrome/Chromium not found" >&2; exit 1; }

# Own throwaway profile, so this never touches the user's browser session
profile="$(mktemp -d)"
trap 'rm -rf "$profile"' EXIT

mkdir -p "$(dirname "$out")"
echo "Capturing $url at ${width}x${height} -> $out"
# virtual-time-budget lets the SPA fetch data and render before the capture
"$chrome" --headless=new --disable-gpu --hide-scrollbars \
  --user-data-dir="$profile" \
  --window-size="${width},${height}" \
  --virtual-time-budget=5000 \
  --screenshot="$out" "$url" >/dev/null 2>&1
[ -s "$out" ] && echo "Saved $out" || { echo "Screenshot failed" >&2; exit 1; }
