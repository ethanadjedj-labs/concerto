import type { Metadata } from "next"
import { Inter, JetBrains_Mono } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
  preload: true,
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  weight: ["400", "500"],
})

export const metadata: Metadata = {
  title: "Concerto — Remote Workshop for Claude Code Agents",
  description:
    "Pilot Claude Code workers from your browser. Never open a terminal. Parallel AI agents running 24/7 in your own cloud — one-time $99.",
  metadataBase: new URL("https://concerto.run"),
  openGraph: {
    title: "Concerto — Remote Workshop for Claude Code Agents",
    description:
      "Pilot Claude Code workers from your browser. Never open a terminal. Parallel agents 24/7, your cloud, your billing.",
    type: "website",
    url: "https://concerto.run",
    siteName: "Concerto",
  },
  twitter: {
    card: "summary_large_image",
    title: "Concerto — Remote Workshop for Claude Code Agents",
    description: "Pilot Claude Code workers from your browser. One-time $99.",
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <head>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%237c3aed'/><circle cx='16' cy='16' r='6' fill='none' stroke='white' stroke-width='1.5'/><circle cx='16' cy='16' r='2.5' fill='white'/></svg>" />
      </head>
      <body className={`${inter.className} antialiased`}>{children}</body>
    </html>
  )
}
