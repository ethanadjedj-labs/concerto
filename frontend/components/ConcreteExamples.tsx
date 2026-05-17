"use client"

const cards = [
  {
    quote: "Create a landing page",
    body: "Claude launches one session for the frontend, one for deployment, one for DNS/checks, then reports the live URL.",
  },
  {
    quote: "Fix this bug",
    body: "Claude launches debugging sessions, reads logs, tests fixes, and tells you what changed.",
  },
  {
    quote: "Try three approaches",
    body: "Claude runs three Claude Code sessions in parallel, compares the outputs, and recommends the best one.",
  },
  {
    quote: "Audit my project",
    body: "Claude launches sessions for repo structure, security, tests, and deployment, then gives you a clean report.",
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
