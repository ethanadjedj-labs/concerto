"use client"

const steps = [
  {
    n: 1,
    title: "You ask Claude",
    body: 'Example: "Build a landing page and deploy it."',
  },
  {
    n: 2,
    title: "Claude plans the work",
    body: "Claude breaks the request into separate tasks: frontend, deployment, DNS, testing.",
  },
  {
    n: 3,
    title: "Claude launches Claude Code sessions",
    body: "Each session runs on your remote machine with its own task.",
  },
  {
    n: 4,
    title: "Claude monitors progress",
    body: "Claude checks logs, sees errors, detects stuck runs, and follows what each session is doing.",
  },
  {
    n: 5,
    title: "Claude analyzes the results",
    body: "If several sessions try different approaches, Claude compares them and keeps the best output.",
  },
  {
    n: 6,
    title: "Claude reports back",
    body: "You get a clear summary: what worked, what failed, what changed, and what decision is needed.",
  },
]

export function WhatActuallyHappens() {
  return (
    <section id="how" className="px-6 py-24 bg-[#f3efe5]">
      <div className="mx-auto max-w-6xl">
        <div className="reveal mb-14 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            What actually happens
          </h2>
          <p className="text-[#8a847b]">
            Exactly what Claude does after you send a message.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {steps.map((step, i) => (
            <div
              key={step.n}
              className={`reveal reveal-d${(i % 3) + 1} flex gap-5 rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-7 shadow-[0_1px_2px_rgba(25,25,25,0.04)]`}
            >
              <div className="shrink-0 pt-0.5">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[rgba(204,120,92,0.10)] font-mono text-sm font-medium text-[#cc785c]">
                  {step.n}
                </span>
              </div>
              <div>
                <h3 className="mb-2 text-[15px] font-medium text-[#191919]">
                  {step.title}
                </h3>
                <p className="text-sm leading-relaxed text-[#8a847b]">{step.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
