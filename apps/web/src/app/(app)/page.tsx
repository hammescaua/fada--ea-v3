"use client";

import { useRouter } from "next/navigation";
import { useScenario } from "@/lib/store";
import { useRadar } from "@/lib/queries";
import { HomeOverview } from "@/components/HomeOverview";

export default function MinhaSafraPage() {
  const router = useRouter();
  const { scenario, debounced, soilReal } = useScenario();
  const { data: radar, isFetching } = useRadar(debounced);

  return (
    <HomeOverview
      radar={radar}
      scenario={scenario}
      soilReal={soilReal}
      loading={isFetching}
      onSeeDetails={() => router.push("/talhao")}
    />
  );
}
