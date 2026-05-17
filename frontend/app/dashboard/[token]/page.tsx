"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Copy, Check, ExternalLink, Terminal, Zap } from "lucide-react"

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-1.5">
      <label className="text-xs text-white/40 font-medium uppercase tracking-wider">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <code className="flex-1 rounded-md border border-white/8 bg-white/[0.03] px-3 py-2 text-sm font-mono text-white/80 break-all">
          {value}
        </code>
        <Button
          variant="ghost"
          size="icon"
          onClick={copy}
          className="shrink-0 text-white/40 hover:text-white hover:bg-white/10"
        >
          {copied ? (
            <Check className="h-4 w-4 text-green-400" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}

export default function DashboardPage({ params }: { params: { token: string } }) {
  const [dashData, setDashData] = useState<{
    mcp_url?: string
    bearer_token?: string
  } | null>(null)

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.maestro.run"
  const terminalUrl = `${backendUrl}/terminal/${params.token}`

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) => setDashData({ mcp_url: d.mcp_url, bearer_token: d.bearer_token }))
      .catch(() => {})
  }, [backendUrl, params.token])

  const mcpUrl = dashData?.mcp_url ?? `${backendUrl}/mcp/${params.token}`
  const bearerToken = dashData?.bearer_token ?? "Loading..."

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Top bar */}
      <header className="border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-violet-500 to-indigo-600" />
            <span className="font-semibold text-white tracking-tight">Maestro</span>
            <Separator orientation="vertical" className="h-4 bg-white/10 mx-1" />
            <span className="text-white/30 text-sm font-mono truncate max-w-[120px]">
              {params.token}
            </span>
          </div>
          <Badge className="bg-green-500/15 text-green-400 border-green-500/20 text-xs">
            <span className="h-1.5 w-1.5 rounded-full bg-green-400 mr-1.5 inline-block animate-pulse" />
            Online
          </Badge>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 space-y-8">
        {/* Connect to claude.ai guide */}
        <Card className="bg-white/[0.03] border-violet-500/20 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-violet-600/5 to-transparent pointer-events-none" />
          <CardHeader className="relative">
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-violet-400" />
              <CardTitle className="text-white text-lg">Connect to claude.ai</CardTitle>
            </div>
            <p className="text-white/40 text-sm mt-1">
              Paste these 3 values into claude.ai → Settings → Connectors → Add custom connector.
            </p>
          </CardHeader>
          <CardContent className="relative space-y-5">
            <CopyField label="MCP URL" value={mcpUrl} />
            <CopyField label="Bearer Token" value={bearerToken} />
            <CopyField label="Connector Name" value="Maestro" />

            <Separator className="bg-white/8" />

            <div className="space-y-3">
              <p className="text-xs font-medium text-white/40 uppercase tracking-wider">
                Step-by-step
              </p>
              <ol className="space-y-2.5">
                {[
                  <>Open <a href="https://claude.ai" target="_blank" rel="noopener noreferrer" className="text-violet-400 hover:text-violet-300 inline-flex items-center gap-0.5">claude.ai <ExternalLink className="h-3 w-3" /></a> and click your avatar → <strong className="text-white/70">Settings</strong></>,
                  <>Navigate to <strong className="text-white/70">Connectors</strong> → <strong className="text-white/70">Add custom connector</strong></>,
                  <>Paste the <strong className="text-white/70">MCP URL</strong> and <strong className="text-white/70">Bearer Token</strong> above, name it <strong className="text-white/70">Maestro</strong>, and click Save</>,
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-sm">
                    <span className="h-5 w-5 rounded-full bg-violet-500/20 text-violet-300 flex items-center justify-center text-xs shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="text-white/50 leading-relaxed">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </CardContent>
        </Card>

        {/* Terminal */}
        <Card className="bg-white/[0.03] border-white/8 overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-white/40" />
              <CardTitle className="text-white text-base">Browser Terminal</CardTitle>
            </div>
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="text-white/40 hover:text-white hover:bg-white/10 text-xs gap-1.5"
            >
              <a href={terminalUrl} target="_blank" rel="noopener noreferrer">
                Open in new tab <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="w-full bg-[#0d0d0d] rounded-b-lg overflow-hidden border-t border-white/5">
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-white/5 bg-black/20">
                <div className="h-2.5 w-2.5 rounded-full bg-red-500/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/60" />
                <div className="h-2.5 w-2.5 rounded-full bg-green-500/60" />
                <span className="ml-2 text-white/20 text-xs font-mono">maestro · shell</span>
              </div>
              <iframe
                src={terminalUrl}
                className="w-full h-[520px] border-0"
                title="Maestro Terminal"
                allow="clipboard-read; clipboard-write"
              />
            </div>
          </CardContent>
        </Card>

        {/* Support footer */}
        <div className="text-center py-4">
          <p className="text-white/25 text-sm">
            Need help?{" "}
            <a
              href="mailto:support@maestro.run"
              className="text-violet-400 hover:text-violet-300 transition-colors"
            >
              support@maestro.run
            </a>
          </p>
        </div>
      </main>
    </div>
  )
}
