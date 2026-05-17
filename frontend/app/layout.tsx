import type { Metadata } from "next"
import { Inter, JetBrains_Mono, Fraunces } from "next/font/google"
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

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  style: ["normal", "italic"],
  weight: ["300", "400", "500"],
})

export const metadata: Metadata = {
  metadataBase: new URL("https://concerto.run"),
  title: {
    default: "Concerto — Remote Workshop for Claude Code Agents",
    template: "%s — Concerto",
  },
  description:
    "Run Claude Code from Claude chat. Claude spawns sessions on your dedicated remote machine — no terminal, no setup. Solo $49/mo · Pro $99/mo.",
  keywords: [
    "Claude Code",
    "AI agents",
    "remote workshop",
    "Claude Code agents",
    "AI automation",
    "developer tools",
    "parallel AI workers",
    "cloud AI",
  ],
  openGraph: {
    title: "Concerto — Remote Workshop for Claude Code Agents",
    description:
      "Pilot Claude Code agents from your browser. Parallel AI workers running 24/7 in your own cloud — no terminal required.",
    url: "https://concerto.run",
    siteName: "Concerto",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "Concerto — Remote Workshop for Claude Code Agents",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Concerto — Remote Workshop for Claude Code Agents",
    description:
      "Pilot Claude Code agents from your browser. Parallel AI workers 24/7, your cloud, your billing.",
    images: ["/twitter-image"],
    creator: "@ethanadjedj",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/icon",
    apple: "/apple-icon",
  },
}

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://concerto.run/#organization",
      name: "Concerto",
      url: "https://concerto.run",
      logo: {
        "@type": "ImageObject",
        url: "https://concerto.run/icon",
      },
      sameAs: ["https://github.com/ethanadjedj-labs/concerto"],
    },
    {
      "@type": "WebSite",
      "@id": "https://concerto.run/#website",
      url: "https://concerto.run",
      name: "Concerto",
      publisher: { "@id": "https://concerto.run/#organization" },
    },
    {
      "@type": "Product",
      "@id": "https://concerto.run/#product-solo",
      name: "Concerto Solo",
      description:
        "Dedicated remote machine for Claude Code — 4GB memory, up to 2 parallel sessions, email support included.",
      url: "https://concerto.run",
      brand: { "@id": "https://concerto.run/#organization" },
      offers: {
        "@type": "Offer",
        price: "49.00",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "RecurringCharge",
          price: "49.00",
          priceCurrency: "USD",
          billingDuration: "P1M",
        },
        availability: "https://schema.org/InStock",
        url: "https://concerto.run/#checkout-solo",
      },
    },
    {
      "@type": "Product",
      "@id": "https://concerto.run/#product-pro",
      name: "Concerto Pro",
      description:
        "Dedicated remote machine for Claude Code — 8GB memory, up to 6–8 parallel sessions, email support included.",
      url: "https://concerto.run",
      brand: { "@id": "https://concerto.run/#organization" },
      offers: {
        "@type": "Offer",
        price: "99.00",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "RecurringCharge",
          price: "99.00",
          priceCurrency: "USD",
          billingDuration: "P1M",
        },
        availability: "https://schema.org/InStock",
        url: "https://concerto.run/#checkout-pro",
      },
    },
  ],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${jetbrainsMono.variable} ${fraunces.variable}`}
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body className={`${inter.className} antialiased`}>{children}</body>
    </html>
  )
}
