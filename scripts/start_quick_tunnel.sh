#!/usr/bin/env bash
# Expose a locally running Life Switch server through a temporary Cloudflare URL.
# The URL is printed by cloudflared and expires when this process stops.

set -euo pipefail

PORT="${1:-8000}"

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared is not installed. Install it, then run this script again." >&2
  exit 1
fi

echo "Creating a Cloudflare Quick Tunnel for http://127.0.0.1:${PORT}"
echo "Copy the https://*.trycloudflare.com URL below to your phone."
exec cloudflared tunnel --url "http://127.0.0.1:${PORT}"
