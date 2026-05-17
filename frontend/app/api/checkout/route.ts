import { NextResponse } from "next/server"
import Stripe from "stripe"

export async function POST(request: Request) {
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: "2025-02-24.acacia",
  })

  const origin = request.headers.get("origin") ?? "https://maestro.run"

  const session = await stripe.checkout.sessions.create({
    payment_method_types: ["card"],
    line_items: [
      {
        price: process.env.STRIPE_MAESTRO_PRICE_ID!,
        quantity: 1,
      },
    ],
    mode: "payment",
    metadata: {
      product: "maestro",
    },
    success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${origin}/#pricing`,
  })

  return NextResponse.redirect(session.url!, { status: 303 })
}
