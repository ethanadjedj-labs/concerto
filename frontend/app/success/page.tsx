import Link from "next/link"
import { Button } from "@/components/ui/button"
import { CheckCircle, Mail, ArrowRight } from "lucide-react"

export default function SuccessPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a0b] px-6 py-16 text-white">
      <div className="w-full max-w-md">

        <div className="relative overflow-hidden rounded-2xl border border-green-500/20 bg-white/[0.025]">
          {/* Top highlight */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-green-500/40 to-transparent" />
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_40%_at_50%_0%,rgba(34,197,94,0.06)_0%,transparent_70%)]" />

          <div className="relative p-8 text-center">
            {/* Icon */}
            <div className="mb-7 flex justify-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-500/12 ring-1 ring-green-500/20">
                <CheckCircle className="h-8 w-8 text-green-400" />
              </div>
            </div>

            <h1 className="mb-2 text-2xl font-bold tracking-tight text-white">Payment confirmed</h1>
            <p className="text-[14px] text-white/40">Your Concerto is ready to be set up.</p>

            {/* Email notice */}
            <div className="mt-6 rounded-xl border border-white/[0.07] bg-white/[0.03] p-4 text-left">
              <div className="flex items-start gap-3">
                <Mail className="mt-0.5 h-4.5 w-4.5 shrink-0 text-white/40" />
                <div>
                  <p className="text-[14px] font-medium text-white">Check your email</p>
                  <p className="mt-1 text-[13px] leading-relaxed text-white/40">
                    Your setup link has been sent. It contains your unique token to provision your Concerto droplet.
                  </p>
                </div>
              </div>
            </div>

            {/* Steps */}
            <div className="mt-6 text-left">
              <p className="mb-3 text-[11px] font-medium uppercase tracking-widest text-white/30">
                What happens next
              </p>
              <ol className="space-y-2.5">
                {[
                  "Open the setup link in your email",
                  "Enter your DigitalOcean API key",
                  "Concerto provisions your droplet (~3 min)",
                  "Connect to claude.ai in 3 steps",
                ].map((step, i) => (
                  <li key={i} className="flex items-center gap-3 text-[13px]">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white/[0.07] text-[11px] text-white/40">
                      {i + 1}
                    </span>
                    <span className="text-white/55">{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Support note */}
            <div className="mt-6 rounded-lg border border-white/[0.05] bg-white/[0.02] px-4 py-3 text-[12px] text-white/28">
              Need help?{" "}
              <a href="mailto:support@concerto.run" className="text-violet-400 hover:text-violet-300">
                support@concerto.run
              </a>{" "}
              or join Discord (link in your email).
            </div>

            <Button
              asChild
              variant="outline"
              className="mt-5 w-full border-white/[0.08] text-white/50 hover:bg-white/[0.04] hover:text-white"
            >
              <Link href="/">
                Back to home
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
