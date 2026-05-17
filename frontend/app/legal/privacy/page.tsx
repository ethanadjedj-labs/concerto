import type { Metadata } from "next"
import { getLegalContent } from "@/lib/legal"

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Concerto Privacy Policy — how we collect, use, and protect your data.",
  openGraph: { title: "Privacy Policy — Concerto", url: "https://concerto.run/legal/privacy" },
}

export default function PrivacyPage() {
  const html = getLegalContent("PRIVACY.md")
  return (
    <article
      className="prose prose-invert prose-sm sm:prose-base max-w-none
        prose-headings:font-semibold prose-headings:text-white
        prose-h1:text-2xl prose-h1:mb-2
        prose-h2:text-lg prose-h2:mt-8 prose-h2:mb-3 prose-h2:border-b prose-h2:border-white/10 prose-h2:pb-2
        prose-p:text-white/70 prose-p:leading-relaxed
        prose-a:text-violet-400 prose-a:no-underline hover:prose-a:underline
        prose-strong:text-white
        prose-em:text-white/50
        prose-table:text-sm prose-td:text-white/60 prose-th:text-white/80 prose-th:font-medium
        prose-li:text-white/70
        prose-hr:border-white/10
        prose-code:text-violet-300 prose-code:bg-white/5 prose-code:px-1 prose-code:rounded"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
