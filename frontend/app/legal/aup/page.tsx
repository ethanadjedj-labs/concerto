import type { Metadata } from "next"
import { getLegalContent } from "@/lib/legal"

export const metadata: Metadata = {
  title: "Acceptable Use Policy",
  description: "Concerto Acceptable Use Policy — what you may and may not do with the service.",
  openGraph: { title: "Acceptable Use Policy — Concerto", url: "https://concerto.run/legal/aup" },
}

export default function AupPage() {
  const html = getLegalContent("AUP.md")
  return (
    <article
      className="prose prose-sm sm:prose-base max-w-none
        prose-headings:font-display prose-headings:font-medium
        prose-h1:text-2xl prose-h1:mb-2
        prose-h2:text-lg prose-h2:mt-8 prose-h2:mb-3 prose-h2:border-b prose-h2:pb-2
        prose-p:leading-relaxed
        prose-a:no-underline hover:prose-a:underline
        prose-code:px-1 prose-code:rounded prose-code:text-sm
        prose-table:text-sm prose-th:font-medium"
      style={{
        "--tw-prose-body": "#555049",
        "--tw-prose-headings": "#191919",
        "--tw-prose-lead": "#555049",
        "--tw-prose-links": "#cc785c",
        "--tw-prose-bold": "#191919",
        "--tw-prose-counters": "#8a847b",
        "--tw-prose-bullets": "#c5bfb7",
        "--tw-prose-hr": "rgba(25,25,25,0.08)",
        "--tw-prose-quotes": "#555049",
        "--tw-prose-quote-borders": "#cc785c",
        "--tw-prose-captions": "#8a847b",
        "--tw-prose-code": "#191919",
        "--tw-prose-pre-code": "#191919",
        "--tw-prose-pre-bg": "#f3efe5",
        "--tw-prose-th-borders": "rgba(25,25,25,0.1)",
        "--tw-prose-td-borders": "rgba(25,25,25,0.07)",
      } as React.CSSProperties}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
