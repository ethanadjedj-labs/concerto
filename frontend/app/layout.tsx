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
  metadataBase: new URL("https://concerto.run"),
  title: {
    default: "Concerto — Remote Workshop for Claude Code Agents",
    template: "%s — Concerto",
  },
  description:
    "Pilot Claude Code agents from your browser. Parallel AI workers running 24/7 in your own cloud — no terminal required. Hosted at $39/mo or bring your own cloud for a one-time $99.",
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
      "@id": "https://concerto.run/#product-hosted",
      name: "Concerto Hosted",
      description:
        "Fully managed Claude Code agent workshop — provisioned VPS, managed updates, zero ops.",
      url: "https://concerto.run",
      brand: { "@id": "https://concerto.run/#organization" },
      offers: {
        "@type": "Offer",
        price: "39.00",
        priceCurrency: "USD",
        priceSpecification: {
          "@type": "RecurringCharge",
          price: "39.00",
          priceCurrency: "USD",
          billingDuration: "P1M",
        },
        availability: "https://schema.org/InStock",
        url: "https://concerto.run/#checkout-hosted",
      },
    },
    {
      "@type": "Product",
      "@id": "https://concerto.run/#product-byoc",
      name: "Concerto BYOC",
      description:
        "Bring Your Own Cloud — one-time license to run Concerto on your own DigitalOcean droplet.",
      url: "https://concerto.run",
      brand: { "@id": "https://concerto.run/#organization" },
      offers: {
        "@type": "Offer",
        price: "99.00",
        priceCurrency: "USD",
        availability: "https://schema.org/InStock",
        url: "https://concerto.run/#checkout-byoc",
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
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
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
