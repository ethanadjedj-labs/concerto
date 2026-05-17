import Link from "next/link"

export default function LegalFooter() {
  return (
    <footer className="border-t border-white/5 mt-24">
      <div className="mx-auto max-w-6xl px-6 py-8 flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-8">
        <p className="text-xs text-white/30 sm:mr-auto">
          © {new Date().getFullYear()} Maestro. All rights reserved.
        </p>
        <nav className="flex flex-wrap gap-x-6 gap-y-2">
          <Link href="/legal/terms" className="text-xs text-white/30 hover:text-white/60 transition-colors">
            Terms of Service
          </Link>
          <Link href="/legal/privacy" className="text-xs text-white/30 hover:text-white/60 transition-colors">
            Privacy Policy
          </Link>
          <Link href="/legal/refund" className="text-xs text-white/30 hover:text-white/60 transition-colors">
            Refund Policy
          </Link>
          <Link href="/legal/aup" className="text-xs text-white/30 hover:text-white/60 transition-colors">
            Acceptable Use
          </Link>
        </nav>
      </div>
    </footer>
  )
}
