"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

interface Props {
  scenario: ScenarioIn;
  onLoadField: (patch: Partial<ScenarioIn>) => void;
}

// Persistência simples da seleção (sem auth no Marco atual).
const FARM_KEY = "fada.farmId";
const FIELD_KEY = "fada.fieldId";

export function FarmManager({ scenario, onLoadField }: Props) {
  const qc = useQueryClient();
  const [farmId, setFarmId] = useState<string | null>(null);
  const [fieldId, setFieldId] = useState<string | null>(null);
  const [newFarm, setNewFarm] = useState("");
  const [newField, setNewField] = useState("");
  const [cropYear, setCropYear] = useState("2025/26");

  useEffect(() => {
    setFarmId(localStorage.getItem(FARM_KEY));
    setFieldId(localStorage.getItem(FIELD_KEY));
  }, []);
  const selectFarm = (id: string | null) => {
    setFarmId(id);
    id ? localStorage.setItem(FARM_KEY, id) : localStorage.removeItem(FARM_KEY);
  };
  const selectField = (id: string | null) => {
    setFieldId(id);
    id ? localStorage.setItem(FIELD_KEY, id) : localStorage.removeItem(FIELD_KEY);
  };

  const farms = useQuery({ queryKey: ["farms"], queryFn: api.farms, retry: false });
  const fields = useQuery({
    queryKey: ["fields", farmId],
    queryFn: () => api.fields(farmId!),
    enabled: !!farmId,
    retry: false,
  });
  const soils = useQuery({
    queryKey: ["soils", fieldId],
    queryFn: () => api.soilTests(fieldId!),
    enabled: !!fieldId,
    retry: false,
  });
  const seasons = useQuery({
    queryKey: ["fieldSeasons", fieldId],
    queryFn: () => api.fieldSeasons(fieldId!),
    enabled: !!fieldId,
    retry: false,
  });

  const offline = farms.isError;

  const createFarm = useMutation({
    mutationFn: () => api.createFarm(newFarm.trim(), scenario.municipality),
    onSuccess: (f) => {
      setNewFarm("");
      selectFarm(f.id);
      qc.invalidateQueries({ queryKey: ["farms"] });
    },
  });

  const createField = useMutation({
    mutationFn: () =>
      api.createField(farmId!, {
        name: newField.trim(),
        municipality: scenario.municipality,
        centroid_lat: scenario.latitude,
        centroid_lon: scenario.longitude,
      }),
    onSuccess: (f) => {
      setNewField("");
      selectField(f.id);
      qc.invalidateQueries({ queryKey: ["fields", farmId] });
    },
  });

  const saveSoil = useMutation({
    mutationFn: () =>
      api.createSoilTest(fieldId!, {
        ph: scenario.soil.ph,
        phosphorus_ppm: scenario.soil.phosphorus_ppm,
        potassium_ppm: scenario.soil.potassium_ppm,
        base_saturation_pct: scenario.soil.base_saturation_pct,
        clay_pct: scenario.soil.clay_pct,
        organic_matter_pct: scenario.soil.organic_matter_pct,
        cec: scenario.soil.cec,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["soils", fieldId] }),
  });

  const saveSeason = useMutation({
    mutationFn: () => api.recordSeason(fieldId!, cropYear, scenario),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["fieldSeasons", fieldId] }),
  });

  // Carrega um talhão no laboratório: município, localização e solo salvo mais recente.
  const loadField = (id: string) => {
    selectField(id);
    const field = fields.data?.find((f) => f.id === id);
    const patch: Partial<ScenarioIn> = {};
    if (field) {
      patch.municipality = field.municipality;
      if (field.centroid_lat != null) patch.latitude = field.centroid_lat;
      if (field.centroid_lon != null) patch.longitude = field.centroid_lon;
    }
    api
      .soilTests(id)
      .then((tests) => {
        const s = tests[0];
        if (s) {
          patch.soil = {
            ...scenario.soil,
            ph: s.ph ?? scenario.soil.ph,
            phosphorus_ppm: s.phosphorus_ppm ?? scenario.soil.phosphorus_ppm,
            potassium_ppm: s.potassium_ppm ?? scenario.soil.potassium_ppm,
            base_saturation_pct: s.base_saturation_pct ?? scenario.soil.base_saturation_pct,
            clay_pct: s.clay_pct ?? scenario.soil.clay_pct,
            organic_matter_pct: s.organic_matter_pct ?? scenario.soil.organic_matter_pct,
            cec: s.cec ?? scenario.soil.cec,
          };
        }
      })
      .finally(() => onLoadField(patch));
  };

  const input = "rounded-md border border-stone-300 px-2 py-1 text-sm";
  const btn = "rounded-md bg-leaf px-2.5 py-1 text-xs font-medium text-white hover:bg-leafdark disabled:opacity-50";

  if (offline) {
    return (
      <div className="rounded-lg bg-amber-50 p-2 text-xs text-amber-700">
        Modo laboratório (sem persistência). Suba a API + PostGIS (<code>make db-up</code>,{" "}
        <code>make migrate</code>, <code>make api</code>) para salvar fazendas e talhões.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-stone-600">🗺️ Minha fazenda</h3>

      {/* Fazenda */}
      <div className="flex flex-wrap items-center gap-2">
        <select
          className={input}
          value={farmId ?? ""}
          onChange={(e) => {
            selectFarm(e.target.value || null);
            selectField(null);
          }}
        >
          <option value="">— escolher fazenda —</option>
          {farms.data?.map((f) => (
            <option key={f.id} value={f.id}>
              {f.name} ({f.municipality})
            </option>
          ))}
        </select>
        <input
          className={`${input} w-32`}
          placeholder="nova fazenda"
          value={newFarm}
          onChange={(e) => setNewFarm(e.target.value)}
        />
        <button className={btn} disabled={!newFarm.trim() || createFarm.isPending} onClick={() => createFarm.mutate()}>
          + fazenda
        </button>
      </div>

      {/* Talhões */}
      {farmId && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1.5">
            {fields.data?.map((f) => (
              <button
                key={f.id}
                onClick={() => loadField(f.id)}
                className={`rounded-md border px-2 py-1 text-xs ${
                  f.id === fieldId ? "border-leaf bg-green-50 text-leafdark" : "border-stone-200 text-stone-600"
                }`}
              >
                {f.name}
                {f.area_ha ? ` · ${f.area_ha.toFixed(0)} ha` : ""}
              </button>
            ))}
            {fields.data?.length === 0 && <span className="text-xs text-stone-400">sem talhões ainda</span>}
          </div>
          <div className="flex items-center gap-2">
            <input
              className={`${input} w-36`}
              placeholder="novo talhão"
              value={newField}
              onChange={(e) => setNewField(e.target.value)}
            />
            <button
              className={btn}
              disabled={!newField.trim() || createField.isPending}
              onClick={() => createField.mutate()}
            >
              + talhão (usa o ponto do mapa)
            </button>
          </div>
        </div>
      )}

      {/* Ações do talhão selecionado */}
      {fieldId && (
        <div className="space-y-2 rounded-lg bg-stone-50 p-2">
          <div className="flex flex-wrap items-center gap-2">
            <button className={btn} disabled={saveSoil.isPending} onClick={() => saveSoil.mutate()}>
              Salvar análise de solo
            </button>
            <input
              className={`${input} w-24`}
              value={cropYear}
              onChange={(e) => setCropYear(e.target.value)}
            />
            <button className={btn} disabled={saveSeason.isPending} onClick={() => saveSeason.mutate()}>
              Salvar safra (cenário atual)
            </button>
          </div>

          {soils.data && soils.data.length > 0 && (
            <p className="text-[11px] text-stone-500">
              {soils.data.length} análise(s) de solo · última: pH {soils.data[0].ph ?? "—"}, P{" "}
              {soils.data[0].phosphorus_ppm ?? "—"} ppm
            </p>
          )}

          {seasons.data && seasons.data.length > 0 && (
            <div>
              <div className="text-[11px] font-medium text-stone-500">Histórico de safras</div>
              <ul className="mt-1 space-y-0.5 text-[11px] text-stone-600">
                {seasons.data.map((s) => (
                  <li key={s.id} className="flex justify-between">
                    <span>{s.crop_year}</span>
                    <span>
                      previsto {s.predicted_yield_sc_ha?.toFixed(0) ?? "—"} sc/ha
                      {s.actual_yield_sc_ha != null && ` · colhido ${s.actual_yield_sc_ha.toFixed(0)}`}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
