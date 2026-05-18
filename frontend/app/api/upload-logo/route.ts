import { writeFile, mkdir } from "fs/promises"
import { NextRequest } from "next/server"
export const runtime = "nodejs"
export const dynamic = "force-dynamic"
export async function POST(req: NextRequest) {
  try {
    const fd = await req.formData()
    const f = fd.get("file") as File | null
    const variant = (fd.get("variant") as string) || "dark"
    if (!f) return new Response("no file", { status: 400 })
    if (!["dark","light"].includes(variant)) return new Response("bad variant", { status: 400 })
    const bytes = Buffer.from(await f.arrayBuffer())
    await mkdir("/tmp/concerto-uploads", { recursive: true })
    const name = variant === "light" ? "logo-light.png" : "logo.png"
    await writeFile(`/tmp/concerto-uploads/${name}`, bytes)
    return new Response(`saved ${bytes.length}b → /tmp/concerto-uploads/${name} (variant=${variant})`, { status: 200 })
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err)
    return new Response(`error: ${msg}`, { status: 500 })
  }
}
