import { NextResponse } from "next/server";
import neo4j from "neo4j-driver";

const driver = neo4j.driver(
  "neo4j+s://408cc9a3.databases.neo4j.io",
  neo4j.auth.basic("neo4j", "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw")
);

export async function GET(req: Request) {
  const session = driver.session();

  try {
    const url = new URL(req.url);
    const startDate = url.searchParams.get("startDate");
    const endDate = url.searchParams.get("endDate");

    let query = `
      MATCH (n)-[r]->(m)
      WHERE
        (n.date IS NULL OR (
          ${startDate ? "date(n.date) >= date($startDate)" : "true"} AND
          ${endDate ? "date(n.date) <= date($endDate)" : "true"}
        )) AND
        (m.date IS NULL OR (
          ${startDate ? "date(m.date) >= date($startDate)" : "true"} AND
          ${endDate ? "date(m.date) <= date($endDate)" : "true"}
        ))
      RETURN n, r, m 
    `;

    const result = await session.run(query, {
      startDate,
      endDate,
    });

    const nodesMap = new Map();
    const relations: any[] = [];

    result.records.forEach((record) => {
      const startNode = record.get("n");
      const endNode = record.get("m");
      const relationship = record.get("r");

      [startNode, endNode].forEach((node) => {
        if (!nodesMap.has(node.identity.toString())) {
          nodesMap.set(node.identity.toString(), {
            id: node.identity.toString(),
            label: node.labels[0],
            properties: node.properties,
          });
        }
      });

      relations.push({
        source: startNode.identity.toString(),
        target: endNode.identity.toString(),
        label: relationship.type,
      });
    });

    return NextResponse.json({
      nodes: Array.from(nodesMap.values()),
      relations,
    });
  } catch (error) {
    console.error("Neo4j graph fetch error:", error);
    return NextResponse.json({ error: "Failed to load graph data." }, { status: 500 });
  } finally {
    await session.close();
  }
}
