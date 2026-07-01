"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ScenarioProvider } from "@/lib/store";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      <ScenarioProvider>{children}</ScenarioProvider>
    </QueryClientProvider>
  );
}
