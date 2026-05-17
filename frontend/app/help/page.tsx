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
        a: "Concerto gives Claude the tools to orchestrate Claude Code sessions on your behalf. From any claude.ai conversation you can ask Claude to build, deploy, test, or automate — Claude handles the sessions, reads the logs, and reports back.",
      },
      {
        q: "What do I need before I can start?",
        a: "A claude.ai account (Pro or Max plan) and your Concerto purchase token. That's it — no terminal, no cloud account required. Concerto provisions and manages everything for you.",
      },
      {
        q: "How long does provisioning take?",
        a: "Typically 3–5 minutes from purchase to ready. The dashboard polls automatically and advances each step when it completes.",
      },
      {
        q: "Which regions are available?",
        a: "New York, San Francisco, Frankfurt, Amsterdam, Singapore, London, Bangalore, and Sydney. The default is New York. Contact support before provisioning if you need a specific region.",
      },
    ],
  },
  {
    title: "Connecting to Claude",
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
        a: "The connection may have restarted. Check your dashboard status — if it shows 'reconnecting', wait 30 seconds and refresh. The connection recovers automatically. If it shows 'down' for more than 2 minutes, contact support.",
      },
      {
        q: "Can I use the connector from multiple claude.ai conversations at the same time?",
        a: "Yes. The MCP server handles concurrent connections. Each claude.ai conversation gets its own session context.",
      },
    ],
  },
  {
    title: "Running sessions",
    items: [
      {
        q: "How do I run multiple tasks in parallel?",
        a: "Just ask Claude to work on multiple things at once. Claude will launch separate Claude Code sessions for each task, run them in parallel, and report back with the combined result.",
      },
      {
        q: "Sessions seem to stop before my task finishes.",
        a: "Long-running tasks keep working even after a claude.ai conversation times out. Reconnect via a new claude.ai message and ask Claude to check on progress — Claude will read the latest output and resume from where it left off.",
      },
      {
        q: "Can Claude install packages or modify files?",
        a: "Yes. Claude Code has full access to your workspace. It can install packages, write files, run build scripts, and start services.",
      },
      {
        q: "How do I check what's happening in a session?",
        a: "Ask Claude to check on progress — Claude will read the session output and summarize what's running, what's done, and what needs your input. You can also use the embedded terminal on your dashboard for a direct view.",
      },
    ],
  },
  {
    title: "Subscription + billing",
    items: [
      {
        q: "What's the difference between Solo and Pro?",
        a: "Solo ($49/mo) lets Claude launch and monitor up to 2 Claude Code sessions in parallel. Pro ($99/mo) lets Claude launch and monitor up to 6 Claude Code sessions in parallel. Both include email support and cancel anytime.",
      },
      {
        q: "How do I cancel my subscription?",
        a: "Open your dashboard → Billing tab → Manage Subscription. This opens the Stripe customer portal where you can cancel, change plan, or download invoices. Cancellation takes effect at the end of your current billing period.",
      },
      {
        q: "What happens to my data if I cancel?",
        a: "Your workspace and data are preserved until the end of the billing period, then cleaned up. Contact support@concerto.run before cancelling if you need to export anything.",
      },
      {
        q: "I was charged but the setup never completed.",
        a: "Contact support@concerto.run with your email address. We'll either complete the setup or issue a full refund — no questions asked.",
      },
    ],
  },
  {
    title: "Troubleshooting",
    items: [
      {
        q: "The embedded terminal shows a blank screen.",
        a: "Hard-refresh the dashboard (Ctrl+Shift+R). If still blank after 30 seconds, wait 1 minute and try again — the connection auto-reconnects.",
      },
      {
        q: "Claude Code says 'tool not available' or 'MCP server unreachable'.",
        a: "Open the embedded terminal and run: `systemctl restart concerto-mcp`. The connector in claude.ai will reconnect automatically within 30 seconds.",
      },
      {
        q: "I'm getting rate limit errors from Claude.",
        a: "Rate limits come from your Claude plan. If you're hitting limits frequently, consider upgrading to Claude Max — Pro's token limits run out fast with agentic work. Space out parallel sessions or wait for the rate limit window to reset (typically 1 minute).",
      },
      {
        q: "I can't find the connector config snippet.",
        a: "It's on Step 3 of your dashboard. If you've already completed setup, the full config is still visible — scroll down to the 'Connector config' section on the dashboard home tab.",
      },
    ],
  },
  {
    title: "Privacy + security",
    items: [
      {
        q: "Is my workspace isolated from other customers?",
        a: "Yes. Every Concerto subscription is a dedicated, isolated workspace. There is no shared compute or shared filesystem between customers.",
      },
      {
        q: "Can Anthropic see what runs in my workspace?",
        a: "Claude Code sends your prompts and tool outputs to Anthropic's API per their standard privacy policy. Your workspace content is not sent to Anthropic unless Claude Code explicitly reads a file as part of a task you requested.",
      },
      {
        q: "What data does Concerto collect?",
        a: "Your email address (from Stripe), your region preference, provisioning status, and (optionally) your first session timestamp. We do not log tool calls, shell commands, or file contents.",
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
    `<mark class="bg-[rgba(204,120,92,0.20)] text-[#b86747] rounded px-0.5">${text.slice(idx, idx + query.length)}</mark>` +
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
    <div className="min-h-screen bg-[#faf9f5] text-[#191919]">
      <nav className="border-b border-[rgba(25,25,25,0.07)] bg-[#faf9f5]/88 backdrop-blur-xl">
        <div className="mx-auto max-w-2xl px-4 py-4 flex items-center gap-4">
          <Link href="/" className="text-sm text-[#8a847b] hover:text-[#191919] transition-colors">
            ← concerto.run
          </Link>
        </div>
      </nav>

      <div className="mx-auto max-w-2xl px-4 py-16">
        {/* Header */}
        <div className="mb-10 text-center">
          <h1 className="font-display text-3xl font-[450] tracking-tight text-[#191919] mb-3">Help center</h1>
          <p className="text-[#8a847b] text-base">
            Answers to common questions about Concerto.
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#8a847b]" />
          <input
            type="search"
            placeholder="Search questions…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full rounded-xl border border-[rgba(25,25,25,0.12)] bg-white py-3 pl-11 pr-4 text-sm text-[#191919] placeholder-[#8a847b] outline-none focus:border-[#cc785c] focus:ring-1 focus:ring-[rgba(204,120,92,0.20)]"
          />
          {query && (
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-[#8a847b]">
              {totalResults} result{totalResults !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {/* Sections */}
        {filtered.length === 0 ? (
          <div className="py-12 text-center text-[#8a847b] text-sm">
            No results for &ldquo;{query}&rdquo;.{" "}
            <a href="mailto:support@concerto.run" className="text-[#cc785c] hover:text-[#b86747]">
              Email support →
            </a>
          </div>
        ) : (
          filtered.map((sec) => (
            <div key={sec.title} className="mb-8">
              <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-widest text-[#8a847b]">
                {sec.title}
              </h2>
              <div className="space-y-1.5">
                {sec.items.map((item, i) => {
                  const key = `${sec.title}-${i}`
                  const isOpen = !!openItems[key] || !!query
                  return (
                    <div
                      key={key}
                      className="rounded-xl border border-[rgba(25,25,25,0.08)] bg-white overflow-hidden"
                    >
                      <button
                        onClick={() => toggle(key)}
                        className="flex w-full items-center justify-between px-4 py-3.5 text-left"
                      >
                        <span
                          className="text-sm font-medium text-[#191919] pr-4"
                          dangerouslySetInnerHTML={{
                            __html: highlightMatch(item.q, query),
                          }}
                        />
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4 shrink-0 text-[#8a847b]" />
                        ) : (
                          <ChevronRight className="h-4 w-4 shrink-0 text-[#8a847b]" />
                        )}
                      </button>
                      {isOpen && (
                        <div className="border-t border-[rgba(25,25,25,0.06)] px-4 py-3.5">
                          <p
                            className="text-sm leading-relaxed text-[#555049]"
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
        <div className="mt-12 rounded-2xl border border-[rgba(25,25,25,0.08)] bg-white p-6 text-center">
          <p className="mb-3 text-sm font-medium text-[#191919]">Still need help?</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <a
              href="mailto:support@concerto.run"
              className="rounded-xl bg-[#cc785c] px-4 py-2 text-sm font-medium text-[#faf9f5] transition-opacity hover:opacity-90"
            >
              Email support@concerto.run →
            </a>
          </div>
          <p className="mt-3 text-xs text-[#8a847b]">Human reply within 24 hours.</p>
        </div>
      </div>
    </div>
  )
}
