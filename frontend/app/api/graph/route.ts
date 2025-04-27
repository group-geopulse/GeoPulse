import { NextResponse } from "next/server";
import neo4j from "neo4j-driver";

const driver = neo4j.driver(
  "neo4j+s://408cc9a3.databases.neo4j.io",
  neo4j.auth.basic(
    "neo4j",
    "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw"
  )
);

export async function GET(req: Request) {
  const session = driver.session();
  try {
    const url = new URL(req.url);
    const startDate = url.searchParams.get("startDate");
    const endDate   = url.searchParams.get("endDate");
    const keywords  = url.searchParams.get("keywords") || "";

    // Build a clean array of lowercase keywords
    const keywordList = keywords
      .split(",")
      .map((k) => k.trim().toLowerCase())
      .filter((k) => k);

    // Build the keyword‐conditions string
    const keywordConds = keywordList
      .map(
        (_kw, i) =>
          `toLower(n.name) CONTAINS $kw${i} OR
           toLower(m.name) CONTAINS $kw${i} OR
           toLower(n.headline) CONTAINS $kw${i} OR
           toLower(m.headline) CONTAINS $kw${i}`
      )
      .join(" OR ");

    // If no keywords, this clause becomes just "true"
    const keywordClause =
      keywordConds.length > 0
        ? `size($keywords) = 0 OR (${keywordConds})`
        : "true";

    const query = `
      MATCH (n)-[r]->(m)
      WHERE
        (
          $startDate IS NULL
          OR $endDate IS NULL
          OR (
            n.date IS NOT NULL
            AND date(n.date) >= date($startDate)
            AND date(n.date) <= date($endDate)
          )
        )
        AND (${keywordClause})
      WITH n, r, m
      OPTIONAL MATCH (n)-[s:MENTIONS]->(e:Entity)
      RETURN n, r, m, s, e
      LIMIT 500
    `;

    // Build params
    const params: any = {
      startDate: startDate || null,
      endDate:   endDate   || null,
      keywords:  keywordList,
    };
    keywordList.forEach((kw, idx) => {
      params[`kw${idx}`] = kw;
    });

    const result = await session.run(query, params);

    // Build unique nodes + relations
    const nodesMap = new Map<string, any>();
    const relations: any[] = [];

    result.records.forEach((rec) => {
      const n = rec.get("n");
      const m = rec.get("m");
      const r = rec.get("r");
      const s = rec.get("s");
      const e = rec.get("e");

      const addNode = (node: any) => {
        const id = node.identity.toString();
        if (!nodesMap.has(id)) {
          nodesMap.set(id, {
            id,
            label: node.labels[0],
            properties: node.properties,
          });
        }
      };

      addNode(n);
      addNode(m);
      if (e) addNode(e);

      relations.push({
        source: n.identity.toString(),
        target: m.identity.toString(),
        label: r.type,
      });
      if (s && e) {
        relations.push({
          source: n.identity.toString(),
          target: e.identity.toString(),
          label: s.type,
        });
      }
    });

    return NextResponse.json({
      nodes: Array.from(nodesMap.values()),
      relations,
    });
  } catch (err) {
    console.error(err);
    return NextResponse.json(
      { error: "Failed to load graph data." },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
