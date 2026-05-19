"use client"

import { useState } from "react"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Check, ArrowLeft, RotateCcw } from "lucide-react"

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

const REASONS = [
  "Too expensive",
  "Not using it enough",
  "Missing a feature I need",
  "Hit a bug or it didn't work",
  "Just exploring / temporary",
  "Something else",
]

export default function CancelPage() {
  const params = useParams<{ token: string }>()
  const token = params?.token ?? ""
  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  const [reason, setReason] = useState<string | null>(null)
  const [detail, setDetail] = useState("")
  const [phase, setPhase] = useState<"idle" | "sending" | "done" | "error">(
    "idle",
  )
  const [resultMsg, setResultMsg] = useState("")

  async function submitCancel() {
    setPhase("sending")
    try {
      const r = await fetch(`${backendUrl}/api/cancel-subscription`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, reason: reason ?? "", detail }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d?.detail || "Request failed")
      setResultMsg(
        d?.message ||
          "Your cancellation has been recorded. Questions: support@concerto.run",
      )
      setPhase("done")
    } catch {
      setResultMsg(
        "We couldn't process that automatically. Email support@concerto.run and we'll handle it right away.",
      )
      setPhase("error")
    }
  }

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#faf9f5" }}>
      <header
        style={{
          borderBottom: "1px solid #f0ece1",
          backgroundColor: "rgba(250,249,245,0.90)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3.5">
          <a
            href="https://concerto.run"
            className="flex items-center gap-2.5 transition-opacity hover:opacity-70"
            aria-label="Concerto home"
          >
            <LogoMark size={28} />
            <span
              className="text-[18px] font-medium leading-none tracking-tight"
              style={{ color: "#191919" }}
            >
              Concerto
            </span>
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-lg px-5 py-12">
        {phase === "done" ? (
          <div
            className="rounded-2xl px-7 py-9 text-center"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div
              className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full"
              style={{ backgroundColor: "#cc785c" }}
            >
              <Check className="h-6 w-6" style={{ color: "#fff" }} strokeWidth={3} />
            </div>
            <h1
              className="text-[20px] font-semibold tracking-tight"
              style={{ color: "#191919" }}
            >
              Done — and thank you.
            </h1>
            <p
              className="mx-auto mt-2 max-w-sm text-[14px] leading-relaxed"
              style={{ color: "#8a847b" }}
            >
              {resultMsg}
            </p>
            <a
              href="https://concerto.run"
              className="mt-6 inline-flex items-center justify-center gap-2 rounded-xl px-5 text-[14px] font-semibold transition-opacity hover:opacity-90"
              style={{
                backgroundColor: "#cc785c",
                color: "#fff",
                minHeight: "46px",
              }}
            >
              Back to Concerto
            </a>
          </div>
        ) : (
          <div
            className="rounded-2xl px-7 py-8"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <a
              href="https://concerto.run"
              className="mb-6 inline-flex items-center gap-1.5 text-[13px] transition-opacity hover:opacity-70"
              style={{ color: "#8a847b" }}
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back
            </a>

            <h1
              className="text-[22px] font-semibold tracking-tight"
              style={{ color: "#191919" }}
            >
              Cancel your subscription
            </h1>
            <p
              className="mt-2 text-[14px] leading-relaxed"
              style={{ color: "#8a847b" }}
            >
              You&apos;ll keep full access until the end of the period
              you&apos;ve already paid for — nothing is cut off today. Before
              you go, what&apos;s the main reason? It genuinely helps us.
            </p>

            <div className="mt-6 space-y-2">
              {REASONS.map((rsn) => (
                <button
                  key={rsn}
                  type="button"
                  onClick={() => setReason(rsn)}
                  className="flex w-full items-center justify-between rounded-xl px-4 py-3 text-left text-[14px] transition-all"
                  style={{
                    backgroundColor: reason === rsn ? "#fef8f5" : "#faf9f5",
                    border:
                      reason === rsn
                        ? "1.5px solid #cc785c"
                        : "1px solid #f3efe5",
                    color: "#191919",
                  }}
                >
                  {rsn}
                  {reason === rsn && (
                    <Check
                      className="h-4 w-4 shrink-0"
                      style={{ color: "#cc785c" }}
                      strokeWidth={2.5}
                    />
                  )}
                </button>
              ))}
            </div>

            <textarea
              value={detail}
              onChange={(e) => setDetail(e.target.value)}
              placeholder="Anything more you'd like us to know? (optional)"
              rows={3}
              className="mt-4 w-full rounded-xl px-4 py-3 text-[14px] outline-none transition-shadow focus:shadow-[0_0_0_3px_rgba(204,120,92,0.15)]"
              style={{
                backgroundColor: "#fff",
                border: "1px solid #f3efe5",
                color: "#191919",
                resize: "vertical",
              }}
            />

            <Button
              onClick={submitCancel}
              disabled={!reason || phase === "sending"}
              className="mt-6 w-full rounded-xl text-[15px] font-medium"
              style={{
                backgroundColor: "#cc785c",
                color: "#fff",
                minHeight: "48px",
              }}
            >
              {phase === "sending" ? (
                <>
                  <RotateCcw className="mr-2 h-4 w-4 animate-spin" />
                  Cancelling…
                </>
              ) : (
                "Confirm cancellation"
              )}
            </Button>

            {phase === "error" && (
              <p
                className="mt-3 text-center text-[13px] leading-relaxed"
                style={{ color: "#b91c1c" }}
              >
                {resultMsg}
              </p>
            )}

            <p
              className="mt-5 text-center text-[12px] leading-relaxed"
              style={{ color: "#8a847b" }}
            >
              Changed your mind? Just close this page — nothing happens until
              you confirm. Need help instead?{" "}
              <a
                href="mailto:support@concerto.run"
                className="underline transition-opacity hover:opacity-70"
                style={{ color: "#cc785c" }}
              >
                support@concerto.run
              </a>
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
