import fs from "fs"
import path from "path"
import { marked } from "marked"

const DOCS_LEGAL_DIR = path.join(process.cwd(), "..", "docs", "legal")

export function getLegalContent(filename: string): string {
  const filepath = path.join(DOCS_LEGAL_DIR, filename)
  const raw = fs.readFileSync(filepath, "utf-8")
  return marked(raw) as string
}
