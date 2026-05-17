import { MetadataRoute } from "next"

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://concerto.run"
  const now = new Date()

  return [
    {
      url: base,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1.0,
    },
    {
      url: `${base}/help`,
      lastModified: now,
      changeFrequency: "monthly",
      priority: 0.7,
    },
    {
      url: `${base}/status`,
      lastModified: now,
      changeFrequency: "always",
      priority: 0.5,
    },
    {
      url: `${base}/legal/terms`,
      lastModified: now,
      changeFrequency: "yearly",
      priority: 0.3,
    },
  ]
}
