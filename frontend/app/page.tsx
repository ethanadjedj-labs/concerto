import Link from "next/link"
import { HeroOrbital } from "@/components/HeroOrbital"
import { HeroClaudeDemo } from "@/components/HeroClaudeDemo"
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
import { TrustSection } from "@/components/TrustSection"
import {
  Zap,
  Cloud,
  Check,
  Terminal,
  Shield,
  ArrowRight,
  GitBranch,
  MessageSquare,
} from "lucide-react"

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
      className={`reveal ${revealDelay ?? ""} group rounded-xl border border-[rgba(245,240,233,0.08)] bg-[#1a161c] p-8 shadow-[inset_0_1px_0_rgba(245,240,233,0.06)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[rgba(217,119,87,0.2)] hover:bg-[#221c25]`}
    >
      <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <h3 className="mb-2.5 text-[15px] font-medium tracking-tight text-[#f5f0e9]">{title}</h3>
      <p className="text-sm leading-relaxed text-[#877c70]">{description}</p>
    </div>
  )
}

/* ─── Pricing check item ──────────────────────────────────────── */

function CheckItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-[rgba(217,119,87,0.15)]">
        <Check className="h-3 w-3 text-[#d97757]" />
      </span>
      <span className="text-[#c4b8aa]">{children}</span>
    </li>
  )
}

/* ─── Landing page ────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0f0d10] text-[#f5f0e9]">
      <ScrollReveal />

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <nav className="fixed left-0 right-0 top-0 z-50 border-b border-[rgba(245,240,233,0.05)] bg-[#0f0d10]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <svg width="22" height="22" viewBox="0 0 200 200" fill="none" aria-hidden="true">
              <path d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69" fill="none" stroke="#d97757" strokeWidth={13} strokeLinecap="round"/>
              <path d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"   fill="none" stroke="#b483ff" strokeWidth={13} strokeLinecap="round"/>
              <path d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50" fill="none" stroke="#8b7fff" strokeWidth={13} strokeLinecap="round"/>
              <circle cx="115.56" cy="115.56" r={16} fill="#d97757"/>
              <circle cx="61.36"  cy="89.65"  r={16} fill="#b483ff"/>
              <circle cx="150.23" cy="71.00"  r={16} fill="#8b7fff"/>
              <circle cx="100"    cy="100"    r={22} fill="#f5f0e9"/>
            </svg>
            <span className="font-medium tracking-tight text-[#f5f0e9]">Concerto</span>
          </div>

          <div className="flex items-center gap-5">
            <Link href="#how-it-works" className="hidden text-sm text-[#877c70] transition-colors hover:text-[#f5f0e9] md:block">
              How it works
            </Link>
            <Link href="#pricing" className="hidden text-sm text-[#877c70] transition-colors hover:text-[#f5f0e9] md:block">
              Pricing
            </Link>
            <Link href="#faq" className="hidden text-sm text-[#877c70] transition-colors hover:text-[#f5f0e9] md:block">
              FAQ
            </Link>
            <form action="/api/checkout?plan=hosted" method="POST">
              <Button
                size="sm"
                className="h-8 rounded-md px-4 text-xs"
              >
                Start in 5 minutes
              </Button>
            </form>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pb-16 pt-36 md:pb-24 md:pt-40">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <HeroOrbital />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(139,127,255,0.08)_0%,transparent_70%)]" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0f0d10]/50 to-[#0f0d10]" />
        </div>

        <div className="relative mx-auto max-w-4xl px-6 text-center">
          <div className="animate-fade-up mb-6 flex justify-center">
            <Badge
              variant="outline"
              className="border-[rgba(217,119,87,0.30)] bg-[rgba(217,119,87,0.08)] px-4 py-1.5 text-xs font-medium text-[#e48a62]"
            >
              <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-[#d97757] animate-dot-blink" />
              Works with Claude Pro and Max
            </Badge>
          </div>

          <h1 className="animate-fade-up delay-100 font-display mb-6 text-5xl font-[400] leading-[1.04] tracking-[-0.02em] sm:text-6xl md:text-7xl">
            Run Claude Code{" "}
            <span className="bg-gradient-to-r from-[#d97757] via-[#e09070] to-[#8b7fff] bg-clip-text text-transparent">
              from Claude chat.
            </span>
          </h1>

          <p className="animate-fade-up delay-200 mx-auto mb-4 max-w-2xl text-lg leading-relaxed text-[#c4b8aa] md:text-xl">
            Talk to Claude. Claude runs Claude Code on a remote workspace.
            No terminal. No GitHub juggling. No sandbox.
          </p>

          <p className="animate-fade-up delay-200 mb-8 text-sm text-[#877c70]">
            Works with your Claude Pro or Max subscription.
          </p>

          <div className="animate-fade-up delay-300 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <form action="/api/checkout?plan=hosted" method="POST">
              <Button
                size="lg"
                className="h-12 rounded-md px-8 text-base font-medium"
              >
                Start in 5 minutes — $39/month
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </form>
            <p className="text-sm text-[#877c70]">
              Or{" "}
              <a href="#pricing" className="text-[#c4b8aa] underline underline-offset-2 hover:text-[#f5f0e9]">
                use your own cloud — $99 once
              </a>
            </p>
          </div>

          <div className="animate-fade-up delay-500 mt-16 px-2">
            <HeroClaudeDemo />
          </div>
        </div>
      </section>

      {/* ── Problem block ───────────────────────────────────────── */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight md:text-4xl">
              Claude Code is powerful. Running it is not.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <FeatureCard
              revealDelay="reveal-d1"
              icon={<Terminal className="h-5 w-5 text-orange-400" />}
              iconBg="bg-orange-500/15"
              title="No more terminal"
              description="Claude Code lives in a CLI. Forget that. Concerto puts it inside Claude chat — you type, Claude acts."
            />
            <FeatureCard
              revealDelay="reveal-d2"
              icon={<GitBranch className="h-5 w-5 text-blue-400" />}
              iconBg="bg-blue-500/15"
              title="No more GitHub juggling"
              description="Cloning, branches, PRs handled on the remote workspace. You stay in Claude chat the whole time."
            />
            <FeatureCard
              revealDelay="reveal-d3"
              icon={<Shield className="h-5 w-5 text-emerald-400" />}
              iconBg="bg-emerald-500/15"
              title="No more sandbox limits"
              description="Sandboxed environments cap what Claude Code can do. Your own VPS runs real git, real tests, real deploys."
            />
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────── */}
      <section id="how-it-works" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight md:text-4xl">
              Three steps, then you&apos;re done.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              {
                n: "01",
                title: "Pay $39/month",
                desc: "We spin up your remote workspace. Provisioning takes about 3 minutes. You get an email when it is ready.",
              },
              {
                n: "02",
                title: "Connect Claude chat",
                desc: "One click opens the connector setup. Paste 3 fields into claude.ai. Takes about 2 minutes.",
              },
              {
                n: "03",
                title: "Chat normally.",
                desc: "Claude does the rest. Tell it what to build. It writes code, runs tests, opens PRs — on your workspace.",
              },
            ].map((step, i) => (
              <div key={step.n} className={`reveal reveal-d${i + 1} relative rounded-xl border border-[rgba(245,240,233,0.08)] bg-[#1a161c] p-8 shadow-[inset_0_1px_0_rgba(245,240,233,0.06)]`}>
                <div className="mb-4 font-mono text-[11px] font-medium tracking-widest text-[#d97757]">{step.n}</div>
                <h3 className="mb-2 text-[15px] font-medium text-[#f5f0e9]">{step.title}</h3>
                <p className="text-sm leading-relaxed text-[#877c70]">{step.desc}</p>
                {i < 2 && (
                  <div className="absolute right-0 top-1/2 hidden -translate-y-1/2 translate-x-1/2 sm:block">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border border-[rgba(245,240,233,0.08)] bg-[#0f0d10]">
                      <ArrowRight className="h-3 w-3 text-[#877c70]" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <p className="reveal mt-6 text-center text-sm text-[#877c70]">
            Average setup time: 5 minutes. Most of it is automatic.
          </p>
        </div>
      </section>

      {/* ── What you'll actually do ──────────────────────────────── */}
      <section className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight md:text-4xl">
              What you&apos;ll actually do.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {[
              {
                prompt: "“Refactor my auth module to JWT. Run tests. Open a PR.”",
                result: "Concerto spawns a session, edits files, runs pytest, opens a GitHub PR. You read the result in chat.",
                delay: "reveal-d1",
                iconBg: "bg-[rgba(139,127,255,0.12)]",
                icon: <MessageSquare className="h-5 w-5 text-[#8b7fff]" />,
              },
              {
                prompt: "“Run a 3-hour migration script on my staging database overnight.”",
                result: "Concerto launches it, monitors the run, kills it if stuck, and reports back when done.",
                delay: "reveal-d2",
                iconBg: "bg-blue-500/15",
                icon: <Cloud className="h-5 w-5 text-blue-400" />,
              },
              {
                prompt: "“Try 3 different implementations of this feature in parallel.”",
                result: "Concerto spawns 3 sessions side-by-side. You read each result in chat and pick the best one.",
                delay: "reveal-d3",
                iconBg: "bg-emerald-500/15",
                icon: <Zap className="h-5 w-5 text-emerald-400" />,
              },
            ].map(({ prompt, result, delay, iconBg, icon }) => (
              <div
                key={prompt}
                className={`reveal ${delay} group rounded-xl border border-[rgba(245,240,233,0.08)] bg-[#1a161c] p-8 shadow-[inset_0_1px_0_rgba(245,240,233,0.06)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[rgba(217,119,87,0.2)] hover:bg-[#221c25]`}
              >
                <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg ${iconBg}`}>
                  {icon}
                </div>
                <p className="mb-3 font-mono text-[13px] leading-snug text-[#d97757]">{prompt}</p>
                <p className="text-sm leading-relaxed text-[#877c70]">{result}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust signals ───────────────────────────────────────── */}
      <TrustSection />

      {/* ── Pricing ─────────────────────────────────────────────── */}
      <section id="pricing" className="px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight md:text-4xl">
              Two ways to start.
            </h2>
            <p className="text-[#877c70]">
              Don&apos;t have a cloud account? Pick Hosted. We handle everything.
            </p>
          </div>

          <div className="reveal mx-auto grid max-w-4xl grid-cols-1 gap-6 md:grid-cols-2">

            {/* Hosted — featured */}
            <div className="relative overflow-hidden rounded-2xl border border-[rgba(217,119,87,0.35)] bg-[#1a161c] p-8 shadow-[0_0_0_1px_rgba(217,119,87,0.15),0_8px_40px_rgba(217,119,87,0.10)]">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[rgba(217,119,87,0.55)] to-transparent" />
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_0%,rgba(217,119,87,0.08)_0%,transparent_70%)]" />
              <div className="relative">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-lg font-medium text-[#f5f0e9]">Hosted</span>
                  <Badge className="border-[rgba(217,119,87,0.35)] bg-[rgba(217,119,87,0.12)] text-xs text-[#e48a62]">
                    Most popular
                  </Badge>
                </div>
                <p className="mb-1 text-sm text-[#877c70]">We host the workspace</p>
                <div className="mt-5 flex items-baseline gap-2">
                  <span className="font-display text-6xl font-[400] tracking-tight text-[#f5f0e9]">$39</span>
                  <span className="text-sm text-[#877c70]">/month</span>
                </div>
                <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
                <ul className="space-y-3.5">
                  {[
                    "Zero setup. We provision the VPS.",
                    "3–5 parallel Claude Code sessions",
                    "30-day email + Discord support",
                    "Cancel anytime",
                  ].map((feature) => (
                    <CheckItem key={feature}>{feature}</CheckItem>
                  ))}
                </ul>
                <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
                <form action="/api/checkout?plan=hosted" method="POST">
                  <Button
                    type="submit"
                    className="h-12 w-full rounded-md text-base font-medium"
                  >
                    Start with Hosted
                  </Button>
                </form>
                <p className="mt-3 text-center text-xs text-[#877c70]">
                  Secure payment via Stripe · Cancel anytime
                </p>
              </div>
            </div>

            {/* BYOC */}
            <div className="relative overflow-hidden rounded-2xl border border-[rgba(245,240,233,0.08)] bg-[#1a161c] p-8 shadow-[inset_0_1px_0_rgba(245,240,233,0.05)]">
              <div className="relative">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-lg font-medium text-[#f5f0e9]">BYOC</span>
                  <Badge className="border-[rgba(245,240,233,0.12)] bg-[rgba(245,240,233,0.07)] text-xs text-[#877c70]">
                    One-time
                  </Badge>
                </div>
                <p className="mb-1 text-sm text-[#877c70]">Bring your DigitalOcean account</p>
                <div className="mt-5 flex items-baseline gap-2">
                  <span className="font-display text-6xl font-[400] tracking-tight text-[#f5f0e9]">$99</span>
                  <span className="text-sm text-[#877c70]">once</span>
                </div>
                <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
                <ul className="space-y-3.5">
                  {[
                    "Workspace lives in your DigitalOcean account",
                    "You pay DigitalOcean directly (~$24/month)",
                    "Full control over the VPS",
                    "30-day email + Discord support",
                  ].map((feature) => (
                    <CheckItem key={feature}>{feature}</CheckItem>
                  ))}
                </ul>
                <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
                <form action="/api/checkout?plan=byoc" method="POST">
                  <Button
                    type="submit"
                    variant="outline"
                    className="h-12 w-full rounded-md text-base font-medium"
                  >
                    Start with BYOC
                  </Button>
                </form>
                <p className="mt-3 text-center text-xs text-[#877c70]">
                  Secure payment via Stripe · 30-day refund policy
                </p>
              </div>
            </div>

          </div>

          <div className="reveal mx-auto mt-8 max-w-xl rounded-xl border border-[rgba(245,240,233,0.07)] bg-[#1a161c] px-6 py-4">
            <p className="text-sm leading-relaxed text-[#877c70]">
              Not sure which?{" "}
              <span className="text-[#c4b8aa]">&rarr; Pick Hosted.</span>{" "}
              You can always switch later.
            </p>
          </div>

        </div>
      </section>

      {/* ── FAQ ─────────────────────────────────────────────────── */}
      <section id="faq" className="px-6 py-24">
        <div className="mx-auto max-w-2xl">
          <div className="reveal mb-12 text-center">
            <h2 className="font-display text-3xl font-[450] tracking-tight md:text-4xl">
              Frequently asked questions
            </h2>
          </div>

          <Accordion type="single" collapsible className="reveal space-y-1">
            {[
              {
                q: "Do I need Claude Pro or Max?",
                a: "Yes. Concerto uses your Anthropic subscription via the MCP connector. Pro ($20/mo) or Max ($200/mo) both work. You keep paying Anthropic directly — Concerto is a separate charge.",
              },
              {
                q: "What if I don't have a cloud account?",
                a: "Pick Hosted. We handle the VPS — no DigitalOcean signup needed. You pay $39/month and we provision, manage, and monitor the workspace for you.",
              },
              {
                q: "What if I already use DigitalOcean?",
                a: "Pick BYOC. You bring your DO account, we set up the workspace on a droplet in it, and you pay DigitalOcean directly (~$24/month). One-time $99 setup fee to Concerto.",
              },
              {
                q: "Can I cancel anytime?",
                a: "Yes. Hosted: cancel anytime, workspace is destroyed after a 72-hour data grace period. BYOC is a one-time purchase — no subscription to cancel, and the droplet stays in your account.",
              },
              {
                q: "Where is my code?",
                a: "On your workspace VPS. With Hosted, that's a VPS we provision on our account but dedicate entirely to you. With BYOC, it's in your own DigitalOcean account. We never see or store your code.",
              },
              {
                q: "Where are my Claude conversations?",
                a: "In your Claude chat history, with Anthropic. Concerto only receives tool calls — it never sees the conversation itself.",
              },
              {
                q: "What can Claude Code do via Concerto that it can't do otherwise?",
                a: "Run multi-hour tasks without you watching, work on real repos with real git history, deploy to staging, run actual test suites, and run 3–5 sessions in parallel. Claude Code's built-in sandbox can't do any of this.",
              },
              {
                q: "How fast is '5 minutes setup'?",
                a: "About 3 minutes for provisioning to complete, then about 2 minutes to copy-paste the connector config into claude.ai. Total: typically 5 minutes.",
              },
              {
                q: "What is the refund policy?",
                a: "14-day full refund if provisioning fails on our end. After successful provisioning, no refund — you've used the service (Hosted) or own the setup (BYOC).",
              },
              {
                q: "Who built this?",
                a: "Solo operator. No funding, no VCs, no telemetry beyond what's needed to provision your workspace. View the project on GitHub.",
              },
            ].map(({ q, a }) => (
              <AccordionItem key={q} value={q} className="border-[rgba(245,240,233,0.07)]">
                <AccordionTrigger className="py-5 text-left text-[15px] text-[#f5f0e9] hover:text-[#f5f0e9] hover:no-underline [&[data-state=open]]:text-[#d97757]">
                  {q}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-[14px] leading-relaxed text-[#877c70]">
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
          <div className="relative overflow-hidden rounded-2xl border border-[rgba(217,119,87,0.18)] p-10 text-center md:p-16">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_60%_at_50%_50%,rgba(217,119,87,0.07)_0%,transparent_70%)]" />
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[rgba(217,119,87,0.35)] to-transparent" />

            <div className="relative">
              <h2 className="font-display mb-4 text-3xl font-[450] tracking-tight md:text-4xl">
                Stop juggling tools. Let Claude do it.
              </h2>
              <p className="mx-auto mb-8 max-w-md text-[#877c70]">
                Setup takes 5 minutes. You&apos;ll wonder why you didn&apos;t do this sooner.
              </p>
              <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
                <form action="/api/checkout?plan=hosted" method="POST">
                  <Button
                    type="submit"
                    size="lg"
                    className="h-12 rounded-md px-10 text-base font-medium"
                  >
                    Start with Hosted ($39/mo)
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </form>
                <form action="/api/checkout?plan=byoc" method="POST">
                  <Button
                    type="submit"
                    size="lg"
                    variant="outline"
                    className="h-12 rounded-md px-10 text-base font-medium"
                  >
                    Use my own cloud ($99 once)
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="border-t border-[rgba(245,240,233,0.05)] px-6 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2.5">
              <svg width="18" height="18" viewBox="0 0 200 200" fill="none" aria-hidden="true">
                <path d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69" fill="none" stroke="#d97757" strokeWidth={13} strokeLinecap="round"/>
                <path d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"   fill="none" stroke="#b483ff" strokeWidth={13} strokeLinecap="round"/>
                <path d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50" fill="none" stroke="#8b7fff" strokeWidth={13} strokeLinecap="round"/>
                <circle cx="115.56" cy="115.56" r={16} fill="#d97757"/>
                <circle cx="61.36"  cy="89.65"  r={16} fill="#b483ff"/>
                <circle cx="150.23" cy="71.00"  r={16} fill="#8b7fff"/>
                <circle cx="100"    cy="100"    r={22} fill="#f5f0e9"/>
              </svg>
              <span className="text-sm font-medium text-[#877c70]">Concerto</span>
            </div>
            <p className="text-sm text-[#6e645a]">&copy; {new Date().getFullYear()} Concerto. All rights reserved.</p>
            <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5">
              {[
                { href: "/legal/terms",   label: "Terms" },
                { href: "/legal/privacy", label: "Privacy" },
                { href: "/legal/refund",  label: "Refund" },
                { href: "/legal/aup",     label: "Acceptable Use" },
                { href: "/help",          label: "Help" },
              ].map(({ href, label }) => (
                <Link key={href} href={href} className="text-xs text-[#6e645a] transition-colors hover:text-[#c4b8aa]">
                  {label}
                </Link>
              ))}
              <a href="mailto:support@concerto.run" className="text-xs text-[#6e645a] transition-colors hover:text-[#c4b8aa]">
                support@concerto.run
              </a>
            </div>
          </div>
          <p className="mt-6 text-center text-xs text-[#6e645a]">Built by an operator in Almaty.</p>
        </div>
      </footer>

      {/* ── Mobile sticky CTA (hidden on md+) ───────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-[rgba(245,240,233,0.06)] bg-[#0f0d10]/95 px-4 py-3 backdrop-blur-xl [padding-bottom:max(12px,env(safe-area-inset-bottom))] md:hidden">
        <form action="/api/checkout?plan=hosted" method="POST">
          <Button
            type="submit"
            className="h-12 w-full rounded-md text-base font-medium"
          >
            Start in 5 minutes — $39/mo
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}
