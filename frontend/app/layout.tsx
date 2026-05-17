import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Maestro — Remote Workshop for Claude Code Agents",
  description:
    "Pilot Claude Code workers from your browser. Never open a terminal. Parallel agents 24/7, your cloud, your billing.",
  openGraph: {
    title: "Maestro — Remote Workshop for Claude Code Agents",
    description:
      "Pilot Claude Code workers from your browser. Never open a terminal.",
    type: "website",
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
