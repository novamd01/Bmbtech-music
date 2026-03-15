#!/usr/bin/env python3
"""
implement_secret_message_plan.py
Run from Musicanaz-main root:
    python implement_secret_message_plan.py

PLAN IMPLEMENTED
================

1. SECRET NOTE → routes to /player (not /note)
   - videoId is embedded in the URL → player starts instantly, no cold-load delay
   - sm / smt / smf params carry the message, trigger time, sender name
   - Receiver opens the normal full player, song plays like any shared link

2. SECRET MESSAGE → shows directly (no blur / "Tap to reveal" step)
   - At the chosen second: song pauses, fullscreen takeover slides in
   - Message is visible immediately — no extra tap required
   - "Resume music" resumes playback; "Skip & resume" in top bar skips immediately

3. NOTE PAGE BUTTON → "Get message" instead of icon-only "Open in player"

NON-SECRET notes are unchanged — still route to /note with themed experience.
"""

import shutil
from pathlib import Path

ROOT        = Path.cwd()
PLAYER_PAGE = ROOT / "app" / "player" / "page.tsx"
NOTE_PAGE   = ROOT / "app" / "note"   / "page.tsx"
errors      = []

def backup(p: Path):
    bak = p.with_suffix(p.suffix + ".bak")
    shutil.copy2(p, bak)
    print(f"  📄 Backup → {bak.name}")

def patch(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        msg = f"  ⚠  SKIP [{label}] — already applied or marker not found"
        print(msg); errors.append(msg); return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  ✓  [{label}]")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# app/player/page.tsx
# ══════════════════════════════════════════════════════════════════════════════
print("\n── app/player/page.tsx ──────────────────────────────────────────────────")
backup(PLAYER_PAGE)

# ── 1. Pause song on trigger ──────────────────────────────────────────────────
patch(
    PLAYER_PAGE,
    """\
  // Secret message — watch playback time and trigger overlay at the right moment
  useEffect(() => {
    if (!secretMsg || secretTriggerAt < 0 || secretDismissed || secretVisible) return
    if (Math.floor(currentTime) >= secretTriggerAt) {
      setSecretVisible(true)
    }
  }, [currentTime, secretMsg, secretTriggerAt, secretDismissed, secretVisible])""",
    """\
  // Secret message — pause song at trigger point then show fullscreen takeover
  useEffect(() => {
    if (!secretMsg || secretTriggerAt < 0 || secretDismissed || secretVisible) return
    if (Math.floor(currentTime) >= secretTriggerAt) {
      if (isPlaying) togglePlayPause()   // pause — fullscreen takes over
      setSecretVisible(true)
    }
  }, [currentTime, secretMsg, secretTriggerAt, secretDismissed, secretVisible, isPlaying, togglePlayPause])""",
    "pause song when secret triggers",
)

# ── 2. buildNoteUrl: secret → /player, non-secret → /note ────────────────────
patch(
    PLAYER_PAGE,
    """\
  const buildNoteUrl = () => {
    const vid = currentSong?.videoId || currentSong?.id || ""
    const t   = currentSong?.title   || title  || ""
    const ar  = currentSong?.artist  || artist || ""
    const th  = currentSong?.thumbnail || thumbnail || ""
    const base = typeof window !== "undefined" ? window.location.origin : ""
    const p: Record<string, string> = {
      id: vid, videoId: vid, title: t, artist: ar, thumbnail: th, type: "musiva",
      t:   String(noteTriggerAt),
      nt:  noteTitle   || "A note for you",
      nm:  noteMsg,
      nth: noteTheme,
      nf:  noteSenderName,
      ...(noteSecret ? { sn: "1" } : {}),
    }
    return `${base}/note?${new URLSearchParams(p).toString()}`
  }""",
    """\
  const buildNoteUrl = () => {
    const vid  = currentSong?.videoId || currentSong?.id || ""
    const t    = currentSong?.title   || title  || ""
    const ar   = currentSong?.artist  || artist || ""
    const th   = currentSong?.thumbnail || thumbnail || ""
    const base = typeof window !== "undefined" ? window.location.origin : ""

    if (noteSecret) {
      // Secret note → normal /player URL with message embedded as params.
      // videoId already in URL → player loads song instantly (no /note cold-start).
      // At the chosen second the fullscreen message fires inside the player.
      const p: Record<string, string> = {
        id: vid, videoId: vid, title: t, artist: ar, thumbnail: th, type: "musiva",
        sm:  noteMsg,
        smt: String(noteTriggerAt),
        smf: noteSenderName,
      }
      return `${base}/player?${new URLSearchParams(p).toString()}`
    }

    // Non-secret note → dedicated /note page with themed countdown experience
    const p: Record<string, string> = {
      id: vid, videoId: vid, title: t, artist: ar, thumbnail: th, type: "musiva",
      t:   String(noteTriggerAt),
      nt:  noteTitle || "A note for you",
      nm:  noteMsg,
      nth: noteTheme,
      nf:  noteSenderName,
    }
    return `${base}/note?${new URLSearchParams(p).toString()}`
  }""",
    "buildNoteUrl: secret→/player, non-secret→/note",
)

# ── 3. Secret overlay: show message directly (remove blur/reveal step) ─────────
patch(
    PLAYER_PAGE,
    """\
      {/* ── Secret Message Overlay ─────────────────────────────────────── */}
      {secretVisible && !secretDismissed && (
        <div
          className={[
            "fixed inset-0 z-[200] flex items-center justify-center p-6 transition-all duration-700",
            secretVisible ? "opacity-100" : "opacity-0 pointer-events-none",
          ].join(" ")}
          style={{ backdropFilter: "blur(20px)", backgroundColor: "rgba(0,0,0,0.55)" }}
        >
          <div className="w-full max-w-sm">
            {/* Card */}
            <div className="relative bg-white/10 border border-white/20 rounded-3xl p-6 shadow-2xl text-center space-y-4 animate-in zoom-in-95 fade-in duration-500">
              {/* Close button */}
              <button
                onClick={() => { setSecretDismissed(true); setSecretVisible(false) }}
                className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/60 hover:text-white transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              {/* Icon */}
              <div className="flex justify-center">
                <div className="w-14 h-14 rounded-2xl bg-primary/20 border border-primary/30 flex items-center justify-center text-3xl">🤫</div>
              </div>
              {secretFrom && (
                <p className="text-xs text-white/50 font-medium uppercase tracking-widest">from {secretFrom}</p>
              )}
              {!secretRevealed ? (
                <div className="space-y-3">
                  <p className="text-base text-white font-medium leading-relaxed select-none" style={{ filter: "blur(7px)" }}>
                    {secretMsg}
                  </p>
                  <button
                    onClick={() => setSecretRevealed(true)}
                    className="w-full h-10 rounded-2xl bg-primary text-primary-foreground text-sm font-semibold flex items-center justify-center gap-2 active:scale-95 transition-all"
                  >
                    💫 Reveal message
                  </button>
                </div>
              ) : (
                <div className="space-y-3 animate-in fade-in zoom-in-95 duration-500">
                  <p className="text-base text-white font-medium leading-relaxed whitespace-pre-wrap">{secretMsg}</p>
                  <p className="text-xs text-white/40">🎵 Music keeps playing</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}""",
    """\
      {/* ── Secret Message — fullscreen takeover ────────────────────────── */}
      {secretVisible && !secretDismissed && (
        <div className="fixed inset-0 z-[300] flex flex-col bg-gradient-to-br from-slate-950 via-zinc-900 to-neutral-950 animate-in fade-in duration-500">

          {/* Ambient glow from song thumbnail */}
          {(currentSong?.thumbnail) && (
            <div
              className="absolute inset-0 opacity-15 scale-150 blur-3xl pointer-events-none"
              style={{ backgroundImage: `url(${currentSong.thumbnail})`, backgroundSize: "cover", backgroundPosition: "center" }}
            />
          )}

          {/* Top bar — song info + skip button */}
          <div className="relative z-10 flex items-center justify-between px-5 pt-12 pb-3">
            <div className="flex items-center gap-2 text-white/40 min-w-0">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
              </svg>
              <span className="text-xs truncate">{currentSong?.title || ""}</span>
              <span className="text-white/20 flex-shrink-0">· paused</span>
            </div>
            <button
              onClick={() => { setSecretDismissed(true); setSecretVisible(false); if (!isPlaying) togglePlayPause() }}
              className="flex-shrink-0 flex items-center gap-1.5 ml-3 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white/60 hover:text-white text-xs font-medium transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              Skip &amp; resume
            </button>
          </div>

          {/* Centre content */}
          <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-8 gap-8 text-center">

            {/* Icon + sender */}
            <div className="flex flex-col items-center gap-3 animate-in slide-in-from-bottom-4 fade-in duration-500">
              <div className="w-20 h-20 rounded-3xl bg-white/10 border border-white/15 flex items-center justify-center text-4xl shadow-2xl">
                🤫
              </div>
              {secretFrom && (
                <p className="text-xs text-white/40 font-medium uppercase tracking-[0.2em]">
                  from {secretFrom}
                </p>
              )}
            </div>

            {/* Message card — shows directly, no blur or reveal step */}
            <div className="w-full max-w-sm animate-in slide-in-from-bottom-6 fade-in duration-600 delay-100">
              <div className="bg-white/8 border border-white/12 rounded-3xl p-7 shadow-2xl space-y-5">
                <p className="text-lg text-white font-medium leading-relaxed whitespace-pre-wrap animate-in fade-in duration-500">
                  {secretMsg}
                </p>
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-white/10" />
                  <span className="text-white/25 text-xs">♪</span>
                  <div className="h-px flex-1 bg-white/10" />
                </div>
                <button
                  onClick={() => { setSecretDismissed(true); setSecretVisible(false); if (!isPlaying) togglePlayPause() }}
                  className="w-full h-12 rounded-2xl bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 active:scale-95 transition-all"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  Resume music
                </button>
              </div>
            </div>
          </div>

          {/* Bottom hint */}
          <div className="relative z-10 pb-10 text-center">
            <p className="text-white/20 text-xs">Song is paused · tap Resume to continue</p>
          </div>
        </div>
      )}""",
    "secret overlay: fullscreen takeover, message shown directly",
)

# ══════════════════════════════════════════════════════════════════════════════
# app/note/page.tsx
# ══════════════════════════════════════════════════════════════════════════════
print("\n── app/note/page.tsx ────────────────────────────────────────────────────")
backup(NOTE_PAGE)

patch(
    NOTE_PAGE,
    """\
            <button
              onClick={() => router.push(`/player?id=${videoId}&title=${encodeURIComponent(songTitle)}&artist=${encodeURIComponent(artist)}&thumbnail=${encodeURIComponent(thumbnail)}&type=musiva&videoId=${videoId}`)}
              className="p-2 rounded-full bg-white/10 hover:bg-white/20 text-white/60 hover:text-white transition-colors flex-shrink-0"
              title="Open in player"
            >
              <Music className="w-4 h-4" />
            </button>""",
    """\
            <button
              onClick={() => router.push(`/player?id=${videoId}&title=${encodeURIComponent(songTitle)}&artist=${encodeURIComponent(artist)}&thumbnail=${encodeURIComponent(thumbnail)}&type=musiva&videoId=${videoId}`)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white/60 hover:text-white text-xs font-medium transition-colors flex-shrink-0"
              title="Get message"
            >
              <Music className="w-3.5 h-3.5" />
              Get message
            </button>""",
    'note page: "Get message" button',
)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors:
    print("⚠  Some patches skipped (likely already applied):")
    for e in errors: print(f"   {e}")
    print("\n  Everything else applied cleanly.")
else:
    print("✅ All patches applied!\n")

print("""  WHAT CHANGED
  ─────────────────────────────────────────────────────────────────
  1. Secret note link → /player (not /note)
       Sender taps 🔒 Secret toggle in Note tab → buildNoteUrl()
       generates a normal /player?videoId=...&sm=...&smt=...&smf=...
       URL. videoId is embedded so the player starts the song
       immediately — no /note page, no cold-loading delay.

  2. Secret message fires in the player — no blur/reveal
       At the chosen second: song pauses instantly.
       Fullscreen dark screen slides in (z-300, covers everything).
       Message card appears directly — readable immediately.
       "Resume music" resumes; "Skip & resume" in top bar skips.

  3. Note page → "Get message" button
       The icon-only button in the /note header is now a labelled
       pill reading "Get message" so the purpose is obvious.

  NON-SECRET notes are unchanged:
       Route to /note, themed countdown, emoji particles, etc.
""")
