from mongodb_utils import get_mongo_client
from neo4j import GraphDatabase
import pandas as pd
import os
import logging

URI = os.getenv("URI")
# Suppress only informational messages from Neo4j, but allow warnings and errors
logging.getLogger("neo4j").setLevel(logging.WARNING)

def get_neo4j_driver(test=True):
    # Set Neo4j Connection

    if test:
        NEO4J_URI = "neo4j+s://64cf16ed.databases.neo4j.io"
        NEO4J_PASSWORD = "Yc-aRMOLnyHCudT19V7uZWf-vlQyxKEfplK09RNiMTE"
    
    else:
        NEO4J_URI = "neo4j+s://408cc9a3.databases.neo4j.io"
        NEO4J_PASSWORD = "lCbxlWMtzgFJJdPJiSrDGCRleJ9vKX67ry0Ro4sp_Cw"
    
    NEO4J_USER = "neo4j"
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def update_oilprice_nodes(database, collection, use_testKG=True):
    neo4j_driver = get_neo4j_driver(use_testKG)
    mongo_client = get_mongo_client(URI)
    prices_db = mongo_client[database]

    # Extract new oil prices
    new_prices = list(prices_db[collection].find())

    if not new_prices:
        return f"No new OilPrice nodes were created (collection '{collection}' was empty)"

    with neo4j_driver.session() as session:
        # Insert new OilPrice nodes
        for price in new_prices:
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

        # Add NEXT_DAY relationships for new prices
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

        # Remove records from collection
        prices_db[collection].delete_many({})

    return f"Created {len(new_prices)} new OilPrice nodes & emptied '{collection}'"

def update_entity_db_and_nodes(news_db_name, entitities_db_name, news_col, entity_cols, use_testKG=True):
    neo4j_driver = get_neo4j_driver(use_testKG)
    mongo_client = get_mongo_client(URI)
    news_db = mongo_client[news_db_name]
    entities_db = mongo_client[entitities_db_name]

    # Read news articles from MongoDB
    news_collection = news_db[news_col]
    news_articles = news_collection.find({}, {entity: 1 for entity in entity_cols})  # Fetch only entity columns

    if not news_articles:
        return f"No entity records/nodes were updated (collection '{news_col}' was empty)"
    
    # Define node name for each entity type
    entity_keys = {"Locations": "Location", "Organizations": "Organization", "People": "Person", "Topics": "Topic", "Events": "Event"}
    
    new_entities = 0
    total_entities = 0

    # Create new Neo4j session
    with neo4j_driver.session() as session:
        for article in news_articles:
            for entity_type in entity_cols:
                entity_collection = entities_db[entity_cols[entity_type]]
                for entity_value in article[entity_type]:
                    # Check if the entity already exists
                    existing_entity = entity_collection.find_one({entity_keys[entity_type]: entity_value})
                    total_entities += 1
                    
                    if existing_entity:
                        # Update count in MongoDB & Neo4j
                        entity_collection.update_one({entity_keys[entity_type]: entity_value}, {"$inc": {"Count": 1}})                        
                        
                        session.run(
                            f"""
                            MATCH (e:{entity_keys[entity_type]} {{name: $name}})
                            SET e.mentions = e.mentions + 1
                            """,
                            name=entity_value
                        )

                    else:
                        # Insert new entity in MongoDB & Neo4j
                        entity_collection.insert_one({entity_keys[entity_type]: entity_value, "Count": 1})
                        
                        session.run(
                            f"""
                            CREATE (e:{entity_keys[entity_type]} {{mentions: 1,  name: $name}})
                            """,
                            name=entity_value
                        )
                        
                        new_entities += 1

    return f"Created {new_entities} new entity nodes; {total_entities} entities detected overall"

def update_news_nodes(database, collection, use_testKG=True):
    neo4j_driver = get_neo4j_driver(use_testKG)
    mongo_client = get_mongo_client(URI)
    news_db = mongo_client[database]

    # Find new news articles
    new_news = list(news_db[collection].find())

    if not new_news:
        return f"No new News nodes were created (collection '{collection}' was empty)"
    
    unique_news = pd.DataFrame(new_news).groupby(['Headline', 'Updated_Date']).ngroups

    with neo4j_driver.session() as session:
        for news in new_news:
            # Insert News Node
            session.run(
                """
                MERGE (n:News {headline: $headline, date: $updated_date})
                SET n.source = $source, n.link = $link, n.date = $updated_date,
                    n.headline_sentiment = $headline_sentiment, n.article_sentiment = $article_sentiment,
                    n.sentiment_confidence = $sentiment_confidence
                """,
                headline=news["Headline"], updated_date=news["Updated_Date"], source=news["Source"],
                link=news["Link"], headline_sentiment=news["Headline Sentiment"],
                article_sentiment=news["Article Sentiment"], sentiment_confidence=news["Sentiment Confidence"]
            )

            # Link to OilPrice (if exists)
            session.run(
                """
                MATCH (n:News {headline: $headline, date: $updated_date}), (o:OilPrice {date: $updated_date})
                MERGE (o)-[:HAS_NEWS]->(n)
                """,
                headline=news["Headline"], updated_date=news["Updated_Date"]
            )

            # Link News to Entities
            for loc in news["Locations"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline, date: $updated_date}), (l:Location {name: $loc})
                    MERGE (n)-[:MENTIONS]->(l)
                    """,
                    headline=news["Headline"], updated_date=news["Updated_Date"], loc=loc
                )

            for org in news["Organizations"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline, date: $updated_date}), (o:Organization {name: $org})
                    MERGE (n)-[:MENTIONS]->(o)
                    """,
                    headline=news["Headline"], updated_date=news["Updated_Date"], org=org
                )

            for topic in news["Topics"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline, date: $updated_date}), (t:Topic {name: $topic})
                    MERGE (n)-[:MENTIONS]->(t)
                    """,
                    headline=news["Headline"], updated_date=news["Updated_Date"], topic=topic
                )

            for event in news["Events"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline, date: $updated_date}), (e:Event {name: $event})
                    MERGE (n)-[:MENTIONS]->(e)
                    """,
                    headline=news["Headline"], updated_date=news["Updated_Date"], event=event
                )

            for person in news["People"]:
                session.run(
                    """
                    MATCH (n:News {headline: $headline, date: $updated_date}), (p:Person {name: $person})
                    MERGE (n)-[:MENTIONS]->(p)
                    """,
                    headline=news["Headline"], updated_date=news["Updated_Date"], person=person
                )

        # Remove records from collection
        news_db[collection].delete_many({})
    
    return f"Created {unique_news} new News nodes (processed {len(new_news)}) & emptied '{collection}'"

def update_article_nodes(database, collection, use_testKG=True):
    neo4j_driver = get_neo4j_driver(use_testKG)
    mongo_client = get_mongo_client()
    opinions_db = mongo_client[database]

    # Find new news articles
    new_opinions = list(opinions_db[collection].find())

    if not new_opinions:
        return f"No new Opinion Article nodes were created (collection '{collection}' was empty)"
    
    unique_articles = pd.DataFrame(new_opinions).groupby(['Headline', 'Updated_Date']).ngroups

    with neo4j_driver.session() as session:
        for article in new_opinions:
            # Insert Article Node
            session.run(
                """
                MERGE (a:Article {headline: $headline, date: $updated_date})
                SET a.link = $link, a.info = $full_info
                """,
                headline=article["Headline"], updated_date=article["Updated_Date"],
                link=article["Link"], full_info=article["Full_info"]
            )

            # Link to OilPrice (if exists)
            session.run(
                """
                MATCH (a:Article {headline: $headline, date: $updated_date}), (o:OilPrice {date: $updated_date})
                MERGE (o)-[:HAS_ARTICLE]->(a)
                """,
                headline=article["Headline"], updated_date=article["Updated_Date"]
            )

            # Link Article to Entities
            for loc in article["Locations"]:
                session.run(
                    """
                    MATCH (a:Article {headline: $headline, date: $updated_date}), (l:Location {name: $loc})
                    MERGE (a)-[:MENTIONS]->(l)
                    """,
                    headline=article["Headline"], updated_date=article["Updated_Date"], loc=loc
                )

            for org in article["Organizations"]:
                session.run(
                    """
                    MATCH (a:Article {headline: $headline, date: $updated_date}), (o:Organization {name: $org})
                    MERGE (a)-[:MENTIONS]->(o)
                    """,
                    headline=article["Headline"], updated_date=article["Updated_Date"], org=org
                )

            for topic in article["Topics"]:
                session.run(
                    """
                    MATCH (a:Article {headline: $headline, date: $updated_date}), (t:Topic {name: $topic})
                    MERGE (a)-[:MENTIONS]->(t)
                    """,
                    headline=article["Headline"], updated_date=article["Updated_Date"], topic=topic
                )

            for event in article["Events"]:
                session.run(
                    """
                    MATCH (a:Article {headline: $headline, date: $updated_date}), (e:Event {name: $event})
                    MERGE (a)-[:MENTIONS]->(e)
                    """,
                    headline=article["Headline"], updated_date=article["Updated_Date"], event=event
                )

            for person in article["People"]:
                session.run(
                    """
                    MATCH (a:Article {headline: $headline, date: $updated_date}), (p:Person {name: $person})
                    MERGE (a)-[:MENTIONS]->(p)
                    """,
                    headline=article["Headline"], updated_date=article["Updated_Date"], person=person
                )

        # Remove records from collection
        opinions_db[collection].delete_many({})
    
    return f"Created {unique_articles} new Opinion Article nodes (processed {len(new_opinions)}) & emptied '{collection}'"

