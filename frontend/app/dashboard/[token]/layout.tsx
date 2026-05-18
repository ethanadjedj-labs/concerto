import type { Metadata } from "next"
import type { ReactNode } from "react"

export const metadata: Metadata = {
  title: "Concerto — Setup",
  other: {
    "format-detection": "telephone=no,address=no,email=no,date=no",
    "apple-mobile-web-app-capable": "yes",
  },
}

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
