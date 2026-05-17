"use client"

import { useState } from "react"

// ─── Inline mark components (color-prop, no <img>) ───────────────────────────

function C1Mark({ color = "#cc785c" }: { color?: string }) {
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style={{ display: "block", width: "100%", height: "100%" }}>
      <defs>
        <mask id="c1m-page">
          <rect width="100" height="100" fill="white" />
          <circle cx="50" cy="50" r="28" fill="black" />
          <polygon points="50,50 130,0 130,100" fill="black" />
        </mask>
      </defs>
      <circle cx="50" cy="50" r="43" fill={color} mask="url(#c1m-page)" />
    </svg>
  )
}

function C2Mark({ color = "#cc785c" }: { color?: string }) {
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style={{ display: "block", width: "100%", height: "100%" }}>
      <rect x="10" y="18" width="34" height="72" fill={color} />
      <rect x="56" y="42" width="34" height="48" fill={color} />
    </svg>
  )
}

function C3Mark({ color = "#cc785c" }: { color?: string }) {
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style={{ display: "block", width: "100%", height: "100%" }}>
      <line x1="5" y1="84" x2="95" y2="84" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <path d="M 14 59 A 36 36 0 0 1 86 59" fill="none" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <circle cx="50" cy="59" r="11" fill={color} />
    </svg>
  )
}

function C4Mark({ color = "#cc785c" }: { color?: string }) {
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style={{ display: "block", width: "100%", height: "100%" }}>
      <line x1="8" y1="62" x2="8" y2="82" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <line x1="8" y1="72" x2="92" y2="72" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <line x1="92" y1="62" x2="92" y2="82" stroke={color} strokeWidth="9" strokeLinecap="round" />
      <path d="M 8 72 C 28 18 72 18 92 72" fill="none" stroke={color} strokeWidth="9" strokeLinecap="round" />
    </svg>
  )
}

function C5Mark({ color = "#cc785c" }: { color?: string }) {
  return (
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" style={{ display: "block", width: "100%", height: "100%" }}>
      <path
        d="M 24 15 L 80 50 L 24 85"
        fill="none"
        stroke={color}
        strokeWidth="18"
        strokeLinejoin="miter"
        strokeMiterlimit={8}
        strokeLinecap="square"
      />
    </svg>
  )
}

// ─── Data ────────────────────────────────────────────────────────────────────

const CONCEPTS = [
  {
    id: 1,
    slug: "concept-1-c-serif",
    name: "C-Serif",
    direction: "Typographic mark",
    rationale:
      "A bold donut C — the brand initial rendered with editorial weight. Clean ring with a ±32° gap at 3 o'clock; no stroke, no decoration. Reads instantly at 16 px, scales to a strong app icon at 512 px.",
    Mark: C1Mark,
  },
  {
    id: 2,
    slug: "concept-2-dual-bar",
    name: "Dual-Bar",
    direction: "Geometric abstract",
    rationale:
      "Two bottom-aligned rectangles of different heights: the tall bar (orchestra) and the shorter bar (soloist). Represents the parallel sessions Concerto orchestrates — simple enough to never be mistaken for anything else.",
    Mark: C2Mark,
  },
  {
    id: 3,
    slug: "concept-3-fermata",
    name: "Fermata",
    direction: "Musical reference (subtle)",
    rationale:
      "The fermata (𝄐) — hold indefinitely, let the sound bloom. A thick baseline, a single bold dot, a dome arc above. Reads as tech-product at a glance but rewards anyone who knows the music reference.",
    Mark: C3Mark,
  },
  {
    id: 4,
    slug: "concept-4-signal",
    name: "Signal",
    direction: "Waveform / signal",
    rationale:
      "A single clean sine arch between two grounded ticks — the work Concerto orchestrates rising above a baseline. Echoes Anthropic's spark energy adapted to a ground-signal metaphor. Distinctive at every size.",
    Mark: C4Mark,
  },
  {
    id: 5,
    slug: "concept-5-caret",
    name: "Caret",
    direction: "Wild card",
    rationale:
      "A bold miter-joined chevron: the conductor's decisive downbeat, the shell prompt character, the universal 'begin'. Sharp, intentional, immediately legible. Nothing like it in current dev-tool branding.",
    Mark: C5Mark,
  },
]

const SIZES = [16, 32, 64, 128, 256]

// ─── Component ────────────────────────────────────────────────────────────────

export function LogoConceptsClient() {
  const [voted, setVoted] = useState<number | null>(null)

  return (
    <main style={{ background: "#faf9f5", minHeight: "100vh", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ borderBottom: "1px solid #e8e2d9", padding: "32px 48px 24px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <p style={{ fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase", color: "#aaa", marginBottom: 8, margin: "0 0 8px" }}>
            Internal review · not indexed
          </p>
          <h1
            style={{
              fontFamily: "Fraunces, 'Palatino Linotype', Georgia, serif",
              fontSize: 40,
              fontWeight: 500,
              color: "#191919",
              margin: "0 0 8px",
              letterSpacing: "-0.5px",
            }}
          >
            Concerto — Logo Concepts
          </h1>
          <p style={{ color: "#666", margin: 0, fontSize: 15, lineHeight: 1.6 }}>
            5 distinct directions replacing the orbital mark. Each shown at 16 → 256 px on cream and dark
            backgrounds. Click <strong>Vote for this</strong> to mark your pick.
          </p>
        </div>
      </div>

      {/* Concepts */}
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "48px" }}>
        {CONCEPTS.map((concept) => {
          const { Mark } = concept
          const isVoted = voted === concept.id

          return (
            <section
              key={concept.id}
              style={{
                marginBottom: 80,
                paddingBottom: 80,
                borderBottom: "1px solid #e8e2d9",
              }}
            >
              {/* Concept header */}
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: 32,
                  marginBottom: 32,
                }}
              >
                <div style={{ flex: 1 }}>
                  <p
                    style={{
                      fontSize: 11,
                      color: "#bbb",
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      margin: "0 0 4px",
                    }}
                  >
                    {concept.id} · {concept.direction}
                  </p>
                  <h2
                    style={{
                      fontFamily: "Fraunces, 'Palatino Linotype', Georgia, serif",
                      fontSize: 28,
                      fontWeight: 500,
                      color: "#191919",
                      margin: "0 0 8px",
                      letterSpacing: "-0.3px",
                    }}
                  >
                    {concept.name}
                  </h2>
                  <p style={{ color: "#555", fontSize: 14, maxWidth: 560, margin: 0, lineHeight: 1.6 }}>
                    {concept.rationale}
                  </p>
                </div>

                <button
                  onClick={() => setVoted(isVoted ? null : concept.id)}
                  style={{
                    padding: "10px 22px",
                    borderRadius: 6,
                    border: isVoted ? "2px solid #cc785c" : "2px solid #ddd",
                    background: isVoted ? "#cc785c" : "transparent",
                    color: isVoted ? "#faf9f5" : "#555",
                    fontWeight: 600,
                    fontSize: 14,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                    fontFamily: "inherit",
                  }}
                >
                  {isVoted ? "✓ Selected" : "Vote for this"}
                </button>
              </div>

              {/* Lockup */}
              <div style={{ marginBottom: 28 }}>
                <p
                  style={{
                    fontSize: 10,
                    color: "#bbb",
                    textTransform: "uppercase",
                    letterSpacing: "0.12em",
                    margin: "0 0 10px",
                  }}
                >
                  Lockup
                </p>
                <div
                  style={{
                    background: "#faf9f5",
                    border: "1px solid #e8e2d9",
                    borderRadius: 8,
                    padding: "20px 28px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 16,
                  }}
                >
                  <div style={{ width: 48, height: 48, flexShrink: 0 }}>
                    <Mark color="#cc785c" />
                  </div>
                  <span
                    style={{
                      fontFamily: "Fraunces, 'Palatino Linotype', Georgia, serif",
                      fontSize: 32,
                      fontWeight: 500,
                      color: "#191919",
                      letterSpacing: "-0.5px",
                      lineHeight: 1,
                    }}
                  >
                    Concerto
                  </span>
                </div>
              </div>

              {/* 3-column size grid */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20 }}>
                {/* Peach on cream */}
                <div>
                  <p
                    style={{
                      fontSize: 10,
                      color: "#bbb",
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      margin: "0 0 10px",
                    }}
                  >
                    Peach on cream
                  </p>
                  <div
                    style={{
                      background: "#faf9f5",
                      border: "1px solid #e8e2d9",
                      borderRadius: 8,
                      padding: 16,
                      display: "flex",
                      alignItems: "flex-end",
                      gap: 14,
                      flexWrap: "wrap",
                    }}
                  >
                    {SIZES.map((sz) => (
                      <div key={sz} style={{ textAlign: "center" }}>
                        <div style={{ width: sz, height: sz }}>
                          <Mark color="#cc785c" />
                        </div>
                        <p style={{ fontSize: 9, color: "#ccc", margin: "4px 0 0", lineHeight: 1 }}>{sz}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Dark on cream */}
                <div>
                  <p
                    style={{
                      fontSize: 10,
                      color: "#bbb",
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      margin: "0 0 10px",
                    }}
                  >
                    Dark on cream
                  </p>
                  <div
                    style={{
                      background: "#faf9f5",
                      border: "1px solid #e8e2d9",
                      borderRadius: 8,
                      padding: 16,
                      display: "flex",
                      alignItems: "flex-end",
                      gap: 14,
                      flexWrap: "wrap",
                    }}
                  >
                    {SIZES.map((sz) => (
                      <div key={sz} style={{ textAlign: "center" }}>
                        <div style={{ width: sz, height: sz }}>
                          <Mark color="#191919" />
                        </div>
                        <p style={{ fontSize: 9, color: "#ccc", margin: "4px 0 0", lineHeight: 1 }}>{sz}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Peach on dark */}
                <div>
                  <p
                    style={{
                      fontSize: 10,
                      color: "#bbb",
                      textTransform: "uppercase",
                      letterSpacing: "0.12em",
                      margin: "0 0 10px",
                    }}
                  >
                    Peach on dark
                  </p>
                  <div
                    style={{
                      background: "#191919",
                      borderRadius: 8,
                      padding: 16,
                      display: "flex",
                      alignItems: "flex-end",
                      gap: 14,
                      flexWrap: "wrap",
                    }}
                  >
                    {SIZES.map((sz) => (
                      <div key={sz} style={{ textAlign: "center" }}>
                        <div style={{ width: sz, height: sz }}>
                          <Mark color="#cc785c" />
                        </div>
                        <p style={{ fontSize: 9, color: "#444", margin: "4px 0 0", lineHeight: 1 }}>{sz}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )
        })}

        {/* Side-by-side strip */}
        <section style={{ marginBottom: 48 }}>
          <h2
            style={{
              fontFamily: "Fraunces, 'Palatino Linotype', Georgia, serif",
              fontSize: 22,
              fontWeight: 500,
              color: "#191919",
              margin: "0 0 20px",
            }}
          >
            Side-by-side at 32 px
          </h2>

          {/* On cream */}
          <div
            style={{
              background: "#faf9f5",
              border: "1px solid #e8e2d9",
              borderRadius: 8,
              padding: "20px 24px",
              display: "flex",
              gap: 32,
              flexWrap: "wrap",
              marginBottom: 16,
            }}
          >
            {CONCEPTS.map((c) => (
              <div key={c.id} style={{ textAlign: "center" }}>
                <div style={{ width: 32, height: 32 }}>
                  <c.Mark color="#cc785c" />
                </div>
                <p style={{ fontSize: 10, color: "#bbb", margin: "6px 0 0" }}>{c.name}</p>
              </div>
            ))}
          </div>

          {/* On dark */}
          <div
            style={{
              background: "#191919",
              borderRadius: 8,
              padding: "20px 24px",
              display: "flex",
              gap: 32,
              flexWrap: "wrap",
            }}
          >
            {CONCEPTS.map((c) => (
              <div key={c.id} style={{ textAlign: "center" }}>
                <div style={{ width: 32, height: 32 }}>
                  <c.Mark color="#cc785c" />
                </div>
                <p style={{ fontSize: 10, color: "#444", margin: "6px 0 0" }}>{c.name}</p>
              </div>
            ))}
          </div>
        </section>

        {voted && (
          <div
            style={{
              background: "#cc785c",
              color: "#faf9f5",
              padding: "16px 24px",
              borderRadius: 8,
              fontSize: 15,
              fontWeight: 500,
            }}
          >
            You selected: <strong>{CONCEPTS.find((c) => c.id === voted)?.name}</strong>. Reply with this concept name
            to confirm the swap.
          </div>
        )}
      </div>
    </main>
  )
}
