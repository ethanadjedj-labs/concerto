"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"

export function MobileStickyCTA() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const sentinel = document.getElementById("hero-section-end")
    if (!sentinel) return
    const obs = new IntersectionObserver(
      ([entry]) => setVisible(!entry.isIntersecting),
      { rootMargin: "0px", threshold: 0 }
    )
    obs.observe(sentinel)
    return () => obs.disconnect()
  }, [])

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-[rgba(25,25,25,0.10)] bg-[#faf9f5]/95 px-4 py-3 backdrop-blur-xl md:hidden"
      style={{
        paddingBottom: "max(12px, env(safe-area-inset-bottom))",
        transform: visible ? "translateY(0)" : "translateY(100%)",
        transition: "transform 0.3s ease",
      }}
    >
      <form action="/api/checkout?plan=pro" method="POST">
        <Button
          type="submit"
          className="h-12 w-full rounded-[6px] bg-[#cc785c] text-base font-medium text-[#faf9f5] hover:bg-[#b86747]"
        >
          Start with Pro — $99/mo
        </Button>
      </form>
      <p className="mt-1.5 text-center text-xs text-[#8a847b]">Solo plan also available at $49/mo</p>
    </div>
  )
}
