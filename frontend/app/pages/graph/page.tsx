"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Dynamically import the graph to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });

  useEffect(() => {
    const fetchGraph = async () => {
      const res = await fetch("/api/graph");
      const data = await res.json();
      setGraphData(data);
    };

    fetchGraph();
  }, []);

  return (
    <div className="w-full h-screen">
      <ForceGraph2D
        graphData={graphData}
        nodeLabel={(node: any) => `${node.label}: ${node.properties?.name || node.properties?.headline || ""}`}
        nodeAutoColorBy="label"
        linkLabel={(link: any) => link.label}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
      />
    </div>
  );
}
