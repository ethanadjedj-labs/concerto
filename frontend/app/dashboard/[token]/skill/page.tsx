"use client"

import { useState, useRef } from "react"
import { Check, Copy, ExternalLink, ArrowLeft } from "lucide-react"

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

function ConcertoSkillCard() {
  const [copiedDesc, setCopiedDesc] = useState(false)
  const [copiedInstr, setCopiedInstr] = useState(false)
  const dt = useRef<ReturnType<typeof setTimeout> | null>(null)
  const it = useRef<ReturnType<typeof setTimeout> | null>(null)

  const DESCRIPTION =
    "Use whenever the user asks to build, create, ship, scaffold, prototype, fix, refactor, test, or deploy software, an app, a website, a backend, a feature, or any non-trivial code project. Activates Concerto orchestration so Claude decomposes the work, announces a parallel plan, and fans out multiple autonomous Claude Code sessions on the user's machine instead of asking scoping questions or writing code inline in chat."

  async function copyText(
    t: string,
    set: (b: boolean) => void,
    ref: React.MutableRefObject<ReturnType<typeof setTimeout> | null>,
  ) {
    try {
      await navigator.clipboard.writeText(t)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = t
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    set(true)
    if (ref.current) clearTimeout(ref.current)
    ref.current = setTimeout(() => set(false), 2500)
  }

  async function copyInstructions() {
    const full = await fetch("/concerto-custom-style.txt").then((r) => r.text())
    // Strip YAML frontmatter — the Skill UI has separate name/description fields
    const body = full.replace(/^---[\s\S]*?---\s*/, "").trim()
    copyText(body, setCopiedInstr, it)
  }

  return (
    <div
      className="rounded-xl p-4 text-left"
      style={{ border: "1px solid #f3efe5", backgroundColor: "#fff" }}
    >
      <div className="mb-4">
        <p className="text-[15px] font-semibold" style={{ color: "#191919" }}>
          Add the Concerto Skill
        </p>
        <p
          className="mt-1 text-[13px] leading-relaxed"
          style={{ color: "#8a847b" }}
        >
          This is what makes Claude orchestrate builds in parallel
          automatically — so you never have to say &ldquo;use Concerto&rdquo;.
          One-time setup.
        </p>
      </div>
      {true && (
        <div className="space-y-4">
          <div
            className="rounded-xl p-4"
            style={{ backgroundColor: "#fffaf7", border: "1.5px solid #cc785c" }}
          >
            <p className="text-[13px] font-semibold" style={{ color: "#191919" }}>
              Fastest way — upload the ready-made file
            </p>
            <p
              className="mb-3 mt-1 text-[12px] leading-relaxed"
              style={{ color: "#8a847b" }}
            >
              Download the Skill, then in Claude open Skills and use
              &ldquo;Upload skill&rdquo;. Nothing to fill in by hand.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <a
                href="/downloads/concerto-skill.zip"
                download
                className="flex flex-1 items-center justify-center gap-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
                style={{ backgroundColor: "#cc785c", color: "#fff", minHeight: "42px" }}
              >
                Download Concerto Skill
              </a>
              <a
                href="https://claude.ai/customize/skills"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-1 items-center justify-center gap-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
                style={{ backgroundColor: "#fff", color: "#cc785c", border: "1px solid #cc785c", minHeight: "42px" }}
              >
                Open Skills <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
            <p className="mt-2 text-[12px]" style={{ color: "#8a847b" }}>
              Make sure <strong style={{ color: "#191919" }}>Code execution</strong>{" "}
              is on (Settings &rarr; Capabilities) first.
            </p>
          </div>

          <details className="group">
            <summary
              className="cursor-pointer list-none text-[13px] font-medium transition-opacity hover:opacity-70"
              style={{ color: "#8a847b" }}
            >
              Or create it manually with the three fields &rarr;
            </summary>
            <p className="mb-3 mt-3 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              In Skills, click <strong style={{ color: "#191919" }}>Create skill</strong>{" "}
              and fill these three fields:
            </p>

          <div className="space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8a847b" }}>
              Skill name
            </p>
            <div
              className="rounded-lg px-3 py-2 font-mono text-[13px]"
              style={{ backgroundColor: "#faf9f5", border: "1px solid #f3efe5", color: "#191919" }}
            >
              Concerto
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#b3613f" }}>
                Description (required — triggers it)
              </p>
              <button
                type="button"
                onClick={() => copyText(DESCRIPTION, setCopiedDesc, dt)}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-all"
                style={{ backgroundColor: copiedDesc ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
              >
                {copiedDesc ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copiedDesc ? "Copied" : "Copy"}
              </button>
            </div>
            <p
              className="max-h-20 overflow-y-auto rounded-lg px-3 py-2 text-[12px] leading-relaxed"
              style={{ backgroundColor: "#fffaf7", border: "1.5px solid #cc785c", color: "#191919" }}
            >
              {DESCRIPTION}
            </p>
            <p className="text-[12px]" style={{ color: "#8a847b" }}>
              If this field is empty, the Skill never auto-activates. Don&apos;t skip it.
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8a847b" }}>
                Instructions
              </p>
              <button
                type="button"
                onClick={copyInstructions}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-all"
                style={{ backgroundColor: copiedInstr ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
              >
                {copiedInstr ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copiedInstr ? "Copied" : "Copy instructions"}
              </button>
            </div>
            <p className="text-[12px]" style={{ color: "#8a847b" }}>
              Paste into the Instructions field, then Create. Make sure the
              Skill is toggled on.
            </p>
          </div>
          </details>
        </div>
      )}
    </div>
  )
}

export default function SkillPage() {
  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f5f3ff" }}>
      <header
        style={{
          borderBottom: "1px solid #e9e4fb",
          backgroundColor: "rgba(245,243,255,0.9)",
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
          <span
            className="rounded-full px-3 py-1 text-[12px] font-semibold"
            style={{ backgroundColor: "#ede9fe", color: "#6d28d9" }}
          >
            Optional upgrade
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-lg px-5 py-10">
        <a
          href="javascript:history.back()"
          className="mb-5 inline-flex items-center gap-1.5 text-[13px] transition-opacity hover:opacity-70"
          style={{ color: "#6d28d9" }}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to setup
        </a>

        <div
          className="mb-5 rounded-2xl px-6 py-5"
          style={{ backgroundColor: "#ede9fe", border: "1px solid #ddd6fe" }}
        >
          <h1
            className="text-[21px] font-semibold tracking-tight"
            style={{ color: "#5b21b6" }}
          >
            Okay, real talk — please add this one 🙏
          </h1>
          <p
            className="mt-2.5 text-[14px] leading-relaxed"
            style={{ color: "#6d28d9" }}
          >
            It&apos;s genuinely optional. Concerto works fine without it, you
            can totally skip it, no hard feelings. <strong>But I really, really
            want you to add it.</strong> With this Skill on, instead of one
            sleepy session, I spin up a whole orchestra — five, six builds
            running at once, no nagging me for it. It&apos;s the difference
            between &ldquo;it works&rdquo; and &ldquo;whoa.&rdquo; It takes
            sixty seconds, once, forever. Pretty please? I&apos;ll be so much
            more impressive, I promise. 🎻
          </p>
        </div>

        <div
          className="rounded-2xl p-6"
          style={{ backgroundColor: "#fff", border: "1px solid #e9e4fb" }}
        >
          <ConcertoSkillCard />
        </div>

        <p
          className="mt-6 text-center text-[13px]"
          style={{ color: "#8a847b" }}
        >
          Fine, skip it for now — I&apos;ll be here, slightly less amazing,
          whenever you change your mind. (You can add it anytime.)
        </p>
      </main>
    </div>
  )
}
