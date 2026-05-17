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
        /* Claude-native warm palette */
        warm: {
          DEFAULT: "#d97757",
          50:  "#fdf3ef",
          100: "#fae5dc",
          200: "#f5c9b6",
          300: "#eeaa8a",
          400: "#e48a62",
          500: "#d97757",
          600: "#c66647",
          700: "#a3503a",
          800: "#7d3d2c",
          900: "#5a2b1e",
        },
        cream: {
          DEFAULT: "#f5f0e9",
          50:  "#f5f0e9",
          100: "#ede5d8",
          200: "#c4b8aa",
          300: "#a09285",
          400: "#877c70",
          500: "#6e645a",
        },
        "c-violet": {
          DEFAULT: "#8b7fff",
          soft:    "#6b5fdb",
          50:  "#f0effe",
          100: "#e2ddfd",
          200: "#c5bafb",
          300: "#a897f9",
          400: "#8b7fff",
          500: "#6b5fdb",
          600: "#5246b8",
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
        "warm-radial":   "radial-gradient(ellipse at center, rgba(217,119,87,0.12) 0%, transparent 70%)",
        "violet-radial": "radial-gradient(ellipse at center, rgba(139,127,255,0.10) 0%, transparent 70%)",
        "hero-gradient": "linear-gradient(135deg, #d97757 0%, #8b7fff 100%)",
      },
      boxShadow: {
        "warm-sm":    "0 0 0 1px rgba(217,119,87,0.2)",
        "warm-md":    "0 4px 24px rgba(217,119,87,0.12), 0 0 0 1px rgba(217,119,87,0.15)",
        "warm-lg":    "0 8px 40px rgba(217,119,87,0.18), 0 0 0 1px rgba(217,119,87,0.2)",
        "warm-cta":   "0 8px 24px rgba(217,119,87,0.25)",
        "warm-cta-lg":"0 12px 32px rgba(217,119,87,0.35)",
        "card-inset": "inset 0 1px 0 rgba(245,240,233,0.06)",
        "surface-sm": "0 1px 3px rgba(0,0,0,0.4)",
        "surface-md": "0 4px 16px rgba(0,0,0,0.5)",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
}

export default config
