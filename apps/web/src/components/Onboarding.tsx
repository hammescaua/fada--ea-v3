"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

const input = "rounded-md border border-stone-300 px-2 py-1.5 text-sm focus:border-leaf focus:outline-none";

interface Props {
  scenario: ScenarioIn;
  municipalities: string[];
  onComplete: (patch: Partial<ScenarioIn>, soilInformed: boolean) => void;
  onSkip: () => void;
}

const CULTIVARS = [
  { name: "GMR 5.2 precoce", maturity_group: 5.2, base_potential_sc_ha: 92, cycle_days: 120, disease_tolerance: 0.5 },
  { name: "GMR 5.5 média", maturity_group: 5.5, base_potential_sc_ha: 95, cycle_days: 130, disease_tolerance: 0.6 },
  { name: "GMR 6.2 tardia", maturity_group: 6.2, base_potential_sc_ha: 98, cycle_days: 140, disease_tolerance: 0.4 },
];

export function Onboarding({ scenario, municipalities, onComplete, onSkip }: Props) {
  const [step, setStep] = useState(0);
  const [municipality, setMunicipality] = useState(scenario.municipality);
  const [lat, setLat] = useState(scenario.latitude);
  const [lon, setLon] = useState(scenario.longitude);
  const [hasSoil, setHasSoil] = useState<boolean | null>(null);
  const [soil, setSoil] = useState(scenario.soil);
  const [cultivarIdx, setCultivarIdx] = useState(1);
  const [sowing, setSowing] = useState(scenario.sowing_date);
  const [price, setPrice] = useState(scenario.soybean_price_per_sc);
  const [pop, setPop] = useState(scenario.population_k_per_ha);
  const [prevCrop, setPrevCrop] = useState<NonNullable<ScenarioIn["previous_crop"]>>(scenario.previous_crop ?? "soja");
  const [nematode, setNematode] = useState<NonNullable<ScenarioIn["nematode_pressure"]>>(scenario.nematode_pressure ?? "nenhuma");
  const [enso, setEnso] = useState<NonNullable<ScenarioIn["enso"]>>(scenario.enso ?? "neutro");

  // Cenário montado a partir do que o produtor informou — usado tanto para o
  // payoff ("já encontrei oportunidades") quanto para concluir.
  const patch: Partial<ScenarioIn> = {
    municipality,
    latitude: lat,
    longitude: lon,
    soil: hasSoil ? soil : scenario.soil,
    cultivar: CULTIVARS[cultivarIdx],
    sowing_date: sowing,
    soybean_price_per_sc: price,
    population_k_per_ha: pop,
    previous_crop: prevCrop,
    nematode_pressure: nematode,
    enso,
    use_live_weather: true,
  };
  const assembled: ScenarioIn = { ...scenario, ...patch };

  // Valor antes de "terminar o cadastro": roda o radar real assim que os dados
  // entram, ainda na última tela do onboarding.
  const { data: radar, isFetching: analyzing } = useQuery({
    queryKey: ["onboarding-radar", assembled],
    queryFn: () => api.radar(assembled),
    enabled: step === 4,
  });
  const oportunidades = radar
    ? radar.actions.filter((a) => a.janela_status !== "passou").length
    : 0;

  const finish = () => onComplete(patch, hasSoil === true);

  const setS = (patch: Partial<ScenarioIn["soil"]>) => setSoil((s) => ({ ...s, ...patch }));

  return (
    <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
      {/* Boas-vindas: nenhum dashboard, nenhum formulário — só o convite. */}
      {step === 0 && (
        <div className="space-y-5 text-center">
          <div className="text-4xl">🌱</div>
          <h2 className="text-2xl font-bold text-leafdark">Vamos montar sua safra</h2>
          <p className="mx-auto max-w-md text-sm text-stone-600">
            Leva poucos minutos. Você responde o básico sobre o talhão e o FADA faz o resto —
            previsão, riscos e as próximas decisões. Pode pular o que não tiver em mãos; nada
            trava.
          </p>
          <div className="flex flex-col items-center gap-2">
            <button
              onClick={() => setStep(1)}
              className="rounded-md bg-leaf px-6 py-2.5 text-sm font-semibold text-white hover:bg-leafdark"
            >
              Começar
            </button>
            <button onClick={onSkip} className="text-xs text-stone-400 underline">
              só quero ver um exemplo pronto
            </button>
          </div>
        </div>
      )}

      {step >= 1 && step <= 3 && (
        <>
          <div className="mb-1 flex items-center justify-between">
            <h2 className="text-lg font-bold text-leafdark">🌱 Vamos configurar seu talhão</h2>
            <button onClick={onSkip} className="text-xs text-stone-400 underline">
              pular e usar exemplo
            </button>
          </div>
          <p className="mb-4 text-sm text-stone-500">
            Em 3 passos o gêmeo digital fica personalizado para a sua lavoura. Quanto mais real o
            dado, mais verídica a previsão — e a ferramenta sempre diz de onde veio cada número.
          </p>

          {/* indicador de passos */}
          <div className="mb-5 flex gap-2">
            {[1, 2, 3].map((n) => (
              <div
                key={n}
                className={`h-1.5 flex-1 rounded-full ${n <= step ? "bg-leaf" : "bg-stone-200"}`}
              />
            ))}
          </div>
        </>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-stone-700">1. Onde fica o talhão?</h3>
          <p className="text-xs text-stone-500">
            O município define a janela de semeadura (ZARC). A coordenada permite buscar o clima
            histórico real daquele ponto exato — bem mais preciso que uma média regional.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Município</span>
              <select className={input} value={municipality} onChange={(e) => setMunicipality(e.target.value)}>
                {municipalities.map((m) => (
                  <option key={m}>{m}</option>
                ))}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-2">
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">Latitude</span>
                <input type="number" step={0.01} className={input} value={lat} onChange={(e) => setLat(Number(e.target.value))} />
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">Longitude</span>
                <input type="number" step={0.01} className={input} value={lon} onChange={(e) => setLon(Number(e.target.value))} />
              </label>
            </div>
          </div>
          <div className="flex justify-end">
            <button onClick={() => setStep(2)} className="rounded-md bg-leaf px-4 py-2 text-sm font-medium text-white hover:bg-leafdark">
              Continuar
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-stone-700">2. Você tem a análise de solo do talhão?</h3>
          <p className="text-xs text-stone-500">
            É o dado que mais personaliza a recomendação (calagem, adubação). Sem ele, usamos um
            perfil regional típico — e marcamos isso honestamente na precisão.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setHasSoil(true)}
              className={`rounded-lg border p-3 text-left text-sm ${hasSoil === true ? "border-leaf bg-green-50" : "border-stone-200"}`}
            >
              <div className="font-medium text-stone-800">Sim, tenho análise</div>
              <div className="text-xs text-stone-500">vou informar pH, V%, P, K…</div>
            </button>
            <button
              onClick={() => setHasSoil(false)}
              className={`rounded-lg border p-3 text-left text-sm ${hasSoil === false ? "border-leaf bg-green-50" : "border-stone-200"}`}
            >
              <div className="font-medium text-stone-800">Ainda não</div>
              <div className="text-xs text-stone-500">usar referência regional (NO-RS)</div>
            </button>
          </div>

          {hasSoil && (
            <div className="grid grid-cols-3 gap-3 rounded-lg bg-stone-50 p-3">
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">Textura</span>
                <select className={input} value={soil.texture} onChange={(e) => setS({ texture: e.target.value })}>
                  <option value="arenoso">Arenoso</option>
                  <option value="medio">Médio</option>
                  <option value="argiloso">Argiloso</option>
                </select>
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">pH</span>
                <input type="number" step={0.1} className={input} value={soil.ph} onChange={(e) => setS({ ph: Number(e.target.value) })} />
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">V%</span>
                <input type="number" className={input} value={soil.base_saturation_pct} onChange={(e) => setS({ base_saturation_pct: Number(e.target.value) })} />
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">Fósforo (ppm)</span>
                <input type="number" className={input} value={soil.phosphorus_ppm} onChange={(e) => setS({ phosphorus_ppm: Number(e.target.value) })} />
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">Potássio (ppm)</span>
                <input type="number" className={input} value={soil.potassium_ppm} onChange={(e) => setS({ potassium_ppm: Number(e.target.value) })} />
              </label>
              <label className="flex flex-col gap-1 text-xs">
                <span className="font-medium text-stone-600">M.O. (%)</span>
                <input type="number" step={0.1} className={input} value={soil.organic_matter_pct} onChange={(e) => setS({ organic_matter_pct: Number(e.target.value) })} />
              </label>
            </div>
          )}

          <div className="flex justify-between">
            <button onClick={() => setStep(1)} className="text-sm text-stone-500">
              ← voltar
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={hasSoil === null}
              className="rounded-md bg-leaf px-4 py-2 text-sm font-medium text-white hover:bg-leafdark disabled:opacity-50"
            >
              Continuar
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-stone-700">3. Cultivar e plano da safra</h3>
          <div className="grid grid-cols-2 gap-3">
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Cultivar (grupo de maturação)</span>
              <select className={input} value={cultivarIdx} onChange={(e) => setCultivarIdx(Number(e.target.value))}>
                {CULTIVARS.map((c, i) => (
                  <option key={c.name} value={i}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Data de semeadura</span>
              <input type="date" className={input} value={sowing} onChange={(e) => setSowing(e.target.value)} />
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">População (mil/ha)</span>
              <input type="number" step={10} className={input} value={pop} onChange={(e) => setPop(Number(e.target.value))} />
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Preço da soja (R$/saca)</span>
              <input type="number" className={input} value={price} onChange={(e) => setPrice(Number(e.target.value))} />
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Cultura anterior (rotação)</span>
              <select className={input} value={prevCrop} onChange={(e) => setPrevCrop(e.target.value as typeof prevCrop)}>
                <option value="soja">Soja (monocultura)</option>
                <option value="milho">Milho</option>
                <option value="trigo">Trigo</option>
                <option value="cobertura">Cobertura (aveia/nabo/ervilhaca)</option>
                <option value="pousio">Pousio</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Nematoides no talhão?</span>
              <select className={input} value={nematode} onChange={(e) => setNematode(e.target.value as typeof nematode)}>
                <option value="nenhuma">Não sei / nenhum</option>
                <option value="baixa">Baixa</option>
                <option value="media">Média</option>
                <option value="alta">Alta (reboleiras)</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs">
              <span className="font-medium text-stone-600">Previsão climática (ENSO)</span>
              <select className={input} value={enso} onChange={(e) => setEnso(e.target.value as typeof enso)}>
                <option value="el_nino">El Niño (chuvoso)</option>
                <option value="neutro">Neutro / não sei</option>
                <option value="la_nina">La Niña (seca)</option>
              </select>
            </label>
          </div>
          <p className="text-xs text-stone-500">
            Esses três últimos personalizam o risco e a produtividade ao seu talhão: rotação e
            nematoides entram na conta; o clima (La Niña = ano seco) ajusta o risco. Pode ajustar
            tudo depois. Geramos o resumo e o passo-a-passo na sequência.
          </p>
          <div className="flex justify-between">
            <button onClick={() => setStep(2)} className="text-sm text-stone-500">
              ← voltar
            </button>
            <button onClick={() => setStep(4)} className="rounded-md bg-leaf px-5 py-2 text-sm font-semibold text-white hover:bg-leafdark">
              Analisar minha safra →
            </button>
          </div>
        </div>
      )}

      {/* Payoff: valor imediato, ainda dentro do onboarding. */}
      {step === 4 && (
        <div className="space-y-5 text-center">
          {analyzing || !radar ? (
            <div className="space-y-3 py-6">
              <div className="text-3xl">🌱</div>
              <p className="text-sm font-medium text-stone-600">Analisando sua safra…</p>
              <p className="text-xs text-stone-400">cruzando clima, solo e janela de semeadura do seu talhão</p>
              <div className="mx-auto h-1.5 w-40 overflow-hidden rounded-full bg-stone-100">
                <div className="h-full w-1/2 animate-pulse rounded-full bg-leaf" />
              </div>
            </div>
          ) : (
            <>
              <div className="text-4xl">✅</div>
              <h2 className="text-2xl font-bold text-leafdark">Sua safra está criada</h2>
              <p className="text-sm text-stone-600">
                {oportunidades > 0 ? (
                  <>
                    Já encontrei{" "}
                    <span className="font-semibold text-stone-800">
                      {oportunidades === 1 ? "1 oportunidade" : `${oportunidades} oportunidades`}
                    </span>{" "}
                    no seu talhão.
                  </>
                ) : (
                  <>Seu plano já está bem ajustado — sem ações urgentes no momento.</>
                )}
              </p>

              <div className="mx-auto flex max-w-sm flex-wrap items-center justify-center gap-x-6 gap-y-2 rounded-xl bg-stone-50 p-4">
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-stone-400">Potencial</div>
                  <div className="text-2xl font-bold text-stone-800">
                    {radar.expected_sc_ha.toFixed(0)} <span className="text-sm font-medium text-stone-400">sc/ha</span>
                  </div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-stone-400">Lucro estimado</div>
                  <div className="text-2xl font-bold text-stone-800">
                    {radar.profit_per_ha.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })}
                    <span className="text-sm font-medium text-stone-400">/ha</span>
                  </div>
                </div>
              </div>

              {radar.maior_oportunidade && (
                <p className="mx-auto max-w-md text-sm text-stone-500">
                  Maior oportunidade agora:{" "}
                  <span className="font-medium text-leafdark">{radar.maior_oportunidade.acao}</span>{" "}
                  (+{radar.maior_oportunidade.impacto_sc_ha.toFixed(1)} sc/ha).
                </p>
              )}

              <button
                onClick={finish}
                className="rounded-md bg-leaf px-6 py-2.5 text-sm font-semibold text-white hover:bg-leafdark"
              >
                Ver minha safra →
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
