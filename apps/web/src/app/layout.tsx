import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "FADA — Gêmeo Digital da Soja",
  description:
    "Laboratório virtual de safra: simule manejos e veja o impacto na produtividade e na rentabilidade, talhão a talhão.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
