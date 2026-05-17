import Link from "next/link"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: {
    template: "%s — Concerto Legal",
    default: "Legal — Concerto",
  },
}

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      <nav className="border-b border-white/5 bg-[#0a0a0a]/80">
        <div className="mx-auto max-w-3xl px-6 py-4 flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 text-sm font-semibold text-white hover:opacity-80 transition-opacity">
            <div className="h-5 w-5 rounded bg-gradient-to-br from-violet-500 to-indigo-600" />
            Concerto
          </Link>
          <span className="text-white/20">/</span>
          <span className="text-sm text-white/40">Legal</span>
        </div>
      </nav>

      <main className="mx-auto max-w-3xl px-6 py-12">{children}</main>

      <footer className="border-t border-white/5 mt-16">
        <div className="mx-auto max-w-3xl px-6 py-6 flex flex-wrap gap-x-6 gap-y-2 text-xs text-white/30">
          <Link href="/legal/terms" className="hover:text-white/60 transition-colors">Terms of Service</Link>
          <a href="https://www.anthropic.com/legal/aup" target="_blank" rel="noopener noreferrer" className="hover:text-white/60 transition-colors">Acceptable Use (Anthropic)</a>
          <span className="ml-auto">© {new Date().getFullYear()} Concerto</span>
        </div>
      </footer>
    </div>
  )
}
