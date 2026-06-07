import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0e14",
        panel: "#121722",
        panel2: "#1a2130",
        border: "#252e40",
        ink: "#e6edf6",
        muted: "#8a97ad",
        accent: "#5b8cff",
        system: "#f87171",
        domain: "#fbbf24",
        runtime: "#60a5fa",
        milestone: "#34d399",
        quarantine: "#fb7185",
        ok: "#34d399",
        warn: "#fbbf24",
        danger: "#f87171",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
