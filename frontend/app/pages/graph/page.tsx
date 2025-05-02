"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";

// Swap 3D for 2D version
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphPage2D() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; relations: any[], nodesUpdated: boolean }>({
    nodes: [],
    relations: [],
    nodesUpdated: false,
  });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [keywords, setKeywords] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const graphRef = useRef<any>(null);

  const fetchGraph = async () => {
    setIsLoading(true);
    setError("");
    if ((startDate && !endDate) || (!startDate && endDate)) {
      setError("Please provide both start and end dates.");
      setIsLoading(false);
      return;
    }

    if (startDate && endDate) {
      const start = new Date(startDate);
      const end = new Date(endDate);
      const diffTime = Math.abs(end.getTime() - start.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > 14) {
        setError("Date range cannot exceed two weeks.");
        setIsLoading(false);
        return;
      }
    }

    const params = new URLSearchParams();
    if (startDate) params.append("startDate", startDate);
    if (endDate) params.append("endDate", endDate);
    if (keywords.trim()) params.append("keywords", keywords.trim());

    try {
      const res = await fetch(`/api/graph?${params}`);
      const json = await res.json();
      if (Array.isArray(json.nodes) && Array.isArray(json.relations)) {
        setGraphData({ ...json, nodesUpdated: false });
      } else {
        setError("Malformed graph data from server.");
      }
    } catch {
      setError("Error fetching graph data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  useEffect(() => {
    if (graphData.nodesUpdated) {
      setGraphData(prevData => ({ ...prevData, nodesUpdated: false }));
    }
  }, [graphData.nodesUpdated]);

  const getNodeLabel = (n: any) => {
    const p = n.properties;
    switch (n.label) {
      case "News":
        return `News: ${p.headline}\nDate: ${p.date}\nLink: ${p.link}\nSentiment: ${p.headline_sentiment}`;
      case "Article":
        return `Article: ${p.headline}\nDate: ${p.date}\nLink: ${p.link}`;
      case "OilPrice":
        return `Oil on ${p.date}\nWTI Δ%: ${p.CL_F_Daily_Change}\nBrent Δ%: ${p.BZ_F_Daily_Change}`;
      default:
        return `${n.label}: ${p.name || ""}`;
    }
  };

  const getNodeColor = (n: any) => ({
    News: "blue",
    Article: "purple",
    OilPrice: "white",
    Location: "yellow",
    Organization: "green",
    Person: "red",
    Event: "#73c6b6",
    Topic: "hotpink",
  }[n.label] || "gray");

  const handleNodeClick = (node: any) => {
    // For 2D, use pan/zoom to center node (optional)
    const context = graphRef.current;
    if (context && node.x && node.y) {
      context.centerAt(node.x, node.y, 1000);
      context.zoom(12, 1000);
    }
  };

  return (
    <div className="w-full h-screen flex flex-col">
      {error && <div className="p-2 text-red-400">{error}</div>}
      {isLoading && <div className="p-2 text-gray-400">Loading...</div>}

      <div className="flex-1 relative">
        {/* Floating Filters */}
        <div className="absolute top-4 left-4 bg-gray-900 bg-opacity-80 p-4 rounded-lg shadow-lg text-white flex flex-wrap gap-4 z-10">
          <div>
            <label className="text-sm">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="ml-2 p-1 rounded text-black"
            />
          </div>
          <div>
            <label className="text-sm">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="ml-2 p-1 rounded text-black"
            />
          </div>
          <div>
            <label className="text-sm">Keywords</label>
            <input
              type="text"
              placeholder="e.g. oil, inflation"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              className="ml-2 p-1 rounded text-black"
            />
          </div>
          <button
            onClick={fetchGraph}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
          >
            Apply Filter
          </button>
        </div>

        {/* Graph */}
        {graphData.nodes.length ? (
          <ForceGraph2D
            ref={graphRef}
            graphData={{ nodes: graphData.nodes, links: graphData.relations }}
            nodeLabel={getNodeLabel}
            nodeColor={getNodeColor}
            linkLabel={l => l.label}
            linkDirectionalArrowLength={5}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            // Set color for links
            linkColor={() => "rgba(255, 255, 255, 0.06)"}
          />
        ) : (
          !isLoading && <div className="text-center mt-8 text-gray-500">No data to display.</div>
        )}
      </div>
    </div>
  );
}
