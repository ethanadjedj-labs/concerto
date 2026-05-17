import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, Mail } from "lucide-react"

export default function SuccessPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center px-6">
      <div className="max-w-md w-full">
        <Card className="bg-white/[0.04] border-green-500/20 text-center overflow-hidden relative">
          <div className="absolute inset-0 bg-gradient-to-b from-green-600/5 to-transparent pointer-events-none" />
          <CardHeader className="pb-4 relative">
            <div className="flex justify-center mb-6">
              <div className="h-16 w-16 rounded-full bg-green-500/15 flex items-center justify-center">
                <CheckCircle className="h-8 w-8 text-green-400" />
              </div>
            </div>
            <CardTitle className="text-white text-2xl">Payment confirmed</CardTitle>
          </CardHeader>
          <CardContent className="relative space-y-6">
            <div className="rounded-lg border border-white/8 bg-white/[0.03] p-5">
              <div className="flex items-start gap-3 text-left">
                <Mail className="h-5 w-5 text-white/40 mt-0.5 shrink-0" />
                <div>
                  <p className="text-white font-medium text-sm mb-1">Check your email</p>
                  <p className="text-white/40 text-sm leading-relaxed">
                    Your dashboard setup link has been sent. It contains your unique
                    token to provision your Maestro droplet.
                  </p>
                </div>
              </div>
            </div>

            <div className="text-left space-y-3">
              <p className="text-white/40 text-sm font-medium uppercase tracking-wider text-xs">
                What happens next
              </p>
              <ol className="space-y-2">
                {[
                  "Open the setup link in your email",
                  "Enter your DigitalOcean API key",
                  "Maestro provisions your droplet (~3 min)",
                  "Connect to claude.ai in 3 steps",
                ].map((step, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm">
                    <span className="h-5 w-5 rounded-full bg-white/10 flex items-center justify-center text-xs text-white/40 shrink-0">
                      {i + 1}
                    </span>
                    <span className="text-white/60">{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="rounded-lg border border-white/5 bg-white/[0.02] p-4 text-sm text-white/30">
              Need help?{" "}
              <a
                href="mailto:support@maestro.run"
                className="text-violet-400 hover:text-violet-300 transition-colors"
              >
                support@maestro.run
              </a>{" "}
              or join Discord support (link in your email).
            </div>

            <Button asChild variant="outline" className="w-full border-white/10 text-white/60 hover:text-white hover:bg-white/5">
              <Link href="/">← Back to home</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
