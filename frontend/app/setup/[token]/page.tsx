"use client"

import { useState, useEffect } from "react"
import { Copy, Check } from "lucide-react"

export default function SetupPage({ params }: { params: { token: string } }) {
  const [copied, setCopied] = useState(false)
  const [mcpUrl, setMcpUrl] = useState(`https://api.concerto.run/mcp-proxy/${params.token}/mcp`)
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) => { if (d.mcp_url) setMcpUrl(d.mcp_url) })
      .catch(() => {})
  }, [backendUrl, params.token])

  const cmd = `claude mcp add --transport http concerto ${mcpUrl}`

  async function copyCmd() {
    try {
      await navigator.clipboard.writeText(cmd)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = cmd
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div
      className="flex min-h-screen items-center justify-center px-6 py-16"
      style={{ backgroundColor: "#faf9f5", color: "#191919" }}
    >
      <div className="w-full max-w-[480px]">
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <img src="/brand/logo-mark.png?v=3" alt="Concerto" width={36} height={36} />
          <h1 className="mt-2 text-[26px] font-semibold tracking-tight" style={{ color: "#191919" }}>
            Connect Claude to Concerto
          </h1>
          <p className="text-[15px] leading-relaxed" style={{ color: "#8a847b" }}>
            Run this command in your terminal. Your token is already filled in.
          </p>
        </div>

        <div
          className="rounded-2xl"
          style={{
            border: "1.5px solid #cc785c",
            backgroundColor: "#fffaf7",
            boxShadow: "0 2px 10px rgba(204,120,92,0.10)",
            overflow: "hidden",
          }}
        >
          <div className="px-5 pt-4 pb-1">
            <p className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: "#b3613f" }}>
              Terminal / Claude Desktop
            </p>
          </div>
          <div className="flex items-start gap-3 px-5 pb-4">
            <code
              className="min-w-0 flex-1 break-all font-mono text-[13px] leading-relaxed"
              style={{ color: "#191919" }}
            >
              {cmd}
            </code>
            <button
              type="button"
              onClick={copyCmd}
              className="mt-0.5 flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-[13px] font-medium transition-all"
              style={{
                backgroundColor: copied ? "rgba(204,120,92,0.15)" : "#cc785c",
                color: copied ? "#cc785c" : "#fff",
              }}
              aria-label={copied ? "Copied" : "Copy command"}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <p className="text-[13px] leading-relaxed text-center" style={{ color: "#8a847b" }}>
            Works the same for Claude Desktop and any other MCP-compatible client.
          </p>
          <ol className="mt-4 space-y-3">
            {[
              { n: "1", label: "Open your terminal", detail: "or Claude Desktop settings" },
              { n: "2", label: "Paste the command above", detail: "your token is pre-filled" },
              { n: "3", label: "Open Claude and describe what you want built", detail: "Concerto orchestrates the rest" },
            ].map((step) => (
              <li key={step.n} className="flex items-start gap-3">
                <span
                  className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                  style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
                >
                  {step.n}
                </span>
                <div>
                  <span className="text-[13px] font-medium" style={{ color: "#191919" }}>{step.label}</span>
                  <span className="text-[13px]" style={{ color: "#8a847b" }}> — {step.detail}</span>
                </div>
              </li>
            ))}
          </ol>
        </div>

        <p className="mt-8 text-center text-[12px]" style={{ color: "#8a847b" }}>
          Need help?{" "}
          <a href="mailto:support@concerto.run" className="transition-opacity hover:opacity-70" style={{ color: "#cc785c" }}>
            support@concerto.run
          </a>
        </p>
      </div>
    </div>
  )
}
