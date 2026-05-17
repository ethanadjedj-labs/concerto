"use client"

const steps = [
  { n: 1, title: "You ask Claude normally" },
  { n: 2, title: "Claude breaks the work into sessions and picks the right model for each one" },
  { n: 3, title: "Claude launches Claude Code on your machine" },
  { n: 4, title: "Claude monitors logs and progress" },
  { n: 5, title: "Claude detects stuck runs or errors" },
  { n: 6, title: "Claude compares outputs if several sessions run in parallel" },
  { n: 7, title: "Claude reports back with what changed and what needs your decision" },
]

export function WhatActuallyHappens() {
  return (
    <section id="how" className="px-6 py-24 bg-[#f3efe5]">
      <div className="mx-auto max-w-6xl">
        <div className="reveal mb-14 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            What happens after you ask Claude
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {steps.map((step, i) => (
            <div
              key={step.n}
              className={`reveal reveal-d${(i % 3) + 1} flex gap-5 rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-6 shadow-[0_1px_2px_rgba(25,25,25,0.04)]`}
            >
              <div className="shrink-0 pt-0.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[rgba(204,120,92,0.10)] font-mono text-sm font-medium text-[#cc785c]">
                  {step.n}
                </span>
              </div>
              <div className="flex items-center">
                <h3 className="text-[15px] font-medium text-[#191919]">
                  {step.title}
                </h3>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
