"use client"
import { useState } from "react"

export default function TrialPage() {
  const [email, setEmail] = useState("adjedjethan+trial@gmail.com")
  const [status, setStatus] = useState<string>("")
  const [busy, setBusy] = useState(false)
  const [dashUrl, setDashUrl] = useState<string>("")

  async function startTrial() {
    setBusy(true)
    setStatus("Starting…")
    setDashUrl("")
    try {
      const r = await fetch("/api/trial/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      const ct = r.headers.get("content-type") || ""
      let parsed: { token?: string; dashboard_url?: string; error?: string; message?: string; detail?: unknown } = {}
      if (ct.includes("application/json")) {
        try { parsed = await r.json() } catch { /* fall through */ }
      }
      if (!r.ok) {
        const detail = parsed.detail && typeof parsed.detail === "object" ? parsed.detail : parsed
        const errLabel = (detail as { error?: string }).error || `HTTP ${r.status}`
        const errMsg = (detail as { message?: string }).message || ""
        setStatus(`✗ ${errLabel}${errMsg ? ` — ${errMsg}` : ""}`)
        return
      }
      if (parsed.token) {
        const url = parsed.dashboard_url || `/dashboard/${parsed.token}`
        setDashUrl(url)
        setStatus(`✓ Trial started.\n\nSetup takes ~3 minutes. The button below will work once it's ready.`)
      } else {
        setStatus(`✓ Started.`)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setStatus(`✗ Network error — ${msg}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ padding: 32, fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "0 auto", minHeight: "100vh", background: "#faf9f5" }}>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Start a trial</h1>
      <p style={{ color: "#666", marginBottom: 24, fontSize: 14 }}>
        Try Concerto for 30 minutes. No payment, no card.
      </p>
      <label style={{ display: "block", fontSize: 13, color: "#191919", marginBottom: 8, fontWeight: 500 }}>Email</label>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={busy} style={{
        display: "block", width: "100%", padding: "12px 14px", fontSize: 16,
        background: "#fff", border: "1px solid #d4d0c8", borderRadius: 8, marginBottom: 16,
      }} />
      <button onClick={startTrial} disabled={busy || !email} style={{
        display: "block", width: "100%", padding: "14px 20px", fontSize: 16, fontWeight: 500,
        background: busy ? "#d4d0c8" : "#cc785c", color: "#fff", border: "none",
        borderRadius: 8, cursor: busy ? "wait" : "pointer",
      }}>
        {busy ? "Starting…" : "Start trial"}
      </button>
      {status && <pre style={{ marginTop: 24, padding: 16, background: "#f3efe5", borderRadius: 8, fontSize: 13, whiteSpace: "pre-wrap", color: "#191919" }}>{status}</pre>}
      {dashUrl && (
        <a href={dashUrl} style={{
          display: "block", marginTop: 16, padding: "14px 20px", fontSize: 16, fontWeight: 500,
          background: "#191919", color: "#faf9f5", borderRadius: 8, textAlign: "center", textDecoration: "none",
        }}>Open dashboard →</a>
      )}
    </div>
  )
}
