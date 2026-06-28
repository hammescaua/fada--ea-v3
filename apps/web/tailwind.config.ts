import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        soil: "#6b4f3a",
        leaf: "#2f7d32",
        leafdark: "#1b5e20",
      },
    },
  },
  plugins: [],
};

export default config;
