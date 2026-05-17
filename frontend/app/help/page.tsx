"use client"

import { useState, useMemo } from "react"
import Link from "next/link"
import { Search, ChevronDown, ChevronRight } from "lucide-react"

interface QA {
  q: string
  a: string
}

interface Section {
  title: string
  items: QA[]
}

const SECTIONS: Section[] = [
  {
    title: "Getting started",
    items: [
      {
        q: "What is Concerto?",
        a: "Concerto gives you a dedicated remote workspace with Claude Code, an MCP server, and a cloudflared tunnel pre-installed. From any claude.ai conversation you can pilot Claude Code agents running on your workspace — real shell, real filesystem, persistent sessions.",
      },
      {
        q: "What do I need before I can start?",
        a: "A claude.ai account (Pro or Max plan) and your Concerto purchase token. That's it — no SSH client, no terminal, no cloud account required. Concerto provisions and manages the workspace for you.",
      },
      {
        q: "How long does provisioning take?",
        a: "Typically 3–5 minutes from purchase to workspace ready. The dashboard polls automatically and advances each step when it completes.",
      },
      {
        q: "Which regions are available?",
        a: "New York, San Francisco, Frankfurt, Amsterdam, Singapore, London, Bangalore, and Sydney. The default is New York. Contact support before provisioning if you need a specific region.",
      },
    ],
  },
  {
    title: "OAuth + connector setup",
    items: [
      {
        q: "The OAuth step is stuck / spinning forever.",
        a: "Open the embedded terminal on your dashboard, run `claude auth login`, and complete the browser prompt. The step polls every 10 seconds and auto-advances once Claude CLI reports authenticated. If the terminal itself won't load, try a hard-refresh (Ctrl+Shift+R) or a different browser.",
      },
      {
        q: "I ran `claude auth login` but the dashboard didn't advance.",
        a: "The poll can take up to 30 seconds to detect the auth change. Wait a moment, then refresh the dashboard. If it still shows 'waiting', open the terminal again and run `claude --version` — if that returns a version number, auth is complete and the poll will catch up within 60 seconds.",
      },
      {
        q: "The connector doesn't appear in claude.ai Settings → Connectors.",
        a: "Paste the connector config snippet again — it's on Step 3 of your dashboard. Make sure you copy the entire block including the opening and closing braces. If claude.ai shows 'invalid config', check that no characters were cut off at the beginning or end.",
      },
      {
        q: "I get 'connection refused' when claude.ai tries to use the connector.",
        a: "The cloudflared tunnel may have restarted. Check your dashboard status — if it shows 'reconnecting', wait 30 seconds and refresh. The tunnel recovers automatically. If it shows 'down' for more than 2 minutes, contact support.",
      },
      {
        q: "Can I use the connector from multiple claude.ai conversations at the same time?",
        a: "Yes. The MCP server on your workspace handles concurrent connections. Each claude.ai conversation gets its own session context, but they share the same filesystem and running processes on the workspace.",
      },
    ],
  },
  {
    title: "Running sessions",
    items: [
      {
        q: "How do I run multiple tasks in parallel?",
        a: "Ask Claude Code to spawn background tmux sessions: `tmux new-session -d -s task1 'python myscript.py'`. Each session runs independently. Claude Code can attach to any session, read its output, and report back to you.",
      },
      {
        q: "Sessions time out before my task finishes.",
        a: "Claude Code on Concerto runs on your workspace — there's no context timeout on the agent side. The claude.ai conversation may have a session limit, but the workspace process keeps running. Use tmux or nohup to detach long-running jobs; reconnect via a new claude.ai message and check the output.",
      },
      {
        q: "Can Claude Code install packages, run npm install, or modify system files?",
        a: "Yes. The workspace runs with full system access. Claude Code can install packages, write to any path, configure cron jobs, and start background services.",
      },
      {
        q: "How do I check what's running on my workspace?",
        a: "Ask Claude Code to run `tmux ls` (active sessions), `ps aux | grep python` (running processes), or `systemctl list-units --state=running` (system services). You can also use the embedded terminal on your dashboard.",
      },
    ],
  },
  {
    title: "Subscription + billing",
    items: [
      {
        q: "What's the difference between Solo and Pro?",
        a: "Solo ($49/mo) includes a 4GB workspace and up to 2 parallel sessions. Pro ($99/mo) includes an 8GB workspace and up to 6–8 parallel sessions. Both include email support and cancel anytime.",
      },
      {
        q: "How do I cancel my subscription?",
        a: "Open your dashboard → Billing tab → Manage Subscription. This opens the Stripe customer portal where you can cancel, change plan, or download invoices. Cancellation takes effect at the end of your current billing period.",
      },
      {
        q: "What happens to my workspace if I cancel?",
        a: "Your workspace and data are preserved until the end of the billing period, then cleaned up. Contact support@concerto.run before cancelling if you need to export anything.",
      },
      {
        q: "I was charged but the setup never completed.",
        a: "Contact support@concerto.run with your email address. We'll either complete the setup or issue a full refund — no questions asked. Provisioning failures are fully refundable.",
      },
    ],
  },
  {
    title: "Troubleshooting",
    items: [
      {
        q: "The embedded terminal shows a blank screen.",
        a: "This usually means the ttyd process restarted. Hard-refresh the dashboard (Ctrl+Shift+R). If still blank after 30 seconds, the cloudflared tunnel may have dropped — wait 1 minute and try again. The tunnel auto-reconnects.",
      },
      {
        q: "Claude Code says 'tool not available' or 'MCP server unreachable'.",
        a: "The MCP server process may have crashed. Open the embedded terminal and run: `systemctl restart concerto-mcp`. The connector in claude.ai will reconnect automatically within 30 seconds.",
      },
      {
        q: "I'm getting rate limit errors from Claude CLI.",
        a: "Claude CLI uses your Claude plan credits. If you're hitting limits frequently, consider upgrading to Claude Max — Pro's token limits run out fast with agentic work. Space out parallel sessions or wait for the rate limit window to reset (typically 1 minute).",
      },
      {
        q: "I can't find the connector config snippet.",
        a: "It's on Step 3 of your dashboard at concerto.run/dashboard/{your-token}. If you've already completed setup, the full config is still visible — scroll down to the 'Connector config' section on the dashboard home tab.",
      },
    ],
  },
  {
    title: "Privacy + security",
    items: [
      {
        q: "Does Concerto have access to my workspace after provisioning?",
        a: "Only via the cloudflared tunnel, which routes the web terminal and MCP traffic. Concerto does not retain persistent access to your workspace. Your code, files, and data never pass through Concerto's servers — only the tunnel handshake does.",
      },
      {
        q: "Is my workspace isolated from other customers?",
        a: "Yes. Every Concerto subscription is a dedicated workspace. There is no shared compute or shared filesystem between customers.",
      },
      {
        q: "Can Anthropic see what runs on my workspace?",
        a: "Claude Code sends your prompts and tool outputs to Anthropic's API per their standard privacy policy. The filesystem content of your workspace is not sent to Anthropic unless Claude Code explicitly reads a file as part of a task you requested.",
      },
      {
        q: "What data does Concerto collect?",
        a: "Your email address (from Stripe), your region preference, provisioning status, and (optionally) your first session timestamp. We do not log MCP tool calls, shell commands, or file contents. Full privacy policy: concerto.run/legal/privacy.",
      },
    ],
  },
]

function highlightMatch(text: string, query: string): string {
  if (!query) return text
  const idx = text.toLowerCase().indexOf(query.toLowerCase())
  if (idx === -1) return text
  return (
    text.slice(0, idx) +
    `<mark class="bg-violet-500/30 text-violet-200 rounded px-0.5">${text.slice(idx, idx + query.length)}</mark>` +
    text.slice(idx + query.length)
  )
}

export default function HelpPage() {
  const [query, setQuery] = useState("")
  const [openItems, setOpenItems] = useState<Record<string, boolean>>({})

  const filtered = useMemo<Section[]>(() => {
    if (!query.trim()) return SECTIONS
    const q = query.toLowerCase()
    return SECTIONS.flatMap((sec) => {
      const items = sec.items.filter(
        (item) =>
          item.q.toLowerCase().includes(q) || item.a.toLowerCase().includes(q)
      )
      return items.length ? [{ ...sec, items }] : []
    })
  }, [query])

  const totalResults = filtered.reduce((n, s) => n + s.items.length, 0)

  function toggle(key: string) {
    setOpenItems((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  return (
    <div className="min-h-screen bg-[#080810] text-white">
      <div className="mx-auto max-w-2xl px-4 py-16">
        {/* Header */}
        <div className="mb-10 text-center">
          <Link href="/" className="inline-flex items-center gap-2 mb-6 text-white/40 hover:text-white/70 text-sm transition-colors">
            ← concerto.run
          </Link>
          <h1 className="text-3xl font-bold mb-3">Help center</h1>
          <p className="text-white/50 text-base">
            Answers to common questions about Concerto.
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/30" />
          <input
            type="search"
            placeholder="Search questions…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/[0.03] py-3 pl-11 pr-4 text-sm text-white placeholder-white/25 outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20"
          />
          {query && (
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-white/30">
              {totalResults} result{totalResults !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Sections */}
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-white/30 text-sm">
            No results for &ldquo;{query}&rdquo;.{" "}
            <a href="mailto:support@concerto.run" className="text-violet-400 hover:text-violet-300">
              Email support →
            </a>
          </div>
        ) : (
          filtered.map((sec) => (
            <div key={sec.title} className="mb-8">
              <h2 className="mb-3 text-xs font-semibold uppercase tracking-widest text-white/30">
                {sec.title}
              </h2>
              <div className="space-y-1.5">
                {sec.items.map((item, i) => {
                  const key = `${sec.title}-${i}`
                  const isOpen = !!openItems[key] || !!query
                  return (
                    <div
                      key={key}
                      className="rounded-xl border border-white/8 bg-white/[0.02] overflow-hidden"
                    >
                      <button
                        onClick={() => toggle(key)}
                        className="flex w-full items-center justify-between px-4 py-3.5 text-left"
                      >
                        <span
                          className="text-sm font-medium text-white/80 pr-4"
                          dangerouslySetInnerHTML={{
                            __html: highlightMatch(item.q, query),
                          }}
                        />
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4 shrink-0 text-white/30" />
                        ) : (
                          <ChevronRight className="h-4 w-4 shrink-0 text-white/30" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="border-t border-white/6 px-4 py-3.5">
                          <p
                            className="text-sm leading-relaxed text-white/50"
                            dangerouslySetInnerHTML={{
                              __html: highlightMatch(item.a, query),
                            }}
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          ))
        )}

        {/* Footer CTA */}
        <div className="mt-12 rounded-2xl border border-white/8 bg-white/[0.02] p-6 text-center">
          <p className="mb-3 text-sm font-medium text-white/70">Still need help?</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <a
              href="mailto:support@concerto.run"
              className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
            >
              Email support@concerto.run →
            </a>
          </div>
          <p className="mt-3 text-xs text-white/30">Human reply within 24 hours. No community forums.</p>
        </div>
      </div>
    </div>
  )
}
