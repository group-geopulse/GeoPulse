import ast
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from neo4j import GraphDatabase

# MongoDB Connection
MONGO_URI = "mongodb+srv://geopulse5530:x1GJ55GaO0p87U2I@geopulse.oniyq.mongodb.net/?retryWrites=true&w=majority&appName=GeoPulse"
mongo_client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

news_db = mongo_client["ProdNewsDB"]
prices_db = mongo_client["ProdPricesDB"]
entities_db = mongo_client["Entities"]

# Neo4j Connection
NEO4J_URI = "neo4j+s://408cc9a3.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw"

neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def convert_to_list(value):
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except:
            return []
    return value

def transfer_data():
    with neo4j_driver.session() as session:
        # Extract data from MongoDB
        news_data = list(news_db["News"].find())
        oil_prices = list(prices_db["Prices"].find())
        
        # Extract Entities
        locations = list(entities_db["Locations"].find())
        organizations = list(entities_db["Organizations"].find())
        topics = list(entities_db["Topics"].find())
        people = list(entities_db["People"].find())
        events = list(entities_db["Events"].find())

        # Insert OilPrice Nodes
        for price in oil_prices:
            session.run(
                """
                MERGE (o:OilPrice {date: $date})
                SET o.CL_F_Open = $cl_f_open, o.BZ_F_Open = $bz_f_open, 
                    o.CL_F_Close = $cl_f_close, o.BZ_F_Close = $bz_f_close,
                    o.CL_F_Daily_Change = $cl_f_daily, o.BZ_F_Daily_Change = $bz_f_daily,
                    o.CL_F_Weekly_Change = $cl_f_weekly, o.BZ_F_Weekly_Change = $bz_f_weekly
                """,
                date=price["_id"], cl_f_open=price["CL=F Open"], bz_f_open=price["BZ=F Open"],
                cl_f_close=price["CL=F Close"], bz_f_close=price["BZ=F Close"],
                cl_f_daily=price["CL=F Daily % Change"], bz_f_daily=price["BZ=F Daily % Change"],
                cl_f_weekly=price["CL=F Weekly % Change"], bz_f_weekly=price["BZ=F Weekly % Change"]
            )

        # Insert Entity Nodes
        for loc in locations:
            session.run("MERGE (:Location {name: $name, mentions: $count})", name=loc["Location"], count=loc["Count"])
        for org in organizations:
            session.run("MERGE (:Organization {name: $name, mentions: $count})", name=org["Organization"], count=org["Count"])
        for topic in topics:
            session.run("MERGE (:Topic {name: $name, mentions: $count})", name=topic["Topic"], count=topic["Count"])
        for person in people:
            session.run("MERGE (:Person {name: $name, mentions: $count})", name=person["Person"], count=person["Count"])
        for event in events:
            session.run("MERGE (:Event {name: $name, mentions: $count})", name=event["Event"], count=event["Count"])

        # Insert News Articles and Relationships
        for news in news_data:
            # Convert stringified lists to actual lists
            news["Locations"] = convert_to_list(news["Locations"])
            news["Organizations"] = convert_to_list(news["Organizations"])
            news["Topics"] = convert_to_list(news["Topics"])
            news["Events"] = convert_to_list(news["Events"])
            news["People"] = convert_to_list(news["People"])

            # Create News node
            session.run(
                """
                MERGE (n:News {headline: $headline})
                SET n.source = $source, n.link = $link, n.date = $updated_date,
                    n.headline_sentiment = $headline_sentiment, n.article_sentiment = $article_sentiment,
                    n.sentiment_confidence = $sentiment_confidence
                """,
                headline=news["Headline"], source=news["Source"], link=news["Link"],
                updated_date=news["Updated_Date"], headline_sentiment=news["Headline Sentiment"],
                article_sentiment=news["Article Sentiment"], sentiment_confidence=news["Sentiment Confidence"]
            )

            # Link News to OilPrice (Matching Dates)
            session.run(
                """
                MATCH (n:News {date: $updated_date}), (o:OilPrice {date: $updated_date})
                MERGE (o)-[:HAS_NEWS]->(n)
                """,
                updated_date=news["Updated_Date"]
            )

            # Link News to Entities
            for loc in news["Locations"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline}), (l:Location {name: $loc})
                    MERGE (n)-[:MENTIONS]->(l)
                    """,
                    headline=news["Headline"], loc=loc
                )

            for org in news["Organizations"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline}), (o:Organization {name: $org})
                    MERGE (n)-[:MENTIONS]->(o)
                    """,
                    headline=news["Headline"], org=org
                )

            for topic in news["Topics"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline}), (t:Topic {name: $topic})
                    MERGE (n)-[:MENTIONS]->(t)
                    """,
                    headline=news["Headline"], topic=topic
                )

            for event in news["Events"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline}), (e:Event {name: $event})
                    MERGE (n)-[:MENTIONS]->(e)
                    """,
                    headline=news["Headline"], event=event
                )

            for person in news["People"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline}), (p:Person {name: $person})
                    MERGE (n)-[:MENTIONS]->(p)
                    """,
                    headline=news["Headline"], person=person
                )

        # Optimized OilPrice Date Linking
        session.run(
            """
            MATCH (o1:OilPrice)
            WHERE NOT EXISTS { (o1)-[:NEXT_DAY]->() }  // Find nodes without NEXT_DAY outgoing links
            WITH o1
            MATCH (o2:OilPrice)
            WHERE date(o2.date) > date(o1.date)  // Find a future OilPrice node
            WITH o1, o2
            ORDER BY date(o2.date) ASC  // Order future nodes by closest date
            WITH o1, collect(o2)[0] AS closest_future // Pick the closest future node
            WHERE closest_future IS NOT NULL  // Ensure a match exists
            MERGE (o1)-[:NEXT_DAY]->(closest_future)
            """
        )

if __name__ == "__main__":
    transfer_data()
    print("Data transfer from MongoDB to Neo4j complete!")

