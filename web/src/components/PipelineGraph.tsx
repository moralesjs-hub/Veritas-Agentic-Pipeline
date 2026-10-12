"use client";

import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  Position, // <-- Add Position import
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface PipelineGraphProps {
  completedNodes: string[];
  activeNode: string | null;
}

export function PipelineGraph({ completedNodes, activeNode }: PipelineGraphProps) {
  const nodes: Node[] = useMemo(() => {
    const rawNodes = [
      { id: "researcher", label: "Researcher Node", sub: "Information Gathering" },
      { id: "drafter", label: "Drafter Node", sub: "Report Synthesis" },
      { id: "verifier", label: "Verifier Node", sub: "Factuality Check" },
    ];

    return rawNodes.map((item, index) => {
      const isCompleted = completedNodes.includes(item.id);
      const isActive = activeNode === item.id;

      let borderClass = "border-slate-800 bg-slate-900/90 text-slate-400";
      if (isActive) {
        borderClass = "border-blue-500 bg-blue-950/80 text-blue-200 animate-pulse ring-2 ring-blue-500/50";
      } else if (isCompleted) {
        borderClass = "border-emerald-500 bg-emerald-950/40 text-emerald-300";
      }

      return {
        id: item.id,
        position: { x: index * 260 + 20, y: 50 },
        draggable: false,
        sourcePosition: Position.Right, // <-- Connect out from the right
        targetPosition: Position.Left,  // <-- Connect into the left
        style: { background: "transparent", border: "none", padding: 0 },
        data: {
          label: (
            <div className={`px-4 py-3 rounded-lg border font-mono text-left transition-all ${borderClass}`}>
              <div className="text-xs uppercase tracking-wider font-bold">{item.label}</div>
              <div className="text-[10px] opacity-70 mt-0.5">{item.sub}</div>
              <div className="text-[9px] mt-2 font-semibold">
                {isActive ? "RUNNING" : isCompleted ? "COMPLETED" : "IDLE"}
              </div>
            </div>
          ),
        },
      };
    });
  }, [completedNodes, activeNode]);

  const edges: Edge[] = useMemo(() => [
    {
      id: "e-researcher-drafter",
      source: "researcher",
      target: "drafter",
      animated: activeNode === "researcher" || activeNode === "drafter",
      style: { stroke: completedNodes.includes("drafter") ? "#10b981" : "#475569", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed },
    },
    {
      id: "e-drafter-verifier",
      source: "drafter",
      target: "verifier",
      animated: activeNode === "drafter" || activeNode === "verifier",
      style: { stroke: completedNodes.includes("verifier") ? "#10b981" : "#475569", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed },
    },
  ], [completedNodes, activeNode]);

  return (
    <div className="w-full h-44 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1e293b" gap={16} size={1} />
        <Controls showInteractive={false} className="bg-slate-900 border-slate-800 text-slate-300" />
      </ReactFlow>
    </div>
  );
}