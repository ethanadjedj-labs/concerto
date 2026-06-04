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
    <div className="min-h-screen" style={{ backgroundColor: "#faf9f5", color: "#191919" }}>
      <nav style={{ borderBottom: "1px solid rgba(25,25,25,0.07)", backgroundColor: "rgba(250,249,245,0.92)", backdropFilter: "blur(8px)" }}>
        <div className="mx-auto max-w-3xl px-6 py-4 flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 transition-opacity hover:opacity-70" aria-label="Concerto home">
            <img src="/brand/logo-mark.png?v=3" alt="" width={22} height={22} style={{ display: "block" }} />
            <span className="text-[15px] font-medium" style={{ color: "#191919" }}>Concerto</span>
          </Link>
          <span style={{ color: "rgba(25,25,25,0.18)" }}>/</span>
          <span className="text-sm" style={{ color: "#8a847b" }}>Legal</span>
        </div>
      </nav>

      <main className="mx-auto max-w-3xl px-6 py-12">{children}</main>

      <footer style={{ borderTop: "1px solid rgba(25,25,25,0.07)", marginTop: "4rem" }}>
        <div className="mx-auto max-w-3xl px-6 py-6 flex flex-wrap gap-x-6 gap-y-2 text-xs" style={{ color: "#8a847b" }}>
          <Link href="/legal/terms" className="transition-colors hover:opacity-70">Terms of Service</Link>
          <Link href="/legal/privacy" className="transition-colors hover:opacity-70">Privacy Policy</Link>
          <Link href="/legal/refund" className="transition-colors hover:opacity-70">Refund Policy</Link>
          <Link href="/legal/aup" className="transition-colors hover:opacity-70">Acceptable Use</Link>
          <span className="ml-auto">&copy; {new Date().getFullYear()} Concerto</span>
        </div>
      </footer>
    </div>
  )
}
