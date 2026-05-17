"use client"

import { useState } from "react"

const CONCEPTS = [
  {
    id: "concept-a-typographic-c",
    label: "A",
    name: "Typographic C",
    slug: "concept-a-typographic-c",
    signatureMove:
      "Lower terminal bracket-foot: a horizontal spur extending 12px right of the arc edge, 3.5px tall. References the musical system bracket and the square bracket notation ⌐. Absent on the upper terminal — the asymmetry gives the mark directionality and grounds it visually. At 16px the foot collapses to base weight; the C reads cleanly. At 256px the foot is the signature element separating this from any stock C.",
    designDecisions: [
      "Outer radius 70, inner radius 53 with +5px eccentric offset — creates thick (18px) at left, lighter (12px) at terminal without changing the arc radii",
      "Opening angle ±35° from horizontal right — 70° mouth, wider than typical for a C, allowing the mark to breathe without losing enclosure",
      "Terminal cut angle ≈48° — determined by the geometry, not arbitrary. Sits between 45° (mechanical) and 55° (too steep)",
      "The bracket-foot width (21px) is exactly the same as the C's thin stroke at the terminal — it reads as a continuation of the stroke mass, not an addition",
    ],
  },
  {
    id: "concept-b-parallel-geometric",
    label: "B",
    name: "Parallel Geometric",
    slug: "concept-b-parallel-geometric",
    signatureMove:
      "The top-left corner of each parallelogram has a triangular notch — 4×4px on bottom, 3.5×3.5px on middle, 3×3px on top. This notch reads as a play-button indent, suggesting \"execution begins here.\" It's the mechanical mark of parallel session launch. At 16px all notches disappear; at 64px+ they are clearly the defining gesture. No competitor mark uses this — it is specific to the idea of multiple concurrent processes starting.",
    designDecisions: [
      "Three bars in ratio 14:10:7 ≈ 1:0.71:0.5 — close to golden ratio cascade (1:0.618:0.382), creating proportional harmony without mechanical regularity",
      "Lean: 1px horizontal per 7px vertical = 8.1°, not the typical 45° or 30°. Chosen so bars feel in motion but not so steep they read as italic",
      "Flush right edge — the visual anchor is the RIGHT side (where parallel sessions converge), not the left (where they diverge in start time)",
      "Bar widths 80:65:52 — staircase stepping 15px each time on the left edge. Consistent delta creates visual rhythm",
    ],
  },
  {
    id: "concept-c-workshop-bracket",
    label: "C",
    name: "Workshop Bracket",
    slug: "concept-c-workshop-bracket",
    signatureMove:
      "The left bracket is 67% heavier than the right (10px vs 6px arm width). In musical notation, system brackets are uniform weight. This deliberate asymmetry is the mark's identity: the heavy left is the container, the lighter right is the closure. It suggests containment with an open, airy right side — a workspace with a door. The crossbars at top and bottom are direct references to orchestral system brackets, making the musical-form reference legible without being literal.",
    designDecisions: [
      "Bracket arm angle: from outer (68,35)→(40,100), giving ~21° from vertical. Specific to the 130px span and 28px inward travel",
      "Dot at golden ratio from top: y = 35 + 0.382×130 = 84.7 ≈ 85. Off-center vertically, creating tension — not resting, active",
      "Crossbar widths: 36px each (both brackets), but left crossbar is 7px tall and right is 4px tall. Same width, different weight reinforces the asymmetry",
      "Inner arm perpendicular offset: 10px left / 6px right — computed from the actual arm direction, not approximated",
    ],
  },
  {
    id: "concept-d-monogram-co",
    label: "D",
    name: "Monogram Co",
    slug: "concept-d-monogram-co",
    signatureMove:
      "The o's top tangent aligns precisely with the C's upper terminal at y=67. This shared top line makes the eye trace across both letters as a single continuous form — the mark reads as \"Co\" but feels like one glyph. The C's opening is asymmetric: -30° above (tight, hugging the o) and +45° below (open, giving breathing room). This asymmetry is the geometric decision that enables the alignment. No standard monogram uses this construction.",
    designDecisions: [
      "C outer radius 62, inner radius 45 with +5px eccentric offset. Same thick-thin logic as Concept A but scaled to leave room for the o",
      "o oval: rx=22, ry=25 (taller than wide). An optically round shape in typography is taller than it is wide — this is the optical correction that makes ovals feel circular",
      "o center at (150, 92) — 6px above C center (98). The upward offset causes the o to sit in the upper region of the C's mouth, creating asymmetric composition",
      "Both C body and o ring are same fill color — where they overlap (o left edge ~128 vs C inner wall ~131.6 at y=92), they merge naturally without requiring clipping or masking",
    ],
  },
]

type ConceptId = typeof CONCEPTS[number]["id"]

export function LogoConceptsClient() {
  const [selected, setSelected] = useState<ConceptId | null>(null)

  return (
    <div
      style={{
        fontFamily: "'Fraunces', 'Times New Roman', serif",
        background: "#faf9f5",
        minHeight: "100vh",
        color: "#2a2925",
      }}
    >
      {/* Header */}
      <div
        style={{
          borderBottom: "1px solid #e8e4dc",
          padding: "32px 48px 28px",
          display: "flex",
          alignItems: "baseline",
          gap: "24px",
        }}
      >
        <span style={{ fontSize: "22px", fontWeight: 300, letterSpacing: "-0.5px" }}>
          Concerto
        </span>
        <span
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            fontWeight: 400,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
          }}
        >
          Logo v3 · Internal Review · noindex
        </span>
        {selected && (
          <button
            onClick={() => setSelected(null)}
            style={{
              marginLeft: "auto",
              fontFamily: "monospace",
              fontSize: "11px",
              background: "none",
              border: "1px solid #e8e4dc",
              padding: "4px 12px",
              borderRadius: "3px",
              cursor: "pointer",
              color: "#6b6560",
            }}
          >
            ← All concepts
          </button>
        )}
      </div>

      {/* Intro */}
      {!selected && (
        <div style={{ padding: "48px 48px 32px" }}>
          <p
            style={{
              fontSize: "15px",
              lineHeight: 1.7,
              color: "#6b6560",
              maxWidth: "640px",
              fontFamily: "monospace",
              fontWeight: 400,
            }}
          >
            4 finished brand marks. Each has a specific signature move, construction grid, scale
            study across 6 sizes, and 6 colorways. Click any concept to explore. Click &quot;Pick this
            one&quot; to mark your selection.
          </p>
        </div>
      )}

      {/* Concept grid or detail */}
      {!selected ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1px",
            background: "#e8e4dc",
            borderTop: "1px solid #e8e4dc",
          }}
        >
          {CONCEPTS.map((concept) => (
            <ConceptCard
              key={concept.id}
              concept={concept}
              onSelect={() => setSelected(concept.id)}
            />
          ))}
        </div>
      ) : (
        <ConceptDetail
          concept={CONCEPTS.find((c) => c.id === selected)!}
          onPick={() => {
            const name = CONCEPTS.find((c) => c.id === selected)?.name
            alert(`Picked: ${name}. Send this back to the team.`)
          }}
        />
      )}
    </div>
  )
}

function ConceptCard({
  concept,
  onSelect,
}: {
  concept: (typeof CONCEPTS)[number]
  onSelect: () => void
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        background: "#faf9f5",
        padding: "48px",
        cursor: "pointer",
        transition: "background 0.15s",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = "#f3efe5")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "#faf9f5")}
    >
      {/* Mark at 128px */}
      <div
        style={{
          width: 128,
          height: 128,
          marginBottom: "32px",
        }}
      >
        <img
          src={`/logo-concepts-v3/${concept.slug}/mark.svg`}
          width={128}
          height={128}
          alt={`Concept ${concept.label} mark`}
          style={{ display: "block" }}
        />
      </div>

      {/* Label */}
      <div style={{ marginBottom: "8px", display: "flex", alignItems: "baseline", gap: "12px" }}>
        <span
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#cc785c",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Concept {concept.label}
        </span>
        <span style={{ fontSize: "20px", fontWeight: 300, letterSpacing: "-0.3px" }}>
          {concept.name}
        </span>
      </div>

      {/* Signature move teaser */}
      <p
        style={{
          fontFamily: "monospace",
          fontSize: "11px",
          lineHeight: 1.7,
          color: "#6b6560",
          maxWidth: "360px",
          marginBottom: "24px",
        }}
      >
        {concept.signatureMove.slice(0, 140)}…
      </p>

      {/* Lockup preview */}
      <img
        src={`/logo-concepts-v3/${concept.slug}/lockup.svg`}
        height={40}
        alt={`Concept ${concept.label} lockup`}
        style={{ display: "block", opacity: 0.85 }}
      />
    </div>
  )
}

function ConceptDetail({
  concept,
  onPick,
}: {
  concept: (typeof CONCEPTS)[number]
  onPick: () => void
}) {
  return (
    <div style={{ maxWidth: "1200px", padding: "0 48px 96px" }}>
      {/* Hero — mark at 256px */}
      <div
        style={{
          padding: "64px 0 48px",
          display: "flex",
          alignItems: "flex-start",
          gap: "64px",
          borderBottom: "1px solid #e8e4dc",
        }}
      >
        <div>
          <img
            src={`/logo-concepts-v3/${concept.slug}/mark.svg`}
            width={256}
            height={256}
            alt={`Concept ${concept.label} mark at 256px`}
            style={{ display: "block" }}
          />
        </div>
        <div style={{ flex: 1, paddingTop: "8px" }}>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "11px",
              color: "#cc785c",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginBottom: "12px",
            }}
          >
            Concept {concept.label}
          </div>
          <h1
            style={{
              fontSize: "36px",
              fontWeight: 300,
              letterSpacing: "-1px",
              margin: "0 0 24px",
            }}
          >
            {concept.name}
          </h1>
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "12px",
              lineHeight: 1.8,
              color: "#4a4540",
              maxWidth: "480px",
              marginBottom: "32px",
            }}
          >
            <strong style={{ color: "#2a2925", display: "block", marginBottom: "8px" }}>
              Signature move:
            </strong>
            {concept.signatureMove}
          </div>
          <button
            onClick={onPick}
            style={{
              background: "#cc785c",
              color: "#faf9f5",
              border: "none",
              padding: "12px 28px",
              fontSize: "14px",
              fontFamily: "'Fraunces', serif",
              fontWeight: 300,
              letterSpacing: "-0.2px",
              borderRadius: "2px",
              cursor: "pointer",
            }}
          >
            Pick this one →
          </button>
        </div>
      </div>

      {/* Design decisions */}
      <div
        style={{
          padding: "48px 0",
          borderBottom: "1px solid #e8e4dc",
        }}
      >
        <h2
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            margin: "0 0 24px",
          }}
        >
          Design decisions
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          {concept.designDecisions.map((decision, i) => (
            <div
              key={i}
              style={{
                background: "#f3efe5",
                padding: "20px 24px",
                borderRadius: "2px",
                fontFamily: "monospace",
                fontSize: "11px",
                lineHeight: 1.7,
                color: "#4a4540",
              }}
            >
              {decision}
            </div>
          ))}
        </div>
      </div>

      {/* Construction grid */}
      <div
        style={{
          padding: "48px 0",
          borderBottom: "1px solid #e8e4dc",
        }}
      >
        <h2
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            margin: "0 0 24px",
          }}
        >
          Construction grid
        </h2>
        <img
          src={`/logo-concepts-v3/${concept.slug}/construction-grid.svg`}
          style={{ display: "block", maxWidth: "480px", width: "100%" }}
          alt="Construction grid"
        />
      </div>

      {/* Scale chart */}
      <div
        style={{
          padding: "48px 0",
          borderBottom: "1px solid #e8e4dc",
        }}
      >
        <h2
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            margin: "0 0 24px",
          }}
        >
          Scale chart — 16 to 128px
        </h2>
        <img
          src={`/logo-concepts-v3/${concept.slug}/scale-chart.svg`}
          style={{ display: "block", width: "100%", maxWidth: "640px" }}
          alt="Scale chart"
        />
      </div>

      {/* Colorways */}
      <div
        style={{
          padding: "48px 0",
          borderBottom: "1px solid #e8e4dc",
        }}
      >
        <h2
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            margin: "0 0 24px",
          }}
        >
          Colorways — 9 variants
        </h2>
        <img
          src={`/logo-concepts-v3/${concept.slug}/colorways.svg`}
          style={{ display: "block", width: "100%", maxWidth: "540px" }}
          alt="Color variants"
        />
      </div>

      {/* Wordmark and lockup */}
      <div style={{ padding: "48px 0" }}>
        <h2
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            margin: "0 0 32px",
          }}
        >
          Wordmark &amp; lockup — Fraunces 300
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          <div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: "10px",
                color: "#9b9490",
                marginBottom: "12px",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              Wordmark
            </div>
            <div style={{ background: "#f3efe5", padding: "24px", borderRadius: "2px" }}>
              <img
                src={`/logo-concepts-v3/${concept.slug}/wordmark.svg`}
                height={50}
                alt="Wordmark"
                style={{ display: "block" }}
              />
            </div>
          </div>
          <div>
            <div
              style={{
                fontFamily: "monospace",
                fontSize: "10px",
                color: "#9b9490",
                marginBottom: "12px",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}
            >
              Lockup (mark + wordmark)
            </div>
            <div style={{ background: "#f3efe5", padding: "24px", borderRadius: "2px" }}>
              <img
                src={`/logo-concepts-v3/${concept.slug}/lockup.svg`}
                height={60}
                alt="Lockup"
                style={{ display: "block" }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div
        style={{
          display: "flex",
          gap: "16px",
          alignItems: "center",
          padding: "32px 0 0",
          borderTop: "1px solid #e8e4dc",
        }}
      >
        <button
          onClick={onPick}
          style={{
            background: "#cc785c",
            color: "#faf9f5",
            border: "none",
            padding: "14px 32px",
            fontSize: "16px",
            fontFamily: "'Fraunces', serif",
            fontWeight: 300,
            letterSpacing: "-0.3px",
            borderRadius: "2px",
            cursor: "pointer",
          }}
        >
          Pick Concept {concept.label} — {concept.name}
        </button>
        <span
          style={{
            fontFamily: "monospace",
            fontSize: "11px",
            color: "#9b9490",
          }}
        >
          Ethan selects → team executes
        </span>
      </div>
    </div>
  )
}
