"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { DEMO_SCRIPT, type TerminalLine } from "./hero-demo-data";

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);
  return reduced;
}

type Phase =
  | "idle"
  | "typing"
  | "response"
  | "terminal"
  | "complete"
  | "resetting";

const PREFIX_COLORS: Record<TerminalLine["color"], string> = {
  cyan: "#22d3ee",
  green: "#4ade80",
  yellow: "#facc15",
  white: "#f1f5f9",
  magenta: "#c084fc",
};

export function HeroDemo() {
  const reduced = usePrefersReducedMotion();

  const [phase, setPhase] = useState<Phase>("idle");
  const [typedCount, setTypedCount] = useState(0);
  const [showResponse, setShowResponse] = useState(false);
  const [showTerminal, setShowTerminal] = useState(false);
  const [visibleLineCount, setVisibleLineCount] = useState(0);
  const [fading, setFading] = useState(false);

  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  }, []);

  const addTimer = useCallback((fn: () => void, ms: number) => {
    timers.current.push(setTimeout(fn, ms));
  }, []);

  const runSequence = useCallback(() => {
    const { userPrompt, typingSpeedMs, terminalLines } = DEMO_SCRIPT;

    // Reset state
    setPhase("typing");
    setTypedCount(0);
    setShowResponse(false);
    setShowTerminal(false);
    setVisibleLineCount(0);
    setFading(false);

    // Phase 1: type the user prompt
    for (let i = 1; i <= userPrompt.length; i++) {
      addTimer(() => setTypedCount(i), i * typingSpeedMs);
    }

    const typingDone = userPrompt.length * typingSpeedMs + 200;

    // Phase 2: show Claude response
    addTimer(() => {
      setPhase("response");
      setShowResponse(true);
    }, typingDone);

    // Phase 3: slide in terminal
    const terminalStart = typingDone + 700;
    addTimer(() => {
      setPhase("terminal");
      setShowTerminal(true);
    }, terminalStart);

    // Phase 4: reveal terminal lines
    terminalLines.forEach((line, idx) => {
      addTimer(
        () => setVisibleLineCount(idx + 1),
        terminalStart + 300 + line.delay
      );
    });

    // Phase 5: mark complete
    const lastLineDelay =
      terminalLines[terminalLines.length - 1].delay + 600;
    addTimer(
      () => setPhase("complete"),
      terminalStart + 300 + lastLineDelay
    );

    // Phase 6: fade + reset
    const resetAt = DEMO_SCRIPT.loopIntervalMs - 800;
    addTimer(() => {
      setFading(true);
      setPhase("resetting");
    }, resetAt);

    addTimer(() => runSequence(), DEMO_SCRIPT.loopIntervalMs);
  }, [addTimer]);

  useEffect(() => {
    if (reduced) return;
    const kickoff = setTimeout(() => runSequence(), 600);
    return () => {
      clearTimeout(kickoff);
      clearTimers();
    };
  }, [reduced, runSequence, clearTimers]);

  const userPrompt = DEMO_SCRIPT.userPrompt;
  const displayedPrompt =
    phase === "idle" ? "" : userPrompt.slice(0, typedCount);
  const showCursor =
    phase === "typing" || phase === "idle";

  if (reduced) {
    return <StaticFallback />;
  }

  return (
    <div
      aria-label="Concerto demo: Claude Code agent running your sessions"
      role="img"
      className="relative mx-auto w-full max-w-2xl select-none"
      style={{ opacity: fading ? 0 : 1, transition: "opacity 0.6s ease" }}
    >
      {/* Gradient border wrapper */}
      <div
        className="rounded-xl p-[1.5px]"
        style={{
          background:
            "linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #22d3ee 100%)",
          boxShadow:
            "0 0 40px rgba(99,102,241,0.35), 0 0 80px rgba(34,211,238,0.15)",
        }}
      >
        {/* Browser chrome */}
        <div
          className="rounded-[10px] overflow-hidden"
          style={{ background: "#0f1117" }}
        >
          {/* Browser top bar */}
          <div
            className="flex items-center gap-2 px-3 py-2 border-b"
            style={{ borderColor: "#1e2435", background: "#12161f" }}
          >
            <div className="flex gap-1.5 shrink-0">
              <span className="w-3 h-3 rounded-full bg-red-500/80 block" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/80 block" />
              <span className="w-3 h-3 rounded-full bg-green-500/80 block" />
            </div>
            <div
              className="flex-1 rounded-md text-center text-xs py-0.5 px-3 truncate"
              style={{ background: "#1a1f2e", color: "#64748b" }}
            >
              claude.ai
            </div>
            {/* Concerto connector badge */}
            <div
              className="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium shrink-0"
              style={{
                background: "rgba(34,211,238,0.1)",
                border: "1px solid rgba(34,211,238,0.25)",
                color: "#22d3ee",
              }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{
                  background: "#4ade80",
                  boxShadow: "0 0 6px #4ade80",
                  animation: "pulse-dot 2s ease-in-out infinite",
                }}
              />
              <span className="hidden sm:inline">Concerto</span>
            </div>
          </div>

          {/* Chat area */}
          <div className="px-4 py-3 space-y-3" style={{ background: "#0f1117" }}>
            {/* User bubble */}
            <div className="flex justify-end">
              <div
                className="rounded-2xl rounded-tr-sm px-3 py-2 text-sm max-w-[85%] break-words leading-relaxed"
                style={{
                  background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
                  color: "#f1f5f9",
                  minHeight: "2rem",
                }}
              >
                <span>{displayedPrompt}</span>
                {showCursor && (
                  <span
                    className="inline-block w-[2px] h-[1em] ml-px align-middle"
                    style={{
                      background: "#a5b4fc",
                      animation: "blink 1s step-end infinite",
                    }}
                  />
                )}
              </div>
            </div>

            {/* Claude response */}
            {showResponse && (
              <div
                className="flex justify-start"
                style={{
                  animation: "fade-slide-up 0.35s ease both",
                }}
              >
                <div className="flex items-start gap-2 max-w-[85%]">
                  <div
                    className="w-6 h-6 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold mt-0.5"
                    style={{
                      background:
                        "linear-gradient(135deg, #6366f1, #22d3ee)",
                      color: "#fff",
                    }}
                  >
                    M
                  </div>
                  <div
                    className="rounded-2xl rounded-tl-sm px-3 py-2 text-sm leading-relaxed"
                    style={{
                      background: "#1a1f2e",
                      color: "#cbd5e1",
                      border: "1px solid #1e2a3a",
                    }}
                  >
                    {DEMO_SCRIPT.claudeResponse}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Terminal pane */}
          {showTerminal && (
            <div
              className="relative overflow-hidden"
              style={{
                background: "#080b10",
                borderTop: "1px solid #1e2435",
                animation: "slide-in-terminal 0.4s cubic-bezier(0.4,0,0.2,1) both",
              }}
            >
              {/* Scan line overlay */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 z-10"
                style={{
                  background:
                    "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.12) 2px, rgba(0,0,0,0.12) 4px)",
                  animation: "scan-line 8s linear infinite",
                }}
              />

              {/* Terminal header */}
              <div
                className="flex items-center gap-2 px-3 py-1.5"
                style={{
                  background: "#0c1018",
                  borderBottom: "1px solid #1e2435",
                }}
              >
                <span className="text-xs font-mono" style={{ color: "#4ade80" }}>
                  ●
                </span>
                <span
                  className="text-xs font-mono"
                  style={{ color: "#475569" }}
                >
                  concerto — sess_abc123 — remote-nyc
                </span>
              </div>

              {/* Terminal lines */}
              <div className="px-3 py-2 font-mono space-y-0.5 text-xs sm:text-sm min-h-[8rem]">
                {DEMO_SCRIPT.terminalLines
                  .slice(0, visibleLineCount)
                  .map((line, idx) => (
                    <div
                      key={idx}
                      className="flex gap-2 leading-relaxed"
                      style={{
                        animation: "fade-in-line 0.2s ease both",
                      }}
                    >
                      <span
                        className="shrink-0 font-semibold"
                        style={{ color: PREFIX_COLORS[line.color] }}
                      >
                        {line.prefix}
                      </span>
                      <span style={{ color: "#94a3b8" }}>{line.text}</span>
                    </div>
                  ))}
                {/* Blinking caret at end */}
                {phase === "terminal" &&
                  visibleLineCount <
                    DEMO_SCRIPT.terminalLines.length && (
                    <div className="flex gap-2 leading-relaxed">
                      <span style={{ color: "#4ade80" }}>▌</span>
                    </div>
                  )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* CSS keyframes injected inline */}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(0.85); }
        }
        @keyframes fade-slide-up {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slide-in-terminal {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fade-in-line {
          from { opacity: 0; transform: translateX(-4px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes scan-line {
          0% { background-position: 0 0; }
          100% { background-position: 0 100px; }
        }
      `}</style>
    </div>
  );
}

function StaticFallback() {
  return (
    <div
      aria-label="Concerto: Claude Code agent running your sessions"
      role="img"
      className="relative mx-auto w-full max-w-2xl"
    >
      <div
        className="rounded-xl p-[1.5px]"
        style={{
          background:
            "linear-gradient(135deg, #6366f1 0%, #8b5cf6 40%, #22d3ee 100%)",
        }}
      >
        <div
          className="rounded-[10px] overflow-hidden font-mono text-xs px-4 py-6 space-y-1"
          style={{ background: "#080b10", color: "#94a3b8" }}
        >
          <div style={{ color: "#22d3ee" }}>
            [concerto] spawning session sess_abc123 on remote-nyc
          </div>
          <div style={{ color: "#facc15" }}>[claude] reading src/auth/...</div>
          <div style={{ color: "#facc15" }}>[claude] writing src/auth/jwt.py</div>
          <div style={{ color: "#facc15" }}>[claude] running pytest...</div>
          <div style={{ color: "#4ade80" }}>[pytest] ✓ 42 tests passed</div>
          <div style={{ color: "#c084fc" }}>
            [git] creating branch refactor/auth-jwt-v2
          </div>
          <div style={{ color: "#c084fc" }}>
            [gh] opening PR #142 to yourname/myproject
          </div>
          <div style={{ color: "#4ade80" }}>
            ✓ Session complete — 4 min 12 sec
          </div>
        </div>
      </div>
    </div>
  );
}
