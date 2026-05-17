import type { ReactNode } from "react"
import Link from "next/link"
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

/* ─── Logo mark — works on cream background ──────────────────── */

function LogoMark({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 200 200" fill="none" aria-hidden="true">
      <path d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69" fill="none" stroke="#cc785c" strokeWidth={13} strokeLinecap="round"/>
      <path d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"   fill="none" stroke="#2a2925" strokeWidth={13} strokeLinecap="round" opacity={0.55}/>
      <path d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50" fill="none" stroke="#2a2925" strokeWidth={13} strokeLinecap="round" opacity={0.35}/>
      <circle cx="115.56" cy="115.56" r={14} fill="#cc785c"/>
      <circle cx="61.36"  cy="89.65"  r={14} fill="#2a2925" opacity={0.55}/>
      <circle cx="150.23" cy="71.00"  r={14} fill="#2a2925" opacity={0.35}/>
      <circle cx="100"    cy="100"    r={20} fill="#191919"/>
    </svg>
  )
}

/* ─── Feature card ────────────────────────────────────────────── */

function FeatureCard({
  icon,
  iconBg,
  title,
  description,
  revealDelay,
}: {
  icon: ReactNode
  iconBg: string
  title: string
  description: string
  revealDelay?: string
}) {
  return (
    <div
      className={`reveal ${revealDelay ?? ""} rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)] transition-colors duration-300 hover:border-[rgba(204,120,92,0.25)]`}
    >
      <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg ${iconBg}`}>
        {icon}
      </div>
      <h3 className="mb-2.5 text-[15px] font-medium tracking-tight text-[#191919]">{title}</h3>
      <p className="text-sm leading-relaxed text-[#8a847b]">{description}</p>
    </div>
  )
}

/* ─── Pricing check item ──────────────────────────────────────── */

function CheckItem({ children }: { children: ReactNode }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-[rgba(204,120,92,0.12)]">
        <Check className="h-3 w-3 text-[#cc785c]" />
      </span>
      <span className="text-[#555049]">{children}</span>
    </li>
  )
}

/* ─── Landing page ────────────────────────────────────────────── */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#faf9f5] text-[#191919]">
      <ScrollReveal />

      {/* ── Nav ─────────────────────────────────────────────────── */}
      <nav className="fixed left-0 right-0 top-0 z-50 border-b border-[rgba(25,25,25,0.07)] bg-[#faf9f5]/88 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2.5">
            <LogoMark size={22} />
            <span className="font-medium tracking-tight text-[#191919]">Concerto</span>
          </div>

          <div className="flex items-center gap-5">
            <Link href="#how-it-works" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              How it works
            </Link>
            <Link href="#pricing" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              Pricing
            </Link>
            <Link href="#faq" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              FAQ
            </Link>
            <form action="/api/checkout?plan=hosted" method="POST">
              <Button
                size="sm"
                className="h-8 rounded-[6px] bg-[#cc785c] px-4 text-xs font-medium text-[#faf9f5] hover:bg-[#b86747]"
              >
                Start in 5 minutes
              </Button>
            </form>
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────── */}
      <section className="pb-16 pt-36 md:pb-20 md:pt-40">
        <div className="mx-auto max-w-6xl px-6">

          {/* Desktop: two-column | Mobile: stacked */}
          <div className="flex flex-col gap-12 lg:flex-row lg:items-center lg:gap-16">

            {/* Left column — ~45% width on desktop */}
            <div className="animate-fade-up flex-shrink-0 lg:w-[44%]">

              {/* Editorial peach line — book/manifesto mark */}
              <div className="mb-8 h-px w-[60px] bg-[#cc785c]" />

              <div className="mb-5 flex">
                <Badge
                  variant="outline"
                  className="border-[rgba(204,120,92,0.30)] bg-[rgba(204,120,92,0.07)] px-4 py-1.5 text-xs font-medium text-[#b86747]"
                >
                  <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-[#cc785c] animate-dot-blink" />
                  Works with Claude Pro and Max
                </Badge>
              </div>

              <h1 className="font-display mb-5 text-[2.75rem] font-[450] leading-[1.06] tracking-[-0.02em] text-[#191919] sm:text-5xl md:text-[3.25rem]">
                Run Claude Code{" "}
                <span className="text-[#cc785c]">from Claude chat.</span>
              </h1>

              <p className="mb-3 text-lg leading-relaxed text-[#555049]">
                Talk to Claude. Claude runs Claude Code on a remote workspace.
                No terminal. No GitHub juggling. No sandbox.
              </p>

              <p className="mb-10 text-sm text-[#8a847b]">
                Works with your Claude Pro or Max subscription.
              </p>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <form action="/api/checkout?plan=hosted" method="POST">
                  <Button
                    size="lg"
                    className="h-12 rounded-[6px] bg-[#cc785c] px-8 text-base font-medium text-[#faf9f5] hover:bg-[#b86747]"
                  >
                    Start in 5 minutes — $39/month
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </form>
                <p className="text-sm text-[#8a847b]">
                  Or{" "}
                  <a href="#pricing" className="text-[#555049] underline underline-offset-2 hover:text-[#191919]">
                    use your own cloud — $99 once
                  </a>
                </p>
              </div>
              <p className="mt-2 text-sm text-[#a09890]">
                Not sure?{" "}
                <Link href="/try" className="text-[#8a847b] underline underline-offset-2 hover:text-[#555049] transition-colors">
                  Try free for 30 minutes, no card required →
                </Link>
              </p>
            </div>

            {/* Right column — flex-1 (~55%) on desktop */}
            <div className="animate-fade-up delay-200 min-w-0 flex-1">
              <HeroClaudeDemo />
            </div>
          </div>
        </div>
      </section>

      {/* ── Problem block ───────────────────────────────────────── */}
      <section className="px-6 py-24 bg-[#f3efe5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
              Claude Code is powerful. Running it is not.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <FeatureCard
              revealDelay="reveal-d1"
              icon={<Terminal className="h-5 w-5 text-[#cc785c]" />}
              iconBg="bg-[rgba(204,120,92,0.10)]"
              title="No more terminal"
              description="Claude Code lives in a CLI. Forget that. Concerto puts it inside Claude chat — you type, Claude acts."
            />
            <FeatureCard
              revealDelay="reveal-d2"
              icon={<GitBranch className="h-5 w-5 text-[#555049]" />}
              iconBg="bg-[rgba(25,25,25,0.05)]"
              title="No more GitHub juggling"
              description="Cloning, branches, PRs handled on the remote workspace. You stay in Claude chat the whole time."
            />
            <FeatureCard
              revealDelay="reveal-d3"
              icon={<Shield className="h-5 w-5 text-[#555049]" />}
              iconBg="bg-[rgba(25,25,25,0.05)]"
              title="No more sandbox limits"
              description="Sandboxed environments cap what Claude Code can do. Your own VPS runs real git, real tests, real deploys."
            />
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────── */}
      <section id="how-it-works" className="px-6 py-24 bg-[#faf9f5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
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
              <div
                key={step.n}
                className={`reveal reveal-d${i + 1} relative rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)]`}
              >
                <div className="mb-4 font-mono text-[11px] font-medium tracking-widest text-[#cc785c]">{step.n}</div>
                <h3 className="mb-2 text-[15px] font-medium text-[#191919]">{step.title}</h3>
                <p className="text-sm leading-relaxed text-[#8a847b]">{step.desc}</p>
                {i < 2 && (
                  <div className="absolute right-0 top-1/2 hidden -translate-y-1/2 translate-x-1/2 sm:block">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full border border-[rgba(25,25,25,0.10)] bg-[#faf9f5]">
                      <ArrowRight className="h-3 w-3 text-[#8a847b]" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <p className="reveal mt-6 text-center text-sm text-[#8a847b]">
            Average setup time: 5 minutes. Most of it is automatic.
          </p>
        </div>
      </section>

      {/* ── What you'll actually do ──────────────────────────────── */}
      <section className="px-6 py-24 bg-[#f3efe5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
              What you&apos;ll actually do.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {[
              {
                prompt: "“Refactor my auth module to JWT. Run tests. Open a PR.”",
                result: "Concerto spawns a session, edits files, runs pytest, opens a GitHub PR. You read the result in chat.",
                delay: "reveal-d1",
                iconBg: "bg-[rgba(204,120,92,0.10)]",
                icon: <MessageSquare className="h-5 w-5 text-[#cc785c]" />,
              },
              {
                prompt: "“Run a 3-hour migration script on my staging database overnight.”",
                result: "Concerto launches it, monitors the run, kills it if stuck, and reports back when done.",
                delay: "reveal-d2",
                iconBg: "bg-[rgba(25,25,25,0.05)]",
                icon: <Cloud className="h-5 w-5 text-[#555049]" />,
              },
              {
                prompt: "“Try 3 different implementations of this feature in parallel.”",
                result: "Concerto spawns 3 sessions side-by-side. You read each result in chat and pick the best one.",
                delay: "reveal-d3",
                iconBg: "bg-[rgba(25,25,25,0.05)]",
                icon: <Zap className="h-5 w-5 text-[#555049]" />,
              },
            ].map(({ prompt, result, delay, iconBg, icon }) => (
              <div
                key={prompt}
                className={`reveal ${delay} rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)] transition-colors duration-300 hover:border-[rgba(204,120,92,0.25)]`}
              >
                <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-lg ${iconBg}`}>
                  {icon}
                </div>
                <p className="mb-3 font-mono text-[13px] leading-snug text-[#cc785c]">{prompt}</p>
                <p className="text-sm leading-relaxed text-[#8a847b]">{result}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust signals ───────────────────────────────────────── */}
      <TrustSection />

      {/* ── Pricing ─────────────────────────────────────────────── */}
      <section id="pricing" className="px-6 py-24 bg-[#faf9f5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
              Two ways to start.
            </h2>
            <p className="text-[#8a847b]">
              Don&apos;t have a cloud account? Pick Hosted. We handle everything.
            </p>
          </div>

          <div className="reveal mx-auto grid max-w-4xl grid-cols-1 gap-6 md:grid-cols-2">

            {/* Hosted — featured with peach border */}
            <div className="relative overflow-hidden rounded-xl border border-[rgba(204,120,92,0.45)] bg-white p-8 shadow-[0_2px_12px_rgba(204,120,92,0.08)]">
              <div className="relative">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-lg font-medium text-[#191919]">Hosted</span>
                  <span className="rounded bg-[rgba(204,120,92,0.10)] px-2.5 py-1 text-xs font-medium text-[#cc785c]">
                    Most popular
                  </span>
                </div>
                <p className="mb-1 text-sm text-[#8a847b]">We host the workspace</p>
                <div className="mt-5 flex items-baseline gap-2">
                  <span className="font-display text-6xl font-[400] tracking-tight text-[#191919]">$39</span>
                  <span className="text-sm text-[#8a847b]">/month</span>
                </div>
                <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
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
                <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
                <form action="/api/checkout?plan=hosted" method="POST">
                  <Button
                    type="submit"
                    className="h-12 w-full rounded-[6px] bg-[#cc785c] text-base font-medium text-[#faf9f5] hover:bg-[#b86747]"
                  >
                    Start with Hosted
                  </Button>
                </form>
                <p className="mt-3 text-center text-xs text-[#8a847b]">
                  Secure payment via Stripe · Cancel anytime
                </p>
              </div>
            </div>

            {/* BYOC */}
            <div className="relative overflow-hidden rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)]">
              <div className="relative">
                <div className="mb-1 flex items-center justify-between">
                  <span className="text-lg font-medium text-[#191919]">BYOC</span>
                  <span className="rounded bg-[rgba(25,25,25,0.05)] px-2.5 py-1 text-xs font-medium text-[#8a847b]">
                    One-time
                  </span>
                </div>
                <p className="mb-1 text-sm text-[#8a847b]">Bring your DigitalOcean account</p>
                <div className="mt-5 flex items-baseline gap-2">
                  <span className="font-display text-6xl font-[400] tracking-tight text-[#191919]">$99</span>
                  <span className="text-sm text-[#8a847b]">once</span>
                </div>
                <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
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
                <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
                <form action="/api/checkout?plan=byoc" method="POST">
                  <Button
                    type="submit"
                    variant="outline"
                    className="h-12 w-full rounded-[6px] border-[rgba(25,25,25,0.15)] text-base font-medium text-[#191919] hover:bg-[#f3efe5]"
                  >
                    Start with BYOC
                  </Button>
                </form>
                <p className="mt-3 text-center text-xs text-[#8a847b]">
                  Secure payment via Stripe · 30-day refund policy
                </p>
              </div>
            </div>

          </div>

          <div className="reveal mx-auto mt-8 max-w-xl rounded-lg border border-[rgba(25,25,25,0.08)] bg-white px-6 py-4">
            <p className="text-sm leading-relaxed text-[#8a847b]">
              Not sure which?{" "}
              <span className="text-[#555049]">&rarr; Pick Hosted.</span>{" "}
              You can always switch later.
            </p>
          </div>

          <p className="reveal mt-5 text-center text-sm text-[#a09890]">
            Not sure if Concerto is for you?{" "}
            <Link href="/try" className="text-[#8a847b] underline underline-offset-2 hover:text-[#555049] transition-colors">
              Try free for 30 minutes — no card needed →
            </Link>
          </p>

        </div>
      </section>

      {/* ── FAQ ─────────────────────────────────────────────────── */}
      <section id="faq" className="px-6 py-24 bg-[#f3efe5]">
        <div className="mx-auto max-w-2xl">
          <div className="reveal mb-12 text-center">
            <h2 className="font-display text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
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
              <AccordionItem key={q} value={q} className="border-b border-[rgba(25,25,25,0.08)]">
                <AccordionTrigger className="py-5 text-left text-[15px] text-[#191919] hover:text-[#191919] hover:no-underline [&[data-state=open]]:text-[#cc785c]">
                  {q}
                </AccordionTrigger>
                <AccordionContent className="pb-5 text-[14px] leading-relaxed text-[#8a847b]">
                  {a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* ── Bottom CTA — inverted dark section ───────────────────── */}
      <section className="px-6 py-24 bg-[#2a2925]">
        <div className="reveal mx-auto max-w-3xl text-center">
          <div className="mx-auto mb-2 h-px w-[60px] bg-[#cc785c] opacity-60" />
          <h2 className="font-display mt-8 mb-4 text-3xl font-[450] tracking-tight text-[#faf9f5] md:text-4xl">
            Stop juggling tools. Let Claude do it.
          </h2>
          <p className="mx-auto mb-10 max-w-md text-[#8a847b]">
            Setup takes 5 minutes. You&apos;ll wonder why you didn&apos;t do this sooner.
          </p>
          <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <form action="/api/checkout?plan=hosted" method="POST">
              <Button
                type="submit"
                size="lg"
                className="h-12 rounded-[6px] bg-[#faf9f5] px-10 text-base font-medium text-[#2a2925] hover:bg-[#e9b8a4]"
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
                className="h-12 rounded-[6px] border-[rgba(250,249,245,0.25)] px-10 text-base font-medium text-[#faf9f5] hover:bg-white/10"
              >
                Use my own cloud ($99 once)
              </Button>
            </form>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="border-t border-[rgba(250,249,245,0.07)] bg-[#2a2925] px-6 py-10">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2.5">
              <LogoMark size={18} />
              <span className="text-sm font-medium text-[rgba(250,249,245,0.55)]">Concerto</span>
            </div>
            <p className="text-sm text-[rgba(250,249,245,0.30)]">&copy; {new Date().getFullYear()} Concerto. All rights reserved.</p>
            <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5">
              {[
                { href: "/legal/terms",   label: "Terms" },
                { href: "/legal/privacy", label: "Privacy" },
                { href: "/legal/refund",  label: "Refund" },
                { href: "/legal/aup",     label: "Acceptable Use" },
                { href: "/help",          label: "Help" },
              ].map(({ href, label }) => (
                <Link key={href} href={href} className="text-xs text-[rgba(250,249,245,0.35)] transition-colors hover:text-[rgba(250,249,245,0.65)]">
                  {label}
                </Link>
              ))}
              <a href="mailto:support@concerto.run" className="text-xs text-[rgba(250,249,245,0.35)] transition-colors hover:text-[rgba(250,249,245,0.65)]">
                support@concerto.run
              </a>
            </div>
          </div>
          <p className="mt-6 text-center text-xs text-[rgba(250,249,245,0.25)]">Built by an operator in Almaty.</p>
        </div>
      </footer>

      {/* ── Mobile sticky CTA (hidden on md+) ───────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-[rgba(25,25,25,0.10)] bg-[#faf9f5]/95 px-4 py-3 backdrop-blur-xl [padding-bottom:max(12px,env(safe-area-inset-bottom))] md:hidden">
        <form action="/api/checkout?plan=hosted" method="POST">
          <Button
            type="submit"
            className="h-12 w-full rounded-[6px] bg-[#cc785c] text-base font-medium text-[#faf9f5] hover:bg-[#b86747]"
          >
            Start in 5 minutes — $39/mo
          </Button>
        </form>
      </div>
    </div>
  )
}
