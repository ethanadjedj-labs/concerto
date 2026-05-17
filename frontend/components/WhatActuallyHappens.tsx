"use client"

const bullets = [
  "Claude breaks the work into Claude Code sessions, picking the right model for each",
  "Claude launches them and monitors logs and progress in real time",
  "Claude catches stuck runs, compares parallel attempts, and adjusts",
  "Claude reports back with what changed — and what needs your call",
]

export function WhatActuallyHappens() {
  return (
    <section id="how" className="px-6 py-24 bg-[#f3efe5]">
      <div className="mx-auto max-w-3xl">
        <div className="reveal mb-10 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            What happens after you ask Claude
          </h2>
        </div>

        <div className="reveal rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)]">
          <p className="mb-8 text-base leading-relaxed text-[#555049]">
            You ask Claude normally. Claude breaks the work into Claude Code sessions, picks the right model for each, launches them, watches the logs, catches stuck runs, compares parallel attempts, and reports back with what changed — and what needs your call.
          </p>

          <ul className="space-y-3.5">
            {bullets.map((b) => (
              <li key={b} className="flex items-start gap-3 text-sm leading-relaxed text-[#555049]">
                <span className="mt-1 shrink-0 text-[#cc785c]" aria-hidden="true">•</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
