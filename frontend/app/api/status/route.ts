import { NextResponse } from "next/server"
import { readFile } from "fs/promises"
import path from "path"

const STATUS_FILE = process.env.CONCERTO_STATUS_FILE || "/var/www/concerto-status/status.json"

export async function GET() {
  try {
    const raw = await readFile(STATUS_FILE, "utf8")
    const data = JSON.parse(raw)
    return NextResponse.json(data, {
      headers: {
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": "*",
      },
    })
  } catch {
    return NextResponse.json(
      {
        updated_at: Math.floor(Date.now() / 1000),
        services: [
          { name: "Concerto API", status: "unknown", latency_ms: null },
          { name: "Workspace API", status: "unknown", latency_ms: null },
          { name: "Stripe API", status: "unknown", latency_ms: null },
          { name: "Resend API", status: "unknown", latency_ms: null },
        ],
        incidents: [],
        _error: "status file unavailable",
      },
      {
        status: 200,
        headers: { "Access-Control-Allow-Origin": "*" },
      }
    )
  }
}
