import type { Config } from "tailwindcss";

/**
 * All values below are taken directly from the Karabakh University Digital
 * Design System (KUDS) v1.0 guidelines document (sections 3-9, 11-14).
 * Do not introduce colors, radii, shadows, or spacing values outside of
 * this file - KUDS explicitly prohibits per-project design deviation.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    // KUDS section 9 - Responsive Breakpoints
    screens: {
      md: "768px", // Tablet
      lg: "1024px", // Laptop
      xl: "1280px", // Desktop
      "2xl": "1536px", // Large Desktop
    },
    extend: {
      colors: {
        // KUDS section 3 - Brand Identity
        "ku-green": "#44766C",
        "ku-dark-green": "#16423C",
        "ku-soft-green": "#D3E8BF",
        "ku-light-blue": "#CAEAF1",
        "ku-cream": "#F0F3BF",
        background: "#F8FAFC",
        surface: "#FFFFFF",
        border: "#E2E8F0",
        "text-primary": "#1E293B",
        "text-secondary": "#64748B",
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
      },
      fontFamily: {
        // KUDS section 4 - Typography (Poppins, fallback Tahoma)
        sans: ["var(--font-poppins)", "Tahoma", "sans-serif"],
      },
      fontSize: {
        // KUDS typography scale table
        display: ["40px", { lineHeight: "150%", fontWeight: "700" }],
        h1: ["32px", { lineHeight: "150%", fontWeight: "700" }],
        h2: ["24px", { lineHeight: "150%", fontWeight: "600" }],
        h3: ["20px", { lineHeight: "150%", fontWeight: "600" }],
        h4: ["18px", { lineHeight: "150%", fontWeight: "500" }],
        body: ["16px", { lineHeight: "150%", fontWeight: "400" }],
        small: ["14px", { lineHeight: "150%", fontWeight: "400" }],
        caption: ["12px", { lineHeight: "150%", fontWeight: "400" }],
      },
      borderRadius: {
        // KUDS section 6 - Border Radius
        button: "8px",
        input: "8px",
        badge: "999px",
        card: "12px",
        modal: "16px",
      },
      boxShadow: {
        // KUDS section 7 - Shadows ("heavy shadows must not be used")
        xs: "0 1px 2px rgba(0,0,0,.04)",
        sm: "0 2px 6px rgba(0,0,0,.06)",
        md: "0 8px 20px rgba(0,0,0,.08)",
      },
      spacing: {
        // KUDS section 5 - Spacing System (only these values may be used)
        1: "4px",
        2: "8px",
        3: "12px",
        4: "16px",
        6: "24px",
        8: "32px",
        12: "48px",
        16: "64px",
        24: "96px",
      },
      maxWidth: {
        // KUDS section 8 - Layout System
        desktop: "1440px",
      },
      width: {
        sidebar: "280px",
      },
      height: {
        header: "72px",
      },
    },
  },
  plugins: [],
};

export default config;
