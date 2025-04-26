import os
import requests
import json
import re
from neo4j import GraphDatabase
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
 
# --- Configuration ---
TOGETHER_API_KEY = "fc08bc662bc0c7f4e8ed64805409c1dfc05e4c27775b2a15b653b0f7f1c23f80"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
LLM_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
 
NEO4J_URI = "neo4j+s://408cc9a3.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw"
 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
 
def extract_keywords(text):
    text = text.replace('-', ' ')  # Replace hyphens with spaces
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    keywords = [w for w in words if w.isalnum() and w not in stop_words]
    return keywords
 
def call_together_ai(prompt, max_tokens=1024, temperature=0.2):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "top_k": 40,
        "repetition_penalty": 1.1
    }
    try:
        response = requests.post(TOGETHER_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return content.strip() if content else None
    except Exception as e:
        logging.error(f"Error calling Together AI API: {e}")
        return None
 
SCHEMA_GUIDANCE = """
Graph Schema:
- (:News)-[:MENTIONS]->(:Organization|:Event|:Location|:Person|:Topic)
- (:News {date})
- (:Article)-[:MENTIONS]->(:Organization|:Event|:Location|:Person|:Topic)
- (:Article {date})
- (:OilPrice {date, CL_F_Close, BZ_F_Close, CL_F_Daily_Change, BZ_F_Daily_Change})
- (:OilPrice)-[:NEXT_DAY]->(:OilPrice)
 
Cypher Query Template for GeoPulse:
MATCH (n)-[:MENTIONS]->(e)
WHERE (n:News OR n:Article) AND (e:Organization OR e:Event OR e:Location OR e:Person OR e:Topic) AND (toLower(e.name) CONTAINS toLower('<keyword>'))
WITH n
MATCH (p:OilPrice) WHERE n.date = p.date
OPTIONAL MATCH (p)-[:NEXT_DAY]->(p2:OilPrice)
RETURN n.headline, n.date, p.CL_F_Close, p.BZ_F_Close, p.CL_F_Daily_Change, p.BZ_F_Daily_Change,
       p2.CL_F_Close AS next_day_CL_F_Close, p2.BZ_F_Close AS next_day_BZ_F_Close
ORDER BY n.date DESC LIMIT 20
"""
 
def generate_cypher_query(user_question, keywords):
    keyword_list = ', '.join([f'"{k}"' for k in keywords])
    prompt = f"""
You are a Neo4j Cypher expert. Based ONLY on the graph schema and the user question, generate an optimized query.
 
{SCHEMA_GUIDANCE}
 
Instructions:
- Filter news and entities using any of these keywords: [{keyword_list}]
- STRICTLY use: MATCH (n)-[:MENTIONS]->(e)
- Use : WHERE any(k IN [{keyword_list}] WHERE toLower(e.name) CONTAINS toLower(k) OR toLower(n.headline) CONTAINS toLower(k))
- Match oil prices using: n.date = p.date
- Include next-day oil prices (OPTIONAL MATCH)
- Use correct labels: News, Organization, Event, Location, Person, Topic, OilPrice, Article
- DO NOT use invalid labels like Entity or Keyword
 
User Question:
\"\"\"{user_question}\"\"\"
 
 
Cypher Query:
"""
    cypher = call_together_ai(prompt)
    if cypher:
        cypher = re.sub(r"^```cypher|```$", "", cypher).strip()
        if cypher.upper().startswith(("MATCH", "OPTIONAL MATCH")):
            logging.info(f"Generated Cypher: {cypher}")
            return cypher
    return None
 
def execute_neo4j_query(cypher_query):
    if not cypher_query:
        return []
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    results = []
    try:
        with driver.session(database="neo4j") as session:
            result = session.run(cypher_query)
            for record in result:
                results.append(record.data())
            summary = result.consume()
            if summary.notifications:
                for n in summary.notifications:
                    logging.warning(f"Neo4j Notification: {n.get('description')}")
        return results
    except Exception as e:
        logging.error(f"Neo4j query error: {e}")
        return []
    finally:
        driver.close()
 
def summarize_results_with_llm(user_question, cypher_query, query_results):
    if not query_results:
        return "⚠️ No data returned from the graph.", []
 
    def serialize(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
 
    results_json = json.dumps(query_results[:15], indent=2, default=serialize)
    prompt = f"""
You are GeoPulse, an expert AI financial analyst.
 
User Question: "{user_question}"
 
Data Sample (JSON):
{results_json}
 
Instructions:
- Only use the data sample provided above
- Provide a detailed and structured analysis of how the event(s) affected global oil prices.
- Identify specific dates and describe what happened to oil prices before and after those events.
- Use numbers in your summary (price surges, peaks, drops, exact dates).
- Mention major contributing factors (e.g. sanctions, wars, supply cuts, production boosts).
- Structure your response with a timeline, a cause-effect summary, and supporting news headlines.
 
Format:
Summary:
[summary - including timeline, peak/trough prices, and attribution to causes like war, sanctions, production changes.]
 
Relevant Headlines:
- Headline 1 (Date) — Price movement and interpretation
- Headline 2 (Date) — Price movement and interpretation
"""
    response = call_together_ai(prompt, max_tokens=1024, temperature=0.3)
    if not response:
        return "⚠️ LLM failed to generate summary.", []
 
    summary = "Summary could not be parsed."
    headlines = []
    try:
        parts = re.split(r"Relevant Headlines:\s*", response, flags=re.IGNORECASE)
        summary = parts[0].replace("Summary:", "").strip()
        if len(parts) > 1:
            headlines = [line.strip("-• ").strip() for line in parts[1].splitlines() if line.strip()]
    except Exception as e:
        logging.warning(f"Failed to parse LLM response: {e}")
    return summary, headlines
 
def process_user_query(user_question):
    logging.info(f"Processing: {user_question}")
    keywords = extract_keywords(user_question)
    print("\n🔍 Extracted Keywords:", keywords)
    cypher = generate_cypher_query(user_question, keywords)
    if cypher:
        print("\n🧩 Generated Cypher Query:\n", cypher)
    else:
        return "⚠️ Cypher generation failed.", []
    results = execute_neo4j_query(cypher)
    if not results:
        return ("It seems your question is not directly related to the contents of this knowledge graph...\n" +
        " This graph focuses on oil prices and their relation to geopolitical events.\n " +
        "Try asking about: \n" +
        "- 'How did the Russia-Ukraine war affect oil prices?' \n" +
        "- 'What was the effect of G7 summits on oil?'"), []
    summary, headlines = summarize_results_with_llm(user_question, cypher, results)
    return summary, headlines
 
if __name__ == "__main__":
    while True:
        user_input = input("\n🗣️ Ask a question (or type 'exit'): ")
        if user_input.lower() in ("exit", "quit"):
            break
        summary, headlines = process_user_query(user_input)
        print("\n📝 Summary:\n", summary)
        if headlines:
            print("\n📰 Relevant Headlines:")
            for h in headlines:
                print(f"- {h}")
        else:
            print("\n📰 Relevant Headlines: None listed.")
