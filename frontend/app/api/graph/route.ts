import { NextResponse } from "next/server";
import neo4j from "neo4j-driver";

const driver = neo4j.driver(
  "neo4j+s://408cc9a3.databases.neo4j.io",
  neo4j.auth.basic("neo4j", "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw")
);

export async function GET() {
  const session = driver.session();

  try {
    const query = `
      MATCH (n)-[r]->(m)
      RETURN n, r, m LIMIT 100
    `;

    const result = await session.run(query);

    const nodesMap = new Map();
    const links: any[] = [];

    result.records.forEach((record) => {
      const startNode = record.get("n");
      const endNode = record.get("m");
      const relationship = record.get("r");

      if (!nodesMap.has(startNode.identity.toString())) {
        nodesMap.set(startNode.identity.toString(), {
          id: startNode.identity.toString(),
          label: startNode.labels[0],
          properties: startNode.properties,
        });
      }

      if (!nodesMap.has(endNode.identity.toString())) {
        nodesMap.set(endNode.identity.toString(), {
          id: endNode.identity.toString(),
          label: endNode.labels[0],
          properties: endNode.properties,
        });
      }

      // Adding the relationship
      links.push({
        source: startNode.identity.toString(),
        target: endNode.identity.toString(),
        label: relationship.type,
      });
    });

    return NextResponse.json({
      nodes: Array.from(nodesMap.values()),
      links,
    });
  } catch (error) {
    console.error("Neo4j graph fetch error:", error);
    return NextResponse.json({ error: "Failed to load graph data." }, { status: 500 });
  } finally {
    await session.close();
  }
}
