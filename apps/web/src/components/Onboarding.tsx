"use client";

import { useState } from "react";
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
  const [step, setStep] = useState(1);
  const [municipality, setMunicipality] = useState(scenario.municipality);
  const [lat, setLat] = useState(scenario.latitude);
  const [lon, setLon] = useState(scenario.longitude);
  const [hasSoil, setHasSoil] = useState<boolean | null>(null);
  const [soil, setSoil] = useState(scenario.soil);
  const [cultivarIdx, setCultivarIdx] = useState(1);
  const [sowing, setSowing] = useState(scenario.sowing_date);
  const [price, setPrice] = useState(scenario.soybean_price_per_sc);
  const [pop, setPop] = useState(scenario.population_k_per_ha);

  const finish = () => {
    const cultivar = CULTIVARS[cultivarIdx];
    onComplete(
      {
        municipality,
        latitude: lat,
        longitude: lon,
        soil: hasSoil ? soil : scenario.soil,
        cultivar,
        sowing_date: sowing,
        soybean_price_per_sc: price,
        population_k_per_ha: pop,
        use_live_weather: true,
      },
      hasSoil === true,
    );
  };

  const setS = (patch: Partial<ScenarioIn["soil"]>) => setSoil((s) => ({ ...s, ...patch }));

  return (
    <div className="rounded-2xl border border-leaf/30 bg-white p-6 shadow-sm">
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
          </div>
          <p className="text-xs text-stone-500">
            Pronto. Geramos o resumo da safra e o passo-a-passo dos manejos — e você poderá ajustar
            qualquer coisa no Laboratório depois.
          </p>
          <div className="flex justify-between">
            <button onClick={() => setStep(2)} className="text-sm text-stone-500">
              ← voltar
            </button>
            <button onClick={finish} className="rounded-md bg-leaf px-5 py-2 text-sm font-semibold text-white hover:bg-leafdark">
              Ver minha safra →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
