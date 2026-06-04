"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function SetupPage({ params }: { params: { token: string } }) {
  const router = useRouter()

  useEffect(() => {
    // Redirect to dashboard — the real onboarding happens there
    router.replace(`/dashboard/${params.token}`)
  }, [params.token, router])

  return (
    <div
      className="flex min-h-screen items-center justify-center px-6 py-16"
      style={{ backgroundColor: "#faf9f5", color: "#191919" }}
    >
      <div className="w-full max-w-[480px] text-center">
        <img src="/brand/logo-mark.png?v=3" alt="Concerto" width={36} height={36} className="mx-auto mb-4" />
        <p className="text-[15px]" style={{ color: "#8a847b" }}>Loading your dashboard…</p>
      </div>
    </div>
  )
}
