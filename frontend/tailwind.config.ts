import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        /* Anthropic-adjacent warm palette */
        peach: {
          DEFAULT: "#cc785c",
          hover:   "#b86747",
          soft:    "#e9b8a4",
          100:     "#fdf0ea",
          200:     "#f5d4c4",
          300:     "#e9b8a4",
          400:     "#d99b80",
          500:     "#cc785c",
          600:     "#b86747",
          700:     "#96523a",
        },
        cream: {
          DEFAULT: "#faf9f5",
          surface: "#ffffff",
          subtle:  "#f3efe5",
          50:      "#faf9f5",
          100:     "#f3efe5",
          200:     "#e8e3d8",
        },
        ink: {
          DEFAULT: "#191919",
          secondary: "#555049",
          tertiary:  "#8a847b",
          deep:      "#2a2925",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
      },
      fontFamily: {
        sans:    ["var(--font-inter)",      "system-ui",       "sans-serif"],
        mono:    ["var(--font-mono)",       "JetBrains Mono",  "ui-monospace", "monospace"],
        display: ["var(--font-fraunces)",   "Iowan Old Style", "Palatino",     "serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to:   { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to:   { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.22s cubic-bezier(0.16,1,0.3,1)",
        "accordion-up":   "accordion-up   0.22s cubic-bezier(0.16,1,0.3,1)",
      },
      backgroundImage: {
        "peach-radial": "radial-gradient(ellipse at center, rgba(204,120,92,0.10) 0%, transparent 70%)",
      },
      boxShadow: {
        "card":       "0 1px 2px rgba(25,25,25,0.04)",
        "card-hover": "0 2px 8px rgba(25,25,25,0.06)",
        "peach-sm":   "0 0 0 1px rgba(204,120,92,0.20)",
        "peach-md":   "0 4px 24px rgba(204,120,92,0.12), 0 0 0 1px rgba(204,120,92,0.15)",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
}

export default config
