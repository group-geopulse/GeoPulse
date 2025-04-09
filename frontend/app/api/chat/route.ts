import { NextResponse } from "next/server";
import requests from "axios";
import GraphDatabase from "neo4j-driver";

const NEO4J_URI = "neo4j+s://408cc9a3.databases.neo4j.io";
const NEO4J_USER = "neo4j";
const NEO4J_PASSWORD = "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw";

const TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions";
const TOGETHER_API_KEY = "fc08bc662bc0c7f4e8ed64805409c1dfc05e4c27775b2a15b653b0f7f1c23f80";
const LLM_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1";

const driver = GraphDatabase.driver(NEO4J_URI, GraphDatabase.auth.basic(NEO4J_USER, NEO4J_PASSWORD));

async function executeNeo4jQuery(cypherQuery: string) {
  const session = driver.session();
  try {
    const result = await session.run(cypherQuery);
    return result.records.map((record) => record.toObject());
  } catch (error) {
    console.error("Neo4j query error:", error);
    return [];
  } finally {
    await session.close();
  }
}

async function callTogetherAI(prompt: string) {
  try {
    const response = await requests.post(
      TOGETHER_API_URL,
      {
        model: LLM_MODEL,
        messages: [{ role: "user", content: prompt }],
        max_tokens: 1024,
        temperature: 0.2,
        top_p: 0.9,
        top_k: 40,
        repetition_penalty: 1.1,
      },
      {
        headers: {
          Authorization: `Bearer ${TOGETHER_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    return response.data.choices?.[0]?.message?.content?.trim() || "";
  } catch (error) {
    console.error("Error calling Together AI:", error);
    return "⚠️ Error generating a response.";
  }
}

export async function POST(req: Request) {
  try {
    const { user_question } = await req.json();

    const cypherPrompt = `
You are a Neo4j Cypher expert. Based ONLY on the example pattern and the user question below, generate a valid Cypher query.

Cypher Query Template:

MATCH (n:News)-[:MENTIONS]->(o:Organization)
WHERE toLower(o.name) CONTAINS '<keyword>'
MATCH (p:OilPrice) WHERE n.date = p.date
OPTIONAL MATCH (p)-[:NEXT_DAY]->(p2:OilPrice)
RETURN n.headline, n.date, p.CL_F_Close, p.BZ_F_Close, p.CL_F_Daily_Change, p.BZ_F_Daily_Change,
       p2.CL_F_Close AS next_day_CL_F_Close, p2.BZ_F_Close AS next_day_BZ_F_Close
ORDER BY n.date DESC LIMIT 10

User Question:
"${user_question}"

- Use toLower(o.name) CONTAINS '<keyword>' for filtering organizations.
- Match oil prices on the same day as the news using n.date = p.date.
- Use OPTIONAL MATCH for next day's oil prices.
- DO NOT use sentiment properties or invalid syntax.
- Output only the Cypher query.

Cypher Query:
    `;

    const cypherQuery = await callTogetherAI(cypherPrompt);

    if (!cypherQuery.startsWith("MATCH")) {
      console.error("Invalid Cypher Query:", cypherQuery);
      return NextResponse.json({ summary: "⚠️ Failed to generate a valid Cypher query.", headlines: [] });
    }

    console.log("Generated Cypher Query:\n", cypherQuery); // Debugging

    // Run the Cypher query in Neo4j
    const results = await executeNeo4jQuery(cypherQuery);
    console.log("Query Results:", results); // Debugging

    if (!results.length) {
      return NextResponse.json({ summary: "⚠️ No data returned from the graph.", headlines: [] });
    }

    const summaryPrompt = `
You are GeoPulse, an AI financial analyst.

User Question: "${user_question}"

Cypher Query Used:
${cypherQuery}

Data Sample (JSON):
${JSON.stringify(results.slice(0, 5), null, 2)}

Instructions:
- Summarize how the event affected oil prices.
- Highlight oil price changes and timing.
- Include 3–7 relevant news headlines from the data.

Format:
Summary:
[summary]

Relevant Headlines:
- Headline 1
- Headline 2
    `;

    const summaryResponse = await callTogetherAI(summaryPrompt);

    let summary = "Summary could not be parsed.";
    let headlines: string[] = [];

    try {
      const parts = summaryResponse.split("Relevant Headlines:");
      summary = parts[0].replace("Summary:", "").trim();
      if (parts.length > 1) {
        headlines = parts[1].split("\n").map((line: string) => line.replace(/^- /, "").trim()).filter(Boolean);
      }
    } catch (error) {
      console.error("Failed to parse LLM response:", error);
    }

    return NextResponse.json({ summary, headlines });
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json({ summary: "⚠️ Server error.", headlines: [] }, { status: 500 });
  }
}


//testing for connection go to http://localhost:3000/api/chat
export async function GET() {
  try {
    const session = driver.session();
    const result = await session.run("MATCH (n) RETURN n LIMIT 1");
    await session.close();

    return NextResponse.json({ message: "Neo4j Connected", data: result.records.length });
  } catch (error) {
    console.error("Neo4j Connection Error:", error);
    return NextResponse.json({ error: "Neo4j Connection Failed" }, { status: 500 });
  }
}
