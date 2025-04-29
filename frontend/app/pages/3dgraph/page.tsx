"use client";
 
import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
 
// Import the 3D graph
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });
 
export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; relations: any[] }>({
    nodes: [],
    relations: [],
  });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
 
  const graphRef = useRef<any>(null);
 
  const fetchGraph = async () => {
    setIsLoading(true);
    setError("");
 
    if (!startDate || !endDate) {
      setError("Please provide both start and end dates.");
      setIsLoading(false);
      return;
    }
 
    const queryParams = new URLSearchParams();
    queryParams.append("startDate", startDate);
    queryParams.append("endDate", endDate);
 
    try {
      const res = await fetch(`/api/graph?${queryParams.toString()}`);
      const data = await res.json();
 
      if (data && Array.isArray(data.nodes) && Array.isArray(data.relations)) {
        console.log("Fetched graph data:", data);
        setGraphData(data);
      } else {
        console.error("Malformed graph data:", data);
        setError("Malformed graph data received from the server.");
        setGraphData({ nodes: [], relations: [] });
      }
    } catch (error) {
      console.error("Error fetching graph data:", error);
      setGraphData({ nodes: [], relations: [] });
    } finally {
      setIsLoading(false);
    }
  };
 
  useEffect(() => {
    if (startDate && endDate) {
      fetchGraph();
    }
  }, [startDate, endDate]);
 
  // 🌍 Auto-Rotate the Graph
  useEffect(() => {
    const interval = setInterval(() => {
      if (!graphRef.current) return;
      const camera = graphRef.current.camera();
      const distance = 300;
      const angle = Date.now() * 0.0001;
      camera.position.x = distance * Math.sin(angle);
      camera.position.z = distance * Math.cos(angle);
      camera.lookAt(0, 0, 0);
    }, 50);
 
    return () => clearInterval(interval);
  }, []);
 
  // Node Label Formatter
  const getNodeLabel = (node: any) => {
    const { label, properties } = node;
 
    switch (label) {
      case "News":
        return `News: ${properties?.headline || ""}\nDate: ${properties?.date || ""}\nLink: ${properties?.link || ""}\nSentiment: ${properties?.headline_sentiment || ""}`;
      case "Article":
        return `Article: ${properties?.headline || ""}\nDate: ${properties?.date || ""}\nLink: ${properties?.link || ""}`;
      case "OilPrice":
        return `OilPrice: ${properties?.date || ""}\n% Increase in WTI: ${properties?.CL_F_Daily_Change || ""}\n% Increase in Brent: ${properties?.BZ_F_Daily_Change || ""}`;
      case "Location":
        return `Location: ${properties?.name || ""}`;
      case "Organization":
        return `Organization: ${properties?.name || ""}`;
      case "Person":
        return `Person: ${properties?.name || ""}`;
      case "Event":
        return `Event: ${properties?.name || ""}`;
      case "Topic":
        return `Topic: ${properties?.name || ""}`;
      default:
        return label;
    }
  };
 
  // Node Color Formatter
  const getNodeColor = (node: any) => {
    switch (node.label) {
      case "News":
        return "blue";
      case "Article":
        return "purple";
      case "OilPrice":
        return "white";
      case "Location":
        return "yellow";
      case "Organization":
        return "green";
      case "Person":
        return "red";
      case "Event":
        return "#CCCCFF"; // Lilac
      case "Topic":
        return "hotpink"; // Bright Pink
      default:
        return "gray";
    }
  };
 
  return (
<div className="w-full h-screen">
      {/* Date Filters UI */}
<div className="flex gap-4 mb-4">
<div>
<label className="block text-sm font-medium">Start Date</label>
<input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="border px-2 py-1 rounded"
          />
</div>
<div>
<label className="block text-sm font-medium">End Date</label>
<input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="border px-2 py-1 rounded"
          />
</div>
<button
          onClick={fetchGraph}
          className="self-end px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
>
          Apply Filter
</button>
</div>
 
      {/* Error Message */}
      {error && <div className="text-red-500 mb-4">{error}</div>}
 
      {/* Loading State */}
      {isLoading && <div>Loading...</div>}
 
      {/* Graph Rendering */}
      {!isLoading &&
      graphData.nodes &&
      graphData.relations &&
      graphData.nodes.length > 0 &&
      graphData.relations.length > 0 ? (
<ForceGraph3D
          ref={graphRef}
          graphData={{
            nodes: graphData.nodes,
            links: graphData.relations,
          }}
          nodeLabel={getNodeLabel}
          nodeAutoColorBy={null}
          nodeColor={getNodeColor}
          linkLabel={(link: any) => link.label}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
        />
      ) : (
        !isLoading && (
<div className="text-center text-gray-500">
            No data available for the selected filter.
</div>
        )
      )}
</div>
  );
}