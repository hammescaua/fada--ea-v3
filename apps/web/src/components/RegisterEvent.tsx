"use client";

import { useState } from "react";
import type { OperationIn } from "@/lib/types";

/** Registro conversacional: um único lugar para dizer "o que aconteceu hoje".
 *  Parece uma conversa, não um formulário. As aplicações entram direto na
 *  previsão (viram operations do cenário); os demais eventos são reconhecidos
 *  honestamente como parte do Diário da Safra (persistência chega na V2). */

const MANEJOS: { kind: string; label: string; cost: number }[] = [
  { kind: "fungicida", label: "Fungicida", cost: 180 },
  { kind: "inseticida", label: "Inseticida", cost: 120 },
  { kind: "herbicida", label: "Herbicida", cost: 160 },
  { kind: "cobertura", label: "Adubação de cobertura", cost: 220 },
  { kind: "adubacao_foliar", label: "Adubação foliar", cost: 80 },
];

type Kind = "aplicacao" | "plantio" | "chuva" | "monitoramento" | "foto" | "outro";
const EVENTOS: { kind: Kind; icon: string; label: string }[] = [
  { kind: "aplicacao", icon: "🧪", label: "Fiz uma aplicação" },
  { kind: "plantio", icon: "🌱", label: "Plantei / emergiu" },
  { kind: "chuva", icon: "🌧️", label: "Choveu" },
  { kind: "monitoramento", icon: "🔍", label: "Fiz um monitoramento" },
  { kind: "foto", icon: "📷", label: "Tirei uma foto" },
  { kind: "outro", icon: "✍️", label: "Outra coisa" },
];

function Bubble({ me, children }: { me?: boolean; children: React.ReactNode }) {
  return (
    <div className={`flex ${me ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-3.5 py-2 text-sm ${
          me ? "bg-leaf text-white" : "bg-stone-100 text-stone-700"
        }`}
      >
        {children}
      </div>
    </div>
  );
}

export function RegisterEvent({
  today,
  onRegister,
}: {
  today: string;
  onRegister: (op: OperationIn) => void;
}) {
  const [kind, setKind] = useState<Kind | null>(null);
  const [manejo, setManejo] = useState<(typeof MANEJOS)[number] | null>(null);
  const [date, setDate] = useState(today);
  const [cost, setCost] = useState(0);
  const [done, setDone] = useState(false);

  const reset = () => {
    setKind(null);
    setManejo(null);
    setDate(today);
    setCost(0);
    setDone(false);
  };

  const confirm = () => {
    if (!manejo) return;
    onRegister({ kind: manejo.kind, op_date: date, cost_per_ha: cost, quality: 0.9 });
    setDone(true);
  };

  return (
    <div className="mx-auto max-w-lg space-y-3 rounded-2xl border border-stone-200 bg-white p-5">
      <Bubble>Bom dia! O que aconteceu hoje no seu talhão?</Bubble>

      {/* Passo 1: escolher o tipo de evento */}
      {!kind && (
        <div className="grid grid-cols-2 gap-2 pt-1">
          {EVENTOS.map((e) => (
            <button
              key={e.kind}
              onClick={() => {
                setKind(e.kind);
                if (e.kind !== "aplicacao") setManejo(null);
              }}
              className="flex items-center gap-2 rounded-xl border border-stone-200 px-3 py-2.5 text-left text-sm text-stone-700 hover:border-leaf hover:bg-green-50"
            >
              <span className="text-lg">{e.icon}</span> {e.label}
            </button>
          ))}
        </div>
      )}

      {/* Caminho da aplicação: entra direto na previsão */}
      {kind === "aplicacao" && !done && (
        <>
          <Bubble me>Fiz uma aplicação</Bubble>
          <Bubble>Qual manejo?</Bubble>
          {!manejo ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {MANEJOS.map((m) => (
                <button
                  key={m.kind}
                  onClick={() => {
                    setManejo(m);
                    setCost(m.cost);
                  }}
                  className="rounded-full border border-stone-200 px-3 py-1.5 text-sm text-stone-700 hover:border-leaf hover:bg-green-50"
                >
                  {m.label}
                </button>
              ))}
            </div>
          ) : (
            <>
              <Bubble me>{manejo.label}</Bubble>
              <Bubble>Quando e quanto custou por hectare? (já preenchi com uma referência)</Bubble>
              <div className="flex flex-wrap items-end gap-3 pt-1">
                <label className="flex flex-col gap-1 text-xs">
                  <span className="font-medium text-stone-600">Data</span>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs">
                  <span className="font-medium text-stone-600">Custo (R$/ha)</span>
                  <input
                    type="number"
                    value={cost}
                    onChange={(e) => setCost(Number(e.target.value))}
                    className="w-28 rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none"
                  />
                </label>
                <button
                  onClick={confirm}
                  className="rounded-md bg-leaf px-4 py-1.5 text-sm font-semibold text-white hover:bg-leafdark"
                >
                  Registrar
                </button>
              </div>
            </>
          )}
        </>
      )}

      {/* Sucesso: o registro já reflete na previsão */}
      {done && (
        <>
          <Bubble me>{manejo?.label} em {new Date(date).toLocaleDateString("pt-BR")}</Bubble>
          <Bubble>
            Registrado ✓ Já atualizei sua previsão e o custo da safra com essa aplicação.
          </Bubble>
          <button onClick={reset} className="text-sm font-medium text-leafdark underline">
            Registrar outro evento
          </button>
        </>
      )}

      {/* Eventos que ainda não entram no motor — honestidade, sem fingir */}
      {kind && kind !== "aplicacao" && (
        <>
          <Bubble me>{EVENTOS.find((e) => e.kind === kind)?.label}</Bubble>
          <Bubble>
            Anotado. Esse tipo de registro vai virar parte do Diário da Safra na próxima versão. Por
            enquanto, o que entra direto na previsão são as aplicações — quer registrar uma?
          </Bubble>
          <div className="flex gap-2">
            <button
              onClick={() => setKind("aplicacao")}
              className="rounded-md bg-leaf px-3 py-1.5 text-sm font-medium text-white hover:bg-leafdark"
            >
              Sim, registrar aplicação
            </button>
            <button onClick={reset} className="rounded-md border border-stone-300 px-3 py-1.5 text-sm text-stone-600">
              Voltar
            </button>
          </div>
        </>
      )}
    </div>
  );
}
