import type { ReactNode } from "react"
import Link from "next/link"
import { HeroClaudeDemo } from "@/components/HeroClaudeDemo"
import { MobileStickyCTA } from "@/components/MobileStickyCTA"
import { SessionCardsDiagram } from "@/components/SessionCardsDiagram"
import { WhatActuallyHappens } from "@/components/WhatActuallyHappens"
import { ConcreteExamples } from "@/components/ConcreteExamples"
import { BeforeAfter } from "@/components/BeforeAfter"
import { Tagline } from "@/components/Tagline"
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
  Check,
  ArrowRight,
  Star,
} from "lucide-react"

/* ─── Logo mark — bubble+baton, works on cream background ───── */

function LogoMark({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 128 128" fill="none" aria-hidden="true">
      <defs>
        <clipPath id="nav-bubble-clip">
          <path d="M 32,8 H 96 a 18,18 0 0 1 18,18 V 90 a 18,18 0 0 1 -18,18 H 32 L 7,115 L 14,90 V 26 a 18,18 0 0 1 18,-18 Z"/>
        </clipPath>
      </defs>
      <g clipPath="url(#nav-bubble-clip)">
        <line x1="26" y1="96" x2="104" y2="18" stroke="#cc785c" strokeWidth={12} strokeLinecap="butt"/>
        <circle cx="104" cy="18" r="9" fill="#cc785c"/>
      </g>
      <path d="M 32,8 H 96 a 18,18 0 0 1 18,18 V 90 a 18,18 0 0 1 -18,18 H 32 L 7,115 L 14,90 V 26 a 18,18 0 0 1 18,-18 Z"
        fill="none" stroke="#1f1e1c" strokeWidth={4} strokeLinejoin="round"/>
    </svg>
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
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-3">
            <LogoMark size={36} />
            <span className="text-[26px] font-medium leading-none tracking-tight text-[#191919]">Concerto</span>
          </div>

          <div className="flex items-center gap-5">
            <Link href="#how" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              How it works
            </Link>
            <Link href="#pricing" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              Pricing
            </Link>
            <Link href="#faq" className="hidden text-sm text-[#8a847b] transition-colors hover:text-[#191919] md:block">
              FAQ
            </Link>
            <form action="/api/checkout?plan=solo" method="POST">
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
      <section id="hero" className="pb-16 pt-36 md:pb-20 md:pt-40">
        <div className="mx-auto max-w-6xl px-6">

          {/* Desktop: two-column | Mobile: stacked */}
          <div className="flex flex-col gap-12 lg:flex-row lg:items-center lg:gap-16">

            {/* Left column */}
            <div className="animate-fade-up flex-shrink-0 lg:w-[44%] lg:pr-8">

              {/* Editorial peach line */}
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
                Talk to Claude.{" "}
                <span className="text-[#cc785c]">Claude runs Claude Code.</span>
              </h1>

              <p className="mb-6 text-lg leading-relaxed text-[#555049]">
                Concerto gives Claude the tools to orchestrate Claude Code. Claude decides which sessions to launch, starts them on your machine, monitors progress, reads logs, compares results, and reports back — you stay in Claude chat the whole time.
              </p>

              {/* Hero bullets */}
              <ul className="mb-10 space-y-2.5">
                {[
                  "Claude decides which sessions to launch",
                  "Claude picks the right model per session to save your tokens",
                  "Claude starts and monitors Claude Code runs",
                  "Claude reads logs and detects stuck sessions",
                  "Claude compares outputs from parallel attempts",
                  "You stay in Claude chat, not the terminal",
                ].map((bullet) => (
                  <li key={bullet} className="flex items-start gap-3 text-base leading-relaxed text-[#555049]">
                    <span className="mt-1 shrink-0 text-[#cc785c]" aria-hidden="true">•</span>
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <form action="/api/checkout?plan=solo" method="POST">
                  <Button
                    size="lg"
                    className="h-12 rounded-[6px] bg-[#cc785c] px-8 text-base font-medium text-[#faf9f5] hover:bg-[#b86747]"
                  >
                    Start with Solo — $49/month
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </form>
                <form action="/api/checkout?plan=pro" method="POST">
                  <Button
                    size="lg"
                    variant="outline"
                    className="h-12 rounded-[6px] border-[rgba(25,25,25,0.15)] px-6 text-base font-medium text-[#191919] hover:bg-[#f3efe5]"
                  >
                    Start with Pro — $99/month
                  </Button>
                </form>
              </div>
              <p className="mt-2 text-sm text-[#8a847b]">
                Works with your Claude Pro or Max subscription.
              </p>
            </div>

            {/* Right column — hidden on mobile */}
            <div className="animate-fade-up delay-200 hidden lg:block lg:flex-1 lg:min-w-0">
              <HeroClaudeDemo />
            </div>
          </div>
        </div>
      </section>

      {/* Sentinel for mobile CTA IntersectionObserver */}
      <div id="hero-section-end" aria-hidden="true" />

      {/* ── Session cards diagram ────────────────────────────────── */}
      <SessionCardsDiagram />

      {/* ── What happens after you ask Claude ───────────────────── */}
      <WhatActuallyHappens />

      {/* ── Concrete examples ───────────────────────────────────── */}
      <ConcreteExamples />

      {/* ── Before / After ──────────────────────────────────────── */}
      <BeforeAfter />

      {/* ── Pricing ─────────────────────────────────────────────── */}
      <section id="pricing" className="px-6 py-24 bg-[#faf9f5]">
        <div className="mx-auto max-w-6xl">
          <div className="reveal mb-14 text-center">
            <h2 className="font-display mb-3 text-3xl font-[450] tracking-tight text-[#191919] md:text-4xl">
              Pick your plan.
            </h2>
            <p className="text-[#8a847b]">
              Both plans include a dedicated remote machine. Start with Solo, upgrade when you need more sessions.
            </p>
          </div>

          <div className="reveal mx-auto grid max-w-2xl grid-cols-1 gap-6 md:grid-cols-2">

            {/* Solo */}
            <div className="relative overflow-hidden rounded-xl border border-[rgba(25,25,25,0.08)] bg-white p-8 shadow-[0_1px_2px_rgba(25,25,25,0.04)]">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-lg font-medium text-[#191919]">Solo</span>
              </div>
              <p className="mb-1 text-sm text-[#8a847b]">Dedicated remote machine, 4GB</p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#191919]">$49</span>
                <span className="text-sm text-[#8a847b]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <ul className="space-y-3.5">
                {[
                  "Dedicated remote machine, 4GB",
                  "Up to 2 parallel sessions",
                  "Email support included",
                  "Cancel anytime",
                ].map((feature) => (
                  <CheckItem key={feature}>{feature}</CheckItem>
                ))}
              </ul>
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
              <p className="mb-1 text-sm text-[#8a847b]">Dedicated remote machine, 8GB</p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#191919]">$99</span>
                <span className="text-sm text-[#8a847b]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(25,25,25,0.08)]" />
              <ul className="space-y-3.5">
                {[
                  "Dedicated remote machine, 8GB",
                  "Up to 6–8 parallel sessions",
                  "Email support included",
                  "Cancel anytime",
                ].map((feature) => (
                  <CheckItem key={feature}>{feature}</CheckItem>
                ))}
              </ul>
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
              Real human email support in every plan. <span className="text-[#555049]">No community forums.</span> Write to support@concerto.run — reply within 24 hours.
            </p>
          </div>

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
                q: "What is Concerto?",
                a: "Concerto lets Claude operate Claude Code on a remote machine while you stay in the normal Claude chat. You describe what to build, Claude decides which sessions to launch, starts them, monitors progress, reads logs, and reports back with a summary of what was done.",
              },
              {
                q: "Do I need to know how to code?",
                a: "No. Concerto is most useful for people who have a project in mind but don't want to set up a development environment. You describe what you want, Claude builds it.",
              },
              {
                q: "Should I use Claude Pro or Max with Concerto?",
                a: "We strongly recommend Max. Claude Pro's token limits get exhausted quickly with the kind of work Concerto enables — launching and monitoring multiple sessions, reading logs, comparing outputs. Max ($200/month) gives you 5× the usage. Pro works for light experimentation but you'll hit limits fast.",
              },
              {
                q: "Is my machine dedicated to me?",
                a: "Yes. Every Concerto subscription is a dedicated remote machine isolated from other customers. Your code, files, and history stay yours.",
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

      {/* ── Final tagline band ───────────────────────────────────── */}
      <Tagline />

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
      <MobileStickyCTA />
    </div>
  )
}
