"use client"

type SessionStatus = "working" | "done" | "needs-input"

interface SessionCard {
  name: string
  status: SessionStatus
}

const sessions: SessionCard[] = [
  { name: "frontend", status: "working" },
  { name: "tests", status: "done" },
  { name: "deploy", status: "done" },
  { name: "review", status: "needs-input" },
]

function StatusBadge({ status }: { status: SessionStatus }) {
  if (status === "working") {
    return (
      <span className="inline-flex min-w-0 shrink-0 items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium bg-[rgba(204,120,92,0.10)] text-[#cc785c]">
        <span className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[#cc785c] animate-dot-blink" />
        working
      </span>
    )
  }
  if (status === "needs-input") {
    return (
      <span className="inline-flex min-w-0 shrink-0 items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium bg-[rgba(138,132,123,0.12)] text-[#8a847b]">
        <span className="text-[10px] font-bold leading-none">?</span>
        needs input
      </span>
    )
  }
  return (
    <span className="inline-flex min-w-0 shrink-0 items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium bg-[rgba(204,120,92,0.10)] text-[#cc785c]">
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
        <path d="M2 5l2.5 2.5L8 3" stroke="#cc785c" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      done
    </span>
  )
}

export function SessionCardsDiagram() {
  return (
    <section className="px-6 py-20 bg-[#faf9f5]">
      <div className="mx-auto max-w-6xl">
        <div className="reveal mb-12 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            One chat. Four parallel sessions.
          </h2>
        </div>

        <div className="reveal mx-auto max-w-3xl rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-6 shadow-[0_1px_4px_rgba(25,25,25,0.06)] sm:p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:gap-10">

            {/* Left: user request */}
            <div className="md:w-[42%]">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#8a847b]">
                You say
              </p>
              <div className="rounded-lg border border-[rgba(25,25,25,0.08)] bg-[#faf9f5] p-4">
                <p className="text-sm font-medium text-[#191919] leading-relaxed">
                  &ldquo;Build and deploy this landing page&rdquo;
                </p>
              </div>
            </div>

            {/* Right: 4 session cards in 2×2 grid */}
            <div className="flex-1 min-w-0">
              <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#8a847b]">
                Claude launches
              </p>
              <div className="grid grid-cols-2 gap-2">
                {sessions.map((session) => (
                  <div
                    key={session.name}
                    className="flex min-w-0 flex-wrap items-center justify-between gap-1.5 rounded-lg border border-[rgba(25,25,25,0.08)] bg-[#faf9f5] px-3 py-2.5"
                  >
                    <span className="truncate font-mono text-[12px] text-[#191919]">{session.name}</span>
                    <StatusBadge status={session.status} />
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Arrow */}
          <div className="my-6 flex items-center justify-center">
            <svg width="16" height="24" viewBox="0 0 16 24" fill="none" aria-hidden="true">
              <path
                d="M8 2v16M3 13l5 6 5-6"
                stroke="#cc785c"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.40"
              />
            </svg>
          </div>

          {/* Bottom: Claude summary */}
          <div>
            <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-[#8a847b]">
              Claude reports back
            </p>
            <div className="rounded-lg border border-[rgba(204,120,92,0.20)] bg-[rgba(204,120,92,0.04)] p-4">
              <p className="text-sm text-[#555049] leading-relaxed">
                &ldquo;Project built and deployed. Tests passing. Live at concerto.run.&rdquo;
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
