"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";

// Dynamically import the graph to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: any[]; relations: any[] }>({
    nodes: [],
    relations: [],
  });
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch the graph data when both dates are provided
  const fetchGraph = async () => {
    setIsLoading(true); // Set loading state to true while fetching data
    setError(""); // Clear any previous errors

    // Only fetch if both startDate and endDate are set
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

      // Ensure the data has nodes and relations
      if (data && Array.isArray(data.nodes) && Array.isArray(data.relations)) {
        console.log("Fetched graph data:", data); // Debugging
        setGraphData(data);
      } else {
        console.error("Malformed graph data:", data); // Debugging
        setError("Malformed graph data received from the server.");
        setGraphData({ nodes: [], relations: [] }); // Default to empty arrays if data is malformed
      }
    } catch (error) {
      console.error("Error fetching graph data:", error);
      setGraphData({ nodes: [], relations: [] }); // Fallback to empty data on error
    } finally {
      setIsLoading(false); // Set loading state to false once data is fetched
    }
  };

  useEffect(() => {
    // Don't fetch the graph unless both startDate and endDate are available
    if (startDate && endDate) {
      fetchGraph();
    }
  }, [startDate, endDate]);

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
      {/* Only render the graph if we have valid graphData */}
      {!isLoading && graphData.nodes && graphData.relations && graphData.nodes.length > 0 && graphData.relations.length > 0 ? (
        <ForceGraph2D
        graphData={{
          nodes: graphData.nodes,
          links: graphData.relations, // <-- Remap to what the library expects
        }}
          nodeLabel={(node: any) => `${node.label}: ${node.properties?.name || node.properties?.headline || ""}`}
          nodeAutoColorBy="label"
          linkLabel={(link: any) => link.label}
          linkDirectionalArrowLength={6}
          linkDirectionalArrowRelPos={1}
          linkColor={() => "#ffffff"}
        />
      ) : (
        !isLoading && <div className="text-center text-gray-500">No data available for the selected filter.</div>
      )}
    </div>
  );
}
