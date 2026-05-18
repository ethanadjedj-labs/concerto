import { NextRequest } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const BACKEND = process.env.CONCERTO_BACKEND_URL || "http://127.0.0.1:8090"

export async function POST(req: NextRequest) {
  try {
    const body = await req.text()
    const ip = req.headers.get("x-forwarded-for")?.split(",")[0].trim() || req.headers.get("x-real-ip") || ""
    const r = await fetch(`${BACKEND}/api/trial/start`, {
      method: "POST",
      headers: {
        "Content-Type": req.headers.get("content-type") || "application/json",
        ...(ip ? { "X-Forwarded-For": ip } : {}),
      },
      body,
    })
    const text = await r.text()
    return new Response(text, {
      status: r.status,
      headers: { "Content-Type": r.headers.get("content-type") || "application/json" },
    })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    return new Response(JSON.stringify({ error: "proxy_error", message: msg }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    })
  }
}
