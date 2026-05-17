"use client"

const beforeItems = [
  "You ask Claude for help.",
  "You copy the plan into Claude Code.",
  "You watch the terminal.",
  "You paste errors back into Claude.",
  "You restart sessions manually.",
  "You check GitHub/Vercel yourself.",
  "You lose the overview.",
]

const afterItems = [
  "You ask Claude once.",
  "Claude launches the right Claude Code sessions.",
  "Claude monitors them.",
  "Claude reads the logs.",
  "Claude compares outputs.",
  "Claude reports back in chat.",
]

export function BeforeAfter() {
  return (
    <section className="px-6 py-24 bg-[#faf9f5]">
      <div className="mx-auto max-w-4xl">
        <div className="reveal mb-14 text-center">
          <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
            Before / After
          </h2>
        </div>

        <div className="reveal grid grid-cols-1 gap-5 md:grid-cols-2">
          {/* Before */}
          <div className="rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-7">
            <h3 className="mb-5 text-xs font-semibold uppercase tracking-widest text-[#a09a94]">
              Before Concerto
            </h3>
            <ul className="space-y-3">
              {beforeItems.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm">
                  <span className="mt-0.5 shrink-0 text-[#a09a94]">×</span>
                  <span className="text-[#a09a94]">{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* After */}
          <div className="rounded-lg border border-[rgba(204,120,92,0.25)] bg-white p-7">
            <h3 className="mb-5 text-xs font-semibold uppercase tracking-widest text-[#cc785c]">
              With Concerto
            </h3>
            <ul className="space-y-3">
              {afterItems.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm">
                  <span className="mt-0.5 shrink-0 text-[#cc785c]">→</span>
                  <span className="text-[#555049]">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}
