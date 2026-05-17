import { NextResponse } from "next/server"
import Stripe from "stripe"

export async function POST(request: Request) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: "2025-02-24.acacia",
  })

  const origin = request.headers.get("origin") ?? "https://concerto.run"

  // Accept plan from JSON body or query param
  let plan = "byoc"
  let region = "nyc1"
  const contentType = request.headers.get("content-type") ?? ""
  if (contentType.includes("application/json")) {
    try {
      const body = await request.json()
      plan = body.plan ?? "byoc"
      region = body.region ?? "nyc1"
    } catch {
      // ignore parse errors; fall back to defaults
    }
  } else {
    const url = new URL(request.url)
    plan = url.searchParams.get("plan") ?? "byoc"
    region = url.searchParams.get("region") ?? "nyc1"
  }

  const isHosted = plan === "hosted"

  // Optional: trial_token passed when upgrading from a trial
  let trialToken = ""
  const urlObj = new URL(request.url)
  trialToken = urlObj.searchParams.get("trial_token") ?? ""

  const priceId = isHosted
    ? process.env.STRIPE_CONCERTO_HOSTED_PRICE_ID!
    : process.env.STRIPE_CONCERTO_PRICE_ID!

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ["card"],
    line_items: [
      {
        price: priceId,
        quantity: 1,
      },
    ],
    mode: isHosted ? "subscription" : "payment",
    automatic_tax: { enabled: true },
    metadata: {
      product: "concerto",
      plan,
      region,
      ...(trialToken ? { trial_token: trialToken } : {}),
    },
    success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${origin}/#pricing`,
  })

  return NextResponse.redirect(session.url!, { status: 303 })
}
