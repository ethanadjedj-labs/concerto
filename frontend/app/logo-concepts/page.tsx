import type { Metadata } from "next"
import { LogoConceptsClient } from "./client"

export const metadata: Metadata = {
  title: "Logo Concepts — Concerto",
  description: "Internal logo review page — 5 concepts replacing the orbital mark.",
  robots: {
    index: false,
    follow: false,
    googleBot: { index: false, follow: false },
  },
}

export default function LogoConceptsPage() {
  return <LogoConceptsClient />
}
