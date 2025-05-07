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
  const session = driver.session(); // Base session for the request
  try {
    const url = new URL(req.url);
    const startDate = url.searchParams.get("startDate");
    const endDate = url.searchParams.get("endDate");
    const keywords = url.searchParams.get("keywords") || "";

    // Build keyword array and conditions
    const keywordList = keywords
      .split(",")
      .map((k) => k.trim().toLowerCase())
      .filter((k) => k);

      console.log("Start Date:", startDate);
      console.log("End Date:", endDate);


      const params = {
        startDate: startDate || "2025-04-01", // Default to April 1st if no start date provided
        endDate: endDate || "2025-04-07", // Default to April 7th if no end date provided
        keywords: keywordList,
      };
  
      const newsQuery = `
        MATCH (p:OilPrice)
        WHERE date(p.date) >= date($startDate) AND date(p.date) <= date($endDate)
        OPTIONAL MATCH (p)-[r1:HAS_NEWS]->(n:News)
        WHERE SIZE($keywords) = 0 OR ANY(keyword IN $keywords WHERE toLower(n.headline) CONTAINS keyword)
        OPTIONAL MATCH (n)-[r2:MENTIONS]->(e)
          WHERE e:Location OR e:Person OR e:Organization OR e:Topic OR e:Event
        RETURN p, n, e, r1, r2
        LIMIT 5000
      `;
  
      const articleQuery = `
        MATCH (p:OilPrice)
        WHERE date(p.date) >= date($startDate) AND date(p.date) <= date($endDate)
        OPTIONAL MATCH (p)-[r1:HAS_ARTICLE]->(a:Article)
        WHERE SIZE($keywords) = 0 OR ANY(keyword IN $keywords WHERE toLower(a.headline) CONTAINS keyword)
        OPTIONAL MATCH (a)-[r2:MENTIONS]->(ae)
          WHERE ae:Location OR ae:Person OR ae:Organization OR ae:Topic OR ae:Event
        RETURN p, a, ae, r1, r2
        LIMIT 5000
      `;

    // Create separate sessions for each query to avoid transaction conflicts
    const session1 = driver.session();
    const session2 = driver.session();

    console.log("Query params:", params);


    // Run both queries in parallel
    const [newsResult, articleResult] = await Promise.all([
      session1.run(newsQuery, params),
      session2.run(articleQuery, params),
    ]);

    // Combine results
    const nodesMap = new Map();
    const relations: any[] = [];


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
    
    const processResultsNews = (result: any) => {
      result.records.forEach((rec: any) => {
        const p = rec.get("p"); // OilPrice
        const n = rec.get("n"); // News
        const e = rec.get("e"); // Entity (e.g., Location, Person, etc.)
        const r1 = rec.get("r1"); // Relationship (OilPrice - News)
        const r2 = rec.get("r2"); // Relationship (News - Entity)
    
        // Add nodes only if they exist
        if (p) addNode(p);
        if (n) addNode(n);
        if (e) addNode(e);
    
        // Add relations if they exist
        if (p && n) {
          relations.push({
            source: p.identity.toString(),
            target: n.identity.toString(),
            label: r1.type,
          });
        }
        if (n && e) {
          relations.push({
            source: n.identity.toString(),
            target: e.identity.toString(),
            label: r2.type,
          });
        }
      });
    };
    
    const processResultsArticles = (result: any) => {
      result.records.forEach((rec: any) => {
        const p = rec.get("p"); // OilPrice
        const a = rec.get("a"); // Article
        const ae = rec.get("ae"); // Entity (e.g., Location, Person, etc.)
        const r1 = rec.get("r1"); // Relationship (OilPrice - Article)
        const r2 = rec.get("r2"); // Relationship (Article - Entity)
    
        // Add nodes only if they exist
        if (p) addNode(p);
        if (a) addNode(a);
        if (ae) addNode(ae);
    
        // Add relations if they exist
        if (p && a) {
          relations.push({
            source: p.identity.toString(),
            target: a.identity.toString(),
            label: r1.type,
          });
        }
        if (a && ae) {
          relations.push({
            source: a.identity.toString(),
            target: ae.identity.toString(),
            label: r2.type,
          });
        }
      });
    };
    
    // Process results from both queries
    processResultsNews(newsResult);
    processResultsArticles(articleResult);
    
    // Return the combined result
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
    // Close sessions
    await session.close();
  }
}

