#!/usr/bin/env python3
"""
Query Neo4j to show the vehicle lifecycle graph data
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_neo4j():
    """Connect to Neo4j database"""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "8^@Cxgqyqgn%9BDY9^4L")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        return driver
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        return None

def run_query(driver, query, description):
    """Run a query and display results"""
    print(f"\n🔍 {description}")
    print("=" * 50)
    
    try:
        with driver.session() as session:
            result = session.run(query)
            records = list(result)
            
            if not records:
                print("No results found.")
                return
                
            for i, record in enumerate(records[:10]):  # Show first 10 results
                print(f"{i+1}. {record}")
                
            if len(records) > 10:
                print(f"... and {len(records) - 10} more results")
            
            print(f"\nTotal results: {len(records)}")
            
    except Exception as e:
        print(f"❌ Error running query: {e}")

def main():
    """Main function to demonstrate Neo4j queries"""
    print("🔍 Neo4j Vehicle Lifecycle Graph Query Demo")
    print("=" * 60)
    
    # Connect to Neo4j
    driver = connect_to_neo4j()
    if not driver:
        print("❌ Could not connect to Neo4j. Make sure it's running.")
        return
    
    print("✅ Connected to Neo4j successfully!")
    
    # Query 1: All nodes
    query1 = """
    MATCH (n:KGNode) 
    WHERE n.graph_name = 'vehicle_lifecycle_demo'
    RETURN n.id, n.label, n.color
    ORDER BY n.label
    """
    run_query(driver, query1, "All Vehicle Lifecycle Nodes")
    
    # Query 2: All relationships
    query2 = """
    MATCH (a:KGNode)-[r:RELATED]->(b:KGNode) 
    WHERE a.graph_name = 'vehicle_lifecycle_demo'
    RETURN a.id, r.label, b.id
    ORDER BY a.id, b.id
    """
    run_query(driver, query2, "All Relationships")
    
    # Query 3: Lifecycle flow (design to disposal)
    query3 = """
    MATCH path = (start:KGNode {id: 'design'})-[:RELATED*]->(end:KGNode {id: 'disposal'})
    WHERE start.graph_name = 'vehicle_lifecycle_demo'
    WITH path, length(path) as pathLength
    ORDER BY pathLength
    LIMIT 1
    RETURN [node in nodes(path) | node.label] as lifecycle_stages
    """
    run_query(driver, query3, "Shortest Lifecycle Path (Design → Disposal)")
    
    # Query 4: Vehicle components
    query4 = """
    MATCH (v:KGNode {id: 'vehicle'})-[:RELATED]->(c:KGNode)
    WHERE v.graph_name = 'vehicle_lifecycle_demo'
    RETURN v.label, c.label, c.id
    ORDER BY c.label
    """
    run_query(driver, query4, "Vehicle Components")
    
    # Query 5: Stakeholder responsibilities
    query5 = """
    MATCH (s:KGNode)-[r:RELATED]->(t:KGNode)
    WHERE s.graph_name = 'vehicle_lifecycle_demo'
    AND s.id IN ['manufacturer', 'dealer', 'owner', 'service_center', 'regulator']
    RETURN s.label as stakeholder, r.label as relationship, t.label as target
    ORDER BY s.label, t.label
    """
    run_query(driver, query5, "Stakeholder Responsibilities")
    
    # Query 6: Maintenance-related nodes
    query6 = """
    MATCH (m:KGNode {id: 'maintenance'})-[:RELATED*1..2]-(related:KGNode)
    WHERE m.graph_name = 'vehicle_lifecycle_demo'
    RETURN DISTINCT related.label, related.id
    ORDER BY related.label
    """
    run_query(driver, query6, "Maintenance-Related Entities")
    
    # Query 7: Graph statistics
    query7 = """
    MATCH (n:KGNode) 
    WHERE n.graph_name = 'vehicle_lifecycle_demo'
    WITH count(n) as nodeCount
    MATCH (a:KGNode)-[r:RELATED]->(b:KGNode)
    WHERE a.graph_name = 'vehicle_lifecycle_demo'
    WITH nodeCount, count(r) as edgeCount
    RETURN nodeCount, edgeCount
    """
    run_query(driver, query7, "Graph Statistics")
    
    # Close connection
    driver.close()
    
    print("\n🎉 Neo4j query demo completed!")
    print("🌐 Open Neo4j Browser at http://localhost:7474 to run these queries interactively")
    print("🌐 Open Streamlit app at http://localhost:8501 to visualize the graph")

if __name__ == "__main__":
    main()