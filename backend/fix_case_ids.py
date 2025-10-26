"""
Script to retroactively add case_id to existing nodes in Neo4j.
Run this once to fix existing data.
"""
import os
import neo4j
from dotenv import load_dotenv

load_dotenv()

def fix_case_ids():
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "admin123")
    
    driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        # Tag all nodes without case_id as "test" (since your uploads are in test folder)
        result = session.run(
            """
            MATCH (n)
            WHERE n.case_id IS NULL
            SET n.case_id = 'test'
            RETURN count(n) as updated_count
            """
        )
        record = result.single()
        if record:
            print(f"Tagged {record['updated_count']} nodes with case_id: test")
    
    driver.close()
    print("Done!")

if __name__ == "__main__":
    fix_case_ids()
