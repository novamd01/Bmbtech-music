#!/usr/bin/env python3
"""
Musicanaz — ENV URL Patcher
============================
Replaces every hardcoded URL in the project with the appropriate
process.env / NEXT_PUBLIC_ environment variable, and generates
.env.example + .env.local with sensible defaults.

Usage:
    python env_url_patcher.py [project_root]

If project_root is omitted it defaults to the current working directory.
The script is idempotent — running it twice will not double-wrap vars.
"""

import os
import sys
import re

# ── Colour helpers ────────────────────────────────────────────────────────────
def green(s):  return f"\033[92m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def red(s):    return f"\033[91m{s}\033[0m"
def bold(s):   return f"\033[1m{s}\033[0m"

# ── Resolve project root ──────────────────────────────────────────────────────
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
print(bold(f"\n🎵  Musicanaz ENV URL Patcher"))
print(f"   Project root: {ROOT}\n")

# ── Patch registry ────────────────────────────────────────────────────────────
# Each entry: (relative_file_path, old_string, new_string, description)
PATCHES = []

# ─────────────────────────────────────────────────────────────────────────────
# 1.  MUSIVA / TURBO backend  (server-side API routes → MUSIVA_API_URL)
# ─────────────────────────────────────────────────────────────────────────────
MUSIVA_FILES_BASE = [
    "app/api/musiva/artist-albums/route.ts",
    "app/api/musiva/artist-songs/route.ts",
    "app/api/musiva/artist/route.ts",
    "app/api/musiva/album/route.ts",
    "app/api/musiva/explore/route.ts",
    "app/api/musiva/home/route.ts",
    "app/api/musiva/lyrics-by-video/route.ts",
    "app/api/musiva/mood/route.ts",
    "app/api/musiva/now-playing/route.ts",
    "app/api/musiva/play/[videoId]/route.ts",
    "app/api/musiva/playlist/route.ts",
    "app/api/musiva/podcast/route.ts",
    "app/api/musiva/related-songs/route.ts",
    "app/api/musiva/search/route.ts",
    "app/api/musiva/suggestions/route.ts",
    "app/api/musiva/top-playlists/route.ts",
    "app/api/musiva/upnext/route.ts",
    "app/api/trending/route.ts",
]

for f in MUSIVA_FILES_BASE:
    # handles both `const BASE =` and `const BASE     =` (extra spaces in mood route)
    PATCHES.append((
        f,
        re.compile(r'const BASE\s*=\s*"https://turbo-14uz\.onrender\.com"'),
        'const BASE = process.env.MUSIVA_API_URL || "https://turbo-14uz.onrender.com"',
        "Replace hardcoded MUSIVA BASE URL with env var",
    ))

# Files that used BASE_URL instead of BASE
MUSIVA_FILES_BASE_URL = [
    "app/api/musiva/stream/[videoId]/route.ts",
    "app/api/musiva/song/route.ts",
    "app/api/musiva/video/search/route.ts",
]
for f in MUSIVA_FILES_BASE_URL:
    PATCHES.append((
        f,
        re.compile(r'const BASE_URL\s*=\s*"https://turbo-14uz\.onrender\.com"'),
        'const BASE_URL = process.env.MUSIVA_API_URL || "https://turbo-14uz.onrender.com"',
        "Replace hardcoded MUSIVA BASE_URL with env var",
    ))

# ─────────────────────────────────────────────────────────────────────────────
# 2.  DEEZER CHART  (server-side → DEEZER_CHART_URL)
# ─────────────────────────────────────────────────────────────────────────────
PATCHES.append((
    "app/api/musiva/trending/route.ts",
    re.compile(r'const DEEZER_CHART\s*=\s*"https://api\.deezer\.com/chart/0/tracks"'),
    'const DEEZER_CHART = (process.env.DEEZER_CHART_URL || "https://api.deezer.com/chart") + "/0/tracks"',
    "Replace hardcoded Deezer chart URL (trending) with env var",
))

PATCHES.append((
    "app/api/musiva/charts/route.ts",
    re.compile(r'const DEEZER_CHART\s*=\s*"https://api\.deezer\.com/chart"'),
    'const DEEZER_CHART = process.env.DEEZER_CHART_URL || "https://api.deezer.com/chart"',
    "Replace hardcoded Deezer chart URL (charts) with env var",
))

# ─────────────────────────────────────────────────────────────────────────────
# 3.  GROQ API  (server-side → GROQ_API_URL)
# ─────────────────────────────────────────────────────────────────────────────
PATCHES.append((
    "app/api/groq/transform/route.ts",
    re.compile(r'const GROQ_API\s*=\s*"https://api\.groq\.com/openai/v1/chat/completions"'),
    'const GROQ_API = process.env.GROQ_API_URL || "https://api.groq.com/openai/v1/chat/completions"',
    "Replace hardcoded Groq API URL with env var",
))

# ─────────────────────────────────────────────────────────────────────────────
# 4.  SPONSORBLOCK API  (server-side → SPONSORBLOCK_API_URL)
# ─────────────────────────────────────────────────────────────────────────────
PATCHES.append((
    "app/api/sponsorblock/route.ts",
    re.compile(
        r'const url = `https://sponsor\.ajay\.app/api/skipSegments\?videoID=\$\{encodeURIComponent\(videoId\)\}'
        r'&categories=\["poi_highlight"\]&actionTypes=\["poi"\]`'
    ),
    'const SPONSORBLOCK_BASE = process.env.SPONSORBLOCK_API_URL || "https://sponsor.ajay.app"\n'
    '    const url = `${SPONSORBLOCK_BASE}/api/skipSegments?videoID=${encodeURIComponent(videoId)}'
    '&categories=["poi_highlight"]&actionTypes=["poi"]`',
    "Replace hardcoded SponsorBlock URL with env var",
))

# ─────────────────────────────────────────────────────────────────────────────
# 5.  APP PUBLIC URL  (NEXT_PUBLIC_APP_URL)
# ─────────────────────────────────────────────────────────────────────────────
APP_URL_FILES_BASE_URL = [
    ("app/robots.ts",   re.compile(r'const BASE_URL\s*=\s*"https://musicanaz\.vercel\.app"')),
    ("app/sitemap.ts",  re.compile(r'const BASE_URL\s*=\s*"https://musicanaz\.vercel\.app"')),
    ("app/layout.tsx",  re.compile(r'const BASE_URL\s*=\s*"https://musicanaz\.vercel\.app"')),
]
for (f, pattern) in APP_URL_FILES_BASE_URL:
    PATCHES.append((
        f,
        pattern,
        'const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || "https://musicanaz.vercel.app"',
        "Replace hardcoded app URL with NEXT_PUBLIC_APP_URL env var",
    ))

# song/page.tsx uses `const BASE` (not BASE_URL) for the same app URL
PATCHES.append((
    "app/song/page.tsx",
    re.compile(r'const BASE\s*=\s*"https://musicanaz\.vercel\.app"'),
    'const BASE = process.env.NEXT_PUBLIC_APP_URL || "https://musicanaz.vercel.app"',
    "Replace hardcoded app URL (song page) with NEXT_PUBLIC_APP_URL",
))

# ─────────────────────────────────────────────────────────────────────────────
# 6.  PARTY SERVER  (NEXT_PUBLIC_PARTY_SERVER — remove hardcoded default)
#     These files already use the env var but fall back to the hardcoded URL.
#     We keep the fallback so the app still works without the env var set, but
#     we make the fallback value itself driven by an empty string so it's clear.
#     Actually — the existing pattern is fine; we just ensure no NEW hardcoded
#     URLs sneak in.  Nothing to change here beyond what's already done.
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Apply all patches
# ─────────────────────────────────────────────────────────────────────────────
total_changed = 0
total_skipped = 0
total_missing = 0

for (rel_path, pattern, replacement, description) in PATCHES:
    abs_path = os.path.join(ROOT, rel_path)

    if not os.path.isfile(abs_path):
        print(yellow(f"  ⚠  MISSING  {rel_path}"))
        total_missing += 1
        continue

    with open(abs_path, "r", encoding="utf-8") as fh:
        original = fh.read()

    if isinstance(pattern, re.Pattern):
        new_content = pattern.sub(replacement, original)
    else:
        new_content = original.replace(pattern, replacement)

    if new_content == original:
        print(yellow(f"  –  SKIP (already patched or not found)  {rel_path}"))
        total_skipped += 1
    else:
        with open(abs_path, "w", encoding="utf-8") as fh:
            fh.write(new_content)
        print(green(f"  ✓  PATCHED  {rel_path}"))
        print(f"         → {description}")
        total_changed += 1

# ─────────────────────────────────────────────────────────────────────────────
# Generate .env.example
# ─────────────────────────────────────────────────────────────────────────────
ENV_EXAMPLE = """\
# ─────────────────────────────────────────────────────────────────
# Musicanaz — Environment Variables
# Copy this file to .env.local and fill in your values.
# Variables prefixed NEXT_PUBLIC_ are exposed to the browser.
# ─────────────────────────────────────────────────────────────────

# ── Backend / Music API ───────────────────────────────────────────
# The Musiva / Turbo API that powers search, streaming, lyrics, etc.
MUSIVA_API_URL=https://turbo-14uz.onrender.com

# ── Chart Data ───────────────────────────────────────────────────
# Deezer public chart endpoint (no key required)
DEEZER_CHART_URL=https://api.deezer.com/chart

# ── AI / Groq ────────────────────────────────────────────────────
# Groq API base URL (users supply their own API key in the UI)
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions

# ── SponsorBlock ─────────────────────────────────────────────────
SPONSORBLOCK_API_URL=https://sponsor.ajay.app

# ── Party / Real-time Server ─────────────────────────────────────
# Your deployed party/signalling server
NEXT_PUBLIC_PARTY_SERVER=https://y-brown-two.vercel.app

# ── App Public URL ────────────────────────────────────────────────
# Used for OG tags, sitemap, robots.txt, and share links
NEXT_PUBLIC_APP_URL=https://musicanaz.vercel.app

# ── Community / ToPlay API ───────────────────────────────────────
# Optional — enables community trending data overlay
NEXT_PUBLIC_TOPLAY_API_URL=
"""

env_example_path = os.path.join(ROOT, ".env.example")
with open(env_example_path, "w", encoding="utf-8") as fh:
    fh.write(ENV_EXAMPLE)
print(green(f"\n  ✓  CREATED  .env.example"))

# Also create .env.local only if it doesn't already exist
env_local_path = os.path.join(ROOT, ".env.local")
if not os.path.isfile(env_local_path):
    with open(env_local_path, "w", encoding="utf-8") as fh:
        fh.write(ENV_EXAMPLE.replace(
            "# Copy this file to .env.local and fill in your values.",
            "# Auto-generated by env_url_patcher.py — edit as needed."
        ))
    print(green(f"  ✓  CREATED  .env.local  (pre-filled with defaults)"))
else:
    print(yellow(f"  –  SKIP  .env.local  (already exists — not overwritten)"))

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print(f"""
{bold('─' * 55)}
{bold('Summary')}
  {green(f'Patched  : {total_changed} file(s)')}
  {yellow(f'Skipped  : {total_skipped} (already up-to-date or not found)')}
  {(red if total_missing else yellow)(f'Missing  : {total_missing} file(s) not found on disk')}
{bold('─' * 55)}

{bold('Vercel Dashboard → Settings → Environment Variables')}
Add these keys:

  MUSIVA_API_URL            https://turbo-14uz.onrender.com
  DEEZER_CHART_URL          https://api.deezer.com/chart
  GROQ_API_URL              https://api.groq.com/openai/v1/chat/completions
  SPONSORBLOCK_API_URL      https://sponsor.ajay.app
  NEXT_PUBLIC_PARTY_SERVER  https://y-brown-two.vercel.app
  NEXT_PUBLIC_APP_URL       https://musicanaz.vercel.app
  NEXT_PUBLIC_TOPLAY_API_URL  (your toplay URL if you have one)

Done! 🎵
""")
