"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; relations: any[] }>({
    nodes: [],
    relations: [],
  });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [keywords, setKeywords] = useState(""); 
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [autorotate, setAutorotate] = useState(true); // State to control autorotate
  const graphRef = useRef<any>(null);

  const fetchGraph = async () => {
    setIsLoading(true);
    setError("");
  
    if ((startDate && !endDate) || (!startDate && endDate)) {
      setError("Please provide both start and end dates.");
      setIsLoading(false);
      return;
    }
  
    const queryParams = new URLSearchParams();
    if (startDate) queryParams.append("startDate", startDate);
    if (endDate) queryParams.append("endDate", endDate);
    if (keywords.trim()) queryParams.append("keywords", keywords.trim());
  
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

  // Function to align OilPrice nodes horizontally
  const alignOilPriceNodes = (nodes: any[]) => {
    const oilPriceNodes = nodes.filter((node) => node.label === "OilPrice");
    
    // Sort OilPrice nodes by date
    oilPriceNodes.sort((a, b) => {
      const dateA = new Date(a.properties?.date);
      const dateB = new Date(b.properties?.date);
      return dateA - dateB;
    });

    // Align OilPrice nodes along the x-axis (horizontal spine)
    oilPriceNodes.forEach((node, index) => {
      node.y = 0;  // Keep the y-axis fixed for horizontal alignment
      node.z = 0;  // Keep the z-axis fixed
      node.x = index * 100;  // Space out OilPrice nodes along the x-axis horizontally
    });

    // Update the nodes with the new positions
    return nodes.map((node) =>
      node.label === "OilPrice" ? { ...node, ...oilPriceNodes.shift() } : node
    );
  };

  useEffect(() => {
    if (startDate && endDate) {
      fetchGraph();
    }
  }, [startDate, endDate]);

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      const alignedNodes = alignOilPriceNodes(graphData.nodes);
      setGraphData((prevData) => ({
        ...prevData,
        nodes: alignedNodes,
      }));
    }
  }, [graphData.nodes.length]);

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
      <div className="flex flex-col sm:flex-row gap-4 mb-4">
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
        <div>
          <label className="block text-sm font-medium">Keywords (comma-separated)</label>
          <input
            type="text"
            placeholder="e.g. oil, inflation, russia"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="border px-2 py-1 rounded w-64"
          />
        </div>
        <button
          onClick={fetchGraph}
          className="self-end px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Apply Filter
        </button>
      </div>

      {error && <div className="text-red-500 mb-4">{error}</div>}

      {isLoading && <div>Loading...</div>}

      <button
        onClick={() => setAutorotate((prev) => !prev)}
        className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
      >
        Toggle Autorotate
      </button>

      {!isLoading &&
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
          // Set initial camera position and field of view
          cameraPosition={{
            x: 0,
            y: 300,
            z: 500, // Adjust this value for a better starting zoom
          }}
          fov={60} // Adjust field of view for a better perspective
          forceEngine="none" // Disable force layout
          autoRotate={autorotate} // Enable auto-rotation if needed
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
