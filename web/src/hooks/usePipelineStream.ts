"use client";

import { useState, useEffect, useRef } from "react";

export interface NodeTraceEvent {
  node_name: string;
  latency_ms: number;
  output: Record<string, any>;
}

export interface StreamState {
  status: "IDLE" | "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  verifierScore: number | null;
  traces: NodeTraceEvent[];
  finalOutput: string | null;
  errorMessage: string | null;
}

export function usePipelineStream(runId: string | null) {
  const [streamState, setStreamState] = useState<StreamState>({
    status: "IDLE",
    verifierScore: null,
    traces: [],
    finalOutput: null,
    errorMessage: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!runId) return;

    setStreamState({
      status: "PENDING",
      verifierScore: null,
      traces: [],
      finalOutput: null,
      errorMessage: null,
    });

    const es = new EventSource(`http://localhost:8000/api/runs/${runId}/stream`);
    eventSourceRef.current = es;

    es.addEventListener("status", (event: MessageEvent) => {
  const data = JSON.parse(event.data);
  setStreamState((prev) => ({
    ...prev,
    status: data.status,
    verifierScore: data.verifier_score ?? prev.verifierScore,
    finalOutput: data.final_output ?? prev.finalOutput, // preserve intermediate draft
  }));
});

    es.addEventListener("node_trace", (event: MessageEvent) => {
      const data: NodeTraceEvent = JSON.parse(event.data);
      setStreamState((prev) => ({
        ...prev,
        traces: [...prev.traces, data],
      }));
    });

    es.addEventListener("complete", (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      setStreamState((prev) => ({
        ...prev,
        status: data.status,
        verifierScore: data.verifier_score,
        finalOutput: data.final_output,
        errorMessage: data.error_message,
      }));
      es.close();
    });

    es.addEventListener("error", () => {
      es.close();
    });

    return () => {
      es.close();
    };
  }, [runId]);

  return streamState;
}