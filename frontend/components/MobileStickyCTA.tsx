"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"

export function MobileStickyCTA() {
  const [visible, setVisible] = useState(false)
  const [pricingReached, setPricingReached] = useState(false)

  useEffect(() => {
    const sentinel = document.getElementById("hero-section-end")
    if (sentinel) {
      const obs = new IntersectionObserver(
        ([entry]) => setVisible(!entry.isIntersecting),
        { rootMargin: "0px", threshold: 0 }
      )
      obs.observe(sentinel)
      return () => obs.disconnect()
    }
  }, [])

  useEffect(() => {
    const pricing = document.getElementById("pricing")
    if (!pricing) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        // Mark pricing as reached once it scrolls into view; do NOT reset on scroll back up
        if (entry.isIntersecting) setPricingReached(true)
      },
      { rootMargin: "0px 0px -50% 0px", threshold: 0 }
    )
    obs.observe(pricing)
    return () => obs.disconnect()
  }, [])

  const buttonLabel = pricingReached ? "Start Pro — $99/mo" : "Start in 5 minutes"
  const subLabel = pricingReached ? "Solo plan also available at $49/mo" : "Choose your plan below"

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-[rgba(25,25,25,0.10)] bg-[#faf9f5]/95 px-4 py-2 backdrop-blur-xl md:hidden"
      style={{
        paddingBottom: "max(8px, env(safe-area-inset-bottom))",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(8px)",
        pointerEvents: visible ? "auto" : "none",
        transition: "opacity 0.3s ease, transform 0.3s ease",
      }}
    >
      {pricingReached ? (
        <form action="/api/checkout?plan=pro" method="POST">
          <Button
            type="submit"
            className="h-10 w-full rounded-[6px] bg-[#cc785c] text-sm font-medium text-[#faf9f5] hover:bg-[#b86747]"
          >
            {buttonLabel}
          </Button>
        </form>
      ) : (
        <a href="#pricing" className="block">
          <Button
            type="button"
            className="h-10 w-full rounded-[6px] bg-[#cc785c] text-sm font-medium text-[#faf9f5] hover:bg-[#b86747]"
          >
            {buttonLabel}
          </Button>
        </a>
      )}
      <p className="mt-1 text-center text-xs text-[#8a847b]">{subLabel}</p>
    </div>
  )
}
