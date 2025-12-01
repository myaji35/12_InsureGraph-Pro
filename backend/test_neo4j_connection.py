"""
Test Neo4j connection
"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "change-me-in-production")

print("=" * 70)
print("Neo4j Connection Test")
print("=" * 70)
print(f"URI: {NEO4J_URI}")
print(f"User: {NEO4J_USER}")
print(f"Password: {'*' * len(NEO4J_PASSWORD)}")
print("-" * 70)

try:
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_pool_size=50
    )

    # Verify connectivity
    driver.verify_connectivity()

    print("✅ Connection successful!")

    # Test query
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        record = result.single()
        print(f"✅ Test query result: {record['test']}")

    # Check database
    with driver.session() as session:
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        print(f"✅ Existing labels: {labels if labels else 'None (empty database)'}")

    driver.close()
    print("\n" + "=" * 70)
    print("🎉 Neo4j is ready to use!")
    print("=" * 70)

except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if Neo4j container is running: docker ps | grep neo4j")
    print("2. Check Neo4j logs: docker logs neo4j-townin")
    print("3. Try resetting password:")
    print("   docker exec -it neo4j-townin cypher-shell -u neo4j -p <current-password>")
    print("   ALTER USER neo4j SET PASSWORD 'change-me-in-production';")
