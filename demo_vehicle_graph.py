#!/usr/bin/env python3
"""
Demo script for Vehicle Lifecycle Management Knowledge Graph
This script demonstrates the vehicle lifecycle graph data and saves it to Neo4j
"""

import os
import sys
from datetime import datetime
from neo4j import GraphDatabase
from streamlit_agraph import Node, Edge
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to sys.path to import from app.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import generate_vehicle_lifecycle_graph, Neo4jConnection

def print_graph_summary(nodes, edges):
    """Print a summary of the graph structure"""
    print("🚗 Vehicle Lifecycle Management Knowledge Graph")
    print("=" * 60)
    print(f"📊 Graph Statistics:")
    print(f"   • Nodes: {len(nodes)}")
    print(f"   • Edges: {len(edges)}")
    print()
    
    # Group nodes by category
    lifecycle_nodes = []
    stakeholder_nodes = []
    component_nodes = []
    data_nodes = []
    
    for node in nodes:
        if node.id in ['design', 'manufacturing', 'assembly', 'testing', 'delivery', 
                      'registration', 'operation', 'maintenance', 'inspection', 
                      'repair', 'recall', 'disposal']:
            lifecycle_nodes.append(node)
        elif node.id in ['manufacturer', 'dealer', 'owner', 'service_center', 
                        'regulator', 'insurer', 'recycler']:
            stakeholder_nodes.append(node)
        elif node.id in ['engine', 'transmission', 'brakes', 'electronics', 'body']:
            component_nodes.append(node)
        elif node.id in ['vin', 'service_record', 'warranty', 'manual', 'compliance']:
            data_nodes.append(node)
    
    print("🔄 Lifecycle Stages:")
    for node in lifecycle_nodes:
        print(f"   • {node.label} ({node.id})")
    
    print("\n👥 Stakeholders:")
    for node in stakeholder_nodes:
        print(f"   • {node.label} ({node.id})")
    
    print("\n🔧 Vehicle Components:")
    for node in component_nodes:
        print(f"   • {node.label} ({node.id})")
    
    print("\n📋 Data & Documentation:")
    for node in data_nodes:
        print(f"   • {node.label} ({node.id})")
    
    print("\n🔗 Key Relationships:")
    for edge in edges[:10]:  # Show first 10 relationships
        print(f"   • {edge.source} --[{edge.label}]--> {edge.to}")
    if len(edges) > 10:
        print(f"   ... and {len(edges) - 10} more relationships")

def save_to_neo4j(nodes, edges):
    """Save the vehicle lifecycle graph to Neo4j"""
    try:
        # Connect to Neo4j (using environment variables)
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        username = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        print(f"\n🔌 Connecting to Neo4j at {uri}...")
        conn = Neo4jConnection(uri, username, password)
        
        if not conn.test_connection():
            print("❌ Failed to connect to Neo4j. Make sure Neo4j is running.")
            return False
        
        print("✅ Connected to Neo4j successfully!")
        
        # Save the graph
        graph_name = "vehicle_lifecycle_demo"
        description = "Demo graph showing vehicle lifecycle management with stakeholders, components, and processes"
        
        print(f"\n💾 Saving graph '{graph_name}' to Neo4j...")
        success, error = conn.save_graph(graph_name, description, nodes, edges)
        
        if success:
            print("✅ Graph saved successfully!")
            print(f"   • Graph name: {graph_name}")
            print(f"   • Description: {description}")
            print(f"   • Nodes saved: {len(nodes)}")
            print(f"   • Edges saved: {len(edges)}")
            
            # Print Cypher queries to explore the data
            print("\n🔍 Explore the data in Neo4j Browser with these queries:")
            print("   • View all nodes: MATCH (n:KGNode) RETURN n")
            print("   • View all relationships: MATCH (a:KGNode)-[r:RELATED]->(b:KGNode) RETURN a, r, b")
            print("   • View lifecycle flow: MATCH p=(a:KGNode)-[:RELATED*]->(b:KGNode) WHERE a.id='design' AND b.id='disposal' RETURN p")
            print("   • View vehicle components: MATCH (v:KGNode {id:'vehicle'})-[:RELATED]->(c:KGNode) RETURN v, c")
            print("   • View stakeholder relationships: MATCH (s:KGNode)-[:RELATED]->(t:KGNode) WHERE s.id IN ['manufacturer', 'dealer', 'owner'] RETURN s, t")
            
            return True
        else:
            print(f"❌ Failed to save graph: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        return False

def main():
    """Main demo function"""
    print("🚀 Vehicle Lifecycle Management Knowledge Graph Demo")
    print("=" * 60)
    
    # Generate the vehicle lifecycle graph
    print("🔄 Generating vehicle lifecycle graph...")
    nodes, edges = generate_vehicle_lifecycle_graph()
    
    # Print graph summary
    print_graph_summary(nodes, edges)
    
    # Save to Neo4j automatically
    print("\n" + "=" * 60)
    print("💾 Saving graph to Neo4j...")
    
    if save_to_neo4j(nodes, edges):
        print("\n🎉 Demo completed successfully!")
        print("🌐 Open Neo4j Browser at http://localhost:7474 to explore the data")
        print("🌐 Open Streamlit app at http://localhost:8501 to visualize the graph")
    else:
        print("\n⚠️  Demo completed but graph was not saved to Neo4j")
        print("💡 Make sure Neo4j is running with 'make infrastructure-up'")

if __name__ == "__main__":
    main()