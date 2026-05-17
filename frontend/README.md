# Concerto Frontend

Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui frontend for Concerto.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page — hero, features, pricing, FAQ |
| `/api/checkout` | POST → creates Stripe Checkout session |
| `/success` | Post-payment confirmation |
| `/setup/[token]` | DigitalOcean key entry + provisioning progress |
| `/dashboard/[token]` | MCP credentials, browser terminal, connect guide |

## Environment variables

Copy `.env.local.example` → `.env.local` and fill in:

| Variable | Description |
|----------|-------------|
| `STRIPE_SECRET_KEY` | Stripe secret key (server-side) |
| `NEXT_PUBLIC_STRIPE_PUBLIC_KEY` | Stripe publishable key |
| `STRIPE_CONCERTO_PRICE_ID` | Stripe Price ID for the $99 one-time product |
| `NEXT_PUBLIC_BACKEND_URL` | Backend API base URL (default: `https://api.concerto.run`) |

## Development

```bash
npm install
npm run dev
```

## Deploy

Deploy to Vercel. Add all env vars in the Vercel dashboard under Project → Settings → Environment Variables.
