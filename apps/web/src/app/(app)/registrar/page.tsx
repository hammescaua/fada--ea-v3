"use client";

import { useScenario } from "@/lib/store";
import { PageHeader } from "@/components/PageHeader";
import { RegisterEvent } from "@/components/RegisterEvent";
import type { OperationIn } from "@/lib/types";

export default function RegistrarPage() {
  const { scenario, setScenario } = useScenario();

  const registerOp = (op: OperationIn) =>
    setScenario((s) => ({ ...s, operations: [...s.operations, op] }));

  const n = scenario.operations.length;

  return (
    <div className="space-y-8">
      <PageHeader title="Registrar evento" subtitle="conte o que aconteceu no campo — leva segundos" />

      <RegisterEvent today={new Date().toISOString().slice(0, 10)} onRegister={registerOp} />

      {n > 0 && (
        <p className="text-center text-xs text-stone-400">
          {n} {n === 1 ? "manejo registrado" : "manejos registrados"} nesta safra · aparecem no Calendário e já entram na previsão.
        </p>
      )}
    </div>
  );
}
