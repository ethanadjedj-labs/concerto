import Link from "next/link"
import LegalFooter from "@/components/LegalFooter"
import { HeroDemo } from "@/components/HeroDemo"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Zap,
  Cloud,
  DollarSign,
  Check,
  Terminal,
  Globe,
  Shield,
} from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-violet-500 to-indigo-600" />
            <span className="font-semibold text-white tracking-tight">Maestro</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="#features" className="text-sm text-white/50 hover:text-white transition-colors hidden md:block">
              Features
            </Link>
            <Link href="#pricing" className="text-sm text-white/50 hover:text-white transition-colors hidden md:block">
              Pricing
            </Link>
            <Link href="#faq" className="text-sm text-white/50 hover:text-white transition-colors hidden md:block">
              FAQ
            </Link>
            <form action="/api/checkout" method="POST">
              <Button size="sm" className="bg-white text-black hover:bg-white/90 font-medium">
                Get started →
              </Button>
            </form>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-violet-600/10 rounded-full blur-[120px]" />
          <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[400px] h-[300px] bg-indigo-600/10 rounded-full blur-[80px]" />
        </div>

        <div className="relative mx-auto max-w-4xl text-center">
          <Badge
            variant="outline"
            className="mb-6 border-violet-500/30 bg-violet-500/10 text-violet-300 px-4 py-1.5 text-xs font-medium"
          >
            Now available · Claude Code remote workshop
          </Badge>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] mb-6">
            Pilot{" "}
            <span className="bg-gradient-to-r from-violet-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
              Claude Code
            </span>{" "}
            workers from your browser
          </h1>

          <p className="text-xl md:text-2xl text-white/50 mb-10 max-w-2xl mx-auto leading-relaxed">
            Never open a terminal. Ship code with autonomous AI agents running
            24/7 in your own cloud.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <form action="/api/checkout" method="POST">
              <Button
                size="lg"
                className="bg-white text-black hover:bg-white/90 font-semibold text-base px-8 h-12 rounded-lg"
              >
                Get Maestro for $99 →
              </Button>
            </form>
            <span className="text-white/30 text-sm">One-time payment · No subscription</span>
          </div>

          {/* Interactive hero demo */}
          <div className="mt-20 px-2">
            <HeroDemo />
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything you need to run agents at scale
            </h2>
            <p className="text-white/40 text-lg max-w-xl mx-auto">
              Maestro handles provisioning, authentication, and monitoring — so you
              can focus on shipping.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-violet-500/20 flex items-center justify-center mb-4">
                  <Zap className="h-5 w-5 text-violet-400" />
                </div>
                <CardTitle className="text-white text-lg">Parallel agents, 24/7</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Spawn multiple Claude Code workers simultaneously. Run long-running
                  tasks overnight without babysitting a terminal. Your agents work while
                  you sleep.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-blue-500/20 flex items-center justify-center mb-4">
                  <Cloud className="h-5 w-5 text-blue-400" />
                </div>
                <CardTitle className="text-white text-lg">Your cloud, your billing</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Maestro provisions a DigitalOcean droplet directly in your account.
                  You own the infrastructure. No markup, no vendor lock-in — just a
                  $24/mo VPS billed to your card.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-green-500/20 flex items-center justify-center mb-4">
                  <DollarSign className="h-5 w-5 text-green-400" />
                </div>
                <CardTitle className="text-white text-lg">No token-by-token cost</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Maestro uses your existing Claude Max plan. No per-token API fees,
                  no surprise bills. Run as many tasks as you want — the model cost is
                  already covered.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Secondary features row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-orange-500/20 flex items-center justify-center mb-4">
                  <Terminal className="h-5 w-5 text-orange-400" />
                </div>
                <CardTitle className="text-white text-lg">Browser terminal</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Full-featured web terminal embedded in your dashboard. SSH into
                  your droplet from any device — no client software required.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-pink-500/20 flex items-center justify-center mb-4">
                  <Globe className="h-5 w-5 text-pink-400" />
                </div>
                <CardTitle className="text-white text-lg">MCP integration</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Connect to claude.ai in 3 copy-paste steps. Your remote agents
                  appear as MCP tools in the Claude interface — send tasks from
                  anywhere.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/8 hover:bg-white/[0.05] transition-colors">
              <CardHeader>
                <div className="h-10 w-10 rounded-lg bg-cyan-500/20 flex items-center justify-center mb-4">
                  <Shield className="h-5 w-5 text-cyan-400" />
                </div>
                <CardTitle className="text-white text-lg">Isolated environment</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-white/40 text-sm leading-relaxed">
                  Each customer gets a dedicated droplet. Your code, keys, and
                  agent sessions are completely isolated from other users.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 px-6">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Simple, one-time pricing
            </h2>
            <p className="text-white/40 text-lg">
              Pay once, own forever. No subscriptions, no surprises.
            </p>
          </div>

          <div className="max-w-md mx-auto">
            <Card className="bg-white/[0.04] border-violet-500/30 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-violet-600/5 to-indigo-600/5 pointer-events-none" />
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between mb-2">
                  <CardTitle className="text-white text-xl">Maestro</CardTitle>
                  <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30">
                    One-time
                  </Badge>
                </div>
                <div className="flex items-baseline gap-2 mt-4">
                  <span className="text-5xl font-bold text-white">$99</span>
                  <span className="text-white/30 text-sm">one-time</span>
                </div>
                <p className="text-white/40 text-sm mt-2">
                  Plus ~$24/mo DigitalOcean droplet cost (billed directly to your DO account)
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <Separator className="bg-white/10" />
                <ul className="space-y-3">
                  {[
                    "Auto-provisioned DigitalOcean droplet",
                    "Claude Code pre-installed & configured",
                    "Browser-based terminal (ttyd)",
                    "MCP connector for claude.ai",
                    "Parallel agent support",
                    "Dedicated Discord support channel",
                    "Lifetime access to updates",
                  ].map((feature) => (
                    <li key={feature} className="flex items-start gap-3 text-sm">
                      <Check className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                      <span className="text-white/70">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Separator className="bg-white/10" />
                <form action="/api/checkout" method="POST">
                  <Button
                    type="submit"
                    className="w-full bg-white text-black hover:bg-white/90 font-semibold h-12 text-base rounded-lg"
                  >
                    Get Maestro for $99 →
                  </Button>
                </form>
                <p className="text-center text-white/25 text-xs">
                  Secure payment via Stripe · 30-day refund policy
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-24 px-6">
        <div className="mx-auto max-w-2xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Frequently asked questions
            </h2>
          </div>

          <Accordion type="single" collapsible className="space-y-1">
            <AccordionItem value="q1" className="border-white/10">
              <AccordionTrigger className="text-white text-left hover:text-white hover:no-underline py-5">
                What do I need to get started?
              </AccordionTrigger>
              <AccordionContent className="text-white/50 leading-relaxed">
                You need a Claude Max subscription (for unlimited Claude Code usage),
                a DigitalOcean account (free to create, you only pay for the droplet),
                and a credit card for the $99 Maestro fee. That&apos;s it — no server
                knowledge required.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="q2" className="border-white/10">
              <AccordionTrigger className="text-white text-left hover:text-white hover:no-underline py-5">
                How is this different from running Claude Code locally?
              </AccordionTrigger>
              <AccordionContent className="text-white/50 leading-relaxed">
                Local Claude Code ties up your machine and stops when you close the
                lid. Maestro runs on a dedicated cloud VPS 24/7 — agents keep working
                while your laptop is off. You control everything from a browser tab
                with no SSH client needed.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="q3" className="border-white/10">
              <AccordionTrigger className="text-white text-left hover:text-white hover:no-underline py-5">
                Who pays for the DigitalOcean droplet?
              </AccordionTrigger>
              <AccordionContent className="text-white/50 leading-relaxed">
                You do, directly. Maestro provisions the droplet into your DigitalOcean
                account using your API key. The $24/mo (or chosen size) is charged by
                DigitalOcean to your card — we never see or mark up your infrastructure
                costs.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="q4" className="border-white/10">
              <AccordionTrigger className="text-white text-left hover:text-white hover:no-underline py-5">
                What happens to my droplet if I cancel?
              </AccordionTrigger>
              <AccordionContent className="text-white/50 leading-relaxed">
                Your droplet is in your DigitalOcean account — you control it fully.
                You can keep it running, resize it, or destroy it anytime through the
                DigitalOcean dashboard. Maestro never has persistent access to your
                infrastructure after initial provisioning.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="q5" className="border-white/10">
              <AccordionTrigger className="text-white text-left hover:text-white hover:no-underline py-5">
                Can I run multiple agents in parallel?
              </AccordionTrigger>
              <AccordionContent className="text-white/50 leading-relaxed">
                Yes. The default 2 vCPU / 4 GB droplet handles 2–4 parallel Claude Code
                sessions comfortably. For heavier workloads, choose a larger size during
                setup (4 vCPU / 8 GB available). Claude Max plan rate limits apply
                regardless of hardware.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </section>

      {/* CTA Strip */}
      <section className="py-24 px-6">
        <div className="mx-auto max-w-3xl text-center">
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-violet-600/10 via-indigo-600/5 to-transparent p-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to run agents without a terminal?
            </h2>
            <p className="text-white/40 text-lg mb-8">
              Get set up in under 10 minutes. Your first agent runs before you
              finish your coffee.
            </p>
            <form action="/api/checkout" method="POST">
              <Button
                type="submit"
                size="lg"
                className="bg-white text-black hover:bg-white/90 font-semibold text-base px-10 h-12 rounded-lg"
              >
                Get started for $99 →
              </Button>
            </form>
          </div>
        </div>
      </section>

      <LegalFooter />
    </div>
  )
}
