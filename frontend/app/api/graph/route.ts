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
    const keywords = url.searchParams.get("keywords"); // new

    const keywordList = keywords
      ? keywords.split(",").map((k) => k.trim()).filter((k) => k.length > 0)
      : [];

    let query = "";
    let params: any = { startDate, endDate };

    if (!startDate && !endDate && keywordList.length === 0) {
      // No filters - fetch latest 500 nodes
      query = `
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT 500
      `;
    } else {
      query = `
        MATCH (n)-[r]->(m)
        WHERE
          (${startDate && endDate
            ? `(n.date IS NULL OR (date(n.date) >= date($startDate) AND date(n.date) <= date($endDate))) 
              AND (m.date IS NULL OR (date(m.date) >= date($startDate) AND date(m.date) <= date($endDate)))`
            : "true"
          })
          AND
          (${keywordList.length > 0
            ? keywordList.map((_, idx) => `
                (
                  toLower(n.name) CONTAINS $keyword${idx} OR
                  toLower(m.name) CONTAINS $keyword${idx} OR
                  toLower(n.headline) CONTAINS $keyword${idx} OR
                  toLower(m.headline) CONTAINS $keyword${idx}
                )
              `).join(" OR ")
            : "true"
          })
        RETURN n, r, m
        LIMIT 500
      `;

      keywordList.forEach((kw, idx) => {
        params[`keyword${idx}`] = kw.toLowerCase();
      });
    }

    const result = await session.run(query, params);

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
