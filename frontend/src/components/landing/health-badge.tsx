"use client";

import { useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { AsyncStateView } from "@/components/common/async-state-view";
import { getHealth } from "@/lib/api";
import { useAsync } from "@/hooks/use-async";
import type { HealthResponse } from "@/types/api";

export function HealthBadge() {
  const health = useAsync<HealthResponse>();

  useEffect(() => {
    health.run(() => getHealth());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AsyncStateView
      state={health}
      loadingMessage="Checking API…"
      onRetry={() => health.run(() => getHealth())}
    >
      {(data) => (
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
            API {data.status}
          </Badge>
          <Badge variant="secondary" className="bg-muted/50">
            Whisper: {data.whisper_model}
          </Badge>
          {data.ollama_enabled && (
            <Badge variant="secondary">Ollama enabled</Badge>
          )}
        </div>
      )}
    </AsyncStateView>
  );
}
