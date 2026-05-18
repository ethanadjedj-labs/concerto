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
    default: "Concerto — Talk to Claude. Claude runs Claude Code.",
    template: "%s — Concerto",
  },
  description:
    "Concerto gives Claude the tools to orchestrate Claude Code sessions. Claude launches sessions, monitors progress, reads logs, compares results, and reports back. Solo $49/mo · Pro $99/mo.",
  keywords: [
    "Claude Code",
    "Claude chat",
    "Claude Code sessions",
    "parallel Claude Code",
    "developer tools",
    "AI orchestration",
    "Claude MCP",
  ],
  openGraph: {
    title: "Concerto — Talk to Claude. Claude runs Claude Code.",
    description:
      "Concerto gives Claude the tools to orchestrate Claude Code sessions — you stay in the normal Claude chat.",
    url: "https://concerto.run",
    siteName: "Concerto",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "Concerto — Claude Code orchestration from one Claude chat",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Concerto — Talk to Claude. Claude runs Claude Code.",
    description:
      "Concerto gives Claude the tools to orchestrate Claude Code sessions — you stay in the normal Claude chat.",
    images: ["/twitter-image"],
    creator: "@concerto_run",
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
      sameAs: ["https://concerto.run"],
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
        "Claude Code orchestration from Claude chat — up to 2 parallel runs, email support included.",
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
        "Claude Code orchestration from Claude chat — up to 6 parallel runs, priority support included.",
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
