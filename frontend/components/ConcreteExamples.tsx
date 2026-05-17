"use client"

const cards = [
  {
    quote: "Build and deploy this landing page",
    body: "Claude breaks it into frontend, deployment, DNS, and verification sessions. You get the live URL back in chat.",
  },
  {
    quote: "Fix this bug in my repo",
    body: "Claude reads the failing logs, launches debug sessions, tests fixes, and tells you exactly what changed.",
  },
  {
    quote: "Run three implementation attempts in parallel",
    body: "Claude launches three Claude Code sessions with different approaches, compares the outputs, and recommends the best one.",
  },
  {
    quote: "Audit my repo, tests, and deployment setup",
    body: "Claude launches sessions for repo structure, test coverage, and deploy config, then gives you a clean report.",
  },
]

export function ConcreteExamples() {
  return (
    <section className="px-6 py-24 bg-[#f3efe5]">
      <div className="mx-auto max-w-6xl">
        <div className="reveal mb-14 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            Concrete examples
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {cards.map((card, i) => (
            <div
              key={card.quote}
              className={`reveal reveal-d${i + 1} rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-7 shadow-[0_1px_2px_rgba(25,25,25,0.04)]`}
            >
              <p className="mb-4 text-base italic font-medium text-[#191919]">
                &ldquo;{card.quote}&rdquo;
              </p>
              <p className="text-sm leading-relaxed text-[#8a847b]">{card.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
