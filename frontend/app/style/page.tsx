"use client"

import { useState, useRef } from "react"
import Link from "next/link"
import { CONCERTO_CUSTOM_STYLE } from "@/lib/concerto-custom-style"

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <img
      src="/brand/logo-mark.png?v=3"
      alt="Concerto"
      width={size}
      height={size}
      style={{ display: "block", width: size, height: size }}
    />
  )
}

export default function StylePage() {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  async function copy() {
    try {
      await navigator.clipboard.writeText(CONCERTO_CUSTOM_STYLE)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = CONCERTO_CUSTOM_STYLE
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    setCopied(true)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), 3000)
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: "#faf9f5" }}>
      {/* Header */}
      <header style={{ borderBottom: "1px solid #f3efe5", backgroundColor: "rgba(250,249,245,0.95)" }}>
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3.5">
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark size={26} />
            <span className="text-[17px] font-medium" style={{ color: "#191919" }}>Concerto</span>
          </Link>
          <span
            className="rounded-full px-3 py-1 text-[12px] font-medium"
            style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
          >
            Custom Style
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-5 py-12">
        {/* Hero */}
        <div className="mb-10">
          <h1 className="mb-3 text-[28px] font-medium leading-tight" style={{ color: "#191919" }}>
            Concerto Orchestrator
          </h1>
          <p className="text-[16px] leading-relaxed" style={{ color: "#8a847b" }}>
            A Claude.ai Custom Style that primes Claude to spawn sessions proactively,
            parallelize work, and report back clearly — instead of describing what it would do.
          </p>
        </div>

        {/* Style text block */}
        <div
          className="mb-8 rounded-2xl overflow-hidden"
          style={{ border: "1px solid #f3efe5", backgroundColor: "#fff", boxShadow: "0 1px 4px rgba(25,25,25,0.04)" }}
        >
          <div
            className="flex items-center justify-between px-5 py-3.5"
            style={{ borderBottom: "1px solid #f3efe5" }}
          >
            <span className="text-[12px] font-medium uppercase tracking-widest" style={{ color: "#8a847b" }}>
              Style text — paste into claude.ai
            </span>
            <button
              type="button"
              onClick={copy}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-all"
              style={{
                backgroundColor: copied ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)",
                color: "#cc785c",
              }}
            >
              {copied ? "✓ Copied" : "Copy style"}
            </button>
          </div>
          <pre
            className="overflow-x-auto p-5 text-[13px] leading-relaxed whitespace-pre-wrap"
            style={{ color: "#191919", fontFamily: "var(--font-mono, ui-monospace, monospace)" }}
          >
            {CONCERTO_CUSTOM_STYLE}
          </pre>
        </div>

        {/* How to activate */}
        <div
          className="rounded-2xl p-6 mb-8"
          style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
        >
          <h2 className="mb-5 text-[16px] font-medium" style={{ color: "#191919" }}>
            How to activate
          </h2>
          <ol className="space-y-4">
            {[
              { label: "Open claude.ai Settings", detail: "Click your avatar → Settings → Custom Styles" },
              { label: "Create a new style", detail: "Click \"Add style\" and paste the text above" },
              { label: "Name it and save", detail: "Name it \"Concerto Orchestrator\" and click Save" },
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-3">
                <span
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold"
                  style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
                >
                  {i + 1}
                </span>
                <div>
                  <p className="text-[14px] font-medium" style={{ color: "#191919" }}>{step.label}</p>
                  <p className="text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-5 pt-5" style={{ borderTop: "1px solid #f3efe5" }}>
            <p className="text-[13px]" style={{ color: "#8a847b" }}>
              Once saved, activate the style by selecting it in any Claude conversation. It takes effect immediately.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center">
          <Link href="/" className="text-[13px] transition-opacity hover:opacity-70" style={{ color: "#8a847b" }}>
            ← Back to concerto.run
          </Link>
        </div>
      </main>
    </div>
  )
}
