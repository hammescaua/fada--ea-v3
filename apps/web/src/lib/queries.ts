"use client";

import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ScenarioIn } from "@/lib/types";

/** Hooks de dados com chaves consistentes: várias páginas podem pedir o mesmo
 *  sem duplicar rede (o React Query deduplica pela chave). Cada página só chama
 *  o que precisa. */

const keep = { placeholderData: keepPreviousData } as const;

export const useSim = (s: ScenarioIn, enabled = true) =>
  useQuery({ queryKey: ["simulate", s], queryFn: () => api.simulate(s), enabled, ...keep });

export const useRadar = (s: ScenarioIn, enabled = true) =>
  useQuery({ queryKey: ["radar", s], queryFn: () => api.radar(s), enabled, ...keep });

export const useBriefing = (s: ScenarioIn, prov: Record<string, string>, enabled = true) =>
  useQuery({ queryKey: ["briefing", s, prov], queryFn: () => api.briefing(s, prov), enabled, ...keep });

export const useAccuracy = (s: ScenarioIn, prov: Record<string, string>, enabled = true) =>
  useQuery({ queryKey: ["accuracy", s, prov], queryFn: () => api.accuracy(s, prov), enabled, ...keep });

export const useCropPlan = (s: ScenarioIn, prov: Record<string, string>, enabled = true) =>
  useQuery({ queryKey: ["crop-plan", s, prov], queryFn: () => api.cropPlan(s, prov), enabled, ...keep });

export const useSeasonPlan = (s: ScenarioIn, enabled = true) =>
  useQuery({ queryKey: ["season-plan", s], queryFn: () => api.seasonPlan(s), enabled, ...keep });

export const useFertility = (s: ScenarioIn, enabled = true) =>
  useQuery({ queryKey: ["fertility", s], queryFn: () => api.fertility(s), enabled, ...keep });

export const useDecisions = (s: ScenarioIn, enabled = true) =>
  useQuery({ queryKey: ["decisions", s], queryFn: () => api.decisions(s), enabled, ...keep });

export const useMunicipalities = () =>
  useQuery({ queryKey: ["municipalities"], queryFn: api.municipalities });
