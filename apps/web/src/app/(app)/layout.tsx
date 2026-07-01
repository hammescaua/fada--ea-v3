"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useScenario } from "@/lib/store";
import { useMunicipalities, useSim, useBriefing, useAccuracy } from "@/lib/queries";
import { Onboarding } from "@/components/Onboarding";
import { SeasonReport } from "@/components/SeasonReport";

const NAV = [
  { href: "/", icon: "🌱", label: "Minha safra" },
  { href: "/talhao", icon: "🌾", label: "Meu talhão" },
  { href: "/calendario", icon: "📅", label: "Calendário" },
  { href: "/registrar", icon: "✍️", label: "Registrar" },
  { href: "/simular", icon: "🔬", label: "Simular" },
  { href: "/resultados", icon: "📈", label: "Resultados" },
];

const hoje = () => new Date().toLocaleDateString("pt-BR", { day: "numeric", month: "long" });

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { scenario, debounced, provenance, patchScenario, setSoilReal, configured, setConfigured, hydrated } =
    useScenario();
  const { data: municipalities = [] } = useMunicipalities();

  // Dados do relatório (PDF), compartilhados via cache com as páginas.
  const { data: sim, isFetching } = useSim(debounced, configured && hydrated);
  const { data: briefing } = useBriefing(debounced, provenance, configured && hydrated);
  const { data: accuracy } = useAccuracy(debounced, provenance, configured && hydrated);

  // Enquanto lê o navegador, um respiro neutro (evita piscar telas).
  if (!hydrated) {
    return <div className="flex min-h-screen items-center justify-center text-stone-300">🌱</div>;
  }

  // Primeira vez (ou "Reconfigurar"): a jornada de onboarding, tela cheia.
  if (!configured) {
    return (
      <main className="mx-auto max-w-3xl px-4 py-10">
        <Onboarding
          scenario={scenario}
          municipalities={municipalities}
          onComplete={(patch, soilInformed) => {
            patchScenario(patch);
            setSoilReal(soilInformed);
            setConfigured(true);
            window.localStorage.setItem("fada_setup", "1");
          }}
          onSkip={() => {
            setConfigured(true);
            window.localStorage.setItem("fada_setup", "1");
          }}
        />
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Relatório imprimível — some da tela, aparece só no PDF. */}
      <div className="hidden print:block">
        <SeasonReport scenario={scenario} briefing={briefing} sim={sim ?? undefined} accuracy={accuracy} />
      </div>

      <header className="sticky top-0 z-20 border-b border-stone-200 bg-white/90 backdrop-blur print:hidden">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-3">
          <div className="flex items-center gap-2.5">
            <span className="text-xl font-bold text-leafdark">🌱 FADA</span>
            <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs font-medium capitalize text-stone-500">
              Hoje · {hoje()}
            </span>
            {isFetching && <span className="text-xs text-stone-400">atualizando…</span>}
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Link href="/guia" className="rounded-md px-3 py-1.5 text-stone-500 hover:bg-stone-100">
              ❔ Ajuda
            </Link>
            <button onClick={() => window.print()} className="rounded-md px-3 py-1.5 text-stone-500 hover:bg-stone-100">
              📄 PDF
            </button>
            <button
              onClick={() => setConfigured(false)}
              className="rounded-md px-3 py-1.5 text-stone-500 hover:bg-stone-100"
            >
              Reconfigurar
            </button>
          </div>
        </div>

        {/* Navegação em abas: separação clara, um destino por página. */}
        <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4">
          {NAV.map((n) => {
            const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
            return (
              <Link
                key={n.href}
                href={n.href}
                className={`flex items-center gap-1.5 whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition ${
                  active
                    ? "border-leaf text-leafdark"
                    : "border-transparent text-stone-500 hover:text-stone-700"
                }`}
              >
                <span>{n.icon}</span>
                <span>{n.label}</span>
              </Link>
            );
          })}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10 print:hidden">{children}</main>
    </div>
  );
}
