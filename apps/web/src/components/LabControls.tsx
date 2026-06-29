"use client";

import type { ScenarioIn } from "@/lib/types";

interface Props {
  scenario: ScenarioIn;
  municipalities: string[];
  onChange: (next: ScenarioIn) => void;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs">
      <span className="font-medium text-stone-600">{label}</span>
      {children}
    </label>
  );
}

const input =
  "rounded-md border border-stone-300 px-2 py-1 text-sm focus:border-leaf focus:outline-none";

export function LabControls({ scenario, municipalities, onChange }: Props) {
  const s = scenario;
  const set = (patch: Partial<ScenarioIn>) => onChange({ ...s, ...patch });
  const setSoil = (patch: Partial<ScenarioIn["soil"]>) =>
    onChange({ ...s, soil: { ...s.soil, ...patch } });
  const setCultivar = (patch: Partial<ScenarioIn["cultivar"]>) =>
    onChange({ ...s, cultivar: { ...s.cultivar, ...patch } });

  const fungicidas = s.operations.filter((o) => o.kind === "fungicida").length;
  const setFungicidas = (n: number) => {
    const others = s.operations.filter((o) => o.kind !== "fungicida");
    const fung = Array.from({ length: n }, (_, i) => ({
      kind: "fungicida",
      op_date: `2026-01-${String(10 + i * 14).padStart(2, "0")}`,
      cost_per_ha: 180,
      quality: 0.9,
    }));
    set({ operations: [...others, ...fung] });
  };

  return (
    <div className="space-y-4">
      <section>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">
          Plantio
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Data de semeadura">
            <input
              type="date"
              className={input}
              value={s.sowing_date}
              onChange={(e) => set({ sowing_date: e.target.value })}
            />
          </Field>
          <Field label="Município">
            <select
              className={input}
              value={s.municipality}
              onChange={(e) => set({ municipality: e.target.value })}
            >
              {municipalities.map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </Field>
          <Field label={`População (${s.population_k_per_ha.toFixed(0)} mil/ha)`}>
            <input
              type="range"
              min={180}
              max={420}
              step={10}
              value={s.population_k_per_ha}
              onChange={(e) => set({ population_k_per_ha: Number(e.target.value) })}
            />
          </Field>
          <Field label="Preço (R$/saca)">
            <input
              type="number"
              className={input}
              value={s.soybean_price_per_sc}
              onChange={(e) => set({ soybean_price_per_sc: Number(e.target.value) })}
            />
          </Field>
        </div>
      </section>

      <section>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">
          Cultivar
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <Field label={`Grupo maturação (${s.cultivar.maturity_group.toFixed(1)})`}>
            <input
              type="range"
              min={4.8}
              max={7}
              step={0.1}
              value={s.cultivar.maturity_group}
              onChange={(e) => setCultivar({ maturity_group: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Potencial (${s.cultivar.base_potential_sc_ha} sc/ha)`}>
            <input
              type="range"
              min={70}
              max={110}
              step={1}
              value={s.cultivar.base_potential_sc_ha}
              onChange={(e) => setCultivar({ base_potential_sc_ha: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Tolerância a doenças (${(s.cultivar.disease_tolerance * 100).toFixed(0)}%)`}>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={s.cultivar.disease_tolerance}
              onChange={(e) => setCultivar({ disease_tolerance: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Resistência a nematoides (${((s.cultivar.nematode_tolerance ?? 0.5) * 100).toFixed(0)}%)`}>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={s.cultivar.nematode_tolerance ?? 0.5}
              onChange={(e) => setCultivar({ nematode_tolerance: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Aplicações de fungicida (${fungicidas})`}>
            <input
              type="range"
              min={0}
              max={4}
              step={1}
              value={fungicidas}
              onChange={(e) => setFungicidas(Number(e.target.value))}
            />
          </Field>
        </div>
      </section>

      <section>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-400">
          Solo do talhão
        </h4>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Textura">
            <select
              className={input}
              value={s.soil.texture}
              onChange={(e) => setSoil({ texture: e.target.value })}
            >
              <option value="arenoso">Arenoso</option>
              <option value="medio">Médio</option>
              <option value="argiloso">Argiloso</option>
            </select>
          </Field>
          <Field label="Compactação">
            <select
              className={input}
              value={s.soil.compaction}
              onChange={(e) => setSoil({ compaction: e.target.value })}
            >
              <option value="nenhuma">Nenhuma</option>
              <option value="leve">Leve</option>
              <option value="moderada">Moderada</option>
              <option value="severa">Severa</option>
            </select>
          </Field>
          <Field label="Nematoides (pressão)">
            <select
              className={input}
              value={s.nematode_pressure ?? "nenhuma"}
              onChange={(e) => set({ nematode_pressure: e.target.value as ScenarioIn["nematode_pressure"] })}
            >
              <option value="nenhuma">Nenhuma / não sei</option>
              <option value="baixa">Baixa</option>
              <option value="media">Média</option>
              <option value="alta">Alta (reboleiras)</option>
            </select>
          </Field>
          <Field label="Cultura anterior (rotação)">
            <select
              className={input}
              value={s.previous_crop ?? "soja"}
              onChange={(e) => set({ previous_crop: e.target.value as ScenarioIn["previous_crop"] })}
            >
              <option value="soja">Soja (monocultura)</option>
              <option value="milho">Milho</option>
              <option value="trigo">Trigo</option>
              <option value="cobertura">Cobertura (aveia/nabo/ervilhaca)</option>
              <option value="pousio">Pousio</option>
            </select>
          </Field>
          <Field label={`pH (${s.soil.ph.toFixed(1)})`}>
            <input
              type="range"
              min={4.5}
              max={7}
              step={0.1}
              value={s.soil.ph}
              onChange={(e) => setSoil({ ph: Number(e.target.value) })}
            />
          </Field>
          <Field label={`V% (${s.soil.base_saturation_pct.toFixed(0)})`}>
            <input
              type="range"
              min={30}
              max={80}
              step={1}
              value={s.soil.base_saturation_pct}
              onChange={(e) => setSoil({ base_saturation_pct: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Fósforo (${s.soil.phosphorus_ppm.toFixed(0)} ppm)`}>
            <input
              type="range"
              min={3}
              max={30}
              step={1}
              value={s.soil.phosphorus_ppm}
              onChange={(e) => setSoil({ phosphorus_ppm: Number(e.target.value) })}
            />
          </Field>
          <Field label={`Potássio (${s.soil.potassium_ppm.toFixed(0)} ppm)`}>
            <input
              type="range"
              min={40}
              max={250}
              step={5}
              value={s.soil.potassium_ppm}
              onChange={(e) => setSoil({ potassium_ppm: Number(e.target.value) })}
            />
          </Field>
        </div>
      </section>

      <label className="flex items-center gap-2 text-xs text-stone-600">
        <input
          type="checkbox"
          checked={s.use_live_weather}
          onChange={(e) => set({ use_live_weather: e.target.checked })}
        />
        Usar clima histórico real (Open-Meteo) — mais lento, porém calcula o déficit
        hídrico observado.
      </label>
    </div>
  );
}
