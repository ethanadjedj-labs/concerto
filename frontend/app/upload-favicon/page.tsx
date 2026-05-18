"use client"
import { useState } from "react"

export default function UploadFavicon() {
  const [status, setStatus] = useState<string>("")
  const [busy, setBusy] = useState(false)

  async function handle(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    setStatus(`uploading ${f.name} (${(f.size / 1024).toFixed(1)} KB)...`)
    try {
      const fd = new FormData()
      fd.append("file", f)
      const r = await fetch("/api/upload-favicon", { method: "POST", body: fd })
      const t = await r.text()
      setStatus(r.ok ? `✓ ${t}` : `✗ ${t}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setStatus(`✗ ${msg}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ padding: 32, fontFamily: "system-ui, sans-serif", maxWidth: 480, margin: "0 auto", minHeight: "100vh", background: "#faf9f5" }}>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Upload favicon</h1>
      <p style={{ color: "#666", marginBottom: 24, fontSize: 14 }}>PNG ou ICO. Sera converti en multi-resolution favicon.ico côté serveur.</p>
      <input type="file" accept="image/*,.ico" onChange={handle} disabled={busy} style={{
        display: "block", width: "100%", padding: 24, fontSize: 16,
        background: "#fff", border: "2px dashed #cc785c", borderRadius: 12,
        cursor: busy ? "wait" : "pointer",
      }} />
      {status && <pre style={{ marginTop: 24, padding: 16, background: "#f3efe5", borderRadius: 8, fontSize: 13, whiteSpace: "pre-wrap" }}>{status}</pre>}
    </div>
  )
}
