import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { ScrollReveal } from "@/components/scroll-reveal"
import {
  Zap,
  Cloud,
  DollarSign,
  Check,
  Terminal,
  Globe,
  Shield,
  ArrowRight,
} from "lucide-react"

/* ─── Hero orbital SVG ────────────────────────────────────────── */

function HeroOrbit() {
  return (
    <svg
      viewBox="0 0 1200 680"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="hero-orbit absolute inset-0 h-full w-full"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <pattern id="hero-grid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
          <circle cx="0.5" cy="0.5" r="0.75" fill="rgba(255,255,255,0.045)" />
        </pattern>
        {/* Ellipse paths for animateMotion */}
        <path id="mp-1" d="M700,340 A100,50 0 1,0 500,340 A100,50 0 1,0 700,340Z" />
        <path id="mp-2" d="M800,340 A200,100 0 1,0 400,340 A200,100 0 1,0 800,340Z" />
        <path id="mp-3" d="M920,340 A320,155 0 1,0 280,340 A320,155 0 1,0 920,340Z" />
        <path id="mp-4" d="M1070,340 A470,215 0 1,0 130,340 A470,215 0 1,0 1070,340Z" />
      </defs>

      {/* Dot grid */}
      <rect width="1200" height="680" fill="url(#hero-grid)" />

      {/* Orbital rings */}
      <use href="#mp-1" stroke="rgba(139,92,246,0.28)" strokeWidth="1" />
      <use href="#mp-2" stroke="rgba(139,92,246,0.18)" strokeWidth="1" />
      <use href="#mp-3" stroke="rgba(139,92,246,0.11)" strokeWidth="1" />
      <use href="#mp-4" stroke="rgba(139,92,246,0.06)" strokeWidth="1" />

      {/* Center node glow layers */}
      <circle cx="600" cy="340" r="56" fill="rgba(139,92,246,0.05)" />
      <circle cx="600" cy="340" r="24" fill="rgba(139,92,246,0.14)" />
      <circle cx="600" cy="340" r="9"  fill="rgba(167,139,250,0.95)" />

      {/* Orbit 1 — 2 agents */}
      <circle r="4" fill="#a78bfa">
        <animateMotion dur="6s" repeatCount="indefinite">
          <mpath href="#mp-1" />
        </animateMotion>
      </circle>
      <circle r="3" fill="#60a5fa" opacity="0.75">
        <animateMotion dur="6s" begin="-3s" repeatCount="indefinite">
          <mpath href="#mp-1" />
        </animateMotion>
      </circle>

      {/* Orbit 2 — 2 agents */}
      <circle r="4.5" fill="#a78bfa" opacity="0.85">
        <animateMotion dur="10s" repeatCount="indefinite">
          <mpath href="#mp-2" />
        </animateMotion>
      </circle>
      <circle r="3.5" fill="#34d399" opacity="0.65">
        <animateMotion dur="10s" begin="-4.5s" repeatCount="indefinite">
          <mpath href="#mp-2" />
        </animateMotion>
      </circle>

      {/* Orbit 3 — 2 agents */}
      <circle r="5" fill="#a78bfa" opacity="0.65">
        <animateMotion dur="16s" repeatCount="indefinite">
          <mpath href="#mp-3" />
        </animateMotion>
      </circle>
      <circle r="3.5" fill="#f472b6" opacity="0.5">
        <animateMotion dur="16s" begin="-7s" repeatCount="indefinite">
          <mpath href="#mp-3" />
        </animateMotion>
      </circle>

      {/* Orbit 4 — 1 agent */}
      <circle r="5.5" fill="#a78bfa" opacity="0.38">
        <animateMotion dur="26s" repeatCount="indefinite">
          <mpath href="#mp-4" />
        </animateMotion>
      </circle>
    </svg>
  )
}

/* ─── Feature card ────────────────────────────────────────────── */

interface FeatureCardProps {
  icon: React.ReactNode
  iconBg: string
  title: string
  description: string
  revealDelay?: string
}

function FeatureCard({ icon, iconBg, title, description, revealDelay }: FeatureCardProps) {
  return (
    <div
      className={`reveal ${revealDelay ?? ""} group rounded-xl border border-white/[0.07] bg-white/[0.025] p-6 transition-all duration-200 hover:-translate-y-1 hover:border-violet-500/25 hover:bg-white/[0.045] hover:shadow-violet-md`}
    >
      <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <h3 className="mb-2.5 text-[15px] font-semibold tracking-tight text-white">{title}</h3>
      <p className="text-sm leading-relaxed text-white/40">{description}</p>
    </div>
  )
}

/* ─── Pricing check item ──────────────────────────────────────── */

function CheckItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-green-500/15">
        <Check className="h-3 w-3 text-green-400" />
      </span>
      <span className="text-white/65">{children}</span>
    </li>
  )
}

/* ─── Landing page ────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <ScrollReveal />

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <nav className="fixed left-0 right-0 top-0 z-50 border-b border-white/[0.05] bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
              <rect width="22" height="22" rx="6" fill="#7c3aed" />
              <circle cx="11" cy="11" r="5.5" stroke="white" strokeWidth="1.25" fill="none" />
              <circle cx="11" cy="11" r="2" fill="white" />
            </svg>
            <span className="font-semibold tracking-tight text-white">Maestro</span>
          </div>

          <div className="flex items-center gap-5">
            <Link href="#features" className="hidden text-sm text-white/45 transition-colors hover:text-white md:block">
              Features
            </Link>
            <Link href="#pricing" className="hidden text-sm text-white/45 transition-colors hover:text-white md:block">
              Pricing
            </Link>
            <Link href="#faq" className="hidden text-sm text-white/45 transition-colors hover:text-white md:block">
              FAQ
            </Link>
            <form action="/api/checkout" method="POST">
              <Button
                size="sm"
                className="h-8 rounded-lg bg-white px-4 text-xs font-semibold text-black hover:bg-white/90"
              >
                Get started
              </Button>
            </form>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pb-16 pt-36 md:pb-24 md:pt-40">
        {/* Orbital SVG background */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <HeroOrbit />
          {/* Radial gradient overlay — fades SVG into the page background */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(124,58,237,0.14)_0%,transparent_70%)]" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0a0b]/50 to-[#0a0a0b]" />
        </div>

        <div className="relative mx-auto max-w-4xl px-6 text-center">
          {/* Badge */}
          <div className="animate-fade-up mb-6 flex justify-center">
            <Badge
              variant="outline"
              className="border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-300"
            >
              <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-violet-400 animate-dot-blink" />
              Now available · Claude Code remote workshop
            </Badge>
          </div>

          {/* Headline */}
          <h1 className="animate-fade-up delay-100 mb-6 text-5xl font-bold leading-[1.04] tracking-[-0.03em] sm:text-6xl md:text-7xl">
            Pilot{" "}
            <span className="bg-gradient-to-r from-violet-300 via-violet-400 to-indigo-400 bg-clip-text text-transparent">
              Claude Code
            </span>{" "}
            <br className="hidden sm:block" />
            workers from your browser
          </h1>

          {/* Sub-headline */}
          <p className="animate-fade-up delay-200 mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-white/45 md:text-xl">
            Never open a terminal. Ship code with autonomous AI agents running
            24/7 in your own cloud.
          </p>

          {/* CTAs */}
          <div className="animate-fade-up delay-300 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <form action="/api/checkout" method="POST">
              <Button
                size="lg"
                className="h-12 rounded-xl bg-white px-8 text-base font-semibold text-black shadow-[0_0_0_1px_rgba(255,255,255,0.1),0_4px_20px_rgba(255,255,255,0.08)] hover:bg-white/92"
              >
                Get Maestro for $99
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </form>
            <p className="text-sm text-white/28">One-time payment · No subscription</p>
          </div>

          {/* Terminal mockup */}
          <div className="animate-fade-up delay-500 mx-auto mt-16 max-w-3xl">
            <div className="overflow-hidden rounded-xl border border-white/[0.07] bg-[#0d0d10] shadow-[0_32px_80px_rgba(0,0,0,0.6),0_0_0_1px_rgba(255,255,255,0.05)]">
              {/* Titlebar */}
              <div className="flex items-center gap-2 border-b border-white/[0.05] bg-white/[0.02] px-4 py-3">
                <span className="h-3 w-3 rounded-full bg-red-500/55" />
                <span className="h-3 w-3 rounded-full bg-yellow-500/55" />
                <span className="h-3 w-3 rounded-full bg-green-500/55" />
                <span className="ml-3 font-mono text-xs text-white/20">maestro · agent-01</span>
              </div>
              {/* Terminal content */}
              <div className="space-y-2 p-6 text-left font-mono text-[13px]">
                <div className="text-white/28">$ claude --dangerously-skip-permissions</div>
                <div className="text-green-400">✓ Authenticated with Claude Max</div>
                <div className="text-white/45">Watching /workspace for tasks...</div>
                <div className="mt-4 text-violet-300">▶ Task: Refactor auth middleware to JWT</div>
                <div className="text-white/35">  Reading src/middleware/auth.ts...</div>
                <div className="text-white/35">  Analysing 847 lines across 12 files...</div>
                <div className="text-white/35">  Writing changes...</div>
                <div className="text-green-400">✓ 14 files modified · PR #42 opened</div>
                <div className="mt-3 flex items-center gap-2 text-white/20">
                  <span className="animate-dot-blink">▌</span>
                  <span>Awaiting next task</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────── */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="mb-3 text-3xl font-bold tracking-tight md:text-4xl">
              Live in under 10 minutes
            </h2>
            <p className="mx-auto max-w-lg text-white/40">
              Four steps from payment to your first autonomous agent running in the cloud.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { n: "01", title: "Pay once", desc: "Secure Stripe checkout. $99 one-time, no subscription ever." },
              { n: "02", title: "Enter DO key", desc: "Paste your DigitalOcean API key — Maestro provisions your own droplet." },
              { n: "03", title: "Authenticate", desc: "One browser-based OAuth flow for your Claude Max account." },
              { n: "04", title: "Start building", desc: "Paste the connector config into claude.ai. Agents ready." },
            ].map((step, i) => (
              <div key={step.n} className={`reveal reveal-d${i + 1} relative rounded-xl border border-white/[0.07] bg-white/[0.025] p-6`}>
                <div className="mb-4 font-mono text-[11px] font-medium tracking-widest text-violet-500">{step.n}</div>
                <h3 className="mb-2 text-[15px] font-semibold text-white">{step.title}</h3>
                <p className="text-sm leading-relaxed text-white/40">{step.desc}</p>
                {i < 3 && (
                  <div className="absolute right-0 top-1/2 hidden -translate-y-1/2 translate-x-1/2 lg:block">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border border-white/[0.08] bg-[#0a0a0b]">
                      <ArrowRight className="h-3 w-3 text-white/25" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────── */}
      <section id="features" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="mb-3 text-3xl font-bold tracking-tight md:text-4xl">
              Everything you need to run agents at scale
            </h2>
            <p className="mx-auto max-w-xl text-white/40">
              Maestro handles provisioning, authentication, and monitoring — so you can focus on shipping.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <FeatureCard
              revealDelay="reveal-d1"
              icon={<Zap className="h-5 w-5 text-violet-400" />}
              iconBg="bg-violet-500/15"
              title="Parallel agents, 24/7"
              description="Spawn multiple Claude Code workers simultaneously. Run long tasks overnight without babysitting a terminal. Your agents work while you sleep."
            />
            <FeatureCard
              revealDelay="reveal-d2"
              icon={<Cloud className="h-5 w-5 text-blue-400" />}
              iconBg="bg-blue-500/15"
              title="Your cloud, your billing"
              description="Maestro provisions a DigitalOcean droplet directly in your account. You own the infrastructure — no markup, no vendor lock-in."
            />
            <FeatureCard
              revealDelay="reveal-d3"
              icon={<DollarSign className="h-5 w-5 text-emerald-400" />}
              iconBg="bg-emerald-500/15"
              title="No token-by-token cost"
              description="Uses your existing Claude Max plan. No per-token API fees, no surprise bills. Run as many tasks as you want — model cost already covered."
            />
            <FeatureCard
              revealDelay="reveal-d4"
              icon={<Terminal className="h-5 w-5 text-orange-400" />}
              iconBg="bg-orange-500/15"
              title="Browser terminal"
              description="Full-featured web terminal embedded in your dashboard. SSH into your droplet from any device — no client software required."
            />
            <FeatureCard
              revealDelay="reveal-d5"
              icon={<Globe className="h-5 w-5 text-pink-400" />}
              iconBg="bg-pink-500/15"
              title="MCP integration"
              description="Connect to claude.ai in 3 copy-paste steps. Your remote agents appear as MCP tools in the Claude interface — send tasks from anywhere."
            />
            <FeatureCard
              revealDelay="reveal-d6"
              icon={<Shield className="h-5 w-5 text-cyan-400" />}
              iconBg="bg-cyan-500/15"
              title="Isolated environment"
              description="Each customer gets a dedicated droplet. Your code, keys, and agent sessions are completely isolated from other users."
            />
          </div>
        </div>
      </section>

      {/* ── Pricing ─────────────────────────────────────────────── */}
      <section id="pricing" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="mb-3 text-3xl font-bold tracking-tight md:text-4xl">
              Simple, one-time pricing
            </h2>
            <p className="text-white/40">Pay once, own forever. No subscriptions, no surprises.</p>
          </div>

          <div className="reveal mx-auto max-w-md">
            <div className="relative overflow-hidden rounded-2xl border border-violet-500/25 bg-white/[0.03] p-8 shadow-violet-lg">
              {/* Subtle gradient top highlight */}
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/50 to-transparent" />
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_0%,rgba(124,58,237,0.08)_0%,transparent_70%)]" />

              <div className="relative">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-lg font-semibold text-white">Maestro</span>
                  <Badge className="border-violet-500/30 bg-violet-500/15 text-xs text-violet-300">
                    One-time
                  </Badge>
                </div>

                <div className="mt-5 flex items-baseline gap-2">
                  <span className="text-6xl font-bold tracking-tight text-white">$99</span>
                  <span className="text-sm text-white/35">one-time</span>
                </div>
                <p className="mt-1.5 text-sm text-white/35">
                  + ~$24/mo DigitalOcean droplet (billed directly to you)
                </p>

                <Separator className="my-6 bg-white/[0.07]" />

                <ul className="space-y-3.5">
                  {[
                    "Auto-provisioned DigitalOcean droplet",
                    "Claude Code pre-installed & configured",
                    "Browser-based terminal (ttyd)",
                    "MCP connector for claude.ai",
                    "Parallel agent support",
                    "Dedicated Discord support channel",
                    "Lifetime access to updates",
                  ].map((feature) => (
                    <CheckItem key={feature}>{feature}</CheckItem>
                  ))}
                </ul>

                <Separator className="my-6 bg-white/[0.07]" />

                <form action="/api/checkout" method="POST">
                  <Button
                    type="submit"
                    className="h-12 w-full rounded-xl bg-white text-base font-semibold text-black shadow-[0_2px_8px_rgba(255,255,255,0.08)] hover:bg-white/92"
                  >
                    Get Maestro for $99
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </form>

                <p className="mt-3 text-center text-xs text-white/25">
                  Secure payment via Stripe · 30-day refund policy
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ ─────────────────────────────────────────────────── */}
      <section id="faq" className="px-6 py-24">
        <div className="mx-auto max-w-2xl">
          <div className="reveal mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight md:text-4xl">
              Frequently asked questions
            </h2>
          </div>

          <Accordion type="single" collapsible className="reveal space-y-1">
            {[
              {
                q: "What do I need to get started?",
                a: "A Claude Max subscription (for unlimited Claude Code usage), a DigitalOcean account (free to create — you only pay for the droplet), and a credit card for the $99 Maestro fee. No server knowledge required.",
              },
              {
                q: "How is this different from running Claude Code locally?",
                a: "Local Claude Code ties up your machine and stops when you close the lid. Maestro runs on a dedicated cloud VPS 24/7 — agents keep working while your laptop is off. You control everything from a browser tab with no SSH client needed.",
              },
              {
                q: "Who pays for the DigitalOcean droplet?",
                a: "You do, directly. Maestro provisions the droplet into your DigitalOcean account using your API key. The $24/mo (or chosen size) is charged by DigitalOcean to your card — we never see or mark up your infrastructure costs.",
              },
              {
                q: "What happens to my droplet if I cancel?",
                a: "Your droplet is in your DigitalOcean account — you control it fully. You can keep it running, resize it, or destroy it anytime through the DigitalOcean dashboard. Maestro never has persistent access to your infrastructure after initial provisioning.",
              },
              {
                q: "Can I run multiple agents in parallel?",
                a: "Yes. The default 2 vCPU / 4 GB droplet handles 2–4 parallel Claude Code sessions comfortably. For heavier workloads, choose a larger size during setup (4 vCPU / 8 GB available). Claude Max plan rate limits apply regardless of hardware.",
              },
            ].map(({ q, a }) => (
              <AccordionItem key={q} value={q} className="border-white/[0.07]">
                <AccordionTrigger className="py-5 text-left text-[15px] text-white hover:text-white hover:no-underline [&[data-state=open]]:text-violet-300">
                  {q}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-[14px] leading-relaxed text-white/45">
                  {a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* ── Bottom CTA ──────────────────────────────────────────── */}
      <section className="px-6 pb-24 pt-4">
        <div className="reveal mx-auto max-w-3xl">
          <div className="relative overflow-hidden rounded-2xl border border-violet-500/20 p-10 text-center md:p-16">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_50%_50%,rgba(124,58,237,0.1)_0%,transparent_70%)]" />
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/40 to-transparent" />

            <div className="relative">
              <h2 className="mb-4 text-3xl font-bold tracking-tight md:text-4xl">
                Ready to run agents without a terminal?
              </h2>
              <p className="mx-auto mb-8 max-w-md text-white/40">
                Get set up in under 10 minutes. Your first agent runs before you finish your coffee.
              </p>
              <form action="/api/checkout" method="POST">
                <Button
                  type="submit"
                  size="lg"
                  className="h-12 rounded-xl bg-white px-10 text-base font-semibold text-black hover:bg-white/92"
                >
                  Get started for $99
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.05] px-6 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex items-center gap-2.5">
            <svg width="18" height="18" viewBox="0 0 22 22" fill="none" aria-hidden="true">
              <rect width="22" height="22" rx="6" fill="#7c3aed" />
              <circle cx="11" cy="11" r="5.5" stroke="white" strokeWidth="1.25" fill="none" />
              <circle cx="11" cy="11" r="2" fill="white" />
            </svg>
            <span className="text-sm font-medium text-white/40">Maestro</span>
          </div>
          <p className="text-sm text-white/20">© {new Date().getFullYear()} Maestro. All rights reserved.</p>
          <a
            href="mailto:support@maestro.run"
            className="text-sm text-white/28 transition-colors hover:text-white/55"
          >
            support@maestro.run
          </a>
        </div>
      </footer>

      {/* ── Mobile sticky CTA (hidden on md+) ───────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-white/[0.06] bg-[#0a0a0b]/95 px-4 py-3 backdrop-blur-xl [padding-bottom:max(12px,env(safe-area-inset-bottom))] md:hidden">
        <form action="/api/checkout" method="POST">
          <Button
            type="submit"
            className="h-12 w-full rounded-xl bg-white text-base font-semibold text-black hover:bg-white/92"
          >
            Get Maestro for $99
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
