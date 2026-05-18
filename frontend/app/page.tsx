import type { ReactNode } from "react"
import Link from "next/link"
import { HeroClaudeDemo } from "@/components/HeroClaudeDemo"
import { MobileStickyCTA } from "@/components/MobileStickyCTA"
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
import { Check, ArrowRight, Star } from "lucide-react"

/* ─── Logo mark — bubble+baton, works on cream background ───── */

function LogoMark({ size = 22 }: { size?: number }) {
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
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3 md:py-5">
          <div className="flex items-center gap-2 md:gap-3">
            <span className="md:hidden"><LogoMark size={32} /></span>
            <span className="hidden md:inline-block"><LogoMark size={56} /></span>
            <span className="text-[20px] font-medium leading-none tracking-tight text-[#191919] md:text-[26px]">Concerto</span>
          </div>

          <div className="flex items-center gap-4 md:gap-5">
            <Link href="#how" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              How it works
            </Link>
            <Link href="#pricing" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              Pricing
            </Link>
            <Link href="#faq" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              FAQ
            </Link>
            <form action="/api/checkout?plan=pro" method="POST">
              <Button
                size="sm"
                className="h-7 rounded-[6px] bg-[#cc785c] px-3 text-xs font-medium text-[#faf9f5] hover:bg-[#b86747] md:h-8 md:px-4"
              >
                Start in 5 minutes
              </Button>
            </form>
          </div>
        </div>
      </nav>

      {/* ── A. Hero ──────────────────────────────────────────────── */}
      <section id="hero" className="pb-12 pt-28 md:pb-20 md:pt-40">
        <div className="mx-auto max-w-6xl px-6">
          <div className="animate-fade-up max-w-2xl">

            {/* Slogan badge */}
            <div className="mb-5 flex">
              <Badge
                variant="outline"
                className="border-[rgba(204,120,92,0.30)] bg-[rgba(204,120,92,0.07)] px-4 py-1.5 text-xs font-medium text-[#b86747]"
              >
                <span className="mr-2 inline-block h-1.5 w-1.5 rounded-full bg-[#cc785c] animate-dot-blink" />
                Talk to Claude. Claude runs Claude Code.
              </Badge>
            </div>

            <h1 className="font-display mb-5 text-[36px] font-[450] leading-[1.06] tracking-[-0.02em] text-[#191919] md:text-[56px]">
              Run multiple Claude Code sessions from one Claude chat.
            </h1>

            <p className="mb-5 text-lg leading-relaxed text-[#555049]">
              Concerto lets Claude launch, monitor, compare, and report on Claude Code runs — so you stop managing terminals manually.
            </p>

            {/* Claude Max badge */}
            <div className="mb-8">
              <span className="inline-block rounded border border-[rgba(25,25,25,0.12)] bg-[rgba(25,25,25,0.04)] px-3 py-1 text-xs text-[#555049]">
                Works with Claude Pro. Built for Claude Max.
              </span>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <form action="/api/checkout?plan=pro" method="POST">
                <Button
                  size="lg"
                  className="h-11 rounded-[6px] bg-[#cc785c] px-6 text-base font-medium text-[#faf9f5] hover:bg-[#b86747] md:h-12 md:px-8"
                >
                  Start in 5 minutes
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
              <a href="#how">
                <Button
                  size="lg"
                  variant="outline"
                  className="h-11 rounded-[6px] border-[rgba(25,25,25,0.15)] px-5 text-base font-medium text-[#191919] hover:bg-[#f3efe5] md:h-12 md:px-6"
                >
                  See how it works
                </Button>
              </a>
            </div>

            <div className="mt-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-4">
              <p className="text-sm text-[#8a847b]">Pro — $99/mo</p>
              <p className="text-sm text-[#8a847b]">Solo — $49/mo</p>
            </div>

          </div>
        </div>
      </section>

      {/* Sentinel for mobile sticky CTA IntersectionObserver */}
      <div id="hero-section-end" aria-hidden="true" />

      {/* ── B. Demo ───────────────────────────────────────────────── */}
      <section className="px-6 py-12 md:py-20 bg-[#faf9f5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-8 text-center">
            <h2 className="font-display mb-3 text-2xl font-[450] tracking-tight text-[#191919] md:text-3xl">
              One chat. Multiple Claude Code runs.
            </h2>
            <p className="mx-auto max-w-xl text-sm leading-relaxed text-[#8a847b] md:text-base">
              Ask once. Claude decides what to launch, Concerto starts the sessions, and Claude reports back with progress and results.
            </p>
          </div>
          <div className="reveal mx-auto max-w-3xl">
            <HeroClaudeDemo />
          </div>
        </div>
      </section>

      {/* ── C. Pain block ─────────────────────────────────────────── */}
      <section className="px-6 py-12 md:py-20 bg-[#f3efe5]">
        <div className="mx-auto max-w-3xl">
          <div className="reveal">
            <h2 className="font-display mb-8 text-2xl font-[450] tracking-tight text-[#191919] md:text-3xl">
              Claude Code is powerful. Managing it is the bottleneck.
            </h2>
            <ul className="mb-8 space-y-3">
              {[
                "You copy plans from Claude into Claude Code.",
                "You watch terminals.",
                "You paste logs back into Claude.",
                "You restart stuck runs.",
                "You compare attempts manually.",
                "You lose the overview.",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-[#a09a94]">
                  <span className="mt-0.5 shrink-0">×</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <p className="text-base leading-relaxed text-[#555049]">
              With Concerto, Claude can launch sessions, monitor progress, read logs, compare results, and report back inside Claude.
            </p>
          </div>
        </div>
      </section>

      {/* ── D. Mechanism ──────────────────────────────────────────── */}
      <section id="how" className="px-6 py-12 md:py-20 bg-[#faf9f5]">
        <div className="mx-auto max-w-3xl">
          <div className="reveal mb-10 text-center">
            <h2 className="font-display mb-3 text-2xl font-[450] tracking-tight text-[#191919] md:text-3xl">
              How Concerto works
            </h2>
          </div>

          <div className="reveal space-y-4">
            {[
              { n: "1", text: "You ask Claude what you want built, fixed, reviewed, or deployed." },
              { n: "2", text: "Claude decides which Claude Code sessions are needed." },
              { n: "3", text: "Concerto starts and tracks those sessions." },
              { n: "4", text: "Claude compares progress and reports back in the chat." },
            ].map(({ n, text }) => (
              <div key={n} className="flex items-start gap-5 rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-6 shadow-[0_1px_2px_rgba(25,25,25,0.04)]">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[rgba(204,120,92,0.10)] text-sm font-semibold text-[#cc785c]">
                  {n}
                </span>
                <p className="pt-1 text-sm leading-relaxed text-[#555049]">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── E. Use cases ──────────────────────────────────────────── */}
      <section className="px-6 py-12 md:py-20 bg-[#f3efe5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-10 text-center">
            <h2 className="font-display mb-3 text-2xl font-[450] tracking-tight text-[#191919] md:text-3xl">
              What you can do with Concerto
            </h2>
          </div>

          <div className="reveal grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[
              "Build and deploy a landing page.",
              "Run multiple implementation attempts in parallel.",
              "Debug a failing feature without babysitting the terminal.",
              "Compare different fixes before choosing one.",
              "Audit a project and return a structured report.",
              "Restart or redirect stuck sessions from Claude.",
            ].map((useCase) => (
              <div
                key={useCase}
                className="rounded-lg border border-[rgba(25,25,25,0.08)] bg-white p-5 shadow-[0_1px_2px_rgba(25,25,25,0.04)]"
              >
                <p className="text-sm leading-relaxed text-[#555049]">{useCase}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── F. Pricing ────────────────────────────────────────────── */}
      <section id="pricing" className="px-6 py-12 md:py-24 bg-[#faf9f5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
              Pick your plan.
            </h2>
            <p className="text-[#8a847b]">
              Start with Solo, upgrade to Pro when your work scales up.
            </p>
          </div>

          <div className="reveal mx-auto grid max-w-2xl grid-cols-1 gap-6 md:grid-cols-2">

            {/* Solo */}
            <div className="relative overflow-hidden rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)]">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-lg font-medium text-[#191919]">Solo</span>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-[#8a847b]">
                For individual builders who want controlled parallel Claude Code runs.
              </p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#191919]">$49</span>
                <span className="text-sm text-[#8a847b]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <ul className="space-y-3.5">
                {[
                  "Claude can launch and monitor up to 2 Claude Code sessions in parallel",
                  "Email support included",
                  "Cancel anytime",
                ].map((feature) => (
                  <CheckItem key={feature}>{feature}</CheckItem>
                ))}
              </ul>
              <p className="mt-4 text-xs text-[#8a847b]">Works with Claude Pro. Recommended with Claude Max for serious parallel work.</p>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <form action="/api/checkout?plan=solo" method="POST">
                <Button type="submit" variant="outline" className="h-12 w-full rounded-[6px] border-[rgba(25,25,25,0.15)] text-base font-medium text-[#191919] hover:bg-[#f3efe5]">
                  Start with Solo
                </Button>
              </form>
              <p className="mt-3 text-center text-xs text-[#8a847b]">Secure payment via Stripe · Cancel anytime</p>
            </div>

            {/* Pro — FEATURED */}
            <div className="relative overflow-hidden rounded-xl border border-[rgba(204,120,92,0.45)] bg-white p-8 shadow-[0_2px_12px_rgba(204,120,92,0.08)] md:-mt-3 md:mb-[-12px]">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-lg font-medium text-[#191919]">Pro</span>
                <span className="flex items-center gap-1 rounded bg-[rgba(204,120,92,0.10)] px-2.5 py-1 text-xs font-medium text-[#cc785c]">
                  <Star className="h-3 w-3 fill-current" /> Most popular
                </span>
              </div>
              <p className="mt-1 text-sm leading-relaxed text-[#8a847b]">
                For serious Claude Code users who want higher parallelism and less manual session management.
              </p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#191919]">$99</span>
                <span className="text-sm text-[#8a847b]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <ul className="space-y-3.5">
                {[
                  "Claude can launch and monitor up to 6 Claude Code sessions in parallel",
                  "Email support included",
                  "Cancel anytime",
                ].map((feature) => (
                  <CheckItem key={feature}>{feature}</CheckItem>
                ))}
              </ul>
              <p className="mt-4 text-xs text-[#8a847b]">Works with Claude Pro. Recommended with Claude Max for serious parallel work.</p>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <form action="/api/checkout?plan=pro" method="POST">
                <Button type="submit" className="h-12 w-full rounded-[6px] bg-[#cc785c] text-base font-medium text-[#faf9f5] hover:bg-[#b86747]">
                  Start with Pro
                </Button>
              </form>
              <p className="mt-3 text-center text-xs text-[#8a847b]">Secure payment via Stripe · Cancel anytime</p>
            </div>

          </div>

          <p className="reveal mt-8 text-center text-sm font-medium text-[#555049]">
            We recommend <strong>Claude Max</strong> — Claude Pro hits token limits fast when Claude is running multiple sessions.
          </p>

          <div className="reveal mx-auto mt-4 max-w-2xl rounded-lg border border-[rgba(25,25,25,0.08)] bg-white px-6 py-4 text-center">
            <p className="text-sm text-[#8a847b]">
              Real human email support in every plan. Write to support@concerto.run — reply within 24 hours.
            </p>
          </div>

        </div>
      </section>

      {/* ── G. FAQ ───────────────────────────────────────────────── */}
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
                q: "What is Concerto?",
                a: "Concerto gives Claude the tools to orchestrate Claude Code sessions. You describe what to build, Claude decides which sessions to launch, starts them, monitors progress, reads logs, and reports back with a summary of what was done — all from your normal Claude chat.",
              },
              {
                q: "Do I need to know how to code?",
                a: "No. Concerto is most useful for people who have a project in mind but don't want to set up a development environment. You describe what you want, Claude builds it.",
              },
              {
                q: "Should I use Claude Pro or Max with Concerto?",
                a: "We strongly recommend Max. Claude Pro's token limits get exhausted quickly with the kind of work Concerto enables — launching and monitoring multiple sessions, reading logs, comparing outputs. Max ($200/month) gives you 20× the usage. Pro works for light experimentation but you'll hit limits fast.",
              },
              {
                q: "Is my workspace dedicated to me?",
                a: "Yes. Every Concerto subscription gives Claude its own isolated workspace, separate from other customers. Your code, files, and history stay yours.",
              },
              {
                q: "What can I run on it?",
                a: "Anything Claude Code can do: build websites, scripts, prototypes, automations, data processing, document generation, file conversions. Long tasks run for hours. Parallel sessions run several things at once.",
              },
              {
                q: "Can I cancel anytime?",
                a: "Yes, instantly. Cancel from your dashboard, your machine is decommissioned at the end of the billing period. No questions, no contracts.",
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

      {/* ── Footer ───────────────────────────────────────────────── */}
      <footer className="border-t border-[rgba(250,249,245,0.07)] bg-[#2a2925] px-6 pb-28 pt-10 md:pb-10">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2.5">
              <LogoMark size={18} />
              <span className="text-sm font-medium text-[rgba(250,249,245,0.55)]">Concerto</span>
            </div>
            <p className="text-sm text-[rgba(250,249,245,0.30)]">&copy; {new Date().getFullYear()} Concerto. All rights reserved.</p>
            <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5">
              {[
                { href: "/legal/terms", label: "Terms" },
                { href: "/help",        label: "Help" },
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
          <p className="mt-6 text-center text-xs text-[rgba(250,249,245,0.25)]">
            Built by an operator in Almaty.{" "}
            <a href="https://www.anthropic.com/legal/aup" target="_blank" rel="noopener noreferrer" className="hover:text-[rgba(250,249,245,0.50)] transition-colors">
              Subject to Anthropic&apos;s Acceptable Use Policy.
            </a>
          </p>
        </div>
      </footer>

      {/* ── Mobile sticky CTA (hidden on md+) ────────────────────── */}
      <MobileStickyCTA />
    </div>
  )
}
