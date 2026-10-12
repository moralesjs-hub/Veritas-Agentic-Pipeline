"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

interface Trace {
  node_name: string;
  latency_ms: number;
  payload: any;
}

const API_BASE = "http://127.0.0.1:8000";

export default function VeritasDashboard() {
  const [topic, setTopic] = useState("Hierarchical Memory in Autonomous Agents");
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState("IDLE");
  const [output, setOutput] = useState("");
  const [verifierScore, setVerifierScore] = useState<number | null>(null);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const startRun = async () => {
    setStatus("STARTING");
    setOutput("");
    setVerifierScore(null);
    setTraces([]);
    setErrorMessage(null);

    try {
      const res = await fetch(`${API_BASE}/api/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      setRunId(data.id);
      setStatus("RUNNING");
    } catch (err: any) {
      console.error("Execution request failed:", err);
      setStatus("FAILED");
      setErrorMessage(
        `Unable to reach backend gateway at ${API_BASE}. Ensure Uvicorn is running on port 8000.`
      );
    }
  };

  const handleApprove = async () => {
    if (!runId) return;
    setStatus("RUNNING");
    try {
      await fetch(`${API_BASE}/api/runs/${runId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "APPROVE" }),
      });
    } catch (err) {
      console.error("Approve failed:", err);
    }
  };

  const handleReject = async () => {
    if (!runId) return;
    const feedback = prompt(
      "Enter revision critique for the Drafter node:",
      "Deepen trade-offs between dynamic eviction thresholds and prompt context fidelity."
    );
    if (feedback === null) return;

    setStatus("RUNNING");
    try {
      await fetch(`${API_BASE}/api/runs/${runId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "REJECT", critique: feedback }),
      });
    } catch (err) {
      console.error("Reject failed:", err);
    }
  };

  const copyMarkdown = () => {
    navigator.clipboard.writeText(output);
  };

  const downloadMarkdown = () => {
    const blob = new Blob([output], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `veritas-${runId?.slice(0, 8) || "report"}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (!runId) return;

    const es = new EventSource(`${API_BASE}/api/runs/${runId}/stream`);
    eventSourceRef.current = es;

    es.addEventListener("node_trace", (event) => {
      try {
        const data = JSON.parse(event.data);
        setTraces((prev) => [...prev, data]);
      } catch (e) {
        console.error("Trace parse error:", e);
      }
    });

    es.addEventListener("status", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status) setStatus(data.status);
        if (data.final_output) setOutput(data.final_output);
        if (data.verifier_score !== null && data.verifier_score !== undefined) {
          setVerifierScore(data.verifier_score);
        }
      } catch (e) {
        console.error("Status parse error:", e);
      }
    });

    es.addEventListener("complete", (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.status) setStatus(data.status);
        if (data.final_output) setOutput(data.final_output);
        if (data.verifier_score !== null && data.verifier_score !== undefined) {
          setVerifierScore(data.verifier_score);
        }
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          es.close();
        }
      } catch (e) {
        console.error("Complete parse error:", e);
      }
    });

    const poller = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/runs/${runId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.status) setStatus(data.status);
        if (data.final_output) setOutput(data.final_output);
        if (data.verifier_score !== null && data.verifier_score !== undefined) {
          setVerifierScore(data.verifier_score);
        }
        if (data.status === "COMPLETED" || data.status === "FAILED") {
          clearInterval(poller);
        }
      } catch (e) {
        console.error("Poller error:", e);
      }
    }, 2000);

    return () => {
      es.close();
      clearInterval(poller);
    };
  }, [runId]);

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans">
      <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-[#0b1120]">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <h1 className="text-xs font-mono tracking-wider font-bold text-cyan-400">
              VERITAS // CONTROL PLANE
            </h1>
          </div>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-96 px-3 py-1 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={startRun}
            className="px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded tracking-wider transition-colors"
          >
            EXECUTE
          </button>
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-900 border border-slate-800 rounded">
            <span className="text-[10px] font-mono text-slate-400">VERIFIER</span>
            <span className="text-xs font-mono font-bold text-emerald-400">
              {verifierScore !== null ? verifierScore.toFixed(2) : "--"}
            </span>
          </div>
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
              status === "COMPLETED"
                ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                : status === "WAITING_FOR_REVIEW"
                ? "bg-amber-950 text-amber-400 border border-amber-800"
                : status === "RUNNING"
                ? "bg-cyan-950 text-cyan-400 border border-cyan-800"
                : status === "FAILED"
                ? "bg-rose-950 text-rose-400 border border-rose-800"
                : "bg-slate-800 text-slate-400"
            }`}
          >
            {status}
          </span>
        </div>
      </header>

      {errorMessage && (
        <div className="px-6 py-2 bg-rose-950/60 border-b border-rose-800/80 text-rose-300 text-xs font-mono flex justify-between items-center">
          <span>{errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-white ml-4 font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        <section className="col-span-8 border-r border-slate-800 flex flex-col bg-[#080d1a]">
          <div className="h-10 border-b border-slate-800/80 px-6 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>SYNTHESIS WORKSPACE</span>
            <div className="flex items-center gap-3">
              <span>{output.length} characters</span>
              {output && (
                <>
                  <button
                    onClick={copyMarkdown}
                    className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px]"
                  >
                    Copy
                  </button>
                  <button
                    onClick={downloadMarkdown}
                    className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 text-[11px]"
                  >
                    Export .md
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="flex-1 p-8 overflow-y-auto">
            {output ? (
              <article className="prose prose-invert max-w-none prose-headings:font-bold prose-headings:text-slate-100 prose-h1:text-2xl prose-h2:text-lg prose-p:text-slate-300 prose-li:text-slate-300">
                <ReactMarkdown>{output}</ReactMarkdown>
              </article>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-600 font-mono text-xs">
                Awaiting pipeline execution payload...
              </div>
            )}
          </div>

          {status === "WAITING_FOR_REVIEW" && (
            <div className="h-14 border-t border-amber-500/30 bg-amber-950/20 px-6 flex items-center justify-between">
              <span className="text-xs font-mono text-amber-400">
                Gate: Human-in-the-loop verification required.
              </span>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReject}
                  className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded transition-colors"
                >
                  Reject / Revise
                </button>
                <button
                  onClick={handleApprove}
                  className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded transition-colors"
                >
                  Approve & Verify
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="col-span-4 flex flex-col bg-[#060913]">
          <div className="p-4 border-b border-slate-800">
            <h2 className="text-[11px] font-mono tracking-wider text-slate-400 uppercase mb-3">
              Execution Graph
            </h2>
            <div className="space-y-2">
              {[
                { id: "researcher", code: "01 // RESEARCHER", sub: "Web Grounding" },
                { id: "drafter", code: "02 // DRAFTER", sub: "Synthesis Drafting" },
                { id: "verifier", code: "03 // VERIFIER", sub: "Factuality Check" },
              ].map((node) => {
                const trace = traces.find((t) => t.node_name === node.id);
                return (
                  <div
                    key={node.id}
                    className={`p-2.5 rounded border flex items-center justify-between ${
                      trace
                        ? "bg-slate-900/80 border-slate-700"
                        : "bg-slate-950/40 border-slate-800/60 opacity-60"
                    }`}
                  >
                    <div>
                      <div className="text-xs font-mono font-bold text-cyan-400">{node.code}</div>
                      <div className="text-[11px] text-slate-400">{node.sub}</div>
                    </div>
                    {trace && (
                      <span className="text-xs font-mono text-emerald-400">{trace.latency_ms}ms</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="h-8 px-4 flex items-center justify-between border-b border-slate-800 text-[11px] font-mono text-slate-400">
              <span>TELEMETRY FEED</span>
              <span>{traces.length} EVENTS</span>
            </div>
            <div className="flex-1 p-3 overflow-y-auto space-y-2 font-mono text-[11px]">
              {traces.map((t, idx) => (
                <div key={idx} className="p-2 bg-slate-900/60 rounded border border-slate-800 text-slate-300">
                  <div className="flex justify-between text-cyan-400 font-bold mb-1">
                    <span>{t.node_name}</span>
                    <span className="text-slate-400">{t.latency_ms} ms</span>
                  </div>
                  <pre className="text-[10px] text-slate-400 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(t.payload, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}