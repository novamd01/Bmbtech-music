/**
 * Musicanaz AI client helpers
 * All calls go through Next.js API routes so AI_API_URL stays server-side.
 */
import type { Song } from "./types"
import { getOrCreateUID } from "./uid"

const AI_TOGGLE_KEY = "musicanaz_ai_search"

// ── toggle preference ─────────────────────────────────────────────────────
export function getAISearchEnabled(): boolean {
  if (typeof window === "undefined") return false
  try { return localStorage.getItem(AI_TOGGLE_KEY) === "1" } catch { return false }
}

export function setAISearchEnabled(on: boolean): void {
  if (typeof window === "undefined") return
  try { localStorage.setItem(AI_TOGGLE_KEY, on ? "1" : "0") } catch {}
}

export function toggleAISearch(): boolean {
  const next = !getAISearchEnabled()
  setAISearchEnabled(next)
  return next
}

// ── personalized search ───────────────────────────────────────────────────
export async function aiPersonalizedSearch(
  query: string,
  limit = 20,
): Promise<{ results: any[]; personalized: boolean; from_cache: boolean }> {
  const user_id = getOrCreateUID()
  const res = await fetch("/api/ai/search", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ user_id, query, limit }),
    signal:  AbortSignal.timeout(15_000),
  })
  if (!res.ok) throw new Error(`AI search failed: ${res.status}`)
  return res.json()
}

// ── recommendations ───────────────────────────────────────────────────────
export async function getAIRecommendations(
  limit = 20,
): Promise<{ songs: any[]; personalized: boolean; breakdown?: any }> {
  const user_id = getOrCreateUID()
  const res = await fetch(`/api/ai/recommendations?user_id=${encodeURIComponent(user_id)}&limit=${limit}`)
  if (!res.ok) throw new Error(`AI reco failed: ${res.status}`)
  return res.json()
}

// ── collab signals ────────────────────────────────────────────────────────
export async function getCollabSignals(
  limit = 20,
): Promise<{ signals: any[]; count: number }> {
  const user_id = getOrCreateUID()
  const res = await fetch(`/api/ai/signals?user_id=${encodeURIComponent(user_id)}&limit=${limit}`)
  if (!res.ok) throw new Error(`AI signals failed: ${res.status}`)
  return res.json()
}

// ── log listen event (fire-and-forget) ────────────────────────────────────
export function logAIEvent(
  song: Song,
  listenedMs: number,
  liked = false,
  skipped = false,
): void {
  const user_id = getOrCreateUID()
  if (!user_id) return
  const payload = {
    user_id,
    song_id:     song.videoId || song.id || "",
    title:       song.title   || "",
    artist:      typeof song.artist === "string" ? song.artist : "",
    album:       song.album   || "",
    thumbnail:   song.thumbnail || "",
    duration_ms: null,
    listened_ms: listenedMs,
    liked,
    skipped,
  }
  // Fire and forget via the proxy route
  fetch("/api/ai/event", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(payload),
  }).catch(() => {})
}

// ── convert AI song shape → Musicanaz Song ────────────────────────────────
export function aiSongToSong(s: any): Song {
  return {
    id:        s.song_id || s.videoId || "",
    videoId:   s.song_id || s.videoId || "",
    title:     s.title   || "Unknown",
    artist:    s.artist  || "Unknown",
    thumbnail: s.thumbnail || "",
    album:     s.album   || "",
    duration:  s.duration || "",
    type:      "musiva" as const,
  }
}
