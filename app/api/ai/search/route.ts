import { type NextRequest, NextResponse } from "next/server"

const AI_BASE = process.env.AI_API_URL || ""

export async function POST(req: NextRequest) {
  if (!AI_BASE) return NextResponse.json({ error: "AI_API_URL not set" }, { status: 503 })
  try {
    const body = await req.json()
    const res  = await fetch(`${AI_BASE}/search/personalized`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
      signal:  AbortSignal.timeout(12_000),
    })
    const data = await res.json()
    return NextResponse.json(data)
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
