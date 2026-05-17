import type { Metadata } from "next"
import { LogoConceptsClient } from "./client"

export const metadata: Metadata = {
  title: "Logo Concepts v3 — Concerto",
  description: "Internal logo review — 4 finished marks with construction grids and scale studies.",
  robots: {
    index: false,
    follow: false,
    googleBot: { index: false, follow: false },
  },
}

export default function LogoConceptsPage() {
  return <LogoConceptsClient />
}
