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
        q: "What is Maestro?",
        a: "Maestro provisions a cloud VPS in your own DigitalOcean account and pre-installs Claude Code, an MCP server, and a cloudflared tunnel. From any claude.ai conversation you can pilot Claude Code agents running on your Droplet — real shell, real filesystem, persistent sessions.",
      },
      {
        q: "What do I need before I can start?",
        a: "A claude.ai account (any plan), a DigitalOcean account (free to create, you pay DO directly for the Droplet), and your Maestro purchase token. That's it — no SSH client, no terminal, no cloud expertise required.",
      },
      {
        q: "How long does provisioning take?",
        a: "Typically 3–5 minutes from submitting your DO API key to the Droplet being ready. The dashboard polls automatically and advances each step when it completes.",
      },
      {
        q: "Which DigitalOcean regions are supported?",
        a: "All standard DO regions work. The default is nyc1. You can change the region by contacting support before provisioning — region selection in the UI is coming in a future update.",
      },
      {
        q: "Can I use Hetzner instead of DigitalOcean?",
        a: "Not in v1. Hetzner support is planned for v2. If you need Hetzner specifically, reply to your purchase confirmation email and we'll prioritize it.",
      },
    ],
  },
  {
    title: "OAuth + connector setup",
    items: [
      {
        q: "The OAuth step is stuck / spinning forever.",
        a: "Open the embedded terminal on your dashboard, run `claude auth login`, and complete the browser prompt. The step polls via SSH every 10 seconds and auto-advances once Claude CLI reports authenticated. If the terminal itself won't load, try a hard-refresh (Ctrl+Shift+R) or a different browser.",
      },
      {
        q: "I ran `claude auth login` but the dashboard didn't advance.",
        a: "The SSH poll can take up to 30 seconds to detect the auth change. Wait a moment, then refresh the dashboard. If it still shows 'waiting', open the terminal again and run `claude --version` — if that returns a version number, auth is complete and the poll will catch up within 60 seconds.",
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
        a: "Yes. The MCP server on your Droplet handles concurrent connections. Each claude.ai conversation gets its own session context, but they share the same filesystem and running processes on the Droplet.",
      },
    ],
  },
  {
    title: "Spawning sessions",
    items: [
      {
        q: "How do I run multiple tasks in parallel?",
        a: "Ask Claude Code to spawn background tmux sessions: `tmux new-session -d -s task1 'python myscript.py'`. Each session runs independently. Claude Code can attach to any session, read its output, and report back to you.",
      },
      {
        q: "Sessions time out before my task finishes.",
        a: "Claude Code on Maestro runs on your Droplet — there's no context timeout on the agent side. The claude.ai conversation may have a session limit, but the Droplet process keeps running. Use tmux or nohup to detach long-running jobs; reconnect via a new claude.ai message and check the output.",
      },
      {
        q: "Can Claude Code install packages, run npm install, or modify system files?",
        a: "Yes. The Droplet runs as root by default, so Claude Code has full system access. It can install apt packages, run npm/pip installs, write to any path, configure cron jobs, and start background services.",
      },
      {
        q: "How do I check what's running on my Droplet?",
        a: "Ask Claude Code to run `tmux ls` (active sessions), `ps aux | grep python` (running processes), or `systemctl list-units --state=running` (system services). You can also SSH directly into the Droplet using the credentials on your dashboard.",
      },
    ],
  },
  {
    title: "Subscription + billing (Hosted plan)",
    items: [
      {
        q: "What is the Hosted plan?",
        a: "The Hosted plan ($39/mo) is a recurring subscription that keeps your Droplet alive and managed. Maestro monitors the tunnel, renews the cloudflared config, and handles updates automatically. The Droplet itself is billed to your DO account separately.",
      },
      {
        q: "What is the BYOC plan?",
        a: "BYOC (Bring Your Own Cloud) is a one-time $99 payment. Maestro provisions the Droplet and configures everything, but ongoing monitoring and updates are self-managed. Your Droplet runs indefinitely as long as your DO account is active.",
      },
      {
        q: "How do I cancel my subscription?",
        a: "Open your dashboard → Billing tab → Manage Subscription. This opens the Stripe customer portal where you can cancel, change plan, or download invoices. Cancellation takes effect at the end of your current billing period.",
      },
      {
        q: "Will my Droplet be deleted if I cancel?",
        a: "No. Your Droplet lives in your DigitalOcean account — Maestro cannot delete it. Cancelling the Hosted plan stops Maestro's monitoring, but your Droplet and its data remain. You'll need to manage the tunnel and updates yourself after cancellation.",
      },
      {
        q: "I was charged but the setup never completed.",
        a: "Contact support@maestro.run with your email address. We'll either complete the setup or issue a full refund — no questions asked. Provisioning failures are fully refundable.",
      },
    ],
  },
  {
    title: "BYOC specifics",
    items: [
      {
        q: "Do I need to keep my DigitalOcean API key stored anywhere?",
        a: "Once provisioning is complete, your DO API key is no longer needed by Maestro. It's used only during the initial Droplet creation and then discarded (encrypted at rest, deleted after provisioning).",
      },
      {
        q: "Can I SSH into my Droplet directly?",
        a: "Yes. The Droplet's IP address and the SSH public key fingerprint are available on your dashboard. The private key is stored at the path shown in your dashboard details — you can download it from the embedded terminal.",
      },
      {
        q: "What's installed on the Droplet?",
        a: "Ubuntu 24.04, Claude Code (via npm), the Maestro MCP server, cloudflared (tunnel daemon), and ttyd (web terminal). No database, no application server. The Droplet is a clean workspace; Claude Code brings the intelligence.",
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
        a: "The MCP server process may have crashed. Open the embedded terminal and run: `systemctl restart maestro-mcp` (or the equivalent service name shown in your cloud-init docs). The connector in claude.ai will reconnect automatically within 30 seconds.",
      },
      {
        q: "I'm getting rate limit errors from Claude CLI.",
        a: "Claude CLI uses your Max plan credits. If you're hitting limits, it means your Droplet is running intensive workloads. Space out parallel sessions or wait for the rate limit window to reset (typically 1 minute).",
      },
      {
        q: "The provisioning step failed with 'API key invalid'.",
        a: "Your DigitalOcean API key needs write permissions (not read-only). Create a new token at cloud.digitalocean.com/account/api/tokens with full read+write scope, and re-enter it on the setup page.",
      },
      {
        q: "My Droplet is using more bandwidth than expected.",
        a: "Claude Code may be running network-intensive tasks (large downloads, git clones, package installs). Check with `nethogs` or `iftop` in the embedded terminal. DO includes 1TB transfer/month on standard Droplets; excess is billed at $0.01/GB.",
      },
      {
        q: "I can't find the connector config snippet.",
        a: "It's on Step 3 of your dashboard at maestro.run/dashboard/{your-token}. If you've already completed setup, the full config is still visible — scroll down to the 'Connector config' section on the dashboard home tab.",
      },
    ],
  },
  {
    title: "Privacy + security",
    items: [
      {
        q: "Does Maestro have access to my Droplet after provisioning?",
        a: "Only via the cloudflared tunnel, which routes the web terminal and MCP traffic. Maestro does not have persistent SSH access to your Droplet. Your code, files, and data never pass through Maestro's servers — only the tunnel handshake does.",
      },
      {
        q: "Is my DigitalOcean API key stored securely?",
        a: "Your DO API key is encrypted at rest using AES-256 and is only decrypted during the provisioning workflow. It is deleted from our database once provisioning completes successfully.",
      },
      {
        q: "Can Anthropic see what runs on my Droplet?",
        a: "Claude Code sends your prompts and tool outputs to Anthropic's API per their standard privacy policy. The filesystem content of your Droplet is not sent to Anthropic unless Claude Code explicitly reads a file as part of a task you requested.",
      },
      {
        q: "What data does Maestro collect?",
        a: "Your email address (from Stripe), your DO region preference, provisioning status, and (optionally) your first session timestamp. We do not log MCP tool calls, shell commands, or file contents. Full privacy policy: maestro.run/legal/privacy.",
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
            ← maestro.run
          </Link>
          <h1 className="text-3xl font-bold mb-3">Help center</h1>
          <p className="text-white/50 text-base">
            Answers to common questions about Maestro.
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
            <a href="mailto:support@maestro.run" className="text-violet-400 hover:text-violet-300">
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
              href="mailto:support@maestro.run"
              className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white/60 transition-colors hover:border-violet-500/40 hover:text-white"
            >
              Email support
            </a>
            <a
              href={process.env.NEXT_PUBLIC_DISCORD_INVITE_URL || "https://discord.gg/maestro"}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
            >
              Join Discord
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
