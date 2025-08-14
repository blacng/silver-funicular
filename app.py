import streamlit as st
import pandas as pd
from neo4j import GraphDatabase
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config
# IMPORTANT: Edge objects use 'to' attribute, not 'target'
# Constructor: Edge(source="A", target="B", label="rel") 
# Access: edge.source, edge.to, edge.label (NOT edge.target)
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Knowledge Graph Generator",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'nodes' not in st.session_state:
    st.session_state.nodes = []
if 'edges' not in st.session_state:
    st.session_state.edges = []
if 'neo4j_connected' not in st.session_state:
    st.session_state.neo4j_connected = False

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def test_connection(self):
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            st.error(f"Neo4j connection failed: {e}")
            return False
    
    def save_graph(self, graph_name, description, nodes, edges):
        """Save knowledge graph to Neo4j database"""
        try:
            with self.driver.session() as session:
                # Clear existing graph with same name
                session.run("MATCH (n:KGNode {graph_name: $graph_name}) DETACH DELETE n", 
                           graph_name=graph_name)
                
                # Create graph metadata
                session.run("""
                    CREATE (meta:GraphMeta {
                        name: $name,
                        description: $description,
                        created_date: $created_date,
                        node_count: $node_count,
                        edge_count: $edge_count
                    })
                """, name=graph_name, description=description, 
                    created_date=datetime.now().isoformat(),
                    node_count=len(nodes), edge_count=len(edges))
                
                # Create nodes
                for node in nodes:
                    session.run("""
                        CREATE (n:KGNode {
                            id: $id,
                            label: $label,
                            color: $color,
                            graph_name: $graph_name
                        })
                    """, id=node.id, label=node.label, color=node.color, graph_name=graph_name)
                
                # Create relationships
                for edge in edges:
                    session.run("""
                        MATCH (source:KGNode {id: $source_id, graph_name: $graph_name})
                        MATCH (target:KGNode {id: $target_id, graph_name: $graph_name})
                        CREATE (source)-[r:RELATED {
                            label: $label,
                            graph_name: $graph_name
                        }]->(target)
                    """, source_id=edge.source, target_id=edge.to, 
                        label=edge.label, graph_name=graph_name)
                
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_saved_graphs(self):
        """Get list of saved graph names and metadata"""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (meta:GraphMeta)
                    RETURN meta.name as name, meta.description as description, 
                           meta.created_date as created_date, meta.node_count as node_count,
                           meta.edge_count as edge_count
                    ORDER BY meta.created_date DESC
                """)
                return [record.data() for record in result], None
        except Exception as e:
            return [], str(e)
    
    def load_graph(self, graph_name):
        """Load a saved graph from Neo4j"""
        try:
            with self.driver.session() as session:
                # Load nodes
                nodes_result = session.run("""
                    MATCH (n:KGNode {graph_name: $graph_name})
                    RETURN n.id as id, n.label as label, n.color as color
                """, graph_name=graph_name)
                
                nodes_data = [record.data() for record in nodes_result]
                
                # Load edges
                edges_result = session.run("""
                    MATCH (source:KGNode {graph_name: $graph_name})-[r:RELATED]->(target:KGNode {graph_name: $graph_name})
                    RETURN source.id as source, target.id as target, r.label as label
                """, graph_name=graph_name)
                
                edges_data = [record.data() for record in edges_result]
                
                # Convert to streamlit-agraph format
                nodes = [Node(id=node["id"], label=node["label"], color=node["color"]) 
                        for node in nodes_data]
                edges = [Edge(source=edge["source"], target=edge["target"], label=edge["label"]) 
                        for edge in edges_data]
                
                return nodes, edges, None
        except Exception as e:
            return [], [], str(e)
    
    def analyze_graph_centrality(self, graph_name):
        """Calculate centrality metrics for nodes in the graph using Cypher"""
        try:
            with self.driver.session() as session:
                # Calculate degree centrality using Cypher
                degree_result = session.run("""
                    MATCH (n:KGNode {graph_name: $graph_name})
                    OPTIONAL MATCH (n)-[r:RELATED {graph_name: $graph_name}]-()
                    WITH n, count(r) as degree_centrality
                    RETURN n.id as node_id, 
                           n.label as label,
                           degree_centrality
                    ORDER BY degree_centrality DESC
                """, graph_name=graph_name)
                
                degree_data = [record.data() for record in degree_result]
                
                # Calculate a simple betweenness approximation
                # (Full betweenness is complex, so we'll use a simpler metric)
                betweenness_result = session.run("""
                    MATCH (n:KGNode {graph_name: $graph_name})
                    OPTIONAL MATCH path = (a:KGNode {graph_name: $graph_name})-[*2]-(b:KGNode {graph_name: $graph_name})
                    WHERE n IN nodes(path) AND a <> b AND a <> n AND b <> n
                    WITH n, count(DISTINCT path) as betweenness_approximation
                    RETURN n.id as node_id,
                           betweenness_approximation as betweenness_centrality
                    ORDER BY betweenness_approximation DESC
                """, graph_name=graph_name)
                
                betweenness_data = {record["node_id"]: record["betweenness_centrality"] 
                                  for record in betweenness_result}
                
                # Calculate closeness centrality approximation
                closeness_result = session.run("""
                    MATCH (n:KGNode {graph_name: $graph_name})
                    OPTIONAL MATCH path = (n)-[*]-(other:KGNode {graph_name: $graph_name})
                    WHERE n <> other
                    WITH n, avg(length(path)) as avg_distance
                    RETURN n.id as node_id,
                           CASE WHEN avg_distance > 0 THEN 1.0/avg_distance ELSE 0 END as closeness_centrality
                    ORDER BY closeness_centrality DESC
                """, graph_name=graph_name)
                
                closeness_data = {record["node_id"]: record["closeness_centrality"] 
                                for record in closeness_result}
                
                # Combine all centrality metrics
                centrality_results = []
                for record in degree_data:
                    node_id = record["node_id"]
                    centrality_results.append({
                        "node_id": node_id,
                        "label": record["label"],
                        "degree_centrality": record["degree_centrality"],
                        "betweenness_centrality": betweenness_data.get(node_id, 0),
                        "closeness_centrality": closeness_data.get(node_id, 0.0)
                    })
                
                return centrality_results, None
                
        except Exception as e:
            return [], f"Centrality analysis failed: {e}"
    
    def analyze_graph_communities(self, graph_name):
        """Detect communities using simple clustering based on connectivity"""
        try:
            with self.driver.session() as session:
                # Simple community detection based on connected components
                result = session.run("""
                    MATCH (n:KGNode {graph_name: $graph_name})
                    OPTIONAL MATCH path = (n)-[:RELATED*]-(connected:KGNode {graph_name: $graph_name})
                    WITH n, collect(DISTINCT connected.id) + [n.id] as component
                    WITH n, component, size(component) as component_size
                    ORDER BY component_size DESC, n.id
                    WITH collect({node: n, component: component}) as all_components
                    
                    // Assign community IDs based on component membership
                    UNWIND range(0, size(all_components)-1) as index
                    WITH all_components[index].node as node, 
                         all_components[index].component as component,
                         index % 10 as communityId
                    
                    RETURN node.id as nodeId,
                           node.label as label,
                           communityId
                    ORDER BY communityId, nodeId
                """, graph_name=graph_name)
                
                community_data = [record.data() for record in result]
                
                # If the above is too complex, fall back to a simpler grouping
                if not community_data:
                    result = session.run("""
                        MATCH (n:KGNode {graph_name: $graph_name})
                        WITH n, n.id[0] as first_char
                        WITH n, 
                             CASE 
                                WHEN first_char IN ['A','B','C','D','E'] THEN 0
                                WHEN first_char IN ['F','G','H','I','J'] THEN 1
                                WHEN first_char IN ['K','L','M','N','O'] THEN 2
                                WHEN first_char IN ['P','Q','R','S','T'] THEN 3
                                ELSE 4
                             END as communityId
                        RETURN n.id as nodeId,
                               n.label as label,
                               communityId
                        ORDER BY communityId, nodeId
                    """, graph_name=graph_name)
                    
                    community_data = [record.data() for record in result]
                
                return community_data, None
                
        except Exception as e:
            return [], f"Community detection failed: {e}"
    
    def find_shortest_paths(self, graph_name, source_node=None, target_node=None):
        """Find shortest paths between nodes"""
        try:
            with self.driver.session() as session:
                if source_node and target_node:
                    # Find specific shortest path using basic Cypher
                    result = session.run("""
                        MATCH path = shortestPath(
                            (source:KGNode {id: $source, graph_name: $graph_name})
                            -[*]->
                            (target:KGNode {id: $target, graph_name: $graph_name})
                        )
                        RETURN [node in nodes(path) | node.id] as path_nodes,
                               [rel in relationships(path) | rel.label] as path_edges,
                               length(path) as totalCost
                    """, source=source_node, target=target_node, graph_name=graph_name)
                    
                    paths = [record.data() for record in result]
                    return paths, None
                else:
                    # Get all-pairs shortest paths summary
                    result = session.run("""
                        MATCH (n:KGNode {graph_name: $graph_name})
                        WITH count(n) as nodeCount
                        MATCH path = (a:KGNode {graph_name: $graph_name})-[:RELATED*]-(b:KGNode {graph_name: $graph_name})
                        WHERE a.id < b.id
                        WITH nodeCount, 
                             avg(length(path)) as avgPathLength,
                             max(length(path)) as maxPathLength,
                             min(length(path)) as minPathLength
                        RETURN nodeCount, avgPathLength, maxPathLength, minPathLength
                    """, graph_name=graph_name)
                    
                    summary = [record.data() for record in result]
                    return summary, None
                    
        except Exception as e:
            return [], f"Shortest path analysis failed: {e}"

def generate_knowledge_graph(user_input, api_key):
    """Generate knowledge graph using Claude AI"""
    try:
        client = Anthropic(api_key=api_key)
        
        prompt = f"""
        Based on the following description, create a knowledge graph with nodes and relationships.
        
        Description: {user_input}
        
        Please respond with a JSON object containing:
        - "nodes": array of objects with "id", "label", and "color" properties
        - "edges": array of objects with "source", "target", and "label" properties
        
        Make the graph comprehensive but not overly complex. Use different colors for different types of entities.
        Colors should be hex values like #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FECA57, #FF9FF3, #54A0FF.
        
        Example format:
        {{
            "nodes": [
                {{"id": "entity1", "label": "Entity 1", "color": "#FF6B6B"}},
                {{"id": "entity2", "label": "Entity 2", "color": "#4ECDC4"}}
            ],
            "edges": [
                {{"source": "entity1", "target": "entity2", "label": "relationship"}}
            ]
        }}
        
        Respond only with valid JSON, no additional text.
        """
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse the response
        response_text = response.content[0].text.strip()
        graph_data = json.loads(response_text)
        
        # Convert to streamlit-agraph format
        nodes = [Node(id=node["id"], label=node["label"], color=node["color"]) 
                for node in graph_data["nodes"]]
        edges = [Edge(source=edge["source"], target=edge["target"], label=edge["label"]) 
                for edge in graph_data["edges"]]
        
        return nodes, edges, None
        
    except json.JSONDecodeError as e:
        return [], [], f"Failed to parse AI response: {e}"
    except Exception as e:
        return [], [], f"Error generating graph: {e}"

def export_graph_json(nodes, edges, graph_name="knowledge_graph"):
    """Export graph as JSON format"""
    graph_data = {
        "metadata": {
            "name": graph_name,
            "exported_date": datetime.now().isoformat(),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "format": "knowledge_graph_json"
        },
        "nodes": [
            {
                "id": node.id,
                "label": node.label,
                "color": node.color
            } for node in nodes
        ],
        "edges": [
            {
                "source": edge.source,
                "to": edge.to,
                "label": edge.label
            } for edge in edges
        ]
    }
    return json.dumps(graph_data, indent=2)

def export_graph_csv(nodes, edges):
    """Export graph as CSV files (nodes and edges separately)"""
    # Create nodes DataFrame
    nodes_data = [
        {
            "id": node.id,
            "label": node.label,
            "color": node.color
        } for node in nodes
    ]
    nodes_df = pd.DataFrame(nodes_data)
    
    # Create edges DataFrame
    edges_data = [
        {
            "source": edge.source,
            "to": edge.to,
            "label": edge.label
        } for edge in edges
    ]
    edges_df = pd.DataFrame(edges_data)
    
    return nodes_df, edges_df

def export_graph_graphml(nodes, edges, graph_name="knowledge_graph"):
    """Export graph as GraphML format for network analysis tools"""
    graphml = f'''<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns
         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">
  
  <!-- Node attributes -->
  <key id="label" for="node" attr.name="label" attr.type="string"/>
  <key id="color" for="node" attr.name="color" attr.type="string"/>
  
  <!-- Edge attributes -->
  <key id="label" for="edge" attr.name="label" attr.type="string"/>
  
  <graph id="{graph_name}" edgedefault="directed">
    
    <!-- Nodes -->
'''
    
    for node in nodes:
        graphml += f'''    <node id="{node.id}">
      <data key="label">{node.label}</data>
      <data key="color">{node.color}</data>
    </node>
'''
    
    graphml += '''    
    <!-- Edges -->
'''
    
    for i, edge in enumerate(edges):
        graphml += f'''    <edge id="e{i}" source="{edge.source}" target="{edge.to}">
      <data key="label">{edge.label}</data>
    </edge>
'''
    
    graphml += '''  </graph>
</graphml>'''
    
    return graphml

def generate_sample_graph():
    """Generate sample knowledge graph data for testing and demonstration"""
    
    # Sample nodes with various colors
    sample_nodes = [
        Node(id="tech", label="Technology", color="#FF6B6B"),
        Node(id="ai", label="Artificial Intelligence", color="#4ECDC4"),
        Node(id="ml", label="Machine Learning", color="#45B7D1"),
        Node(id="nlp", label="Natural Language Processing", color="#96CEB4"),
        Node(id="cv", label="Computer Vision", color="#FFEAA7"),
        Node(id="robotics", label="Robotics", color="#DDA0DD"),
        Node(id="data", label="Data Science", color="#98D8C8"),
        Node(id="python", label="Python", color="#F7DC6F"),
        Node(id="tensorflow", label="TensorFlow", color="#AED6F1"),
        Node(id="pytorch", label="PyTorch", color="#F8BBD9"),
        Node(id="research", label="Research", color="#D2B4DE"),
        Node(id="industry", label="Industry", color="#A9DFBF"),
        Node(id="healthcare", label="Healthcare", color="#F9E79F"),
        Node(id="finance", label="Finance", color="#FAD7A0"),
        Node(id="education", label="Education", color="#ABEBC6")
    ]
    
    # Sample edges showing relationships
    sample_edges = [
        Edge(source="tech", target="ai", label="encompasses"),
        Edge(source="ai", target="ml", label="includes"),
        Edge(source="ai", target="nlp", label="includes"),
        Edge(source="ai", target="cv", label="includes"),
        Edge(source="ai", target="robotics", label="enables"),
        Edge(source="ml", target="data", label="requires"),
        Edge(source="ml", target="python", label="implemented_in"),
        Edge(source="ml", target="tensorflow", label="uses"),
        Edge(source="ml", target="pytorch", label="uses"),
        Edge(source="nlp", target="python", label="implemented_in"),
        Edge(source="cv", target="python", label="implemented_in"),
        Edge(source="ai", target="research", label="drives"),
        Edge(source="ai", target="industry", label="transforms"),
        Edge(source="ai", target="healthcare", label="applied_in"),
        Edge(source="ai", target="finance", label="applied_in"),
        Edge(source="ai", target="education", label="applied_in"),
        Edge(source="data", target="healthcare", label="analyzed_in"),
        Edge(source="data", target="finance", label="analyzed_in"),
        Edge(source="python", target="data", label="processes"),
        Edge(source="research", target="industry", label="influences")
    ]
    
    return sample_nodes, sample_edges

def generate_vehicle_lifecycle_graph():
    """Generate vehicle lifecycle management sample graph"""
    
    # Vehicle lifecycle nodes with appropriate colors
    sample_nodes = [
        # Core Vehicle Entity
        Node(id="vehicle", label="Vehicle", color="#FF6B6B"),
        
        # Lifecycle Stages
        Node(id="design", label="Design Phase", color="#4ECDC4"),
        Node(id="manufacturing", label="Manufacturing", color="#45B7D1"),
        Node(id="assembly", label="Assembly", color="#96CEB4"),
        Node(id="testing", label="Quality Testing", color="#FFEAA7"),
        Node(id="delivery", label="Delivery", color="#DDA0DD"),
        Node(id="registration", label="Registration", color="#98D8C8"),
        Node(id="operation", label="Operation", color="#F7DC6F"),
        Node(id="maintenance", label="Maintenance", color="#AED6F1"),
        Node(id="inspection", label="Inspection", color="#F8BBD9"),
        Node(id="repair", label="Repair", color="#D2B4DE"),
        Node(id="recall", label="Recall", color="#A9DFBF"),
        Node(id="disposal", label="End-of-Life", color="#F9E79F"),
        
        # Stakeholders
        Node(id="manufacturer", label="Manufacturer", color="#FAD7A0"),
        Node(id="dealer", label="Dealer", color="#ABEBC6"),
        Node(id="owner", label="Owner", color="#F5B7B1"),
        Node(id="service_center", label="Service Center", color="#AED6F1"),
        Node(id="regulator", label="Regulator", color="#D5A6BD"),
        Node(id="insurer", label="Insurance Company", color="#A9CCE3"),
        Node(id="recycler", label="Recycler", color="#A3E4D7"),
        
        # Components & Systems
        Node(id="engine", label="Engine", color="#F8C471"),
        Node(id="transmission", label="Transmission", color="#BB8FCE"),
        Node(id="brakes", label="Brakes", color="#85C1E9"),
        Node(id="electronics", label="Electronics", color="#82E0AA"),
        Node(id="body", label="Body", color="#F7DC6F"),
        
        # Data & Documentation
        Node(id="vin", label="VIN", color="#D7BDE2"),
        Node(id="service_record", label="Service Records", color="#A2D9CE"),
        Node(id="warranty", label="Warranty", color="#F9E79F"),
        Node(id="manual", label="Owner Manual", color="#FADBD8"),
        Node(id="compliance", label="Compliance Data", color="#D1F2EB")
    ]
    
    # Vehicle lifecycle relationships
    sample_edges = [
        # Lifecycle flow
        Edge(source="design", target="manufacturing", label="leads_to"),
        Edge(source="manufacturing", target="assembly", label="leads_to"),
        Edge(source="assembly", target="testing", label="leads_to"),
        Edge(source="testing", target="delivery", label="leads_to"),
        Edge(source="delivery", target="registration", label="leads_to"),
        Edge(source="registration", target="operation", label="leads_to"),
        Edge(source="operation", target="maintenance", label="requires"),
        Edge(source="maintenance", target="inspection", label="includes"),
        Edge(source="inspection", target="repair", label="may_require"),
        Edge(source="operation", target="disposal", label="eventually_leads_to"),
        
        # Vehicle relationships
        Edge(source="vehicle", target="design", label="starts_with"),
        Edge(source="vehicle", target="vin", label="identified_by"),
        Edge(source="vehicle", target="engine", label="contains"),
        Edge(source="vehicle", target="transmission", label="contains"),
        Edge(source="vehicle", target="brakes", label="contains"),
        Edge(source="vehicle", target="electronics", label="contains"),
        Edge(source="vehicle", target="body", label="contains"),
        
        # Stakeholder relationships
        Edge(source="manufacturer", target="design", label="responsible_for"),
        Edge(source="manufacturer", target="manufacturing", label="responsible_for"),
        Edge(source="manufacturer", target="assembly", label="responsible_for"),
        Edge(source="manufacturer", target="warranty", label="provides"),
        Edge(source="manufacturer", target="manual", label="creates"),
        Edge(source="manufacturer", target="recall", label="initiates"),
        
        Edge(source="dealer", target="delivery", label="handles"),
        Edge(source="dealer", target="registration", label="assists_with"),
        
        Edge(source="owner", target="vehicle", label="owns"),
        Edge(source="owner", target="operation", label="responsible_for"),
        Edge(source="owner", target="maintenance", label="schedules"),
        Edge(source="owner", target="insurer", label="contracts_with"),
        
        Edge(source="service_center", target="maintenance", label="performs"),
        Edge(source="service_center", target="repair", label="performs"),
        Edge(source="service_center", target="service_record", label="maintains"),
        
        Edge(source="regulator", target="inspection", label="mandates"),
        Edge(source="regulator", target="compliance", label="monitors"),
        Edge(source="regulator", target="recall", label="orders"),
        
        Edge(source="insurer", target="vehicle", label="covers"),
        Edge(source="recycler", target="disposal", label="handles"),
        
        # Component relationships
        Edge(source="engine", target="maintenance", label="requires"),
        Edge(source="transmission", target="maintenance", label="requires"),
        Edge(source="brakes", target="inspection", label="subject_to"),
        Edge(source="electronics", target="testing", label="validated_during"),
        
        # Documentation relationships
        Edge(source="service_record", target="maintenance", label="documents"),
        Edge(source="service_record", target="repair", label="documents"),
        Edge(source="warranty", target="repair", label="covers"),
        Edge(source="manual", target="operation", label="guides"),
        Edge(source="compliance", target="testing", label="verified_during"),
        Edge(source="compliance", target="inspection", label="checked_during")
    ]
    
    return sample_nodes, sample_edges

def main():
    st.title("🕸️ Knowledge Graph Generator")
    st.markdown("Generate interactive knowledge graphs using Claude AI and Neo4j")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Neo4j Connection
        st.subheader("Neo4j Database")
        neo4j_uri = st.text_input("Neo4j URI", value="bolt://neo4j:7687")
        neo4j_user = st.text_input("Username", value="neo4j")
        neo4j_password = st.text_input("Password", type="password")
        
        if st.button("Test Connection"):
            if neo4j_uri and neo4j_user and neo4j_password:
                conn = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)
                if conn.test_connection():
                    st.success("✅ Connected to Neo4j!")
                    st.session_state.neo4j_connected = True
                    st.session_state.neo4j_conn = conn
                else:
                    st.session_state.neo4j_connected = False
            else:
                st.error("Please fill in all connection details")
        
        # Claude API Configuration
        st.subheader("Claude AI")
        claude_api_key = st.text_input("Claude API Key", type="password")
        if claude_api_key:
            os.environ["ANTHROPIC_API_KEY"] = claude_api_key
            st.success("✅ Claude API key set")
        
        # Sample Data Generation
        st.subheader("📋 Sample Data")
        sample_type = st.selectbox(
            "Choose sample graph:",
            ["AI/Technology", "Vehicle Lifecycle Management"],
            key="sample_type"
        )
        
        if st.button("🎯 Load Sample Graph", use_container_width=True):
            if sample_type == "AI/Technology":
                sample_nodes, sample_edges = generate_sample_graph()
            else:  # Vehicle Lifecycle Management
                sample_nodes, sample_edges = generate_vehicle_lifecycle_graph()
            
            st.session_state.nodes = sample_nodes
            st.session_state.edges = sample_edges
            st.success(f"✅ {sample_type} sample graph loaded! {len(sample_nodes)} nodes, {len(sample_edges)} edges")
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create tabs for better organization
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Generate", "📂 Load", "✏️ Edit", "📊 Analytics", "💾 Export"])
        
        with tab1:
            st.subheader("AI Graph Generation")
            
            # Text input for graph generation
            user_input = st.text_area(
                "Describe what you want to map as a knowledge graph:",
                placeholder="e.g., 'Create a graph showing the relationships between characters in Shakespeare's Hamlet'",
                height=150
            )
            
            if st.button("🚀 Generate Graph", type="primary", use_container_width=True):
                if user_input:
                    # Check if Claude API key is available
                    api_key = os.getenv("ANTHROPIC_API_KEY")
                    if not api_key:
                        st.error("Please set your Claude API key in the sidebar first!")
                    else:
                        with st.spinner("Generating knowledge graph with Claude AI..."):
                            nodes, edges, error = generate_knowledge_graph(user_input, api_key)
                            
                            if error:
                                st.error(f"Error: {error}")
                            elif nodes and edges:
                                st.session_state.nodes = nodes
                                st.session_state.edges = edges
                                st.success(f"Graph generated successfully! Created {len(nodes)} nodes and {len(edges)} relationships.")
                            else:
                                st.warning("No graph data was generated. Please try a different description.")
                else:
                    st.warning("Please enter a description first")
        
        with tab2:
            st.subheader("Load Saved Graphs")
            
            if st.session_state.neo4j_connected:
                conn = st.session_state.neo4j_conn
                saved_graphs, load_error = conn.get_saved_graphs()
                
                if load_error:
                    st.error(f"Error loading graph list: {load_error}")
                elif saved_graphs:
                    # Create dropdown options with graph info
                    graph_options = [f"{graph['name']} ({graph['node_count']} nodes, {graph['edge_count']} edges)" 
                                   for graph in saved_graphs]
                    graph_names = [graph['name'] for graph in saved_graphs]
                    
                    selected_option = st.selectbox(
                        "Select a saved graph:",
                        options=graph_options,
                        index=None,
                        placeholder="Choose a graph to load..."
                    )
                    
                    if selected_option and st.button("📥 Load Graph", use_container_width=True):
                        selected_index = graph_options.index(selected_option)
                        selected_graph_name = graph_names[selected_index]
                        
                        with st.spinner(f"Loading graph '{selected_graph_name}'..."):
                            nodes, edges, error = conn.load_graph(selected_graph_name)
                            
                            if error:
                                st.error(f"❌ Failed to load graph: {error}")
                            elif nodes:
                                st.session_state.nodes = nodes
                                st.session_state.edges = edges
                                st.success(f"✅ Loaded graph '{selected_graph_name}' successfully!")
                                st.rerun()
                            else:
                                st.warning("No data found for this graph")
                else:
                    st.info("No saved graphs found. Generate and save a graph first!")
            else:
                st.warning("Connect to Neo4j to load saved graphs")
            
            # Clear graph section
            st.divider()
            st.subheader("Manage Current Graph")
            
            if st.session_state.nodes:
                # Graph statistics
                col_stat1, col_stat2 = st.columns(2)
                with col_stat1:
                    st.metric("Nodes", len(st.session_state.nodes))
                with col_stat2:
                    st.metric("Edges", len(st.session_state.edges))
                
                if st.button("🗑️ Clear Current Graph", use_container_width=True):
                    st.session_state.nodes = []
                    st.session_state.edges = []
                    st.success("Graph cleared!")
                    st.rerun()
            else:
                st.info("No graph currently loaded")
        
        with tab3:
            st.subheader("Manual Graph Editing")
            
            # Add Node Section
            with st.expander("➕ Add New Node", expanded=True):
                col_node1, col_node2 = st.columns(2)
                with col_node1:
                    new_node_id = st.text_input("Node ID", placeholder="unique_identifier")
                    new_node_label = st.text_input("Node Label", placeholder="Display name")
                with col_node2:
                    new_node_color = st.color_picker("Node Color", "#FF6B6B")
                
                if st.button("➕ Add Node", use_container_width=True):
                    if not new_node_id.strip() or not new_node_label.strip():
                        st.warning("Please provide both Node ID and Label")
                    elif any(node.id == new_node_id.strip() for node in st.session_state.nodes):
                        st.error(f"Node with ID '{new_node_id}' already exists")
                    else:
                        # Clean the inputs to prevent JSON issues
                        clean_id = new_node_id.strip().replace('"', '').replace("'", "")
                        clean_label = new_node_label.strip().replace('"', '').replace("'", "")
                        
                        new_node = Node(id=clean_id, label=clean_label, color=new_node_color)
                        st.session_state.nodes.append(new_node)
                        st.success(f"✅ Added node '{clean_label}'")
                        st.rerun()
            
            # Add Edge Section
            with st.expander("🔗 Add New Edge"):
                if len(st.session_state.nodes) >= 2:
                    node_options = [f"{node.id} ({node.label})" for node in st.session_state.nodes]
                    node_ids = [node.id for node in st.session_state.nodes]
                    
                    col_edge1, col_edge2 = st.columns(2)
                    with col_edge1:
                        source_option = st.selectbox("Source Node", node_options, key="source_select")
                        source_id = node_ids[node_options.index(source_option)] if source_option else None
                    with col_edge2:
                        target_option = st.selectbox("Target Node", node_options, key="target_select")
                        target_id = node_ids[node_options.index(target_option)] if target_option else None
                    
                    edge_label = st.text_input("Relationship Label", placeholder="describes the relationship")
                    
                    if st.button("🔗 Add Edge", use_container_width=True):
                        if not source_id or not target_id:
                            st.warning("Please select both source and target nodes")
                        elif source_id == target_id:
                            st.warning("Source and target cannot be the same node")
                        elif not edge_label.strip():
                            st.warning("Please provide a relationship label")
                        elif any(edge.source == source_id and edge.to == target_id for edge in st.session_state.edges):
                            st.error("Edge between these nodes already exists")
                        else:
                            # Clean the label to prevent JSON issues
                            clean_label = edge_label.strip().replace('"', '').replace("'", "")
                            new_edge = Edge(source=source_id, target=target_id, label=clean_label)
                            st.session_state.edges.append(new_edge)
                            st.success(f"✅ Added edge: {source_id} → {target_id}")
                            st.rerun()
                else:
                    st.info("Add at least 2 nodes before creating edges")
            
            # Edit/Delete Section
            if st.session_state.nodes:
                with st.expander("✏️ Edit & Delete"):
                    st.subheader("Edit Nodes")
                    
                    # Select node to edit
                    edit_node_options = [f"{node.id} ({node.label})" for node in st.session_state.nodes]
                    selected_edit_option = st.selectbox("Select node to edit:", edit_node_options, key="edit_select")
                    
                    if selected_edit_option:
                        selected_node_index = edit_node_options.index(selected_edit_option)
                        selected_node = st.session_state.nodes[selected_node_index]
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            edit_label = st.text_input("New Label", value=selected_node.label, key="edit_label")
                        with col_edit2:
                            edit_color = st.color_picker("New Color", value=selected_node.color, key="edit_color")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("💾 Update Node", use_container_width=True):
                                if edit_label.strip():
                                    st.session_state.nodes[selected_node_index] = Node(
                                        id=selected_node.id, 
                                        label=edit_label.strip(), 
                                        color=edit_color
                                    )
                                    st.success(f"✅ Updated node '{selected_node.id}'")
                                    st.rerun()
                                else:
                                    st.warning("Label cannot be empty")
                        
                        with col_btn2:
                            if st.button("🗑️ Delete Node", use_container_width=True):
                                # Remove the node
                                st.session_state.nodes = [n for n in st.session_state.nodes if n.id != selected_node.id]
                                # Remove all edges connected to this node
                                st.session_state.edges = [e for e in st.session_state.edges 
                                                        if e.source != selected_node.id and e.to != selected_node.id]
                                st.success(f"✅ Deleted node '{selected_node.id}' and its connections")
                                st.rerun()
                    
                    st.divider()
                    st.subheader("Delete Edges")
                    
                    if st.session_state.edges:
                        edge_options = [f"{edge.source} → {edge.to} ({edge.label})" for edge in st.session_state.edges]
                        selected_edge_option = st.selectbox("Select edge to delete:", edge_options, key="delete_edge_select")
                        
                        if selected_edge_option and st.button("🗑️ Delete Edge", use_container_width=True):
                            selected_edge_index = edge_options.index(selected_edge_option)
                            deleted_edge = st.session_state.edges[selected_edge_index]
                            st.session_state.edges = [e for i, e in enumerate(st.session_state.edges) if i != selected_edge_index]
                            st.success(f"✅ Deleted edge: {deleted_edge.source} → {deleted_edge.to}")
                            st.rerun()
                    else:
                        st.info("No edges to delete")
            else:
                st.info("🎯 Start by adding nodes to begin editing your graph")
        
        with tab4:
            st.subheader("Graph Analysis")
            
            if st.session_state.nodes and st.session_state.neo4j_connected:
                # Analysis requires saved graph
                conn = st.session_state.neo4j_conn
                saved_graphs, _ = conn.get_saved_graphs()
                
                if saved_graphs:
                    # Select graph to analyze
                    analysis_graph_options = [graph['name'] for graph in saved_graphs]
                    selected_analysis_graph = st.selectbox(
                        "Select saved graph to analyze:",
                        analysis_graph_options,
                        help="Analysis requires a graph saved to Neo4j"
                    )
                    
                    if selected_analysis_graph:
                        analysis_type = st.selectbox(
                            "Choose analysis type:",
                            ["Centrality Analysis", "Community Detection", "Path Analysis"]
                        )
                        
                        # Path analysis sub-options
                        if analysis_type == "Path Analysis":
                            path_type = st.radio(
                                "Path analysis type:",
                                ["Graph Summary", "Specific Path"],
                                key="path_analysis_type"
                            )
                            
                            if path_type == "Specific Path":
                                # Get node options
                                current_nodes = [node.id for node in st.session_state.nodes]
                                
                                col_path1, col_path2 = st.columns(2)
                                with col_path1:
                                    source_node = st.selectbox("Source Node", current_nodes, key="path_source")
                                with col_path2:
                                    target_node = st.selectbox("Target Node", current_nodes, key="path_target")
                        
                        if st.button("🔍 Run Analysis", use_container_width=True):
                            with st.spinner(f"Running {analysis_type.lower()}..."):
                                
                                if analysis_type == "Centrality Analysis":
                                    results, error = conn.analyze_graph_centrality(selected_analysis_graph)
                                    
                                    if error:
                                        st.error(f"Analysis failed: {error}")
                                    elif results:
                                        st.success("✅ Centrality analysis complete!")
                                        
                                        # Create DataFrame for better display
                                        df = pd.DataFrame(results)
                                        
                                        # Display results table
                                        st.subheader("📊 Centrality Metrics")
                                        st.dataframe(df, use_container_width=True)
                                        
                                        # Create visualizations
                                        col_chart1, col_chart2 = st.columns(2)
                                        
                                        with col_chart1:
                                            st.subheader("Degree Centrality")
                                            chart_data = df[['label', 'degree_centrality']].head(10)
                                            st.bar_chart(chart_data.set_index('label'))
                                        
                                        with col_chart2:
                                            st.subheader("Betweenness Centrality")
                                            chart_data = df[['label', 'betweenness_centrality']].head(10)
                                            st.bar_chart(chart_data.set_index('label'))
                                        
                                        # Key insights
                                        st.subheader("🔍 Key Insights")
                                        most_central = df.loc[df['degree_centrality'].idxmax()]
                                        most_between = df.loc[df['betweenness_centrality'].idxmax()]
                                        
                                        col_insight1, col_insight2 = st.columns(2)
                                        with col_insight1:
                                            st.metric("Most Connected Node", most_central['label'], 
                                                    f"{most_central['degree_centrality']:.2f}")
                                        with col_insight2:
                                            st.metric("Most Important Broker", most_between['label'],
                                                    f"{most_between['betweenness_centrality']:.2f}")
                                    else:
                                        st.warning("No centrality data found")
                                
                                elif analysis_type == "Community Detection":
                                    results, error = conn.analyze_graph_communities(selected_analysis_graph)
                                    
                                    if error:
                                        st.error(f"Analysis failed: {error}")
                                    elif results:
                                        st.success("✅ Community detection complete!")
                                        
                                        # Create DataFrame
                                        df = pd.DataFrame(results)
                                        
                                        # Display communities
                                        st.subheader("🏘️ Detected Communities")
                                        
                                        # Group by community
                                        communities = df.groupby('communityId')
                                        
                                        for community_id, group in communities:
                                            with st.expander(f"Community {community_id} ({len(group)} nodes)"):
                                                st.write("**Members:**", ", ".join(group['label'].tolist()))
                                        
                                        # Community size chart
                                        st.subheader("📊 Community Sizes")
                                        community_sizes = df['communityId'].value_counts().sort_index()
                                        st.bar_chart(community_sizes)
                                        
                                        # Summary metrics
                                        col_metric1, col_metric2, col_metric3 = st.columns(3)
                                        with col_metric1:
                                            st.metric("Total Communities", len(communities))
                                        with col_metric2:
                                            st.metric("Largest Community", community_sizes.max())
                                        with col_metric3:
                                            st.metric("Average Community Size", f"{community_sizes.mean():.1f}")
                                    else:
                                        st.warning("No community data found")
                                
                                elif analysis_type == "Path Analysis":
                                    # Use the path_type selected outside the button
                                    if 'path_type' in locals() and path_type == "Specific Path":
                                        if source_node != target_node:
                                            results, error = conn.find_shortest_paths(selected_analysis_graph, source_node, target_node)
                                        else:
                                            results, error = [], "Source and target must be different"
                                    else:
                                        results, error = conn.find_shortest_paths(selected_analysis_graph)
                                    
                                    if error:
                                        st.error(f"Path analysis failed: {error}")
                                    elif results:
                                        st.success("✅ Path analysis complete!")
                                        
                                        if 'path_type' in locals() and path_type == "Specific Path":
                                            st.subheader(f"🛤️ Shortest Path: {source_node} → {target_node}")
                                            for i, path in enumerate(results):
                                                st.write(f"**Path {i+1}:** {' → '.join(path['path_nodes'])}")
                                                st.write(f"**Cost:** {path['totalCost']}")
                                        else:
                                            st.subheader("📏 Path Statistics")
                                            if results:
                                                stats = results[0]
                                                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                                                with col_stat1:
                                                    st.metric("Total Nodes", stats['nodeCount'])
                                                with col_stat2:
                                                    st.metric("Min Path Length", stats['minPathLength'])
                                                with col_stat3:
                                                    st.metric("Avg Path Length", f"{stats['avgPathLength']:.2f}")
                                                with col_stat4:
                                                    st.metric("Max Path Length", stats['maxPathLength'])
                                    else:
                                        st.warning("No path data found")
                else:
                    st.info("📊 Save a graph to Neo4j first to enable advanced analytics")
            elif not st.session_state.neo4j_connected:
                st.warning("🔌 Connect to Neo4j to access graph analytics")
            else:
                st.info("📈 Generate or load a graph first to access analytics")
        
        with tab5:
            if st.session_state.nodes:
                # Save to Neo4j section
                st.subheader("💾 Save to Neo4j")
                
                graph_name = st.text_input("Graph Name", value="my_knowledge_graph")
                graph_description = st.text_area("Description", 
                                                placeholder="Brief description of this knowledge graph",
                                                height=70)
                
                if st.button("💾 Save to Neo4j", use_container_width=True):
                    if not st.session_state.neo4j_connected:
                        st.warning("Please connect to Neo4j first")
                    elif not graph_name.strip():
                        st.warning("Please enter a graph name")
                    else:
                        with st.spinner("Saving graph to Neo4j..."):
                            conn = st.session_state.neo4j_conn
                            success, error = conn.save_graph(
                                graph_name.strip(), 
                                graph_description.strip() or "No description provided",
                                st.session_state.nodes, 
                                st.session_state.edges
                            )
                            
                            if success:
                                st.success(f"✅ Graph '{graph_name}' saved successfully!")
                            else:
                                st.error(f"❌ Failed to save graph: {error}")
                
                # Export section
                st.divider()
                st.subheader("📤 Export Graph")
                
                export_format = st.selectbox(
                    "Select export format:",
                    ["JSON", "CSV (Nodes & Edges)", "GraphML"],
                    help="Choose the format for exporting your knowledge graph"
                )
                
                export_name = st.text_input(
                    "Export filename:",
                    value="knowledge_graph",
                    help="Name for the exported file(s)"
                )
                
                if st.button("📥 Export Graph", type="secondary", use_container_width=True):
                    if not export_name.strip():
                        st.warning("Please enter a filename")
                    else:
                        filename = export_name.strip()
                        
                        if export_format == "JSON":
                            # JSON Export
                            json_data = export_graph_json(st.session_state.nodes, st.session_state.edges, filename)
                            st.download_button(
                                label="💾 Download JSON",
                                data=json_data,
                                file_name=f"{filename}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                            st.success(f"✅ JSON export ready for download!")
                            
                        elif export_format == "CSV (Nodes & Edges)":
                            # CSV Export
                            nodes_df, edges_df = export_graph_csv(st.session_state.nodes, st.session_state.edges)
                            
                            # Convert to CSV strings
                            nodes_csv = nodes_df.to_csv(index=False)
                            edges_csv = edges_df.to_csv(index=False)
                            
                            col_csv1, col_csv2 = st.columns(2)
                            with col_csv1:
                                st.download_button(
                                    label="💾 Nodes CSV",
                                    data=nodes_csv,
                                    file_name=f"{filename}_nodes.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            with col_csv2:
                                st.download_button(
                                    label="💾 Edges CSV",
                                    data=edges_csv,
                                    file_name=f"{filename}_edges.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            st.success(f"✅ CSV exports ready for download!")
                            
                        elif export_format == "GraphML":
                            # GraphML Export
                            graphml_data = export_graph_graphml(st.session_state.nodes, st.session_state.edges, filename)
                            st.download_button(
                                label="💾 Download GraphML",
                                data=graphml_data,
                                file_name=f"{filename}.graphml",
                                mime="application/xml",
                                use_container_width=True
                            )
                            st.success(f"✅ GraphML export ready for download!")
            else:
                st.info("📊 Generate or load a graph first to access save and export options.")
    
    with col2:
        st.header("🌐 Knowledge Graph Visualization")
        
        if st.session_state.nodes:
            # Graph configuration
            config = Config(
                width=800,
                height=600,
                directed=True,
                physics=True,
                hierarchical=False,
            )
            
            # Display the graph
            try:
                return_value = agraph(
                    nodes=st.session_state.nodes,
                    edges=st.session_state.edges,
                    config=config
                )
                
                # Display selected node info
                if return_value:
                    st.subheader("Selected Node Information")
                    try:
                        # Handle the return value more safely
                        if isinstance(return_value, dict):
                            st.json(return_value)
                        elif isinstance(return_value, str):
                            # Try to parse if it's a JSON string
                            import json
                            parsed_value = json.loads(return_value)
                            st.json(parsed_value)
                        else:
                            st.write("Selected:", return_value)
                    except json.JSONDecodeError:
                        st.write("Selected item:", str(return_value))
                    except Exception as e:
                        st.write("Selection data:", str(return_value))
            except Exception as e:
                st.error(f"Error displaying graph: {e}")
                st.info("Try refreshing the page or regenerating the graph")
        else:
            st.info("👆 Generate a graph to see the visualization here")
    

if __name__ == "__main__":
    main()